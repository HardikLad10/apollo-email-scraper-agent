# Outreach workflow design — URL-first implementation

Created November 14, 2026; URL-first priority set November 15, 2026. This document defines
the design contract for `superpowers/plans/2026-11-15-url-outreach.md`. Implementation status: the new URL workflow, Sheet queue, profile freshness guard, cold emails and dry-run are offline-tested. Bulk CSV/XLSX file import is deferred. No real account or Sheet has been connected or live-tested.

## 1. Locked choices and remaining design choices

Confirmed: use original Full Stack, Amazon, and Accessibility TeX sources; preserve
profile-specific BIG descriptions; use Claude Opus 5.5 high; keep the supplied writing
guide as evidence; default cold emails to three concise bullets; human review and manual
sending; maintain scope and an append-only log. Preserve the original style guide.

Prepared artifacts: `../claude_cold_email_prompt_v1.md` and `../profile.md`. They are
loaded by the new route. Active-source freshness checks and generated review excerpts are implemented; changed facts require review. The supplied guide is saved separately; no local original copy
was installed because its transfer failed.

Implementation defaults: five enrichment submissions/day and five/run; one search page
per job, 25 results/page and five search requests/day; at most three selected contacts
per job and never above remaining budget; three draft attempts/run and five/day.
Use local SQLite accounting/recovery and CSV plus JSON exports. Spreadsheet import and
XLSX output follow the core workflow. These defaults are configurable and enforced locally by the new route. Exact Apollo allowance/reset/shared allocation remain unknown and must
be agreed before live runs. Google Sheets is optional follow-on output.

The first release accepts one job URL, or company website plus target role, with optional
supplied JD, employer/role overrides and profile choice. It does not require a manual
LinkedIn URL. Existing person-mode behavior stays available through the inherited CLI;
bringing it under the new safeguards is follow-on work. No legacy command is silently
upgraded by writing these documents.

## 2. Inherited baseline structure and behavior

This section describes the unchanged legacy tools, not the new `outreach` route. See `URL_OUTREACH_GUIDE.md` for the implemented CLI/Sheet contract.

| Area | Legacy implementation |
| --- | --- |
| CLI | `email_finder/main.py`: positional URLs, `--file`, `--draft`, help |
| Parsing | `input_file.py`: text lines, comments/blanks ignored, optional trailing `# note` |
| Pipeline | `service.py`: normalize/dedup, per-run cap, providers, optional note, append |
| Providers | Apollo bulk enrichment, Prospeo single enrichment, Apify actor fallback |
| Drafting | `outreach_client.py`: LinkedIn connection note, one logical call per newly found contact |
| Settings | 20 new URLs/run; Apollo→Prospeo→Apify; Sonnet 5.5; note limit 200 characters |
| Storage | Google Sheets Contacts, header-driven, one append at the end |
| Separate scanner | `job_scanner/`: finds/scores jobs into Jobs; not wired to contact selection |

Current input details:

- CLI URLs, or a plain UTF-8 text file with one personal LinkedIn URL per line.
- Without CLI URLs or `--file`, reads `email_finder/linkedin-profiles.txt`.
- CLI URLs plus `--file` are combined, CLI URLs first.
- A trailing `# note` is saved and can be passed to the connection-note drafter.
- Company names/domains and job URLs are not valid personal-profile inputs. They are
  ignored by profile validation, rather than triggering a people search.
- CSV/XLSX structures are not parsed. `--file` treats a file as plain text regardless
  of extension; passing an Excel file is not a supported workaround.
- There is no `--dry-run`, email-drafting flag, company-search mode, or daily ledger.

Current output:

- Contacts headers: `contacted`, `name`, `company`, `title`, `email`, `email_status`,
  `email_source`, `linkedin_url`, `notes`, `outreach_line`, `date_found`.
- Found and not-found outcomes are appended. Pending URLs after provider errors are
  not saved. Already-recorded normalized URLs are skipped, including not-found rows.
- Console shows URL/status/counts, not found email addresses or drafted text.
- `--draft` saves a connection note in `outreach_line`. No email subject/body is created.
- No email/LinkedIn sending or reply collection exists.

## 3. Use case A — supplied people (guarded adapter deferred)

Input: known LinkedIn URLs, optionally with a company/job on each row.

