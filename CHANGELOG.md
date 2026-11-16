# Append-only project change log

Append new entries at the end. Never edit or delete earlier entries; append corrections.
Record changes, rationale, verification, and unresolved issues. Do not include secrets
or actual contact data. This convention is not enforced by the filesystem.

## 2026-11-13 — Folder creation (recorded retrospectively)

- Created `Apollo Email Extraction Outreach Specialist/` inside `job-search`, as requested.
- Verified the directory existed with `ls -ld`. No files or project behavior added then.

## 2026-11-13 — Upstream source import and baseline review

- Read the explicitly requested `using-superpowers` entry point and its Codex reference;
  consulted brainstorming and verification guidance for subsequent project work.
- Public source: https://github.com/pratyushagarwal22/job-hunt-tools, branch `master`,
  commit `ffe7aee7a57aa9030d886ebb00089579fe867041`.
- Terminal GitHub access failed DNS resolution; GitHub CLI authentication was invalid.
  Downloaded the public GitHub ZIP through the browser and imported its 79 files here.
- Verified all 79 files matched archive contents byte-for-byte. No upstream file edited.
- Reviewed runtime modules, configuration, workflow, upstream documentation, test
  inventory and key test harnesses/fixtures. Recorded implementation/documentation gaps.
- Added `scope.md`, `AGENTS.md`, `CLAUDE.md`, `docs/SOURCE_PROVENANCE.md`,
  `docs/CODEBASE_REVIEW.md`, and this log for future agents and the monthly pilot.
- Verification: 48 Python files parsed, 14 JSON fixtures parsed, 6 YAML files parsed;
  398 test cases passed in 13 modules. Full-suite attempt stopped at 9 collection
  errors from missing Anthropic/Google dependencies; other unavailable dependencies
  are recorded in the review. Tests used mocks/fixtures and no real API key.
- Runtime remains upstream: 20 URLs per run; no daily quota, dry run, durable lookup
  recovery, sender, or outcome tracker. Suggested 5/day Apollo-only controls are scope
  proposals and have not been implemented.
- GitHub fork/clone with history is still pending. No Git mutation occurred in this
  folder or the enclosing unrelated repository. No live extraction, Sheets operation,
  draft generation, job scan, outreach, or workflow execution occurred.
- Next inputs: GitHub authentication, Apollo allowance/reset/shared allocation, daily
  cap, and storage choice. Never request the real API key in chat.

## 2026-11-13 — Final handoff verification

- Rechecked the imported baseline: all 79 upstream files remain byte-identical.
- Verified exactly six local project documents were added, with no project `.git` or
  `.env` created. Python/JSON/YAML parsing checks still pass.
- Selected mocked tests total 398 passing cases; full-suite dependency blockers remain.
- No runtime code/settings change, provider spend, or external write was introduced.

## 2026-11-14 — Local key-file setup

- Created an owner-readable/writable `.env` with an empty `APOLLO_API_KEY` field
  so Hardik can enter the key in the editor. No credential value was supplied or read.
- Verified file existence and 0600 permissions; checking the existing ignore rule.
- No runtime behavior changed and no API request was made.

## 2026-11-14 — Key-file visibility handoff

- Confirmed `.env` is excluded by the project `.gitignore` rule.
- Attempted to open `.env` in the right Codex panel; the app request failed.
  UI automation could not access Codex, so editor visibility is not confirmed.
- Providing the file path/link and Finder hidden-file shortcut for manual access.
  No credential contents were read.

## 2026-11-14 — Credential setup recheck

- Hardik reported updating `.env`; checked the expected project file without displaying
  credential values. `APOLLO_API_KEY` is not populated with a usable non-placeholder
  value in the checked file; `.env` remains ignored by Git.
- The first check used Python without python-dotenv; the Anaconda environment completed
  the check. No API request was made and credential validity remains unverified.

## 2026-11-14 — Anthropic key-field preparation

- Ensured the existing ignored `.env` has an `ANTHROPIC_API_KEY` field, preserving
  all prior contents, including the Apollo configuration. No key values were displayed.
- Verified the field exists, original contents are preserved, Git ignores the file,
  and permissions are 0600. Preparing to open the file for user editing.
- No API request, runtime behavior change, or outreach was performed.

## 2026-11-14 — Anthropic editor-opening attempt

- Opening `.env` in the Codex right panel failed through the app connection.
- TextEdit fallback also failed: Launch Services could not resolve/start the app
  from this execution environment. Editable UI was not opened or confirmed.
- The Anthropic key field is ready for manual editing in the editor Hardik used for
  the Apollo key. No credential contents were displayed and no API call was made.

## 2026-11-14 — Apollo and Anthropic credential presence verified

- After Hardik saved the file, verified both `APOLLO_API_KEY` and
  `ANTHROPIC_API_KEY` are populated in the project `.env`, and Git ignores `.env`.
- No credential values were displayed or logged. Key validity and permissions
  remain untested; no API request or provider spend occurred.

## 2026-11-14 — Scope status correction and existing drafting review

- Updated the stale credential-status line in `scope.md`: Apollo and Anthropic
  fields are populated locally; API validity/access remain untested. No secrets added.
- Rechecked the existing drafting prompt: LinkedIn connection invitations only;
  it explicitly prohibits referral requests and does not generate cold emails.
- Appended this entry without changing earlier log entries. No runtime code change
  or live API request occurred. Daily controls and discovery remain unimplemented.

## 2026-11-14 — Candidate-source discovery and brainstorming

- User requested searching the parent job-search folder's TeX and Markdown files for
  background and preferences using brainstorming. This step is discovery only; no
  implementation or profile content has been approved or created.
