# URL outreach pilot

Status: v2 drafting and mixed URL intake are offline-verified, November 15, 2026
(Chicago). A bounded v1 Apollo/Claude run passed. The v2 live comparison and Google
Sheet API write-back still await final acceptance and Google credentials. No sender
or background polling is included. See GOOGLE_SHEETS_SETUP.md for the remaining setup.


## Normal input — one cell

In the existing Queue, fill only column C (`job_url`). The simple API layout calls
this column `input`. Accepted examples:

- A personal LinkedIn URL: fetch that person's professional email.
- A LinkedIn post URL: resolve one explicit public personal author and look up their
  email. If inaccessible/ambiguous, request the personal profile URL before any spend.
- A LinkedIn /jobs/view/ URL: use the normal job workflow with the company website.
- `Jordan Blake | Northstar`: fetch the named person's email; company can instead go
  in column D (`company_url` / `company`) as a name or website.
- A job URL: discover one relevant contact and prepare a job-specific email draft.
- A company homepage: target software-engineering networking using the global default.

Everything else is optional. Blank IDs and readiness are generated; an explicit FALSE
can still hold a row. Simple rows automatically version actual input edits on the next
on-demand sync, without a manual requeue token. Unchanged input reuses saved results.
There is no background watcher and no automatic retry of uncertain provider requests.
Defaults live once in `outreach/settings.yaml`: one contact, Software Engineer when no
vacancy is supplied, drafts on for job/company discovery, email-only for known people.
Application/attachment assertions still default to unconfirmed. Explicit row overrides
remain available. Simple profile choice prefers Accessibility, then AI/FDE/Amazon,
then Full Stack; original resume sources and claim restrictions remain authoritative.

The CLI accepts the same input directly, without Google access:

```bash
.venv/bin/python -m outreach.main 'https://linkedin.com/in/jordan-blake' --dry-run
.venv/bin/python -m outreach.main 'Jordan Blake | Northstar' --dry-run
.venv/bin/python -m outreach.main 'https://employer.example/jobs/123' --dry-run
```

Once Google API authentication is connected, run `--setup-sheet` once to rename the
input/company headers and show only input, optional company/notes and status. It hides
advanced columns without deleting data and uses one API batch, not browser automation.
`--setup-sheet --dry-run` makes no network calls or writes. Routine sync does not repeat
layout work. Known-person lookup uses Apollo people/match and needs that key permission;
ID-based discovered contacts retain bulk_match. No fallback spend is added.

## Setup