1. Read supported input, validate/normalize URLs, assign source row IDs.
2. Reuse an existing contact lookup where appropriate; check current-employer matches
   when an expected company is supplied. Do not silently substitute another employer.
3. Reserve daily capacity atomically for new submissions before calling Apollo.
4. Enrich only eligible new profiles; store outcomes locally before export/drafting.
5. If cold-email drafting was requested and enough job context exists, select one
   resume profile and build the request. Missing or conflicting facts create a review
   flag rather than an invented claim. Email lookup alone remains independently usable.
6. Export contact results and requested draft subject/body for review.

## 4. Use case B — company and job to relevant people

Input: one company/job per row, with company identity and desired contact roles.

1. Resolve the company domain. Ambiguous company names require clarification or a
   domain; never pick an arbitrary company with the same name.
2. Prefer the supplied job description. If only a URL is present, attempt a supported
   description fetch; keep its source and mark blocked/unavailable pages explicitly.
3. Extract the job title, function, requirements, and explicit team/product keywords.
   User-supplied team keywords can supplement the description. Mark inferred labels.
4. Use Apollo People Search with company, title/seniority, and applicable keyword
   filters. Verify the key has search access first; enrichment access alone is not proof.
5. Check current-employer identity, rank candidates with available evidence, and select
   only the configured number within remaining limits. Start with local ranking and
   review; extra Claude ranking calls are not part of the default call budget.
6. Enrich selected Apollo people IDs/results. Adapt the current URL-only client to
   handle search results; do not assume search always supplies a LinkedIn URL or email.
7. Draft emails from the selected resume profile, recipient, and job context, then export.

Apollo company/title filters help identify candidates. They do not prove that a person
belongs to a particular internal team or owns the vacancy. Keep `team_evidence` and
`team_match` as explicit fields: confirmed only with direct evidence, otherwise inferred
or unknown. Do not turn company-level technology filters into individual expertise.
When evidence is weak, return the uncertainty instead of labeling a team match as fact.

## 5. Proposed Excel/CSV row contract

Use one sheet named `Outreach` for a mixed workbook. CSV uses the same column names.
A minimal LinkedIn-only file may contain just `linkedin_url`. For mixed rows, prefer
an explicit `mode` to avoid unintended discovery calls.

| Column | Meaning / requirement |
| --- | --- |
| `row_id` | Optional caller reference; otherwise generate from file/sheet/row |
| `mode` | `person` or `company`; if absent and a LinkedIn URL is supplied, use person mode |
| `linkedin_url` | Required for person mode |
| `company_name` | Target or expected employer; required for company mode unless domain identifies it |
| `company_domain` | Preferred company identifier; company mode must resolve one before search |
| `job_title` | Target position; infer only from supplied/fetched job text when clear |
| `job_url` | Optional if description supplied; retained in output for traceability |
| `job_description` | Preferred supplied job text; either this or a retrievable job URL for job-specific drafting |
| `team_keywords` | Optional semicolon-separated product/team/domain terms |
| `contact_roles` | Company mode personas, e.g. `technical_recruiter;engineering_manager;engineer` or explicit CEO/founder |
| `max_contacts` | Company-mode selection cap; cannot override global remaining budget |
| `profile` | `auto`, `fullstack`, `amazon`, `accessibility`; explicit choice wins |
| `application_status` | `applied`, `interested`, `unknown`; default unknown |
| `resume_attached` | Explicit true/false confirmation for attachment wording; default false |
| `draft_email` | True/false; requesting enrichment does not automatically authorize a Claude call |
| `notes` | Additional context treated as data, never instructions that override the prompt |

No arbitrary uploaded script is executed as an input format. Existing Python callers
can wrap the current service with appropriate setup, but the CLI does not accept a
script path as a supported data import. A future import command will read data files.

## 6. Profile, style, and exact Claude request boundary

Maintain one derived `profile.md` with common facts once and clearly separated role
profiles. Read original TeX files before paid drafting; refresh generated review excerpts when
source hashes change. No duplicate TeX files, manual resume re-entry, or mixed BIG stacks.
The new loader checks all three original active-text hashes. Its conservative first version refreshes source-review excerpts and holds drafting until source edits/facts are reviewed; per-section semantic refresh is deferred.
Refresh extracted text/provenance automatically; retain reviewed fact-to-source bindings
and existing restrictions. Changed facts are held for local review rather than silently
approving new claims. Paid drafting is held until the changed active original is reviewed in v1. Dry-run never
rewrites the profile. The implementation plan defines this conservative refresh gate.