- Main source map:
  - `../resume-decisions-log.md`: later, variant-specific decisions and claim corrections.
  - `../Hardik_Lad_Resume_Amazon.tex` and `../FDE_accessibility.tex`: recent resume
    wording, with November 2 updates; inspect active content separately from comments.
  - `../Hardik_Lad_AI_FDE_SWE.tex`: explicit early-career AI FDE/SWE targeting and
    supplied relocation/remote preferences; not a universal override for other packets.
  - `../C3 Docs/PIRAMAL_CONTEXT.md`: stakeholder work, claims automation, SQL migration,
    shelf-audit work, role-specific framing, and metric divergence warnings.
  - `../C3 Docs/PROJECTS_CONTEXT.md`: BIG aviation engagement, RainStorm pair ownership,
    Job Finder, teaching, Paperscope, and explicit unverified-claim warnings.
  - `../ischool-accessibility-work-context.md`: accessibility work and boundaries on
    individual/team output, development/live work, and incomplete/proposed work.
  - `../C3 Docs/STYLE.md`: crisp, direct, specific, honest writing; one relevant hook;
    clear ask; no em dashes, contrast constructions, generic praise, or invented claims.
  - `../resume-baseline.md` and `../resume-story-points.md`: older baseline and story
    explanations. Later scoped decisions can supersede the baseline.
  - `../Understanding Systems | Creating Behavioral stories/match-my-style/references/`:
    personal style profile is explicitly provisional and samples are empty. Do not
    claim a calibrated personal voice or treat generated interview answers as samples.
- Usable background themes found: Piramal production workflow/portal work and business
  stakeholders; BIG aviation RAG work; RainStorm distributed-systems project; Job Finder
  filtering/evaluation/testing; UIUC teaching and accessibility work; education and skills.
  These are statements in local source material, not new independent verification.
- Conflicts/limits to preserve before generating a canonical profile:
  - BIG's newer Next.js/Drizzle/Postgres/SSE/cached-history description supersedes the
    older ChromaDB/Dialogflow/EC2 wording for the v2 lineage (D-21). Do not merge stacks.
  - The 85% Claude-spend claim is unverified and removed in newer scoped variants.
    Kubernetes/HPA, older BIG percentage improvements, and some teaching metrics also
    have explicit evidence gaps. Model agreement is not measured accuracy.
  - Shelf-audit time savings and approval-time figures differ across versions/scopes;
    retain the scope or omit unresolved numeric claims rather than silently combining them.
  - iSchool start date differs between the context file and later approved resume;
    D-29 records the direct October instruction taking precedence for that variant.
  - Exact team, ownership, production, accessibility certification, offline inference,
    and deployment claims must stay within documented boundaries.
  - Role-specific and older work-authorization/location statements are not automatically
    universal or current. Confirm time-sensitive details before external use.
  - C3-specific preferences and interview facts should not be applied to every company.
- Proposed next design: a concise factual candidate document compatible with the current
  drafter, separate writing/targeting preferences with explicit loading, and per-job/contact
  context. The current drafter does not automatically read parent files or style rules.
- Only this change log was written for the discovery step. No candidate/profile/examples
  file created, no resume modified, no code/settings changed, and no API call or outreach.

## 2026-11-14 — Direct resume-source decisions and Claude-context proposal

- Recorded Hardik's explicit source choices in `scope.md`: only the current Amazon
  and FDE accessibility TeX files in the parent job-search folder; no duplicate resumes
  or manually synchronized candidate biography. Other TeX variants excluded.
- Rechecked the two file headers and current drafter. Existing code sends the full
  candidate document and optional examples; it still cannot consume parent TeX files.
- Proposed, pending review: local active-text extraction and relevance selection,
  fresh reads per run, source hashes, small per-message context, Amazon precedence for
  shared work, Accessibility for its iSchool role, and explicit conflict handling.
- No runtime implementation, candidate file creation, resume modification, API request,
  prompt transmission, or outreach occurred. Only scope and this append-only log changed.

## 2026-11-14 — Full-stack resume added as a role-specific source

- Hardik explicitly added the latest Full Stack resume for SWE/full-stack-related jobs,
  expanding the previously approved two-source set to three original parent-folder files.
- Inspected `../fullstack.tex`: header currently identifies version 10, September 15,
  2026. Active BIG bullets use ChromaDB/Dialogflow CX, Docker/AWS S3/EC2, and the older
  70%/60% claims. No Kubernetes HPA claim appears in those active bullets.
- Updated `scope.md` to use Full Stack for SWE/full-stack jobs and preserve the older
  BIG description independently of Amazon/Accessibility's newer Next.js description.
- Existing evidence warnings remain: resume inclusion does not verify the older BIG
  percentage, agentic, or concurrency claims. Proposed defaults for other profiles and
  explicit overrides remain design choices awaiting runtime implementation.
- Read original sources directly; created no resume/profile duplicates. No resume,
  runtime code, provider setting, or credential changed; no API request was made.

## 2026-11-14 — Opus 5.5 high preference and call-count clarification

- Recorded Hardik's requested pilot model (`claude-opus-5-5`) and high effort in scope.
  Checked official Anthropic docs for the top-level `output_config.effort` mapping.
- Inspected saved runtime config: email drafting and separate job scoring currently
  select `claude-sonnet-5-5`; drafting has max_tokens 4096 and no explicit effort field.
- Verified drafting loops over newly found contacts: one logical call per contact with
  `--draft`, not per resume line. SDK retries can add HTTP attempts.
- Only scope and this append-only log changed. No runtime switch, API test, credit
  spending, or outreach occurred; implementation remains pending.

## 2026-11-14 — Gemini writing-style guide found and reviewed

- Found the existing saved `claude_code_writing_style_guide_skill.md` (native ID
  `libfile_c6b5db5bcefc8191b2098e6e37813cf0`) and read its full 204-line content.
