# Code review: URL outreach implementation (`outreach/`) — November 15, 2026

Reviewer: Cursor agent plus an independent reviewer subagent. Review was read-only; no
project code was changed. This file is the hand-off for fixing the findings below.

## Instructions for the implementing agent

- Follow `AGENTS.md` first: read `scope.md`, `docs/SOURCE_PROVENANCE.md`,
  `docs/CODEBASE_REVIEW.md`, and recent `CHANGELOG.md` entries before changing code.
- Do not run Git mutations: this folder is untracked inside an unrelated parent repo.
- Never make live Apollo, Anthropic, Google Sheets, or job-page requests. Use fakes,
  fixtures, and `tmp_path`. Do not set `allocation_confirmed: true`.
- Use test-driven development: write the failing test for each issue, watch it fail,
  fix, watch it pass. Keep fixes inside the existing CLI / service / client / store
  boundaries and match the surrounding code style.
- Run the full suite after each fix:
  `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`
  (baseline: 686 passed).
- Append one `CHANGELOG.md` entry per coherent fix (files, reason, verification,
  unresolved issues). Never edit earlier entries. Update `scope.md` if status changes.
- Re-run the dry-run safety check at the end (see "Dry-run safety" below).

Suggested order: Issue 5 (test isolation) first so later test runs cannot touch
`profile.md`, then Issues 1 and 2 (required before any live run), then 3 and 4, then minors.

## Baseline facts verified during review

- Full suite in `.venv`: 686 passed.
- 76 of 79 upstream files are byte-identical to the ZIP; `README.md`, `.gitignore`,
  `.env.example` were modified.
- Resume freshness guard passes for all three profiles (6 facts, 8 restrictions each).
- Concurrency of `Store.reserve`: 40 racing processes, limit 5 → exactly 5 reservations.
- No Anthropic/Apollo/Google retries; only Apollo is called; `.env` is loaded from an
  explicit project path, only on live paths.
- `CHANGELOG.md` has no implementation entries, although `scope.md` says checkpoints 1–7
  are implemented and refers to them. Do not invent past entries; log your own work.

## Dry-run safety (verified safe; keep it that way)

Five `--dry-run` variants were run with sockets disabled and, separately, under a
`sys.addaudithook` that fails on any socket connect, `getaddrinfo`, mkdir, rename, remove,
chmod, `mkstemp` or write-mode open. None tripped. `local-data/` was not created.

| Command | Exit |
|---|---|
| `--company-url https://example.com --target-role "Software Engineer" --dry-run` | 0 |
| same + `--draft-email --application-status interested` | 0 |
| `--company-url https://example.com --target-role "AI Software Engineer" --draft-email --dry-run` | 2 (choose `--profile`) |
| `--job-url https://boards.greenhouse.io/acme/jobs/123 --dry-run` | 2 (needs fetch) |
| `--sync-sheet --dry-run` | 0 |

Gap: existing dry-run tests only check that the working directory is empty, so they would
not catch a write under the project root. Add a test that installs an audit hook (or
monkeypatches `socket.socket.connect`, `socket.getaddrinfo`, `os.open`, `os.mkdir`,
`tempfile.mkstemp`) and asserts nothing fires for each variant above.

---

## Important issues

### Issue 1 — Wrong employer domain is marked "confirmed" (fix before live use)

**Where:** `outreach/context.py` lines 113–121 (`resolve_context`, employer from
`hiringOrganization`).

**What's wrong:** The employer domain is taken from `hiringOrganization.sameAs` first,
then `url`, using the full hostname. Job pages commonly set `sameAs` to a LinkedIn company
page, and `url` to an ATS board or careers subdomain.

- `sameAs: https://www.linkedin.com/company/acme` → `company_domain = linkedin.com`,
  evidence confidence `confirmed`. Apollo then searches LinkedIn employees, and
  `employer_check` after enrichment passes because `linkedin.com == linkedin.com`.
