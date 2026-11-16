# URL-based job outreach implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Work inline unless Hardik requests delegation.

**Goal:** Accept one job URL, or a company website plus target role, and produce a small evidence-labelled contact shortlist, professional emails where available, and optional job-specific cold-email drafts for manual review.

**Architecture:** Add a thin `outreach` CLI and service using focused URL-context, Apollo, profile, drafting, and local-storage modules. Reuse the existing LinkedIn normalizer and Apollo request conventions without routing the new workflow through the legacy Sheets-dependent service. Use one SQLite ledger/cache and export CSV plus JSON; future spreadsheet imports call the same service.

**Tech Stack:** Python 3.12+, requests, BeautifulSoup, PyYAML, python-dotenv, Anthropic SDK, SQLite and csv/json from the standard library, pytest with fake transports and temporary databases.

**Spec:** `docs/OUTREACH_WORKFLOW_PLAN.md`, governed by `scope.md`; approved writing prompt in `claude_cold_email_prompt_v1.md` and candidate context in `profile.md`.

## Global constraints

- Execution status: checkpoints 1–7 are implemented and offline-tested. Checkpoint 8 is complete offline; real Sheet/provider acceptance remains pending. See the execution record and CHANGELOG for actual evidence.
- First release processes job/company requests through CLI or the approved shared Sheets queue; CSV/XLSX file import and outcome analytics are follow-on work.
- Defaults: 5 enrichment submissions/day and 5/run; 3 selected contacts/job; 1 search page/job, 25 results/page, 5 search requests/day; 3 draft attempts/run and 5/day. All values live in `outreach/settings.yaml` and must be positive integers. Per-job caps cannot raise global caps.
- These are conservative local submission/request limits, not verified provider-credit allowances. Live mode additionally requires an explicitly recorded shared-account allocation; other tools on the shared account are outside this ledger.
- Budget days use `America/Chicago` via `zoneinfo`. Count attempts before sending, including timeouts, no-match and failed responses. No automatic retry or automatic refund of uncertain attempts.
- Apollo only; professional email only; no personal-email, phone, waterfall, Prospeo, or Apify calls in the new route.
- Draft model `claude-opus-5-5`, `output_config={"effort":"high"}`, initial `max_tokens=8192`, Anthropic `max_retries=0`. Verify installed SDK support before implementation acceptance; never silently substitute a model or effort.
- One logical draft request per recipient/job when `--draft-email` is present. No default extra Claude call for parsing, ranking, fact selection, critique, or each bullet.
- Include the full approved cold-email prompt and both examples, plus selected-profile supported facts and relevant job/recipient context. Three concise hyphen bullets by default; no invented application, attachment, team, or hiring relationship.
- Approved original resume paths: `../fullstack.tex`, `../Hardik_Lad_Resume_Amazon.tex`, `../FDE_accessibility.tex`. Do not duplicate or edit them; preserve separate BIG implementations and existing claim restrictions.
- A job/company match does not establish the actual HM or poster. Unknown and inferred relationships must be labelled and exported with evidence.
- `--dry-run` makes zero network calls, reserves no quota and writes no database, profile, or export files. It reports planned actions and unresolved context, not fictional contacts or drafts.
- Runtime credentials, contact data, raw payloads and exports stay in ignored local paths. Operational logs contain counts, IDs and safe error codes, not keys or full provider bodies.
- No sender, inbox reader, scheduler, browser scraping, paid web-search service or changes to the separate job scanner.
- Append `CHANGELOG.md` and update `scope.md` after every completed checkpoint with evidence and outstanding limits.
- The folder is a ZIP import inside an unrelated Git repository. Do not stage, commit, push or modify parent remotes. Establish the correct fork/clone before project commits; checkpoint completion does not depend on pretending the import is a fork.

## Deliverable and command contract

The commands below are implemented. Live mode remains gated on confirmed allocation; examples use fictional URLs.

```bash
python -m outreach.main --job-url 'https://jobs.example.org/roles/123' --dry-run
python -m outreach.main --job-url 'https://jobs.example.org/roles/123' --draft-email
python -m outreach.main --company-url 'https://example.org' --target-role 'Full Stack Engineer' --profile fullstack --draft-email
python -m outreach.main --job-url 'https://jobs.example.org/roles/123' --company-url 'https://example.org' --target-role 'Full Stack Engineer' --job-description-file './local-data/job.txt' --draft-email
python -m outreach.main --resume-run RUN_ID
python -m outreach.main --export-run RUN_ID --output-dir './local-data/exports'
```