- Preserved the original. The local transfer attempt failed with service DNS access;
  no local guide copy was installed. Its saved reference and this limitation are in scope.
- Recommended a compact, task-specific style block, with optional sanitized examples,
  rather than the whole guide. Exclude unrelated private correspondence and fact-sheet
  content; continue sourcing background from the three approved role-specific resumes.
- Noted mismatched metric/date/grade contexts in the guide, risks of copying application
  or attachment assertions from examples, and incompatibility of email signatures/bullets
  with the current 200-character connection-note format.
- No Gmail messages were accessed directly, no skill installed, no runtime settings or
  prompt changed, and no content sent to Claude. Only scope and this log were updated.

## 2026-11-14 — Cold-email prompt, derived profile, workflow plan, and offline walkthrough

- Hardik approved three concise bullets as the cold-email default, then expanded the
  desired inputs to person rows and company/job rows, and requested one profile Markdown.
- Created `claude_cold_email_prompt_v1.md` with full relevant writing rules, both complete
  cold-email examples with company/recipient names replaced, three bullets by default,
  and factual/application/attachment checks. Original style guide remains unchanged.
- Created draft `profile.md` from the three approved original TeX sources, common facts
  once, separate BIG profiles, source hashes, and claim restrictions. Refresh is not
  automated; no original resume was edited or duplicated.
- Saved `docs/OUTREACH_WORKFLOW_PLAN.md` with current vs proposed input/output behavior,
  Excel/CSV row contract, company/person workflows, budgets/recovery, team uncertainty,
  optional email drafting, and implementation phases. Storage/cap defaults remain proposed.
- Executed the actual local input parser/URL normalizer on fictional entries: four entries,
  two eligible unique profiles, one duplicate, one invalid company-page URL. Assembled
  an Opus-high request in memory without sending it. Report: `docs/OFFLINE_DRY_RUN.md`.
- Verified all four artifacts, two prompt examples, source hashes against all three
  original resumes, and all 79 imported upstream files byte-for-byte unchanged.
- This was not a full CLI/provider dry run. No API call, model draft, provider spend,
  Sheet write, sending, dependency install, or runtime implementation occurred.
- Updated scope to distinguish saved artifacts, approved choices, and pending features.

## 2026-11-14 — Company/job URL outreach feasibility assessment

- Used requested using-superpowers workflow as a feasibility investigation. Rechecked
  the existing Apollo URL-enrichment client, JD/ATS helpers, and workflow plan.
- Consulted current official Apollo People API Search, People Enrichment, Bulk People
  Enrichment, Authentication, and Claude Opus 5.5 migration documentation.
- Documented feasibility: resolve company/job context, search Apollo by company and
  titles/seniority, shortlist by evidence, enrich returned person IDs, and send case
  context plus the reviewed profile/style prompt to Opus 5.5 high for one draft per
  requested recipient/job. Manual LinkedIn URLs need not be mandatory after integration.
- Search returns person IDs and limited/partly obfuscated identity data, not email
  addresses. Existing URL-keyed enrichment must be extended for IDs/results. Current
  employer checks remain necessary because domain filters can include past employers.
- Limits: company website alone lacks a specific vacancy/team; a job URL can be blocked
  or omit company/team details. A title/company match is not proof of actual hiring
  manager or job-poster identity. No guaranteed email coverage or deliverability.
- Proposed first vertical slice: one job URL, or company website plus target role,
  capped discovery/enrichment, reviewable contacts/evidence, and optional cold-email
  drafts. Add Excel/CSV around that workflow after the core works. This is a design
  recommendation, not an implemented feature or a live-tested result.
- Account key permissions, plan allowance/reset/shared allocation, network access,
  dependency setup, and end-to-end live behavior remain unverified.
- No provider request, credential transmission, paid call, or code change occurred.
- Sources:
  https://docs.apollo.io/reference/people-api-search
  https://docs.apollo.io/reference/people-enrichment
  https://docs.apollo.io/reference/bulk-people-enrichment
  https://docs.apollo.io/reference/authentication
  https://platform.claude.com/docs/en/models/opus-5-5/migration-guide


## 2026-11-15 — URL-first implementation plan and checkpoint checklist

- Saved `docs/superpowers/plans/2026-11-15-url-outreach.md` with eight ordered
  implementation checkpoints, exact file responsibilities/interfaces, representative
  failing tests, verification commands, proposed CLI inputs and completion gates.
- Prioritized one job URL, or company website plus target role, through context
  resolution, Apollo discovery/ID enrichment and optional Opus 5.5 high drafts.
  Deferred spreadsheet import to a wrapper around the same service.
- Planned SQLite budgets/cache/recovery, CSV plus JSON output, optional later Sheets,
  a zero-network/no-write dry-run, local ranking with explicit employer/team evidence,
  current-employer rechecks, full approved style prompt and selected-profile facts.
- Recorded configurable initial limits: five enrichment submissions/day and five/run,
  three contacts/job, one 25-result search page/job and five search requests/day,
  three draft attempts/run and five/day. These are planning defaults, not deployed
  controls, confirmed account allocations or promises about billable credits.
- Clarified profile freshness: automatically extract changed source text/provenance,
  preserve restrictions, hold changed facts for review and keep original TeX untouched.
- Updated `scope.md` and `docs/OUTREACH_WORKFLOW_PLAN.md` to replace the earlier
  manual-person-first sequence and stale discovery exclusion with the URL-first slice.
  Scope now has matching unchecked implementation checkpoints.
- Verification: checked eight checkpoint headings, plan references in both governing
  documents, absence of placeholder markers and Python syntax in eight code examples.
  Compared all 79 imported files against the original ZIP: byte-for-byte unchanged.