- `url: https://boards.greenhouse.io/acme` → `company_domain = boards.greenhouse.io`.
- `careers.acme.com` never equals Apollo's `primary_domain` (`acme.com`).
- Supplying `--company-url https://acme.com` to correct it raises
  `NeedsContext('Explicit company conflicts with job employer ...')`.
- `sameAs` may be a list; that case is currently ignored silently.

**Impact:** Up to 3 paid enrichments per job on the wrong company, with drafts labelled
employer-confirmed. This defeats the main safety check.

**Reproduce (offline):**

```python
import json
from outreach.models import Request
from outreach.context import resolve_context
page = '<script type="application/ld+json">' + json.dumps({"@type": "JobPosting", "title": "Software Engineer",
  "hiringOrganization": {"@type": "Organization", "name": "Acme", "sameAs": "https://www.linkedin.com/company/acme"},
  "description": "Build the platform"}) + '</script>'
ctx = resolve_context(Request(job_url="https://boards.greenhouse.io/acme/jobs/123"), fetch=lambda u: page)
print(ctx.company_domain, ctx.evidence[0].confidence)   # observed: linkedin.com confirmed
```

**Fix:**
- Prefer `url` over `sameAs`; accept `sameAs` as a string or list.
- Reject social and ATS hosts as employer domains (linkedin.com, facebook.com, x.com,
  twitter.com, instagram.com, glassdoor.com, indeed.com, plus `ATS_HOSTS`).
- Normalize both sides to the registrable domain before comparing (`careers.acme.com`
  → `acme.com`). Without adding a dependency, at minimum strip known prefixes such as
  `careers.`, `jobs.`, `www.`; document the limitation.
- An explicit `--company-url` wins over a rejected or ATS/social value instead of
  raising a conflict. Keep the conflict error only for two real, different employer domains.
- If no trustworthy employer domain remains, raise `NeedsContext` asking for `--company-url`.

**Tests to add:** LinkedIn `sameAs` → NeedsContext (no company URL) or uses the explicit
company URL; ATS `url` → same; `careers.acme.com` vs `--company-url https://acme.com` →
no conflict, domain `acme.com`; list-valued `sameAs`; genuine conflict still raises.

### Issue 2 — No way to recover from an uncertain attempt or a stuck claim (fix before live use)

**Where:** `outreach/store.py` line 67 (`reserve` refuses keys with `pending`/`uncertain`
attempts); `outreach/sheets_queue.py` lines 99–101 and 110–111 (claims in `processing`).

**What's wrong:** One Apollo timeout on a search marks that key (domain + roles + page)
uncertain forever, so that company can never be searched again. The same happens to an
enrichment ID or draft key, and to a Sheet row whose claim is stuck in `processing`. A
crash between `reserve` and `finish` leaves `pending` forever. `docs/URL_OUTREACH_GUIDE.md`
says to reconcile, but no command exists, and editing the DB by hand is the only way out.

**Reproduce (offline):**

```python
from pathlib import Path
from outreach.settings import Settings
from outreach.store import Store
from outreach.service import run
from outreach.models import Request
from outreach.apollo import ProviderError
s = Settings(project_root=Path('.').resolve(), state_path=Path('/tmp/r2/state.db'),
             output_dir=Path('/tmp/r2/out'), allocation_confirmed=True)
store = Store(s.state_path, s)
class Apollo:
    calls = 0
    def search(self, *a):
        self.calls += 1
        raise ProviderError('Apollo transport failure; outcome uncertain', uncertain=True)
    def enrich(self, ids): return {}
apollo = Apollo()
req = Request(company_url='https://example.org', target_role='Full Stack Engineer')
fetch = lambda _: '<p>x</p>'
print(run(req, settings=s, store=store, fetch=fetch, apollo=apollo).review_flags)
print(run(req, settings=s, store=store, fetch=fetch, apollo=apollo).review_flags, apollo.calls)
# observed: second run makes 0 new Apollo calls and reports
# 'Previous provider attempt requires manual reconciliation' (permanent)
```