`--job-url` may be supplemented by company/role overrides. Without a job URL, both company URL and target role are required. Other flags: `--profile auto|fullstack|amazon|accessibility`, `--max-contacts 1..3` within settings, `--contact-roles` as a comma-separated subset of `hiring_manager,technical_recruiter,engineering_manager,cto,ceo`, `--application-status unknown|interested|applied` (default unknown), `--resume-attached` (default false), `--settings PATH`, `--output-dir PATH`. Invalid combinations fail before network access.

Default requested personas are hiring-manager candidates, technical recruiters and engineering managers. CTO/CEO selection is explicit through `--contact-roles`; do not quietly use a CEO to fill an empty recruiter shortlist. Output identifies all unconfirmed hiring relationships as candidates.

Without `--draft-email`, no Anthropic key or Claude request is needed. Sheets credentials are never required for the new command. Load only the project `.env`, with existing environment variables taking precedence; do not search parent directories for another `.env`.

Exit codes: `0` completed, including genuine no-match; `2` invalid input or missing context; `3` exhausted budget or unavailable accounting; `4` provider failure/uncertain attempt with saved recovery state. Partial results remain exportable. Dry-run may exit `2` with a useful preview if context cannot be resolved without fetching.

## File map and shared interfaces

| File to create | Responsibility |
| --- | --- |
| `outreach/__init__.py`, `main.py`, `settings.py`, `settings.yaml` | CLI, explicit configuration, environment loading |
| `outreach/models.py` | Shared request, evidence, context, contact and result records |
| `outreach/store.py` | Atomic budgets, runs, lookup/draft cache, recovery |
| `outreach/context.py` | Safe fetching, job parsing and employer resolution |
| `outreach/apollo.py`, `ranking.py` | People search, ID enrichment, evidence-based ordering |
| `outreach/profile.py` | Source freshness, selected profile and restricted facts |
| `outreach/drafting.py` | Exact Claude request, output validation and safe errors |
| `outreach/service.py`, `export.py` | Orchestration, repeat-safe execution, CSV/JSON |
| `config/outreach_profile_sources.yaml` | Source paths, fact-to-section bindings and reviewed hashes; no duplicate resume text |
| `tests/test_url_outreach_*.py`, `tests/fixtures/url_outreach/` | Contract, provider, quota and end-to-end fixtures |
| `requirements-pilot.txt`, `requirements-pilot-dev.txt` | Minimal isolated dependency sets, exact versions after resolution |

Modify `.gitignore`, `.env.example`, `README.md`, `profile.md` (only refresh metadata/generated source excerpts), `scope.md`, this checklist and append `CHANGELOG.md` as relevant. Leave legacy runtime/settings untouched in this release. Explicitly document that its old CLI does not inherit the new guards.

Record declarations below specify frozen dataclasses in `models.py` (all listed fields required unless a default is shown):

```python
Evidence(kind: str, value: str, source_url: str, confidence: str)
Request(job_url: str | None = None, company_url: str | None = None,
        target_role: str | None = None, job_description: str | None = None,
        profile: str = "auto", max_contacts: int = 3,
        contact_roles: tuple[str, ...] = ("hiring_manager", "technical_recruiter", "engineering_manager"),
        application_status: str = "unknown", resume_attached: bool = False,
        draft_email: bool = False)
Context(company_name: str, company_domain: str, job_title: str,
        job_url: str | None, description: str, team_terms: tuple[str, ...],
        evidence: tuple[Evidence, ...])
Person(apollo_id: str, name: str, title: str, company_domain: str,
       linkedin_url: str | None = None, email: str | None = None,
       email_status: str = "unknown", employer_match: str = "unknown",
       team_match: str = "unknown", evidence: tuple[Evidence, ...] = ())
Candidate(profile: str, facts: tuple[str, ...], restrictions: tuple[str, ...],
          source_hashes: dict[str, str], profile_hash: str)
Draft(subject: str, body: str, review_flags: tuple[str, ...] = ())
Outcome(run_id: str, status: str, context: Context | None,
        people: tuple[Person, ...], drafts: dict[str, Draft],
        review_flags: tuple[str, ...])
```

Confidence/match values are `confirmed|inferred|unknown`, plus `mismatch` for employer match. Add `Settings` as a frozen dataclass in `settings.py` with these exact fields:

```python
@dataclass(frozen=True)
class Settings:
    project_root: Path
    state_path: Path
    output_dir: Path
    timezone: str = "America/Chicago"
    enrich_daily_limit: int = 5
    enrich_run_limit: int = 5
    max_contacts: int = 3
    search_pages_per_job: int = 1
    search_page_size: int = 25
    search_daily_limit: int = 5
    draft_run_limit: int = 3
    draft_daily_limit: int = 5
    allocation_confirmed: bool = False
    cache_ttl_days: int = 7
    timeout_seconds: float = 15
    max_tokens: int = 8192
```

`load_settings(path: Path) -> Settings` rejects unknown keys, invalid timezone, booleans masquerading as integers, invalid paths and nonpositive limits. Default config path and project root resolve from the installed module location, not the caller's working directory. Resolve relative state/export paths against that root. Secrets do not belong in Settings. Pytest `settings` fixture constructs `Settings` with temporary state/output paths, `allocation_confirmed=True`, and other defaults; `context` fixture constructs a fictional full-stack job at `example.org`.

Operation/cache keys are SHA-256 of canonical sorted JSON: search = domain + role filters + page; enrich = Apollo ID; draft = Apollo ID + full job context + selected facts/source/profile/prompt hashes + application/attachment flags + model/effort/token budget. Store completed errors separately from cached successful payloads. Never hash credentials into exported keys.

Exceptions defined by owning modules: `InputError`, `NeedsContext` in `context.py`; `BudgetExceeded`, `AccountingUnavailable`, `AttemptUncertain` in `store.py`; `ProviderError` in `apollo.py`; `ProfileNeedsReview` in `profile.py`; `DraftError` in `drafting.py`. CLI maps these to the exit codes above without printing payloads.

## Checkpoint checklist

### Checkpoint 1 — Isolated setup and input contract

**Files:** new package/config/models/dependency files; `.gitignore`, `.env.example`; `tests/test_url_outreach_contract.py`.

**Interfaces:** `parse_request(argv: list[str]) -> Request` in `main.py`; `load_settings(path: Path) -> Settings`; shared records above. CLI main wiring is completed at checkpoint 7.

- [x] Record interpreter/dependency baseline; create project `.venv` without changing system Python. Resolve only requests, BeautifulSoup, PyYAML, python-dotenv, Anthropic and pytest for this route; pin installable tested versions in the two pilot requirement files. Do not copy unresolved inherited minimum versions blindly or install Google dependencies solely for this route.
- [x] Write and run the failing contract tests before introducing these interfaces:

```python
import pytest
from outreach.main import parse_request
from outreach.context import InputError

def test_company_requires_role():
    with pytest.raises(InputError):
        parse_request(["--company-url", "https://example.org"])

def test_drafts_are_explicit():
    req = parse_request(["--job-url", "https://example.org/jobs/1"])
    assert req.draft_email is False
    assert req.application_status == "unknown"
    assert req.resume_attached is False
```

- [x] Implement frozen models, settings validation and argparse conversion. Reject missing/both source forms where ambiguous, invalid persona names and incompatible resume/export flags. Add ignore entries for `.venv/`, `local-data/`, private JD/profile inputs and SQLite sidecars before creating local runtime files.
- [x] Run `.venv/bin/python -m pytest tests/test_url_outreach_contract.py -q`; expect passing tests for all input forms and invalid settings. Verify `--help` requires no credentials or provider imports with side effects.
- [x] Update scope/log and mark this checkpoint complete only when that evidence exists. Record fork/authentication as a separate Git setup limitation; do not mutate parent Git.

### Checkpoint 2 — Durable spending guards and recovery

**Files:** `outreach/store.py`; `tests/test_url_outreach_store.py`.

**Interfaces:** `Store(path: Path, settings: Settings, now: Callable[[], datetime])`; `reserve(kind: str, key: str, units: int = 1) -> str`; `finish(attempt_id: str, status: str, payload: dict) -> None`; `remaining(kind: str) -> int`; `save_run(run_id: str, payload: dict) -> None`; `load_run(run_id: str) -> dict`; `cached(kind: str, key: str) -> dict | None`. Kinds are `search|enrich|draft`. `reserve` raises `AttemptUncertain` on an existing unfinished identical operation rather than retrying it.

- [x] Add the failing persistence test, plus a two-connection reservation test using the same temporary SQLite file:

```python
from datetime import datetime, timezone
from outreach.store import Store

def test_pending_attempt_survives_restart(tmp_path, settings):
    path = tmp_path / "state.sqlite3"
    clock = lambda: datetime(2026, 11, 15, 18, tzinfo=timezone.utc)
    first = Store(path, settings, clock)
    first.reserve("enrich", "person-1")
    reopened = Store(path, settings, clock)
    assert reopened.remaining("enrich") == settings.enrich_daily_limit - 1
```

- [x] Implement tables `attempts(id, kind, operation_key, day, units, status, payload_json, created_at)`, `runs(id, payload_json, updated_at)`, `cache(kind, cache_key, payload_json, expires_at)`. Use unique pending-operation keys, `BEGIN IMMEDIATE`, bounded busy timeout and atomic count/check/insert. Store timestamps in UTC and derive budget day in configured timezone. Corrupt/unavailable ledgers stop live calls.
- [x] Keep run-level counters in orchestration as an additional guard. Reserve before each request, count every submitted person including no-match, and count searches/drafts separately. Zero automatic retries; leave timeout/crash attempts uncertain across day rollover. Persist outcomes before proceeding to the next stage.
- [x] Implement read-only preview access without creating a missing DB; a missing DB previews a first-run allowance, whereas an unreadable/corrupt existing DB stops. Cache successful found/no-match enrichment for 7 days; expiry permits a new budgeted lookup. Do not cache uncertain attempts as successful results.
- [x] Run `.venv/bin/python -m pytest tests/test_url_outreach_store.py -q`; require persistence, concurrency, midnight/DST, corrupt DB, repeated operation, expiration and failed-export recovery tests to pass. Append log/update scope.

### Checkpoint 3 — Job/company context from a URL

**Files:** `outreach/context.py`; `tests/test_url_outreach_context.py`; fictional HTML/JSON-LD fixtures.

**Interfaces:** `validate_request(request: Request) -> None`; `resolve_context(request: Request, *, fetch: Callable[[str], str]) -> Context`; `fetch_public_text(url: str) -> str`. Dependency injection permits a fake fetcher and no-network preview.

- [x] Write a failing test demonstrating that an ATS host is not the employer:

```python
from outreach.context import resolve_context
from outreach.models import Request

def test_uses_hiring_organization_not_ats_host():
    page = '''<script type="application/ld+json">{"@type":"JobPosting",
      "title":"Full Stack Engineer","description":"Build React services",
      "hiringOrganization":{"name":"Example","sameAs":"https://example.org"}}
      </script>'''
    context = resolve_context(Request(job_url="https://boards.example.net/jobs/1"), fetch=lambda url: page)
    assert context.company_domain == "example.org"
    assert context.job_title == "Full Stack Engineer"
```

- [x] Parse `JobPosting` JSON-LD including arrays/`@graph`, then semantic page text; prefer supplied JD and explicit role/company overrides, while conflicting fetched employer identity yields `NeedsContext`. Record source URL for each field. Match team terms from explicit text, not invented hidden reporting lines.
- [x] For company-website mode, use normalized employer domain plus supplied target role; fetch public company text for a company hook. Permit role-targeted networking without a vacancy, and label that context accordingly. Never imply a specific open vacancy without job evidence.
- [x] Use only public HTTP(S) URLs; validate DNS destinations and redirects against private/local addresses, bound redirects to 3, response body to 2 MB, and connect/read timeouts. Do not forward API credentials to page fetches. No executing page scripts, logging into job sites or arbitrary URL execution. Reuse scanner parsing ideas, not its unsafeguarded fetcher wholesale.
- [x] Return `NeedsContext` with exact missing fields for blocked/JS/expired pages or unresolved domain/title. The user can provide `--job-description-file`, `--company-url`, `--target-role`; no additional paid search/Claude parser is silently invoked.
- [x] Run `.venv/bin/python -m pytest tests/test_url_outreach_context.py -q`; cover ATS domains, generic pages, blocked requests, conflicting overrides, redirects, local-address rejection and pasted JD. Update scope/log.

### Checkpoint 4 — Apollo discovery, shortlist and ID-based enrichment

**Files:** `outreach/apollo.py`, `ranking.py`; `tests/test_url_outreach_apollo.py`, `tests/test_url_outreach_apollo.py`; sanitized fictional search/enrichment fixtures.

**Interfaces:** `ApolloClient(api_key: str, transport, timeout: float)`; `.search(context: Context, roles: tuple[str, ...], page: int, per_page: int) -> list[Person]`; `.enrich(ids: list[str]) -> dict[str, Person]`; `rank_people(people: list[Person], context: Context, roles: tuple[str, ...], limit: int) -> list[Person]`. Store/budget reservations belong to service, never hidden inside transport.