- No runtime implementation, dependency installation, tests of proposed runtime code,
  provider call, credential transmission, generated live draft or message sending.
  The plan is complete; every runtime checkpoint remains pending. Before live use,
  confirm real target, key permissions, shared allowance and a bounded live-run scope.
  Correct GitHub fork/history remains required before project commits; parent Git
  was not staged, committed, pushed or reconfigured.


## 2026-11-14 (America/Chicago) — Shared Sheet input-queue proposal

- Investigated existing `shared/sheets.py`: Google authentication, row reads and
  appends exist; ready-row processing, change detection and status updates do not.
- Added a proposed Queue/Results adapter to the implementation plan and noted the
  requested workflow in scope. Sheet input reuses the planned core service and local
  ledger; it is distinct from the deferred CSV/XLSX importer.
- Proposed stable row IDs, explicit ready gating, input hashes, processed-version
  tracking, edit/reorder safety, durable claims and result-write reconciliation.
  Recommended on-demand sync first; unattended polling needs an actual worker/schedule.
- Checked official Google Sheets read/write and service-account-sharing documentation:
  https://developers.google.com/workspace/sheets/api/guides/values
  https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/batchUpdate
  https://developers.google.com/workspace/guides/create-credentials
- No runtime code, Sheet, credentials, external writes, paid API calls or automation
  was created/changed. Row format and trigger are proposed, not locked or implemented.


## 2026-11-15 (America/Chicago) — Recovered implementation record and readiness verification

This appends the implementation record that could not be saved when the local workspace
connection dropped after implementation. Earlier planning entries remain historical.
No runtime code was changed in this status-check turn; Claude Code is reviewing it.

- Checkpoint 1: added the separate `outreach` package, frozen request/result models,
  validated settings, CLI input contract and explicit project dotenv loading. Installed
  pinned direct dependencies in a clean isolated Python 3.12 `.venv`; optional Sheets
  dependencies and SOCKS proxy support are installed. System Python was not modified.
- Checkpoint 2: implemented SQLite attempt reservations, atomic daily budgets, cache,
  durable runs/claims and uncertain-attempt holds. One invocation budget covers all
  rows in a Sheet sync. Successful/no-match results expire after seven days; failed
  or uncertain attempts count, and uncertain calls are not automatically retried.
- Checkpoint 3: implemented public URL validation/fetching, checked/pinned DNS targets,
  bounded redirects/body size, JSON-LD job context and explicit pasted-JD/company/role
  fallback. ATS hosts are not assumed to be employer domains.
- Checkpoint 4: added bounded Apollo people search, local persona ranking, ID-based
  professional-email enrichment, current-employer rechecks and explicit uncertainty.
  No Prospeo/Apify, phone/personal-email reveal or waterfall is used by the new route.
  Initial orchestration enriches one person per request for durable per-person recovery;
  the adapter supports up to ten IDs. Legacy runtime/settings/tests remain unchanged.
- Checkpoint 5: added selected-profile fact loading and conservative whole-active-source
  hash checks, with generated review excerpts on changes. Per-section semantic refresh
  is deferred; changed facts never become approved automatically. No original resume
  was edited. The Full Stack/newer BIG implementations remain separate.
- Checkpoint 6: implemented one cached cold-email draft per recipient/job using the full
  approved prompt and both examples, selected facts/restrictions, Opus 5.5 high and
  explicit application/attachment flags. SDK retries are disabled; incomplete/malformed
  drafts are not silently retried. Actual personal-style calibration remains pending.
- Checkpoint 7: connected the service, private CSV/JSON exports, export/resume commands,
  strict zero-network/no-write dry-run, and the on-demand shared Sheet Queue/Results
  adapter. Stable row IDs/input hashes, explicit requeue tokens, local claims and result
  IDs prevent ordinary repeated work and reconcile ambiguous completed Sheet writes.
  Read-only `--preview-sheet` validates rows without paid calls or state writes.
- Added header-only templates at `config/sheets_queue_headers.csv` and
  `config/sheets_results_headers.csv`; installation/usage/recovery instructions are in
  `docs/URL_OUTREACH_GUIDE.md`. Updated README, env template, ignore rules, scope,
  workflow design and implementation checklist. Those edits were saved before disconnect.
- Checkpoint 8 offline verification: fresh `.venv/bin/python -m pytest -q` passed
  **686 tests** (53 new workflow tests plus 633 inherited tests). Fresh pip check reports
  no broken requirements. The real Anthropic SDK is tested with mock HTTP transport;
  no request reached Anthropic. Tests cover budgets/concurrency/DST, timeouts, safe
  errors, profile freshness, repeat/different-job caching, export failure recovery,
  Sheet readiness/edits/reordering/claim recovery and ambiguous result-write recovery.
- Additional fresh checks: all three original resume hashes match profile provenance;
  76/79 imported files are unchanged, with intended edits only to `.env.example`,
  `.gitignore` and `README.md`. All imported runtime, settings and tests are unchanged.
- Both provider-key fields are populated, but no live account/model permission check
  has occurred. `SHEET_ID` and `GOOGLE_APPLICATION_CREDENTIALS` are unset; there is no
  configured Google credentials file or connected workbook. No real runtime ledger
  has been created. `allocation_confirmed` remains false, preserving the live gate.
- Ready for no-spend validation after the independent review. Real URLs may need pasted
  JD/company/role context. A bounded real extraction/draft still needs agreed shared
  allocation and live endpoint access; Sheets additionally needs a private workbook,
  exact Queue/Results headers, Google authentication and sharing.
- No provider lookup, live draft, Sheet read/write, email/LinkedIn message, background
  schedule, Git stage/commit/push or parent-remote mutation was performed.

## 2026-11-15 (America/Chicago) — Code review of the URL outreach implementation (Cursor agent)