Run commands from `Apollo Email Extraction Outreach Specialist`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-pilot-dev.txt
```

For Sheets, also install the optional adapter dependencies:

```bash
.venv/bin/python -m pip install -r requirements-sheets.txt
```

The existing project `.env` is loaded explicitly for live commands; it is never
overwritten by setup. Keep Apollo/Anthropic keys there, outside all Sheet cells.
Existing process environment values take precedence. Google credentials are needed
only for Sheet sync. Pin files record the tested direct dependency versions; transitive
dependencies are resolved by pip. Python 3.12 or newer is required.

## First use without spending

```bash
.venv/bin/python -m outreach.main --help
.venv/bin/python -m outreach.main --company-url 'https://example.org' --target-role 'Full Stack Engineer' --dry-run
.venv/bin/python -m outreach.main --job-url 'https://example.org/jobs/1' --dry-run
```

Strict dry-run performs no network calls, reservations or file writes. A job URL alone
returns a needs-fetch preview (exit 2), since an offline command cannot read its JD.
A Sheet dry-run checks local configuration/budgets only; it does not fetch rows.

## Live URL inputs, after the account allocation is agreed

`outreach/settings.yaml` defaults to `allocation_confirmed: false`. Agree Hardik's
share of the paid account first, set conservative limits, then set that flag true.
That setting is a deliberate local gate; it cannot measure or control the friend's
separate account usage. For the first authorized live test, set contact/run limits
to one and request at most one draft.

```bash
.venv/bin/python -m outreach.main --job-url 'https://employer.example/jobs/123' --draft-email
.venv/bin/python -m outreach.main --company-url 'https://employer.example' --target-role 'Full Stack Engineer' --profile fullstack --draft-email
```

For a blocked/JavaScript-only job page, supply `--job-description-file` together with
`--company-url` and `--target-role`. The file must be UTF-8, at most 200 KB. No automated
browser login or paid web-search fallback is attempted. A company/role request without
a job URL is role-targeted networking; it does not establish an open vacancy.

Other flags: `--contact-roles technical_recruiter,engineering_manager,cto,ceo`,
`--max-contacts`, `--profile auto|fullstack|amazon|accessibility`, `--application-status
unknown|interested|applied`, `--resume-attached`, `--notes`, `--settings`, `--output-dir`.
CEO/CTO are explicit selections. The default personas are recruiters and manager/HM
candidates; title/company matches do not prove hiring authority or team membership.

## Shared Sheet — exact first-version contract

The supplied workbook already has `Queue` and `Results` with verified headers:
https://docs.google.com/spreadsheets/d/1a4nOTFRZcjvLsUmJxcCrnkTG78spVdd6lmfODdvnN7U/edit

Google API authentication is still required. For another workbook, create these tabs and paste/import
row 1 from these header-only files; headers are matched by name and can be reordered:

- `config/sheets_queue_headers.csv`
- `config/sheets_results_headers.csv`

The credential identity needs Editor access to this workbook to write statuses/results.
Enable Google Sheets API for its project. Set `GOOGLE_APPLICATION_CREDENTIALS` to the
ignored service-account JSON path and `SHEET_ID` to the workbook ID from its URL. Do not
put credentials in the workbook or change the existing Apollo/Anthropic keys. A shared
link alone does not authenticate the code.

| Queue field | What you enter |
| --- | --- |
| `row_id` | Automatic; leave blank for normal entry |
| `ready` | Blank is ready for the next explicit sync; FALSE optionally holds a row |
| `job_url` | Job URL; sufficient if company/role/JD can be resolved |
| `company_url`, `target_role` | Both required when no job URL; also useful overrides |
| `job_description` | Optional pasted JD, preferred over fetched text |
| `profile` | Optional explicit resume choice; `auto` by default |
| `contact_roles` | Optional comma/semicolon-separated personas from CLI choices |
| `max_contacts` | Optional integer within configured cap; default 1 |
| `draft_email` | TRUE to request a Claude email; blank/FALSE means no Claude call |
| `application_status` | `unknown` by default; set `applied` only if true |
| `resume_attached` | Blank/FALSE by default; TRUE explicitly permits attachment wording |
| `notes` | Optional case context treated as data |
| `requeue_token` | Leave blank initially; change to a new value after reviewing an edit/retry |

Keep tool-owned columns `status`, `processed_hash`, `run_id`, `processed_at`, `error`.
Results contains one row per contact/job or a source-level row for unresolved requests,
including email/status, evidence, draft subject/body and provenance. No-match, blocked
or budget-limited work remains visible. Results are never sent as messages.

```bash
.venv/bin/python -m outreach.main --sync-sheet
.venv/bin/python -m outreach.main --sync-sheet --sheet-id WORKBOOK_ID
.venv/bin/python -m outreach.main --sync-sheet --dry-run
.venv/bin/python -m outreach.main --preview-sheet
```

The first two commands are live processing, not previews. They are run on demand after
you say the ready rows can be processed. `--preview-sheet` authenticates and reads the
workbook to validate rows, but makes no Apollo/Claude calls, reserves no quota and writes
no Sheet/local state. It needs Google access but no paid-provider keys/allocation flag.
Strict `--dry-run` does not even read the Sheet. Nothing watches it while chat is idle.

Simple entries automatically requeue real input edits at the next requested sync. For legacy advanced rows with manual readiness, editing a completed row marks it `changed`;
it does not itself authorize another paid attempt. After reviewing, change
`requeue_token` (for example to `reviewed-2`) to authorize processing that version.
Readiness toggles between syncs cannot reliably be observed. Waiting/error outcomes
also need explicit requeue when their missing context, quota or error has been resolved.

Use one worker for a workbook. Local claims prevent duplicate submissions; they are
not a lock shared across computers. Queue status writes re-find the row ID and verify
the input hash, but Sheets has no atomic compare-and-swap between that read and write.
Avoid sorting/editing the Queue while a sync is actively updating it. Input cells are
not overwritten. A later sync detects changed versions.

## Spending, cache and recovery

Default limits: 5 enrichment submissions/day and 5/run; 3 contacts/job; 1 search page
of 25/job and 5 search requests/day; 3 draft attempts/run and 5/day. The run limits
apply to an entire Sheet sync, not independently to each row. Search/enrichment/draft
counts are separate from actual provider credits. Failed and uncertain attempts count.
The budget day is `America/Chicago`, including DST. Configure limits in one YAML file.

SQLite at `local-data/state.sqlite3` is the usage/recovery authority. **Do not delete,
move or replace it to fix a quota error**: that would discard accounting and can cause
repeat spending. Back up the private state file with normal project data. Caches expire
after 7 days; repeated current lookups/drafts reuse results. No-match is cached too.
Identical contacts across different jobs reuse enrichment, with separate job drafts.

Timeout/crash outcomes remain uncertain and are not automatically retried. Stop active
workers and check provider usage/results before running explicit local recovery:

```bash
.venv/bin/python -m outreach.main --list-pending
.venv/bin/python -m outreach.main --reconcile ATTEMPT_ID --as error --confirm
.venv/bin/python -m outreach.main --release-claim CLAIM_ID --confirm
```

Pending listings contain IDs/kinds/states/timestamps, never contact payloads.
Reconciliation moves a pending/uncertain attempt to error, retaining its counted units.
It creates no cache, makes no provider call and does not claim the attempt was free.
A later retry is a new budgeted request and may spend again. Marking done without a
verified result payload is intentionally unsupported in v1.

Claim release covers the stuck row and its related operation claim. Change the row's
`requeue_token` to a new nonempty value before reprocessing. A token alone cannot clear
an uncertain provider attempt: reconcile that separately when appropriate. Both commands
require `--confirm` and append timestamped audit records with previous/new states.
They need an existing local database but no provider/Google keys or allocation approval.
Caught processing errors terminate claims; no automatic paid retry occurs. If accounting
stays unavailable, processing stops; restore it before recovery. Stale completions cannot
overwrite a newer input version. Fully automatic uncertain-result recovery remains
excluded. Completed lookups/drafts survive ordinary export or Sheet-write failures.

```bash
.venv/bin/python -m outreach.main --export-run RUN_ID
.venv/bin/python -m outreach.main --resume-run RUN_ID
```

Export-only requires no provider keys. Resume uses saved input and existing caches,
obeys current limits and never automatically resends uncertain requests. A resumed run
has a new run ID. Results Sheet write failures can be retried with a normal sync; saved
result IDs are reconciled before append. CSV values are protected against spreadsheet
formula execution; JSON preserves original values. Both are private local files.

## Profile freshness and draft review

Only the three approved original TeX files are read. `profile.md` keeps reviewed facts
and restrictions; YAML stores source paths and reviewed active-text hashes, not another
biography. Full Stack keeps the older BIG implementation. Accessibility uses the newer
BIG facts; Simple entries select the more specific AI profile for AI/SWE overlaps; advanced explicit profile overrides still win.

The first version checks the entire active body of all three originals conservatively,
rather than attempting automatic semantic approval of individual changed facts. Comment
changes do not invalidate active text. If active content changes, a drafting run refreshes
generated source-review excerpts in the private `profile.md` and stops before paid calls.
Review/update the affected facts and source hashes locally before drafting again. Dry-run
reports staleness without writing anything. Per-section refresh is not implemented yet.

One Claude call per new requested recipient/job uses Opus 5.5 high, the complete approved
style prompt including both examples, and up to six relevant reviewed facts. No extra
ranking/critic call. SDK retries are disabled. Missing email, unknown/mismatched current
employment or incompatible persona prevents drafting. Local format and wording checks
flag problems but cannot guarantee factual perfection or exact personal voice; review
the draft before manual sending. The first real draft still needs style calibration.

Exit codes: 0 complete, 2 invalid/missing context, 3 budget/accounting/allocation gate,
4 provider/uncertain operation failure. Sheet sync returns nonzero for errors (4),
budget waits (3), and changed rows awaiting requeue (2), including retained error outcomes
on repeat sync. Check row statuses for individual outcomes. Runtime logs do not print
keys or contact bodies.

## Verification

```bash
.venv/bin/python -m pytest tests/test_url_outreach_*.py -q
.venv/bin/python -m pytest -q
```

New tests use fictional identities, fake Apollo/Sheets clients, real temporary SQLite
files and the real Anthropic SDK with a mock HTTP transport. They spend zero credits.
The inherited requirements are separate; `requirements-pilot-dev.txt` installs the
new route, and `requirements-sheets.txt` adds Google dependencies for the full suite.


## Review hardening — November 15, 2026

- Social/ATS hosts cannot be employer domains. Organization URL is preferred over
  string/list `sameAs`; explicit real company URLs can resolve rejected metadata.
  Known `www`, `jobs`, `careers`, `career`, `apply` prefixes are normalized. This is
  not a public-suffix parser; arbitrary subdomains may need the canonical company URL.
- Candidate deduplication uses Apollo IDs and normalized personal LinkedIn URLs before
  enrichment. Duplicate-email warnings are independent of drafting and survive restart
  using email fingerprints plus IDs. An explicit `has_email: false` skips enrichment;
  missing hints remain unknown. Duplicate flags do not prove two distinct people.
- Apollo search filters and enrichment reveal/waterfall switches are query parameters;
  only enrichment `details` goes in the JSON body. All reveal/waterfall switches stay off.
- Single-URL summaries include new enrichment attempts, found/not-found, failed provider
  attempts, skipped profiles, per-operation attempts and remaining local budgets. Found
  counts can include cached results; attempted counts are new submissions, not credits.
- `draft_timeout_seconds` configures Claude separately (default 60). SDK retries stay off.
  Local argument errors are terminal errors; connection/timeouts/server errors remain
  uncertain. Export opens saved state read-only and fails without creating a missing DB.
- Drafting previews check all source hashes even before a job URL can be fetched.
  Allocation-disabled is a warning so no-spend validation stays usable. Malformed source
  manifests produce a profile-review result. Strict dry-run still makes zero writes or
  network calls. Tests use fictional projects; the real profile is guarded against edits.


## Network environments with an HTTP proxy

Public-page fetching honors HTTP_PROXY/HTTPS_PROXY and NO_PROXY. When local DNS is
unavailable in a proxied runtime, it resolves the public hostname through Google DNS
over HTTPS, rejects non-public answers, and opens a proxy CONNECT tunnel to the
checked IP. HTTPS certificate validation/SNI still use the original page hostname.
Every redirect is checked again. There is no direct-connection fallback after proxy
failure. The supported proxy endpoint is HTTP without embedded credentials; unsupported
proxy configuration fails closed. Direct runtimes retain local DNS/IP pinning.

A public workbook can be inspected through its CSV export without Google credentials.
The GoogleQueue API adapter, result writes and one-time layout setup still require
Google Application Default Credentials or GOOGLE_APPLICATION_CREDENTIALS. Link-edit
sharing alone does not authenticate the Sheets API. Local CSV/JSON exports allow a
bounded acceptance test before that write-back connection is configured.


## Job/company reuse

Use only job URL and company URL in Queue. A sync checks saved outcomes before any
website/provider request. Canonical matching normalizes company hosts and job tracking
parameters while preserving meaningful query job IDs. Exact completed duplicates
receive their own result/run record and Queue status reused. The prior contact and
draft are copied with zero provider calls. This applies across appended rows/restarts.

For a new job at the same company, fresh confirmed-employer contacts with emails are
re-ranked against the requested personas. If sufficient contacts are available, Apollo
is skipped and Claude drafts for the new role. Old team certainty is not carried to a
different job. A matching employer/title does not establish the actual hiring manager.
Original enrichment expiry is retained. Expired/unsuitable saved data requires reviewed
refresh; a normal sync does not silently pay to refresh it. No automatic refresh command
or background monitor is introduced in this version.

Changed notes, application/attachment flags, profile/source text, prompt/model or output
budget invalidate completed-job reuse. Existing unchanged Queue claims still republish
their saved outcomes; to regenerate an already processed row deliberately, edit its
input/version following the recovery instructions. Appended rows use current dependencies.

Run --setup-sheet once after connecting Google credentials to append selection_reason,
reuse_type and reused_from_run_id to Results. Existing headers/data are retained;
older 27-column tabs remain readable. CSV/JSON exports include reuse fields immediately.
New rows are processed by --sync-sheet; this does not itself install a scheduler.

The local ledger is the durable authority for reuse, quotas and reconciliation.
A different machine/ephemeral runner needs a state-persistence design before reuse can
be assumed; Notion input and runner deployment are deferred to phase 2.


## V2 review and final acceptance

The active v2 prompt/profile/model/web-search settings are included in completed-job
and draft cache identities. Automatic Sheet rows also version successful work when
these dependencies change, so an older processed row cannot silently serve a v1 draft.
Failed/interrupted claims still require explicit recovery; a prompt edit is not retry
permission. Known-person enrichment caches are shared with/without the optional company
column; employer mismatches remain flagged and cannot receive automatic drafts.

The provider's max_uses cap applies across the whole paused tool turn; it is preserved
unchanged on the one allowed continuation. Draft flags now include api_requests:1 or
api_requests:2, plus any reported web searches and source URLs. Draft quota units count
logical drafts, not HTTP requests or an estimate of billable credits.

LinkedIn posts use only explicit public authorship metadata (JSON-LD posting author,
rel=author, article:author). Slugs, commenters and unrelated profile links are not used.
A post is not a verified vacancy. Post/personal-profile rows remain email-only unless
an optional draft_email override requests a v2 networking draft.

For final test inputs and Google API setup, read [GOOGLE_SHEETS_SETUP.md](GOOGLE_SHEETS_SETUP.md).
All remaining output/status fields are written by --sync-sheet through the API. Appending
rows alone does not start a worker; scheduling/hosting is a separate phase.