The future request has:

- System: the full approved `claude_cold_email_prompt_v1.md`, including both examples.
- User: recipient and job context, shared + selected-profile allowed facts, claim
  restrictions, requested format/ask, and application/attachment flags.
- Model: `claude-opus-5-5`, top-level `output_config={"effort":"high"}`.
- Output: one finished subject/body, or an explicit missing-context result.

The API receives text assembled from local documents; it does not require separate
file uploads for every source. One profile file simplifies maintenance, but selecting
the relevant profile still prevents irrelevant facts and conflicting implementations.

One logical draft call per requested recipient/job pair, not per resume line. No
separate default critique call; checks happen in that response plus local validation.
SDK retries need an explicit implementation policy and accounting. Do not silently
retry uncertain paid actions. Reusing the same contact for another job should reuse
enrichment while allowing a distinct job-specific draft.

## 7. Proposed output and persistence

Use SQLite for reservations, usage, contact cache, outcomes, and pending exports.
Export CSV plus lossless JSON locally. The approved Sheets queue adapter additionally writes Results and Queue statuses; Excel file import/output remains follow-on work.
This recommendation replaces the inherited requirement for a Google service account
only in the implemented new route; the legacy route is unchanged.

One result per recipient/job includes: source row ID, job URL/title, company/domain,
name/title, LinkedIn/Apollo ID, email/status/provider, lookup outcome, employer-match
status, team evidence/confidence, selected profile, draft subject/body, review flags,
source/profile/prompt hashes, and timestamps. Keep budget-skipped and failed source
rows in the report even when no recipient was resolved. Do not print keys or sensitive
contact exports in diagnostic logs.

Keep enrichment attempts, successful emails, search requests/pages, Claude draft calls,
and actual provider credits distinct. A five-submission guard is not a five-credit
guarantee. Local controls cannot constrain a friend's separate shared-account activity.

## 8. Checkpoints and checks before live use

The user chose the single-URL slice next. This supersedes the previous person-mode-first
sequence. The detailed checklist is `superpowers/plans/2026-11-15-url-outreach.md`:

1. Isolated environment, validated settings and input contract.
2. Durable atomic budgets, cache and recovery.
3. Job/company context resolution with supplied-JD fallback.
4. Apollo discovery, local ranking, evidence and ID-based enrichment.
5. Fresh selected-profile facts and claim restrictions.
6. Full-style Opus-high cold-email drafting.
7. Single-URL orchestration, CSV/JSON and actual no-network dry-run.
8. Offline acceptance, setup docs and a separately authorized minimal live pilot.

The first live test is capped at one search page, one enriched person and one draft.
It requires a real target, confirmed key permissions/shared allocation and explicit
live-run scope. Add spreadsheet import, optional Sheets and manual monthly outcome
tracking after the core service works; reuse that service rather than creating another
pipeline. CEO/CTO are explicit persona choices; engineering managers/recruiters are the
default candidates. Unknown current employment is review-only and not auto-drafted.

A real dry run must make zero provider calls and zero external writes, display the
planned actions/remaining allowance, and treat uncertain accounting state as a stop.
It must not mark enrichment as attempted, consume a budget reservation, or populate
real email/draft results. A separate mocked end-to-end test may exercise those states
with fake clients and an isolated temporary database.

The implementation checklist is saved and checkpoints 1–7 plus offline acceptance are implemented. Real workbook/account permissions, shared allocation and the bounded live pilot remain pending.
The real GitHub fork/clone and complete dependency environment still need setup; do not
commit through the unrelated parent repository. Offline development can proceed without
paid requests; restore repository history before actual project commits.


## Shared Sheet queue acceptance

The approved on-demand adapter is implemented with the concrete headers in `config/sheets_queue_headers.csv` and `config/sheets_results_headers.csv`. `--preview-sheet` authenticates/reads only and validates ready rows without paid calls or writes; `--sync-sheet` uses the same guarded core. A stable row ID plus input hash records the version processed, and a changed `requeue_token` explicitly requeues reviewed edits. Local claims and result IDs handle ordinary repeat work/ambiguous completed writes. No background monitor is enabled. See `URL_OUTREACH_GUIDE.md` for one-worker/editing limitations and setup.