- Read-only review of `outreach/`, its tests and configs against `scope.md`, the URL plan and
  `docs/URL_OUTREACH_GUIDE.md`, plus an independent reviewer subagent. No code changed.
- Log gap: `scope.md` marks checkpoints 1–7 implemented and cites "latest append-only log
  entries" for test counts, but this log has no implementation entries; the last prior entry
  is the Sheet-queue proposal. Not reconstructed here to avoid inventing history.
- Verification: `.venv` full suite 686 passed. Upstream comparison with the ZIP: 76 of 79
  files unchanged; `README.md`, `.gitignore`, `.env.example` modified. Five `--dry-run`
  variants run with sockets disabled (and separately under an audit hook): no network,
  no files written, `local-data/` not created. Profile freshness hashes currently match.
- Reproduced before live use: (1) `context.py` takes `hiringOrganization.sameAs`/`url` as the
  employer, so a LinkedIn or ATS URL yields `linkedin.com`/`boards.greenhouse.io` marked
  confirmed; (2) uncertain/pending attempts and stuck Sheet claims have no reconcile command;
  (3) Sheet sync leaves claims `processing` on non-InputError exceptions; (4) dedup is by
  Apollo ID only and duplicate-email flags only fire while drafting within one run;
  (5) `tests/test_url_outreach_service.py` uses the real project root with drafting, so
  `refresh=True` can rewrite `profile.md` after a resume edit. Minor: `cto` substring matches
  "Director"; sync always exits 0; `--export-run` creates the DB.
- Assessment: dry run safe now; live run should wait for fixes to (1) and (2).
- No provider call, Sheet access, paid usage, message or Git mutation occurred.

## 2026-11-15 (America/Chicago) — Review hand-off file for Codex

- Added `docs/reviews/2026-11-15-url-outreach-code-review.md`: the review above as a
  self-contained fix brief (project rules, file:line references, offline reproductions,
  fixes, tests to add, minor issues, definition of done).
- Verification: the Issue 1 and Issue 2 reproduction snippets were executed offline and
  produced the documented output. No code changed; no network, provider or Git action.


## 2026-11-15 — Review issue 5: isolate tests from personal profiles

- Reproduced the service test using the real project root with a failing assertion.
- Added fictional temporary-project fixtures for URL tests, redirected CLI configuration
  and all profile/drafting roots, and added a session guard for the real profile hash.
- Verification: full suite with bytecode/cache writes disabled: 686 passed. Personal
  profile hash was unchanged. No real resume was copied into the fixtures.
- Runtime behavior unchanged; live calls, allocation and Git state untouched.

## 2026-11-15 — Record shared workbook setup completed in the browser

- Recorded previously completed, user-authorized browser setup of workbook
  1a4nOTFRZcjvLsUmJxcCrnkTG78spVdd6lmfODdvnN7U: Queue has 19 exact headers; Results
  has 27. Both header contracts were verified by copying their full row.
- Added styled/frozen headers, column sizing and filters. No contacts or drafts were
  uploaded. This is browser setup only, not Python API authentication or live pilot
  verification. The project was unavailable during that turn, so this record is appended now.


## 2026-11-15 — Review issue 1: trustworthy employer domains

- Reproduced social/ATS metadata being marked confirmed and careers-host conflicts.
- Prefer organization URL, handle string/list sameAs, reject social/ATS hosts, and
  normalize known www/jobs/careers/career/apply prefixes on employer domains.
- Explicit real company URLs override rejected metadata; genuine employer conflicts
  still stop. Apollo current-employer comparison uses the same normalization.
- No public-suffix dependency was added: arbitrary subdomains are not guessed away.
- Verification: full suite, bytecode/cache disabled: 693 passed; seven new cases cover
  metadata rejection, explicit overrides, lists, careers hosts and social company input.
- No live calls; allocation gate and parent Git remain unchanged.


## 2026-11-15 — Review issue 2: explicit audited recovery

- Reproduced missing recovery APIs and CLI flags with four failing regression tests.
- Added --list-pending, --reconcile ID --as error --confirm, and --release-claim ID
  --confirm. Recovery operates on existing local state without keys, allocation or APIs.
- Reconciliation retains all attempted units and creates no cache. Release covers
  related base/operation claims; reprocessing requires a new nonempty requeue token.
- Added timestamped recovery audit records and safe pending listings without payloads.
- Added read-only existing-store access; preview connections now close explicitly.
- Verification: full suite with bytecode/cache disabled: 697 passed. Unknown/terminal
  IDs, missing confirmation, unchanged usage and explicit requeue are covered.
- No live action or quota reset. Recovery documentation will be completed with the
  remaining review fixes; successful response payload import is intentionally excluded.


## 2026-11-15 — Review issue 3: terminal Sheet failures and continued processing

- Reproduced unexpected process failures and pre-processing Sheet write failures
  stranding claims. Added regressions for terminal errors, continuation and privacy.
- Status writes now happen before claiming. Base claims are acquired on requeue as
  well; process exceptions finish both claims as audited errors and continue safely.
- Errors do not auto-retry: a new explicit requeue token is still required. Ambiguous
  result writes retain completed local outcomes for result-ID reconciliation. If the
  ledger itself stays unavailable, processing stops rather than spending without it.
- Verification: full suite with bytecode/cache disabled: 699 passed.
- No external requests, allocation changes or parent Git mutations.


## 2026-11-15 — Review issue 4: profile aliases and durable email flags

- Reproduced two URL aliases spending two lookups and missing duplicate-email flags
  without drafting/across runs. Added three failing-first regression tests.
- Normalize personal LinkedIn URLs and deduplicate by URL and Apollo ID before ranking.
- Persist only normalized email fingerprints and Apollo IDs for cross-run identity
  comparisons. Flag duplicate emails independently of drafting, including current-run
  earlier owners; retain the existing one-draft-per-address current-run behavior.