- [x] Write the failing ID-only search test; `apollo` pytest fixture is an `ApolloClient` with injected fake transport whose search fixture has one obfuscated person ID and no LinkedIn URL:

```python
def test_search_does_not_require_linkedin_url(apollo, context):
    people = apollo.search(context, ("technical_recruiter",), 1, 25)
    assert people[0].apollo_id == "fake-person-1"
    assert people[0].linkedin_url is None
    assert people[0].email is None
```

- [x] Implement POST `/api/v1/mixed_people/api_search` with employer-domain and title filters, one page of 25. Persona title sets: recruiter = technical recruiter/technical sourcer/talent acquisition; manager = engineering manager/software engineering manager/director of engineering; HM candidates use that same manager set; CTO = CTO/chief technology officer; CEO = CEO/chief executive officer/founder. Search union of explicitly selected personas; preserve which persona each title matched. No exact HM claim from title.
- [x] Rank locally: known current employer first, matching persona second, explicit team-term evidence third, stable Apollo ID tie-break. Exclude known previous-only employer matches. At most 3 provisional candidates; obfuscated identities and incomplete employment are review flags, not filled-in names.
- [x] Implement POST `/api/v1/people/bulk_match` with `details=[{"id": person_id}]`, maximum 10 IDs/request, personal-email/phone reveal false and waterfall disabled. Key returned records by Apollo ID, handle null/unmatched records and unrevealed placeholder emails. Retain professional-email status without claiming deliverability.
- [x] Recheck current employer after enrichment against current organization/employment history. Exclude mismatches from draft eligibility; unknown current employer remains review-only. No automatic replacement search/enrichment to fill a rejected slot. Export why fewer contacts were found.
- [x] Run `.venv/bin/python -m pytest tests/test_url_outreach_apollo.py -q`; assert payload flags, pagination cap, missing URL support, ID mapping, previous employer rejection, missing email, 401/403/429 and timeout behavior. Error messages contain safe status/code only; no retries or fallback provider. Update scope/log.

### Checkpoint 5 — Fresh profile context and claim restrictions

**Files:** `outreach/profile.py`, `config/outreach_profile_sources.yaml`; `profile.md` refresh markers/metadata; `tests/test_url_outreach_profile.py`; small TeX fixtures.

**Interfaces:** `select_profile(context: Context, override: str) -> str`; `load_candidate(profile: str, context: Context, *, root: Path, refresh: bool) -> Candidate`; `active_tex_text(text: str) -> str`. `refresh=False` is read-only; any stale/unreviewed required fact raises `ProfileNeedsReview` before paid drafting.

- [x] Add the failing regression demonstrating that commented historical metrics do not become facts:

```python
from outreach.profile import active_tex_text

def test_excludes_comments_but_keeps_escaped_percent():
    text = "% old claim: 85% savings\n\\resumeItem{Reduced effort by 40\\%}"
    plain = active_tex_text(text)
    assert "85" not in plain
    assert "40%" in plain
```

- [x] Parse only `document` content, active resume headings/items and nested formatting commands; strip unescaped comments and macro definitions without dropping escaped percent/ampersand characters. Never execute TeX or a shell. Preserve source heading/line references and hashes.
- [x] Bootstrap the approved sources using reviewed active-document hashes. Keep fact wording/restrictions and fact IDs in the one Markdown profile; YAML stores only source paths and hashes. This conservative v1 guard holds drafting on any active-source edit; per-section semantic refresh is deferred. Match common facts once and profile-specific facts separately.
- [x] On source changes, automatically rebuild generated source excerpts/provenance inside `profile.md` and flag changed sections for review. Hold paid drafting until changed originals/facts are reviewed; never silently promote new metrics, changed dates or conflicting implementations. Changed facts become eligible only after a local reviewed-profile update with new active-document hashes. Refresh writes atomically and preserves restrictions; dry-run reports staleness without rewriting. This is automatic freshness detection/extraction, not automatic factual approval of edits.
- [x] Selection order: explicit override; accessibility when role specifically names accessibility/WCAG; fullstack for SWE/software/full-stack/front/back-end roles; amazon for AI/FDE/applied-AI roles; ambiguous overlap returns `ProfileNeedsReview`. Choose up to 6 relevant supported facts by deterministic job-term overlap, retaining source order on ties, plus identity/common education where relevant. Never mix older/newer BIG sections.
- [x] Run `.venv/bin/python -m pytest tests/test_url_outreach_profile.py -q`; cover all three sources, comments, braces, stale/missing sources, changed restricted metric, role ambiguity and excluded BIG versions. Expect unsupported/changed facts held out and originals untouched. Update scope/log.