**Fix:** Add explicit CLI reconciliation:
- `--list-pending`: prints attempt id, kind, day, status and created_at for `pending` and
  `uncertain` attempts and for `processing` claims. No contact data, emails, or payloads.
- `--reconcile ATTEMPT_ID --as error|done`: moves a `pending`/`uncertain` attempt to a
  terminal status. Never refunds daily usage (units stay counted). Requires an explicit
  `--confirm` flag. Writes an audit record (new table or appended payload note with
  timestamp and previous status). `--as done` must not create a cache entry unless a
  payload is supplied; prefer offering only `error` in v1.
- `--release-claim CLAIM_ID --confirm`: marks a stuck `processing` claim as released so
  the row can be re-claimed under a new `requeue_token`.
- Update `docs/URL_OUTREACH_GUIDE.md` with the recovery procedure.

**Tests to add:** reconcile clears the block and a later run can retry; usage count is
unchanged by reconcile; unknown ID and non-pending status error clearly; without
`--confirm` nothing changes; claim release allows reprocessing only with a new token.

### Issue 3 — Sheet sync strands claims on unexpected exceptions

**Where:** `outreach/sheets_queue.py` lines 109–120 (`QueueProcessor.sync`).

**What's wrong:** Only `InputError` from `self.process(request)` is caught. Any other
exception (for example `AccountingUnavailable` when the DB is locked longer than 5 s)
leaves both the operation claim and the base claim in `processing`, and aborts the whole
sync. The next sync marks that row `error` and gets stuck the same way on the next row.
A failed `write_status(... 'processing')` at line 115, before any provider work, also
strands the claim.

**Reproduce:** Use a fake `sheet` (in-memory `read_queue`/`write_status`/`write_results`)
and a `process` that raises `RuntimeError` for row `r1`. Observed: claim for `r1` stays
`processing`; the next sync writes `error` for `r1` and strands `r2`.

**Fix:** Wrap `process` in a catch-all that records a terminal error payload in both
claims (status not `processing`), writes an `error` status to the row, increments
`summary['errors']`, and continues. Write the `processing` status before claiming, or
release the claims if that status write fails. Keep the "no automatic paid retry" rule:
a released/errored claim is reprocessed only after a new `requeue_token`.

**Tests to add:** exception in `process` → claims not `processing`, sync continues to
the next row; failing status write before processing leaves no stuck claim.

### Issue 4 — Deduplication and repeated-email flagging are incomplete

**Where:** `outreach/service.py` line 79 (dedupe by `apollo_id` only) and lines 101–104
(`duplicate_email` only inside the drafting branch, only within one run).

**What's wrong:** `scope.md` requires deduplicating Apollo IDs and normalized profile
URLs and flagging repeated emails across distinct identities. Today:
- Two Apollo IDs with LinkedIn URLs `https://www.linkedin.com/in/alex/` and
  `http://linkedin.com/in/Alex` are both enriched (two credits).
- Without `--draft-email`, duplicate emails are never flagged; repeats across jobs or
  runs are never flagged.

**Fix:**
- Normalize `linkedin_url` with the existing `shared.linkedin_url.normalize_linkedin_url`
  and dedupe search records by normalized URL as well as by ID, before ranking and
  enrichment.
- Flag `duplicate_email` for every enriched person, whether or not drafting is on.
- Persist seen (normalized email → apollo_id) in SQLite so repeats are flagged across
  jobs and runs. Do not store more contact data than needed.

**Tests to add:** URL variants → one enrichment; same email from two IDs without
drafting → flag; same email in a second run → flag.

### Issue 5 — Tests can rewrite the real `profile.md`

