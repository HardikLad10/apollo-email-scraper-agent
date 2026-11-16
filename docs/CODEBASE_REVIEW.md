# Codebase review — imported baseline

Source commit: `ffe7aee7a57aa9030d886ebb00089579fe867041`.
Status: source import and review complete; GitHub fork/clone still pending.

## What exists

This is a Python command-line project with two independent tools sharing Google
Sheets utilities. The email finder is the useful starting point for this pilot.

| Capability | Actual behavior in this snapshot |
| --- | --- |
| Input | LinkedIn profile URLs from CLI arguments, a chosen text file, or the default local file |
| Parsing | Blank/comment lines ignored; optional trailing `# note` retained as contact context |
| URL normalization | HTTPS, lowercase, LinkedIn subdomains collapsed, tracking removed, extra profile path trimmed |
| Deduplication | Normalized URLs checked against the current input and existing Contacts rows |
| Provider chain | Apollo first, Prospeo second, Apify third; only no-matches move to the next provider |
| Apollo integration | POST `people/bulk_match`; default batches of 10, 15-second timeout, 1.2 seconds between batches |
| Data requested | Professional-email enrichment from supplied profile URLs; personal-email and phone reveal flags false |
| Run cap | 20 new URLs after dedup; excess aborts the whole run before provider requests |
| Provider errors | Stop the chain, retain resolved results in memory, report unresolved URLs as pending, exit nonzero |
| Storage | Append found and not-found rows once to a Google Sheet Contacts tab; header-based mapping |
| Optional drafts | Claude drafts a LinkedIn connection note, usually at most 200 characters; saved in `outreach_line` |
| Sending | No email sender, inbox integration, automatic follow-ups, or LinkedIn sending |
| LinkedIn discovery | No search/extraction of new profile URLs; the user supplies them |
| Pilot metrics | A manual `contacted` field exists; no reply, bounce, referral, interview, or conversion tracking |

The repository comments make claims about vendor credits, prices, model support, and
plan limits. Those are upstream claims, not independently verified account allowances.
Confirm actual plan/key access, remaining usage, reset dates, and shared allocation.

## Structure and responsibilities

| Path | Responsibility | Relevance |
| --- | --- | --- |
| `email_finder/main.py` | CLI arguments, dotenv loading, required-variable checks, summaries/exit codes | Keep |
| `email_finder/service.py` | Parse/normalize/dedup/cap, provider chain, optional drafts, row construction/export | Main adaptation point |
| `email_finder/input_file.py` | Input records and optional notes | Keep |
| `email_finder/apollo_client.py` | Apollo HTTP request and normalized response mapping | Keep |
| `email_finder/prospeo_client.py` | Single-person fallback enrichment | Optional; propose disabled initially |
| `email_finder/apify_client.py` | Synchronous actor-run fallback and result parsing | Optional; propose disabled initially |
| `email_finder/outreach_client.py` | Prompt and response handling for connection-note drafts | Optional; separate Anthropic usage |
| `email_finder/sheets_repo.py` | Contacts header validation, existing-key reads, appends | Keep if Sheets retained |
| `email_finder/settings.yaml` | Per-run cap, provider order, batch/timing, timezone, drafting settings | Central current configuration |
| `email_finder/linkedin-profiles.example.txt` | Sample input format, no active contacts | Keep |
| `shared/linkedin_url.py` | Shared normalization | Keep |
| `shared/sheets.py` | Google auth and low-level reads/appends/header helpers | Needed by existing storage |
| `config/*.example.*` | Candidate profile and connection-note style templates | Personalize only ignored copies |
| `job_scanner/main.py`, `service.py` | Separate job-search orchestration | Outside initial pilot |
| `job_scanner/ats_client.py` | Public Greenhouse/Lever/Ashby boards and individual job details; Workday detail client | Reference |
| `job_scanner/search_client.py`, `jd_client.py` | Serper search and plain-HTTP job description fetches | Outside initial pilot |
| `job_scanner/scoring_client.py` | Claude fit scoring, structured tool response/Pydantic validation, token usage | Outside initial pilot |
| `job_scanner/*_filter.py`, `date_utils.py`, `url_utils.py` | Title/location/experience filters, dates, job URL normalization/platforms | Outside initial pilot |
| `job_scanner/sheets_repo.py` | Jobs tab mapping and export | Outside initial pilot |
| `job_scanner/*.yaml` | Search sources, 76 ATS companies, filters and scanner settings | Upstream settings |
| `.github/workflows/scan.yaml` | Scanner-only twice-daily schedule/manual dispatch; no email finder automation | Do not enable for pilot |
| `tests/` | 22 test modules and 16 fixtures; mocked HTTP/LLM/storage behavior | Reuse |
| `docs/DESIGN.md`, `docs/PLAN.md` | Upstream architecture and build history/plans | Read critically; not pilot scope |
| `README.md`, `.env.example`, `.gitignore`, `requirements.txt` | Upstream setup, secrets template, exclusions and dependency ranges | Preserve baseline |