### Checkpoint 6 — Copy-ready Claude cold-email drafts

**Files:** `outreach/drafting.py`; `tests/test_url_outreach_drafting.py`; fictional successful/malformed/missing-context response fixtures.

**Interfaces:** `build_message(context: Context, person: Person, candidate: Candidate, request: Request) -> str`; `parse_draft(text: str) -> Draft`; `DraftClient(api_key: str, prompt: str, max_tokens: int)` with `.draft(context: Context, person: Person, candidate: Candidate, request: Request) -> Draft`. Inject a fake Anthropic messages client in tests.

- [x] Write the failing output-format test:

```python
from outreach.drafting import parse_draft

def test_parses_subject_and_three_bullets():
    draft = parse_draft("Subject: Full Stack Engineer at Example\n\nHi Alex,\n\n"
        "I’m interested in the role. My relevant work includes:\n"
        "- Built React applications.\n- Integrated REST APIs.\n- Improved SQL queries.\n\n"
        "Would you be open to a brief conversation?\n\nThank you,\nHardik")
    assert draft.subject == "Full Stack Engineer at Example"
    assert sum(line.startswith("- ") for line in draft.body.splitlines()) == 3
```

- [x] Read the full approved prompt, never the original unrelated correspondence. Build one user message with recipient title/company, job role/URL/requirements and evidenced team terms, selected profile facts/restrictions, application status, attachment flag and desired ask. Put fetched/job text in a clearly delimited data section that cannot override instructions. Exclude secrets, full source folder, raw TeX and unrelated profile versions.
- [x] Use the exact model/effort/max-token settings from global constraints with SDK retries disabled and no default extra critique call. Persist successful drafts with cache key hashing person ID, job context, selected facts/source hashes, prompt, flags, model and effort. A different job gets a different draft; identical reruns reuse saved drafts.
- [x] Accept one Subject/body or `NEEDS_CONTEXT:`; reject empty/multiple alternatives, truncated/max-token output and missing three-bullet default. Flag suspicious applied/attached wording against explicit flags for review. Do not claim local string checks prove every factual statement or perfect style; no sending is included. Invalid output is saved as failed and is not automatically re-requested.
- [x] Run `.venv/bin/python -m pytest tests/test_url_outreach_drafting.py -q`; inspect mocked request for complete examples, selected facts only, model/effort and flags. Cover 401/429, timeout, max-token stop and malformed output; assert one attempt per new recipient/job and zero hidden retries. Update scope/log.

### Checkpoint 7 — One URL end to end, exports and real dry-run

**Files:** `outreach/service.py`, `export.py`, finish `main.py`; `tests/test_url_outreach_service.py`, `tests/test_url_outreach_contract.py`.

**Interfaces:** `run(request: Request, *, settings: Settings, store: Store, fetch, apollo: ApolloClient, drafter: DraftClient | None) -> Outcome`; `preview(request: Request, *, settings: Settings) -> dict`; `export_run(outcome: Outcome, directory: Path) -> tuple[Path, Path]`; `main(argv: list[str] | None = None) -> int`.

- [x] Add failing integration tests using fake clients, temporary storage and blocked real network. Include a fake fail-on-call transport for preview:

```python
from outreach.main import main

def test_dry_run_creates_no_runtime_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = main(["--company-url", "https://example.org", "--target-role",
                   "Full Stack Engineer", "--dry-run"])
    assert result == 0
    assert list(tmp_path.iterdir()) == []
```