**Where:** `tests/test_url_outreach_service.py` line 12 (`project_root` is the real
project) with `draft_email=True` at line 31; `outreach/service.py` line 67 calls
`load_candidate(..., refresh=True)`; `outreach/profile.py` lines 74–77 atomically
rewrite `root/'profile.md'` when an original resume's active text changed. The
acceptance dry-run test also reads the real resumes and real `local-data`.

**Impact:** After Hardik edits any of the three resumes, running `pytest` modifies his
personal `profile.md` and the test fails. The suite is not hermetic.

**Fix:** Build a fixture project in `tmp_path` (minimal `profile.md`,
`config/outreach_profile_sources.yaml` with matching hashes, three small `.tex` files)
and point `project_root`, `state_path` and `output_dir` there in every outreach test.
Add a guard test that the real `profile.md` hash is unchanged after the suite runs.

---

## Minor issues

| Where | Problem | Suggested fix |
|---|---|---|
| `outreach/ranking.py` lines 13–15 | Substring matching: `'cto' in 'director of marketing'` is true, so `--contact-roles cto` selects any Director | Match titles on word boundaries (`re.search(r'\b' + re.escape(t) + r'\b', title)`) |
| `outreach/service.py` lines 99–100 | Employer mismatch also produces a misleading `persona_mismatch` flag, because `rank_people` drops mismatches | Check persona by title only for this flag |
| `outreach/main.py` line 111 | Output lacks the scope's attempted / found / not found / failed / skipped / remaining counts | Add these counts to the JSON summary |
| `outreach/main.py` line 105 | `--sync-sheet` always exits 0, even with row errors or budget waits | Non-zero exit when `summary['errors']` > 0 |
| `outreach/main.py` line 81 | `--export-run` constructs `Store`, creating `local-data/` and the DB if missing | Open read-only for export; error if DB missing |
| `outreach/drafting.py` line 45 | Anthropic timeout hard-coded to 60 s | Read from settings |
| `outreach/drafting.py` lines 53–57 | Local exceptions before sending (e.g. `TypeError`) are labelled uncertain, permanently blocking the draft key | Only network/5xx/timeout are uncertain; programming errors are not |
| `outreach/store.py` line 129 | `with sqlite3.connect(...)` does not close the connection | Use `contextlib.closing` |
| `outreach/export.py` line 59 | CSV formula escaping skips values starting with `\t` or `\r` | Include `\t`, `\r` in the prefix check |
| `outreach/service.py` lines 127–143 | Preview: no profile freshness check for job-URL-only input; disabled allocation gate exits 0; malformed profile YAML exits 4 with `KeyError` | Report allocation gate in `missing_context` or a warning; map YAML/KeyError to `ProfileNeedsReview` |
| `outreach/apollo.py` lines 83–85 | `reveal_*` / `run_waterfall_*` sent in the JSON body; Apollo documents them as query parameters (legacy client does the same; unverified offline) | Confirm against Apollo docs; send as query params if needed |
| `outreach/apollo.py` / fixtures | Fixtures invent `employment_history[].organization_domain`; real data falls back to `organization_id` (fails safe) | Align fixtures with documented response shape; consider skipping enrichment when search says `has_email: false` |
| `outreach/context.py` line 63 | `sorted(addresses)[0]` may pick IPv6 on an IPv4-only network → spurious fetch failure | Prefer IPv4 or try addresses in order |
| `outreach/ranking.py` | `hiring_manager` and `engineering_manager` use identical title sets; target role and JD only break ties via `team_terms` | Design note; consider using the target role in search/ranking later |

## Definition of done

- Every Important issue has a failing test first, then a fix; full suite passes.
- Dry-run audit-hook test passes for all five variants above; `local-data/` is not created.
- The real `profile.md` is unchanged by running the suite.
- `docs/URL_OUTREACH_GUIDE.md` documents the reconcile/release commands.
- `CHANGELOG.md` has one appended entry per fix with verification; `scope.md` updated.
- No live calls, no `allocation_confirmed: true`, no Git mutations.