- Verification: full suite with bytecode/cache disabled: 702 passed.
- This flags possible duplicate contacts for review; no email is sent automatically.


## 2026-11-15 — Review minor fixes and dry-run audit coverage

- Reproduced minor CLI/provider issues in failing-first tests: CTO substring matches,
  missing exports creating state, control-character CSV prefixes, local TypeError
  treated as uncertain, ignored timeout configuration, malformed manifests, stale
  job-only draft previews and missing sync exit status behavior.
- Fixed word-boundary persona matching and separated it from employer matching;
  added per-run attempt/result/remaining counters; made export/read-only recovery
  open existing state only; made draft timeout configurable and uncertainty specific
  to connection/timeouts/server errors. CSV prefixes and profile YAML handling are fixed.
- Verified official Apollo docs (documentation requests only): search filters and
  reveal/waterfall flags are query parameters; bulk details remain JSON. Updated
  fixtures to organization IDs and skip enrichment for explicit has_email=false.
  Sources: https://docs.apollo.io/reference/bulk-people-enrichment and
  https://docs.apollo.io/reference/people-api-search. No enrichment call was made.
- Public fetching prefers IPv4 after validating all DNS answers. Stale worker
  completion cannot overwrite a reclaimed row. Repeated cached Sheet errors still
  produce nonzero summaries/exits; budget waits remain visible.
- Added five subprocess audit-hook dry-run tests covering all review variants. They
  prohibit socket lookup/connect, mkdir/rename/remove/chmod/temp files and every
  write-mode open anywhere, and verify no runtime state directory appears.
- Verification: full suite with bytecode/cache disabled: 723 passed (37 more than
  review baseline). Real-profile hash guard passed. The five audit cases also passed
  separately. No real resume/profile edit, paid/API action, allocation change or Git
  mutation occurred during these fixes.
- Updated scope, agent quota guidance and recovery/setup guide; created the companion
  code-review-resolution report, preserving the original review. Manual recovery is
  error/release only: no successful cache import or usage refund. Canonical employer
  inference remains known-prefix based; enhanced role/JD ranking stays a follow-on.
- Browser workbook formatting from the earlier authorized turn is recorded separately;
  Python Google authentication, shared allowance and real pilot calibration remain open.

## 2026-11-15 (America/Chicago) — Final check of review fixes before dry run (Cursor agent)

- Read-only verification of Codex's fixes against `docs/reviews/2026-11-15-url-outreach-code-review.md`.
- Full suite: 723 passed. `profile.md` unchanged (mtime Nov 14 03:00); `local-data/` absent.
- Re-ran original reproductions: LinkedIn/ATS `hiringOrganization` with a bare job URL now
  stops with NeedsContext; with `--company-url` it resolves to the company and confirms;
  `careers.` subdomain no longer conflicts; genuine conflicts still stop; "Director of Sales"
  no longer matches `cto`.
- Dry runs with sockets disabled: company+role (exit 0), +draft-email (0), job URL only (2),
  `--sync-sheet --dry-run` (0); `--list-pending` refuses without creating a DB. No files written.
- Reviewed Apollo request shape (search filters and reveal/waterfall switches as query
  parameters) and recovery code (confirm-gated, units unchanged, audited).
- Sheet: workbook ID is recorded in scope/guide; `.env` has no `SHEET_ID` or
  `GOOGLE_APPLICATION_CREDENTIALS`, and no service-account JSON exists, so Sheet preview/sync
  cannot authenticate yet. `allocation_confirmed` remains false.
- No network, provider, Sheets, Git or code change.


## 2026-11-15 — Dry-run readiness and Queue input guidance

- Rechecked the exact Queue headers and row parser, then ran all five subprocess
  dry-run audit checks: 5 passed. Ran the actual CLI preview with fictional company
  URL, Software Engineer/fullstack, max_contacts=1 and draft_email requested: exit 0,
  zero network calls/writes, matching profile sources, live allocation still disabled.
- Explained user columns A–N (N left blank initially), required job URL or company URL
  plus target role, explicit ready/draft flags, profile choices and one-contact test cap.
  O–S and Results remain tool-managed. No real job row has been supplied/validated yet.
- Google Sheets API authentication remains unconfigured; strict dry-run does not read
  the Sheet, fetch websites, extract emails or call Claude. No code/config/live changes.


## 2026-11-15 — Implement one-cell input instead of fourteen-column entry

- Added `outreach/intake.py`; updated models/settings, CLI, Sheet adapter, service,
  Apollo client, profile selection and cache aliases for one URL or Full Name | Company.
- Blank row IDs/readiness are automatic, explicit FALSE holds, unchanged inputs reuse
  results, and simple input edits version automatically. Default one contact; known
  people are email-only; job/company discovery requests a draft. No broad paid fallback.
- Added API-only --setup-sheet to rename input/company headers and hide advanced columns;
  not run live. Updated README, scope and URL guide with the minimal-entry contract.
- Direct lookup validates identity/employer and conserves cached enrichment; uncertainty
  and recovery/accounting gates remain enforced. No provider calls or live gate change.
- Verification: full suite 745 passed (3.65 seconds), including minimal inputs, auto IDs,
  edit races, exact provider request shape and strict no-network/no-write dry runs.
- Saved the supplied workbook ID as SHEET_ID in ignored .env, preserving credentials.
  Google API authentication and shared allocation remain unconfigured/unconfirmed.


## 2026-11-15 — Validate supplied Queue row without paid calls

- Public Queue CSV read succeeded (HTTP 200): one nonempty row, one ready/valid,
  no invalid rows. Row 2 is a Klaviyo job with employer website supplied. Minimal
  defaults select one contact and a draft; no extra input columns are required.