- [x] Orchestrate validation/local profile readiness, context resolution, search reservation, provisional ranking, enrichment-cache lookup/reservation, final employer check, persisted results, optional draft-cache lookup/reservation, export. Check available budgets before each stage. Do not draft for missing email, mismatched/unknown current employment or missing job/role context. Run IDs/checkpoints allow export-only and safe resume.
- [x] Reserve new enrichment IDs before submitting a batch; a 3-person batch consumes 3 submission units. A rerun with saved successful responses reuses them; an uncertain prior request stops with review instructions, never automatically resends. Store lookup results before Claude so draft/export failures do not repay enrichment.
- [x] Keep `--dry-run` entirely local: validate supplied inputs, show planned stages/limits/current counters and required missing context, report that contact identities/email/model output need a live run. A job URL alone cannot reveal JD/domain offline; return a needs-fetch preview instead of pretending discovery succeeded. No SDK instantiation, public website fetch, quota reservation or output creation.
- [x] Export one row per recipient/job with run/source IDs, role/job URL/company, Apollo ID/name/title/LinkedIn/email/status, employer/team evidence and confidence, outcome, review flags, selected profile/source/prompt hashes, draft subject/body and timestamps. If none resolved, export a source-level outcome row. Save CSV plus lossless JSON atomically. Escape spreadsheet formula prefixes in textual CSV cells; preserve originals in JSON. Restrict runtime file permissions and keep outputs ignored.
- [x] Summarize counts/status/output paths, not full personal data, in console. `--resume-run` handles saved deterministic stages only; unresolved uncertain provider attempts exit with review flags. `--export-run` reads saved outcome without provider keys/calls. Partial quota stops produce saved outcomes and exit 3.
- [x] Run `.venv/bin/python -m pytest tests/test_url_outreach_service.py tests/test_url_outreach_contract.py -q`; require URL-to-export success, missing context, no results, mismatched employer, quota exhaustion, repeated job, same contact/new job, interrupted draft and failed export recovery, CSV quoting/formula safety, no Sheets and no Anthropic requirement when drafting off. Update scope/log.

### Checkpoint 8 — Offline acceptance, docs and bounded live pilot

**Files:** `README.md`, `docs/OFFLINE_DRY_RUN.md`, `scope.md`, `CHANGELOG.md`, this checklist; `tests/test_url_outreach_acceptance.py`.

- [x] Add and pass an end-to-end fixture test: job URL → fictional employer/job → 3 Apollo candidates → one confirmed email, one no-email, one employer mismatch → exactly one Opus draft → CSV/JSON, with zero real network. Assert all three outcomes remain visible and exact search/enrichment/draft counters are 1/3/1.
- [x] Run `.venv/bin/python -m pytest tests/test_url_outreach_*.py -q` and relevant inherited Apollo/normalization tests. Run the full inherited suite only in a compatible dependency environment; record collection/dependency failures distinctly from behavior failures. Check help, no-network preview, export-only and installation instructions using documented commands.
- [x] Update setup/input/output examples, limits, cache expiry, stale-profile review, uncertain-attempt recovery and legacy-command limitations. Mark implementation status by checkpoint; append actual commands/results to log. Verify imported runtime changes are confined to intended new modules and deliberate support files.
- [ ] Before live use, obtain one real job URL (or company URL + role), confirm account/key search/enrichment access, agree shared allocation and daily limits, and explicitly bound paid calls. Verify SDK/model access without falling back silently. These are live-run prerequisites, not blockers for offline implementation.
- [ ] For the first authorized live acceptance, override to at most 1 search page, 1 person enriched and 1 draft. Compare ledger with account usage, inspect employer evidence and review the draft with Hardik against his style. This is a future test requiring that concrete live-run scope; no live call is authorized by this planning document.
- [ ] Record live results and limitations, including no guarantee of exact HM identity, email availability/deliverability or error-free drafts. Set pilot dates and manual review cadence. No email is sent by the code.


## Deferred follow-on checklist

- [ ] Add CSV/XLSX importer using the row contract in the spec and call the same `run()` service per row; reuse ledger/cache/export and row-level outcomes. Do not build a parallel pipeline.
- [ ] Offer supplied LinkedIn URLs through the same guarded service after the URL-based slice works; preserve the inherited manual URL command meanwhile and label its missing guards.
- [x] Add optional Sheets Queue/Results adapter after local outputs; Google is not a CLI/local lookup prerequisite.
- [ ] Add manual outcome updates for sent/replied/bounced/referral/interview, with explicit denominators and pilot dates.
- [ ] Restore correct GitHub fork/clone history before project commits, preserving local documents and ignored secrets. Verify remotes and root before any Git mutation.

## Review and execution record

- [x] Chosen the URL-first slice and separated spreadsheet follow-on work.
- [x] Recorded exact proposed commands, file ownership, interfaces, quota defaults and acceptance gates.
- [x] Distinguished implemented baseline from planned features; removed stale scope exclusions on Apollo-based discovery.
- [x] Checked coverage of context resolution, uncertainty, profile freshness, full style prompt, Opus high, local persistence, zero-network preview and recovery.
- [x] Implement checkpoints 1–7 and offline acceptance; actual live/account/Sheet validation remains pending.