Empty `__init__.py` files define package boundaries. Added local project guidance is
listed in `docs/SOURCE_PROVENANCE.md`.

## Email finder flow

1. `main.main` loads dotenv and checks Sheets credentials plus every enabled provider's
   key. `--draft` additionally needs an Anthropic key. Default settings require all
   three provider keys even if Apollo would resolve every URL.
2. The CLI reads and prints the Sheet title. `service.run` loads settings again,
   optionally reads candidate/style files, reads input and Contacts headers/keys.
3. Normalize profile URLs and discard invalid, duplicate, or already-seen URLs.
4. Reject the run if new URLs exceed `max_urls_per_run`; there is no automatic truncation.
5. Call providers in order. Matches skip later providers; no-matches fall through;
   provider errors halt the chain. Apollo matches are keyed by returned normalized URL.
6. Draft notes only for found contacts when requested. A draft failure leaves a blank
   note and warns; auth/permission errors stop drafting but retain contact rows.
7. Build found and not-found rows and make one Sheets append. Pending URLs are not saved.
8. Print counts and URL/status lines, avoiding names/emails/notes in normal output.

Contacts headers: `contacted`, `name`, `company`, `title`, `email`, `email_status`,
`email_source`, `linkedin_url`, `notes`, `outreach_line`, `date_found`.
All 11 must exist, in any order. The write mode is RAW, and `contacted` is left blank.

## Findings to address before a live pilot

| Priority | Finding and evidence | Impact / action |
| --- | --- | --- |
| High | No persistent daily/account budget: `email_finder/service.py:234` enforces only the run cap | Re-running can exceed the intended daily allowance. Add atomic accounting before requests; distinguish submissions from billable credits. |
| High | Results remain in memory until `service.run` exports at its end | Crash, draft interruption, or failed/ambiguous append can cause repeated paid lookups. Add durable checkpoints and export reconciliation. |
| High | Separate local runs have no shared reservation/lock | Two processes can read the same pre-run Sheet state and spend/export twice. Coordinate quotas and idempotency locally. |
| High | Default `providers: [apollo, prospeo, apify]` | Requires keys for three services and may spend elsewhere after an Apollo miss. Start Apollo-only for this pilot. |
| Medium | `get_existing_keys` reads emails, but `service.run` ignores that returned set (`existing_urls, _`) | Different profile URLs or old rows without URLs can yield duplicate emails; add post-match duplicate checks. |
| Medium | Found rows accept any nonempty unlocked email/status | No verified-only policy or independent deliverability check; Apify marks results unverified. Expose quality explicitly and manually review before outreach. |
| Medium | Not-found rows also block future URL lookups | A transient or unrevealed result may become permanently skipped until the row changes. Design an explicit recheck policy with quota accounting. |
| Medium | Missing Apollo returned records are classified as no-match | An omitted result goes to fallbacks or becomes not-found; distinguish actual no-match from incomplete response where feasible. Miss behavior was assumed in upstream fixtures. |
| Medium | Settings lack a typed validation layer | Invalid batch size/cap/timing can raise late errors or produce surprising behavior. Validate allowed values before any paid request. |
| Medium | Sheets is mandatory even for extraction; no dry-run/local recovery store | Apollo key alone cannot run the pipeline. Choose Sheets setup versus a local persistence/export path. |
| Medium | `load_dotenv()` has no explicit path in either CLI | With no project `.env`, parent-directory configuration may be loaded. Isolate this project before a live run. |
| Medium | No outreach outcome model | Cannot measure the month from a contacted checkbox. Add dated manual outcome tracking first. |
| Low for pilot | Workday docs describe integration beyond current implementation | `ats_client` implements the detail client and URL logic, but `service._search_ats_posting` calls only Ashby/Greenhouse/Lever; queries have no general Workday entry. Keep outside pilot. |