- Strict CLI dry-run made zero network calls/writes and reported needs-fetch, as
  expected for a job URL without an inline JD/title. Live allocation remains false.
- Separate public-page diagnostic succeeded through requests (HTTP 200). The existing
  context parser resolved klaviyo.com, Software Engineer II - Flows Experience,
  and 7,261 description characters. No contact search/enrichment/draft was attempted.
- The production pinned-IP fetcher failed in this environment; ordinary requests
  succeeded. This runtime fetching discrepancy remains unresolved; no unsafe fallback
  or production fetch behavior was introduced.
- Correction to earlier broad read-access guidance: public CSV inspection works without
  Google credentials. Authenticated adapter reads/writes and result synchronization
  still need Google API authentication. No live Sheet values/layout were changed.


## 2026-11-15 — Proxy-aware public fetching and first bounded live acceptance

- Root cause: local DNS returned gaierror while the runtime HTTP proxy could fetch
  the same page. Added HTTP_PROXY/HTTPS_PROXY/NO_PROXY support in outreach/context.py.
  When proxied local DNS is unavailable, fixed HTTPS DNS resolution supplies public
  addresses; CONNECT targets the validated IP while origin TLS/SNI remain unchanged.
  Redirects are revalidated; private/mixed DNS answers and proxy failures fail closed.
  No direct fallback or TLS verification bypass. Documented network behavior in guide.
- Added six regression cases in tests/test_url_outreach_proxy_fetch.py, observed three
  fail before the implementation, then 23 context/proxy cases passed. Existing direct
  IPv4 test now explicitly isolates proxy environment. Full suite: 751 passed (3.04s).
- User authorized proceeding after the bounded-test proposal. Used an in-memory
  settings override for this one row only: one search page, one enrichment and one
  draft maximum; preserved persistent allocation_confirmed:false and daily settings.
  This does not establish an ongoing shared-account allocation.
- Production fetch succeeded on the supplied Klaviyo page. Full Stack source freshness
  preflight passed. Live run 633ebbc6884741f5b9806856bb1f1a1a completed: one search, one
  enrichment, one found professional email (Apollo verified), one Opus 5.5 high draft,
  no failed attempts/retries. Current employer confirmed; hiring/team relationship
  remains unconfirmed. Sender application/attachment status not invented.
- Saved ledger/checkpoints plus private local CSV/JSON and klaviyo-first-pilot.md
  under ignored local-data/. Reopened ledger read-only and verified completed status,
  no pending provider attempts, exact call counts and persistent live gate still off.
- Google service-account/ADC credentials absent; no Sheet API write/layout call made.
  Public CSV was used for input. No contact email/draft text written to this log,
  no message sent, no schedule/Git action enabled. Sheet write-back remains pending.


## 2026-11-15 — Company contact reuse, exact-job reuse and GitHub publication preparation

- Hardik selected the recommended policy: a new job at an existing company reuses a
  suitable saved contact and requests one fresh draft per recipient. Exact completed
  job duplicates reuse the whole result with no page/Apollo/Claude request. Saved the
  approved design and checkpoint plan under docs/superpowers/.
- Added outreach/reuse.py canonical company/job identities (retain job IDs, strip known
  tracking fields), draft dependency signatures and safe pre-upgrade history indexing.
  Added expiring completed snapshots and company-contact provenance to the local Store.
  Reuse inherits original enrichment expiry; old/unsuitable data stops for review.
- Integrated reuse into service.run before network/provider work. New jobs locally
  re-rank fresh confirmed-employer contacts and clear old team certainty. Changed
  drafting inputs/profile/source/prompt/model invalidate full-result reuse. Existing
  budgets, uncertain attempts, recovery and local checkpoints remain in effect.
- Queue publishes each appended duplicate row with its own result/run identity, marks
  exact reuse in status, and reconciles repeated publication without another paid run.
  Added selection_reason/reuse_type/reused_from_run_id to exports and optional Results
  columns. API-only setup appends headers and expands the grid without deleting data.
- Added 14 behavioral regressions, observed failures for missing reuse/history/output
  and grid-expansion behavior, then passed the focused suites. Full suite: 765 passed
  (3.70s). Strict dry-run audits remain included. No prompt wording or real profile edit.
- Verified the existing bounded Klaviyo run can be indexed/reused with provider and
  page callbacks forbidden: zero search/enrich/draft submissions; original allowance
  unchanged and persistent allocation_confirmed remains false. No new paid test.
- Updated README, scope, guide, AGENTS/CLAUDE and provenance. Google API authentication
  is still absent, so live Sheet write-back/layout remains pending. Current contact
  selection remains company/title based; exact HM/team authority is not established.
  No background monitor, message sender, Notion integration or new workflow enabled.
- Restored genuine upstream Git ancestry from the original import commit in this folder,
  preserving the friend's upstream remote and leaving parent Git/worktree files alone.
  Prepared main for private HardikLad10/apollo-email-scraper-agent, as requested.
- Moved inherited scanner YAML outside .github/workflows so publishing cannot activate
  its cron. Expanded dotenv ignore rules and normalized CSV header line endings.
  Pre-publication audit: 134 tracked/staged files, two configured credential values
  checked without printing them, zero key matches, zero private runtime files, zero
  active workflow files. Real .env, profile, SQLite/exports and venv stay ignored.

## 2026-11-15 (America/Chicago) — Cold-email draft v2 design (Cursor agent)

- Added `docs/superpowers/specs/2026-11-15-cold-email-draft-v2-design.md` after a
  brainstorming session with Hardik. Decisions: verbatim first bullet (Hardik's confirmed
  graduation/authorization/availability sentence, kept only in gitignored `profile.md`), job URL in
  every body, all eligible profile facts sent with the full JD, 1–2 fit lines grounded in
  the JD plus Claude web search (max 2 searches), networking draft when no job URL,
  100–140 word target with local checks.