Execution order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8. Complete tests and append the log at each checkpoint before marking it done. If a design choice changes, update the spec/scope/plan and append the reason; never rewrite earlier log entries. Human review remains part of the pilot even when drafts are usually quick to approve.


## Shared Google Sheet input queue — implemented offline, November 14, 2026 (Chicago)

Hardik requested a shared Sheet to enter URLs/context and then run the remaining
pipeline without a frontend. Reuse the core service, budgets and cache. This brings
Sheets input forward from the earlier optional-output-only recommendation; the
CSV/XLSX file importer remains deferred. The adapter is implemented; no automatic watcher exists.

Recommended first trigger: Hardik marks rows ready and requests a sync/run in chat
or invokes the eventual command. Background polling requires a separately configured
running worker or schedule; an idle chat is not a watcher. No schedule is created by
this proposal. The v1 row contract is locked in header templates; the trigger is on-demand sync.

Proposed workbook tabs:
- `Queue`: one job/company request per row. User columns: `row_id`, `ready`, `job_url`,
  `company_url`, `target_role`, optional `job_description`, `profile`, `contact_roles`,
  `max_contacts`, `draft_email`, `application_status`, `resume_attached`, `notes`.
  Apply the same input requirements/defaults as the core Request contract.
- `Results`: one recipient/job outcome, including contact/email/evidence and draft.
  Maintain `source_row_id`, `input_hash`, `run_id`, and `result_id` for reconciliation.
- Tool-owned Queue columns: `status`, `processed_hash`, `run_id`, `processed_at`,
  `error`. Status values: `pending`, `processing`, `done`, `needs_context`, `error`,
  `budget_wait`, `changed`. Editing or sorting rows must not change their identity.

Completed adapter checklist within checkpoint 7:
- [x] Lock headers/defaults and ready semantics; require unique stable row IDs.
- [x] Add `outreach/sheets_queue.py` and fake-client tests for ready-only import,
  header-based mapping, missing/duplicate IDs, reordering, invalid rows and edits.
- [x] Hash user input only; process new ready versions once through the same core
  service. A changed already-processed row is marked changed and held for explicit
  requeue acknowledging its new hash, or submission under a new row ID, before another
  paid run. A readiness off/on toggle between syncs is not observable and must not be
  treated as a reliable requeue event. Never infer readiness from an edit.
- [x] Use SQLite claims as authority for a single local worker; Sheet status is display
  state, not a distributed lock. Reuse enrichment/drafts and reconcile result IDs
  after ambiguous writes before appending again.
- [x] Snapshot input at claim; re-read ID/hash before writing status. Do not overwrite
  user edits or falsely mark a newer version done. Persist outcomes before Sheet writes.
- [x] Add explicit Google auth/config only for this adapter; keep CLI/local output
  independent of Google. Share the selected private workbook with the service account
  as Editor for result/status writes. Keep credentials outside the workbook.
- [x] Write cell values as RAW using the Sheets values API. Export all no-match,
  missing-context, budget-wait and failed outcomes rather than silently dropping rows.
- [x] Add zero-paid-call queue preview and recovery tests; a dry-run never changes
  Sheet cells or local state. Append scope/log evidence after actual implementation.

Existing `shared/sheets.py` supplies authentication; `outreach/sheets_queue.py` adds the queue, version tracking, targeted RAW status updates and result reconciliation. Workbook URL and credentials/sharing remain setup inputs. `requeue_token` records explicit processing intent after a reviewed edit. `--preview-sheet` provides a read-only, zero-provider-call validation command.


### Execution notes — November 14, 2026 (Chicago)

User approved proceeding with the core and shared Sheet queue. Implementation is inline
in the requested folder; no parent worktree/Git mutation was performed. Direct dependencies
were installed in a fresh isolated environment, including optional Google and proxy support.
The source snapshot remains a ZIP import rather than a GitHub fork.

Reviewed adjustments: whole-active-document profile freshness is deliberately conservative
for v1; automatic per-section semantic approval is deferred. Apollo enrichment is invoked
one ID at a time for simple durable per-person recovery, with a ten-ID-capable adapter.
One RunBudget is shared by all rows in a Sheet invocation. No background polling or live
calls were enabled. Full verification results are appended to CHANGELOG.md; actual live
permissions, shared allowance, workbook access and first-draft calibration are still open.