Additional observations: request clients use header credentials and avoid response-body
logging; Apollo requests explicitly suppress phone/personal email reveal; there are no
custom provider retries. These are useful foundations. The 1.2-second/3.1-second pauses
apply only between batches/calls inside a run and are not global rate or credit limits.
Prompts instruct the model about truthful content and prohibited topics, but most of
those content rules are not programmatically validated; review generated notes manually.

## Separate job scanner

The scanner polls 76 companies (31 Greenhouse, 8 Lever, 37 Ashby), plus 20 enabled
Serper query entries among 23 configured entries. It deduplicates URLs, filters titles
and locations, sorts by recency, applies a 150-job per-run cap, fetches descriptions,
filters experience requirements, scores with Claude, and appends a 14-column Jobs tab.
It logs funnel counts and estimated token costs and optionally writes a GitHub step
summary. Individual provider/job errors can be skipped; selected fatal failures abort.

The inherited Actions workflow schedules scanner runs at 10:07 and 20:07 UTC and
allows manual dispatch. It serializes scanner workflow runs with concurrency control;
that does not coordinate local email-finder invocations. It uses GitHub secrets for
the scanner's Sheet, service account, candidate/profile and vendor keys. No workflow
runs the email finder. Local source import activated no workflow.

## Verification performed

- All **79 upstream files** compared byte-for-byte against the downloaded archive.
- All **48 Python files** parsed with `ast.parse` (syntax validation).
- All **14 JSON fixtures** parsed, and all **6 YAML configuration/workflow files** parsed.
- Inventoried **22 test modules** with **428 test functions**; parametrization creates
  additional test cases, so function counts are not execution counts.
- **398 cases passed across 13 runnable test modules**, using the installed Anaconda
  Python 3.12 environment with plugin autoload, bytecode writes and pytest cache disabled.
  First invocation: 347 passed in 11 modules. Second: 51 passed in ATS/input modules.
- Full suite attempted: **9 collection errors**, due to missing `anthropic` and
  `google.auth`. Environment inspection also found `googleapiclient` and `httpx2`
  unavailable. This is not a passing full-suite result. No dependency install performed.
- Upstream setup requests Python 3.13. A local 3.13 executable exists but lacks the
  project dependencies. Passing selected tests on 3.12 does not validate the declared
  dependency ranges or a clean 3.13 setup.
- No live Apollo/Prospeo/Apify/Anthropic request, Sheet read/write, job scan, email, or
  LinkedIn action was performed. No real key was needed for the fixture-based checks.

The passing selection covers provider clients, input/URL handling, ATS parsing,
date/filter logic, JD fetching and search parsing with mocks/fixtures. The pipeline,
CLI, Sheets and drafting/scoring suites remain unverified until dependencies exist.

Commands used, from this folder:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider tests/test_apollo_client.py tests/test_prospeo_client.py tests/test_apify_client.py tests/test_linkedin_url.py tests/test_date_utils.py tests/test_experience_filter.py tests/test_jd_client.py tests/test_location_filter.py tests/test_search_client.py tests/test_title_filter.py tests/test_url_utils.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider tests/test_ats_client.py tests/test_email_finder_input.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider
```

## Inputs needed next

1. Working GitHub authentication for the real fork under Hardik's intended account.
2. Apollo plan/remaining credits/reset date and the portion agreed with the friend;
   share plan/usage information without the API key.
3. Initial daily volume (recommend 5 profiles until allowance is established).
4. Storage preference: own Google Sheet/service account, or local storage/export first.

Sender/inbox integration and target audience details can wait until the extraction
guardrails and experiment tracking are ready.