- Evidence: live Klaviyo draft was 176 words with no link; Claude received the full JD but
  only six locally selected facts. Research sources are listed in the spec.
- Design only: no code, prompt, profile or settings changed; no API calls; not committed
  because Codex is concurrently committing/pushing. Implement after Codex's push, on a
  separate branch.


## 2026-11-15 — Private GitHub push verified

- Published tested implementation commit a49a32902a6aeea8ede298ab5a6ee14f7ae6b5e4
  to https://github.com/HardikLad10/apollo-email-scraper-agent on main.
- GitHub API confirmed private visibility, default branch main, matching remote/local
  implementation SHA, and zero active Actions workflows. No secrets were uploaded.
- Full implementation suite passed 765 tests; the existing Klaviyo outcome was reused
  locally without website/provider calls. Google API credentials remain the write-back
  blocker. No extra live allowance or schedule was enabled.
- Parallel Cursor draft-v2 design and its pending log entry were left untouched and
  excluded from this tested implementation push. This receipt is staged separately
  so the other agent's uncommitted work is preserved.


## 2026-11-15 — Repository made public at user request

- Changed HardikLad10/apollo-email-scraper-agent from private to public using the
  GitHub API, as explicitly requested. GitHub returned private:false/public visibility.
- Verified the repository page returns HTTP 200 through an unauthenticated request.
  Earlier private-visibility notes describe the initial publication and are historical.
- No code, secrets, contact exports, workflow configuration or paid-provider call changed.

## 2026-11-15 20:43 (America/Chicago) — Anthropic web search availability check (Cursor agent)

- At Hardik's explicit request, made one live Anthropic Messages call (`claude-haiku-4-5`,
  `web_search_20250305`, `max_uses: 1`, about $0.01). Result: `end_turn`, 1 search used —
  web search is enabled for the organization. No key or output saved; no outreach data touched.

## 2026-11-15 (America/Chicago) — Cold-email draft v2 implemented (Cursor agent)

- Branch `feat/cold-email-draft-v2` (this repo's own Git; parent repo untouched). Plan:
  `docs/superpowers/plans/2026-11-15-cold-email-draft-v2.md`.
- `outreach/profile.py`: Claude now receives every eligible shared and selected-profile
  fact (17 for the real fullstack profile, previously the top 6 by keyword overlap) and
  picks the JD-relevant ones itself.
- `outreach/drafting.py`: case data adds `job_url`, `email_mode` (job/networking),
  `required_first_bullet` (from the `work_authorization` fact) and mode-specific format/ask;
  web search server tool (`web_search_20250305`) with `max_uses` from the new setting
  `draft_web_search_max_uses` (default 2, 0–5, 0 disables); one `pause_turn` continuation;
  text blocks joined without separators and leading narration dropped; flags
  `web_searches:<n>`, `source:<url>` and `over_length` (>150 words). Hard failures: job URL
  missing from the body, first bullet not the authorization sentence, bullet count not 3
  (job) / 2 (networking). HTTP 400 with search enabled names the setting to disable it.
- New `claude_cold_email_prompt_v2.md` (v1 kept): 100–140 word job format, link in the
  opening line, 3 bullets, 1–2 grounded fit lines, one ask; 70–110 word networking format;
  fictional examples only. `outreach/main.py` loads v2; prompt hash change means existing
  cached drafts are not reused.
- Local `profile.md` (gitignored): added the `work_authorization` fact and a matching claim
  restriction; removed work authorization/start date from the do-not-infer list.
- Verification: 789 tests passed offline (24 new); offline real-profile message build and a
  real-SDK mocked `pause_turn` round trip passed. No live provider calls, sends, Sheet writes
  or pushes. `allocation_confirmed` remains false.


## 2026-11-15 — Review Claude v2 and prepare mixed URL final acceptance

- Read Claude's completed v2 handoff and verified its committed branch; baseline 789
  tests passed. Retained v2 wording, all-profile-fact input, job link and networking mode.
- Added outreach/linkedin_posts.py and Request.linkedin_post_url; routed posts through
  explicit public author metadata to direct Apollo lookup. Extended intake/context,
  service, Sheet parser and CLI preview/help; LinkedIn job URLs remain job inputs.
  Missing/private/ambiguous authors request a personal profile without paid work.
- Personal profile/post rows are email-only by default; optional company constraints
  share normalized profile enrichment cache entries, preserving original expiry.
  Post evidence and accurate direct-person selection reasoning are included in outputs.
- Fixed job/draft/history cache identity for draft_web_search_max_uses. Automatic Sheet
  claims now version drafting dependencies, while failed claims cannot retry just
  because the prompt changes. No raw keys/personal authorization text added to sources.
- Added api_requests counts to draft flags. Verified official Anthropic documentation:
  max_uses already counts searches across the paused tool turn. Preserved the same tool
  definition on continuation; the initial reset-cap hypothesis was corrected, not shipped.
- Missing Google credentials now explain GOOGLE_APPLICATION_CREDENTIALS/ADC setup.
  Added exact setup guide and readiness review; updated normal input guide/README,
  current public-origin agent guidance and scope. Routine updates remain API-only.
- Full suite: 804 passed (4.25s), 15 more than Claude's baseline, with failing-first
  coverage for the gaps and nine strict no-network/no-write dry-run variants.
  Real Full Stack profile freshness passed; 17 eligible facts and required first bullet
  present. Tests did not modify the private profile or original TeX files.
- Zero live provider calls, Google writes, messages or new schedules during review.
  No pending attempts/row claims; persistent allocation_confirmed remains false.
  Google credentials are still missing, so final Sheet-to-Sheet live acceptance is
  pending the one-time connection and user-supplied new test URLs.
