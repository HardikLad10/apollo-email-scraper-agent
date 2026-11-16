# Apollo Email Extraction Outreach Specialist — scope

## Goal and ownership

Hardik is piloting a month of Apollo access shared with a friend to determine whether
finding professional emails and doing targeted outreach leads to useful replies,
conversations, referrals, or interviews. The paid access already exists; the actual
pilot start/end dates, plan allowance, and Hardik's share remain unconfirmed.

Source: https://github.com/pratyushagarwal22/job-hunt-tools

Read `docs/SOURCE_PROVENANCE.md`, `docs/CODEBASE_REVIEW.md`, and the latest entries in
`CHANGELOG.md` before continuing. This document governs the pilot; upstream
`docs/DESIGN.md` and `docs/PLAN.md` describe the friend's broader project and contain
some planned behavior that is absent from this snapshot.

## Current state

- Originally imported 79 upstream files. Legacy runtime remains unchanged; pilot setup/docs changes are recorded below.
- Imported commit: `ffe7aee7a57aa9030d886ebb00089579fe867041`, branch `master`.
- Original ZIP import now has genuine upstream Git history restored in this folder;
  origin is the private HardikLad10/apollo-email-scraper-agent repository.
- Apollo and Anthropic key fields are populated in the ignored local `.env`; their
  Apollo search/enrichment and Anthropic drafting passed one bounded live test.
  Google API credentials remain absent. No credential values belong here.
- One bounded live extraction and draft completed; no Sheets API write or message
  was sent. The shared Queue/Results template was created in an earlier browser step.
- Upstream runtime behavior remains unchanged. Its 20-URL cap is per run, not per day.
- Implemented the separate `outreach` CLI: job/company context, Apollo discovery and ID enrichment, durable budgets/cache, profile freshness checks, Opus-high cold emails, CSV/JSON and a shared Sheet queue. The provider path has one bounded live acceptance; Sheet API write-back is mock-tested only.
- Saved the URL-first implementation checklist at
  `docs/superpowers/plans/2026-11-15-url-outreach.md`. Planning is complete for this
  slice; checkpoints 1–7 are implemented offline and checkpoint 8 awaits live acceptance.

## Authorized requirements

1. Reuse and build on the useful parts of the friend's repository.
2. Keep initial extraction volume small and easily configurable, with a daily limit.
3. Summarize the file structure, existing features, and implementation gaps after review.
4. Maintain an append-only Markdown change log across agents and sessions.
5. Keep this scope document current and provide instructions usable by Codex and Claude Code.
6. Apply the requested `using-superpowers` workflow when available. Its current local
   entry point is `/Users/hardiklad10/.codex/skills/using-superpowers/SKILL.md`;
   this machine-specific path is optional for other agents, not a runtime dependency.

## Confirmed resume-source choices — November 14, 2026

- Approved TeX sources are `../Hardik_Lad_Resume_Amazon.tex`,
  `../FDE_accessibility.tex`, and `../fullstack.tex`. The third source was explicitly
  added for SWE/full-stack targeting after the initial two-source decision.
  Other TeX variants are excluded from future drafting inputs.
- Use `../fullstack.tex` as the resume source for SWE/full-stack-related jobs. Its
  active BIG section describes the older ChromaDB/Dialogflow CX and Docker/AWS work.
  Preserve this as a separate profile; do not combine it with the newer BIG stack.
- Read the original files in the parent job-search folder; do not make duplicate TeX
  copies. Hardik subsequently requested one derived `profile.md`: that snapshot now
  exists for review. Original resumes remain authoritative; active-text freshness detection and generated review excerpts are implemented. Changed facts require local review before drafting.
- The new `outreach` loader reads the three originals and reviewed `profile.md`. The inherited connection-note drafter still expects `config/candidate.md` and is unchanged.
- The plan/context were reviewed first; Hardik subsequently authorized implementation. Live calls/sending remain separate from that implementation authorization.

Proposed handling for review: read active document text from the explicit configured
paths on each run, ignoring historical comments and LaTeX layout code. Build a temporary
in-memory fact set and retain source hashes/references for provenance. Do not choose a
newly named "latest" file by modification time without an explicit path change.
Proposed role defaults: Full Stack for SWE/full-stack targeting; Amazon for AI/FDE
and application-development targeting; Accessibility for accessibility-related roles.
Use the selected profile's shared experience consistently, with an explicit override
for overlapping roles. Do not merge BIG implementations across profiles. Existing
claim restrictions still apply: older BIG percentage/agentic/concurrency claims have
verification warnings and must not be promoted to verified facts by selecting Full Stack.
Flag substantive unresolved disagreements before using them.
Existing Markdown files remain sources for local writing preferences and claim
restrictions, not additional TeX resumes to send to Claude.

Proposed Claude context: concise message-type/output rules, relevant writing constraints,
recipient basics, applicable job requirements/context, a small set of supported candidate
facts, and the intended ask. Select facts locally first; do not send the whole folder,
raw TeX, historical comments, decision logs, credentials, or unrelated personal details.
Job-specific cold-email drafting is implemented in the new route; the inherited note drafter remains separate.

## Confirmed Claude model preference — November 14, 2026

- Hardik requests Claude Opus 5.5 with high effort for the pilot's Claude API calls.
- Target direct-Anthropic configuration: `model="claude-opus-5-5"` and top-level
  `output_config={"effort": "high"}`. High is an effort setting, not part of the model ID.
- Official documentation consulted: https://platform.claude.com/docs/en/models/opus-5-5/migration-guide
  and https://platform.claude.com/docs/en/build-with-claude/effort.
- The new cold-email client uses this configuration with 8192 max tokens and SDK retries disabled. The inherited connection-note drafter and separate job scorer remain Sonnet 5.5 and have not been rewired.
- Existing drafting makes one logical SDK call per newly found contact when `--draft`
  is enabled, not one call per resume bullet/input text line. Skipped contacts and
  lookups without a found email receive no draft. SDK retries may cause additional
  HTTP attempts; this is not a strict network-request cap.
- No live model/access/credit validation has been performed. During implementation,
  check SDK compatibility and thinking/output budget without silently changing the
  requested model or effort.

## Writing-style guide review — November 14, 2026

- Hardik supplied a Gemini-generated guide based on Gmail writing/replies, titled
  `claude_code_writing_style_guide_skill.md`. The existing saved file was found and
  read in full (204 lines, 16,552 bytes); original content was not modified.
- Saved source: `/job-search/claude_code_writing_style_guide_skill.md`, native file ID
  `libfile_c6b5db5bcefc8191b2098e6e37813cf0`.
- User-facing source: https://chatgpt.com/library?file_id=libfile_c6b5db5bcefc8191b2098e6e37813cf0&account_id=personal
- Local-copy attempt failed because the current transfer helper could not reach its
  service. There is no local project copy of the guide yet. Do not claim the runtime
  can load it from a local path until it has been made available and verified.
- The guide mixes style rules, correspondence examples, application examples, and a
  candidate fact sheet. Its style does not override the three approved resume sources
  for background facts. Original emails were not independently retrieved or audited.
- Approved cold-email direction: complete relevant style rules plus both full cold-email
  examples, with names anonymized; three concise bullets by default. This supersedes
  the earlier tiny-style-block/optional-example proposal. Exclude unrelated private
  correspondence and the guide's fact sheet. `claude_cold_email_prompt_v1.md` is saved;
  API integration is implemented and mock-transport tested; real-draft calibration remains pending.
- Keep format constraints separate: connection notes remain one line, at most 200
  characters, with no signature or referral ask. Cold emails/replies need their own
  formats; the current Python drafter does not implement them.
- Do not copy claims that an application was submitted, a resume attached, or an action
  completed from a style example unless the current task explicitly confirms that fact.
- Merely saving a Markdown file with skill frontmatter does not make the Python
  Anthropic client load it. The new cold-email client explicitly loads the approved prompt; it does not install the original guide as a skill.

## Expanded workflows and review artifacts — November 14, 2026

Hardik described two desired data workflows: (A) supplied LinkedIn URLs to email lookup,
and (B) company/job-description/job-URL rows to relevant people, enrichment, and optional
job-specific cold emails. The next implementation prioritizes the single job/company
URL workflow; bulk row imports follow it. Discovery is implemented offline; bulk file import is deferred.
The legacy input remains LinkedIn URL arguments/plain text. The new `outreach` route accepts job/company inputs and Sheets Queue rows, provides cold emails and strict dry-run; Excel/CSV file import is still absent.

- `claude_cold_email_prompt_v1.md`: exact reusable cold-email instructions; three bullets
  default; two source examples; application/attachment and factual checks.
- `profile.md`: one reviewed-source snapshot, common facts once and role-specific BIG
  descriptions separate. Source hashes and claim restrictions included. Active-text hashes now guard paid drafting; changed originals generate review excerpts and block until reviewed. Do not treat newly extracted text as approved facts.
- `docs/OUTREACH_WORKFLOW_PLAN.md`: current contract, proposed Excel/CSV columns,
  workflows, request boundary, persistence/output recommendation, phases, and checks.
- `docs/OFFLINE_DRY_RUN.md`: actual local parser/normalizer demonstration plus a locally
  assembled proposed request. No real provider results/drafts and no network requests.

The implementation plan uses SQLite for quota/recovery and CSV plus JSON output, with
XLSX import/export and optional Sheets as follow-on work. Current code still requires
Sheets. This is implemented in the new route; it does not change legacy storage.
The five-profile daily cap and search/selection defaults are enforced local defaults, not confirmed account allowances. Keep company/team match evidence and uncertainty in
results; company/title matching does not prove membership of a particular hiring team.

One logical Claude call is made per uncached requested recipient/job pair; one company row can
produce multiple recipient drafts. Reuse enrichment across jobs where appropriate.
No automated sender, inbox reader, live test, or runtime workflow change is authorized
merely by saving these design artifacts.

## Implemented first slice — single URL, offline verified

Build one job URL, or company website plus target role, into a capped shortlist,
Apollo professional-email enrichment and optional Claude cold-email drafts. Implement
the checklist in `docs/superpowers/plans/2026-11-15-url-outreach.md`. This supersedes
the earlier manual-LinkedIn-first sequence. Reuse useful existing code conventions,
but isolate the new CLI/service from legacy Sheets requirements. Keep the scanner
outside this slice. Spreadsheet input will wrap the same service in a later release.

- Accept `--job-url`, or `--company-url` plus `--target-role`; permit supplied JD,
  employer/role overrides and explicit profile selection when fetching is incomplete.
  Require explicit `--draft-email` for Claude use. No manual LinkedIn URL is required
  once discovery is implemented.
- Default to **5 new enrichment submissions per day and at most 5 per run**, whether
  identified by Apollo ID or LinkedIn URL, with at most 3 contacts per job. Limit search
  to 1 page/job, 25 results/page and 5 requests/day; drafts to 3/run and 5/day. These are
  configurable local controls, not verified credit costs.
- Start with technical-recruiter and engineering-manager/HM candidates. CEO/CTO are
  explicit persona choices, not automatic fallback recipients. Title matches alone
  never establish the actual job poster or HM. Recheck current employment after
  enrichment; unknown/mismatched employment is not eligible for automatic drafting.
- Keep daily and per-run settings in one documented configuration location. Configure
  the quota timezone explicitly, initially proposing `America/Chicago`.
- Count profile submissions attempted before making paid requests, including uncertain
  timeout outcomes. Track found emails separately; a submission count is not a verified
  Apollo credit count. Do not refund uncertain attempts automatically.
- Persist usage across process restarts and repeated invocations, reserve capacity
  atomically before requests, and protect concurrent local runs from exceeding the cap.
- Keep lookup/draft checkpoints before exporting locally so failed exports can be
  retried without paying for extraction again. Sheets is optional follow-on work.
- Deduplicate Apollo IDs and normalized profile URLs; flag repeated emails across
  distinct identities. Reuse fresh enrichment across jobs, with distinct job drafts.
- Add a dry run that validates input and shows planned count and remaining allowance
  without contacting websites/providers, reserving quota or writing any runtime file.
  A job URL alone cannot reveal its job description offline; show missing context and
  planned fetching rather than fictional shortlist or draft results.
- Fail closed on invalid quota settings, unavailable/corrupt accounting state, and
  exhausted quota. Do not silently use another paid provider or retry uncertain requests.
- Display attempted, found, not found, failed/uncertain, skipped, and remaining counts.
- Refresh extracted resume text/provenance from the approved originals when it changes,
  preserving claim restrictions. Changed facts require reviewed bindings before paid
  drafting; automatic freshness detection must not silently approve new metrics.
- Load the complete reviewed cold-email prompt and both examples; send selected-profile
  supported facts and pertinent job/recipient context. Use Opus 5.5 high, one logical
  draft per requested recipient/job, and no hidden SDK retries or extra critique calls.
- Store secrets in ignored local files; never put real keys or contact exports in logs,
  examples, commits, or this scope document.

A local quota can limit this tool's usage only. It cannot constrain the friend's
separate tools or other activity on the shared Apollo account. Confirm an agreed
credit allocation and compare it with actual account usage before live runs.

## Measuring the pilot

Record a baseline and review date once the pilot dates and available allowance are known.
Track each contact's lookup source/status, outreach channel and date, message version,
reply status/date, bounce, positive response, referral, and interview outcome. Allow
manual updates first; distinguish pending delivery from confirmed delivery.

Useful measures: emails found / profiles attempted; bounces / emails sent; replies /
emails sent; positive replies / emails sent; referrals and interviews; and credits or
cost per useful response where actual consumption is available. Use explicit date
windows and denominators; do not infer delivery or replies from a `contacted` checkbox.

## Explicitly outside the initial pilot

- Automated email sending, scheduled sequences, inbox reading, or LinkedIn actions.
- LinkedIn scraping/actions, phone enrichment, or personal emails. Apollo-based people
  discovery is now part of the planned URL workflow; exact HM identity is not guaranteed.
- Expanding the job scanner, enabling its cron, or implementing the incomplete Workday flow.
- Prospeo/Apify spending, new subscriptions, or a hosted UI.

These can be reconsidered when Hardik requests them. The project goal does not itself
authorize sending messages; each sending workflow needs an explicit user instruction.

## Next sequence and checkpoint tracking

The detailed plan contains the exact files, interfaces, representative failing tests,
verification commands, completion gates and deferred work. Complete each checkpoint
before checking it off; update this scope and append verification to the log as work proceeds.

- [x] Save the URL-first implementation plan and reconcile the scope/design documents.
- [x] 1. Isolated setup, validated configuration and CLI input contract.
- [x] 2. Durable spending limits, cache and interruption recovery.
- [x] 3. Job/company URL context resolution and explicit missing-context fallback.
- [x] 4. Apollo search, evidence-labelled shortlist and ID-based email enrichment.
- [x] 5. Fresh resume/profile loading and claim restrictions.
- [x] 6. Opus 5.5 high cold-email drafting using the full reviewed style prompt.
- [x] 7. End-to-end single-URL command, CSV/JSON output and zero-network dry-run.
- [ ] 8. Offline acceptance/docs are complete; actual Sheet/account access and bounded live pilot are pending.

Original Git ancestry is restored. Preserve ignored secrets/local data and never mutate parent Git. Offline implementation does not require
paid calls. Before live acceptance, confirm plan/key access, allowance/reset, shared
allocation and daily caps, and select a real job URL or company/role. Start the live
test with at most one search page, one person enriched and one draft under its explicit
authorization. This planning step does not authorize the live test or any sending.

## Completion criteria for the first implementation

- Daily usage survives restarts; repeated and concurrent invocations cannot bypass it.
- Duplicate input consumes no extra lookup; batches cannot exceed remaining capacity.
- Invalid/zero/negative limits, day rollover, provider errors/timeouts, exhausted allowance,
  failed exports, and recovery are covered by meaningful tests.
- Dry run spends zero provider credits and makes no external writes.
- A job/company URL leads to traceable company/role context, bounded discovery,
  current-employer checks and reviewable contact outcomes; exact HM/team claims require evidence.
- Optional cold-email drafts use the selected fresh profile, complete approved prompt,
  Opus high and correct application/attachment flags, with no sending.
- Only configured providers run; keys and contact data stay out of diagnostic output.
- Documentation explains setup, controls, recovery, outcomes, and remaining limitations.
- Every change and its verification is appended to `CHANGELOG.md`.


## Shared Google Sheet queue — template ready, API not connected

The new adapter reads the private workbook's `Queue` tab, processes ready rows through
one shared guarded service, and writes `Results` plus Queue statuses. Lock the concrete
v1 headers in `config/sheets_queue_headers.csv` and `config/sheets_results_headers.csv`.
The supplied workbook is `1a4nOTFRZcjvLsUmJxcCrnkTG78spVdd6lmfODdvnN7U`; Queue/Results headers were verified in-browser (19/27). Python Google authentication remains a setup input; routine processing uses the API, not browser automation.

Run on demand only. `--preview-sheet` reads/validates without provider calls or writes;
`--sync-sheet` processes ready rows. `--dry-run` performs no network at all. Stable row
IDs/input hashes, explicit `requeue_token` for reviewed changes, local claims and result
IDs prevent ordinary repeated paid work and reconcile ambiguous completed writes.
An interrupted/uncertain claim is held for manual investigation. One worker/workbook;
Sheets status updates cannot provide atomic compare-and-swap against concurrent editing.
Do not sort/edit while a sync writes statuses. No background monitor is enabled.

## Implementation verification and remaining acceptance — November 14, 2026 (Chicago)

- New tests cover strict inputs, durable/concurrent/DST budgets, uncertain attempts,
  Apollo payloads/status errors, current employment, profile restrictions/freshness,
  Opus effort and full prompt, end-to-end cache/export, Sheet row gating and recovery.
- Real Anthropic SDK was exercised against a mock HTTP transport, with no external call.
- Fresh isolated `.venv`, pinned direct requirements and dependency checks are in place.
- New route uses one-person enrichment calls initially for simple per-person durable
  accounting; the Apollo adapter accepts up to ten IDs. Search pages are bounded.
- Conservative v1 profile guard binds reviewed facts to whole active original documents,
  not per-section semantic refresh. Changes trigger generated review excerpts and hold
  drafting; raw new claims never become approved automatically.
- No live provider/account validation, Sheets API request, paid call, message, schedule or Git mutation has occurred. Browser-only workbook formatting is recorded separately. Shared allocation remains unconfirmed and live mode defaults off.
- Setup guide: `docs/URL_OUTREACH_GUIDE.md`. Detailed evidence/actual test counts are
  recorded in the latest append-only log entries. Complete live acceptance only after
  the target workbook/job, Google access and bounded shared usage are agreed.


## Code-review resolution — November 15, 2026 (Chicago)

The five important findings in `docs/reviews/2026-11-15-url-outreach-code-review.md`
are fixed with regression tests: hermetic tests; trustworthy employer domains; explicit
local recovery; terminal Sheet error handling; URL deduplication/durable email flags.
Actionable minor findings are fixed too; details and limits are in the companion
`2026-11-15-url-outreach-code-review-resolution.md` and appended log entries.

Recovery is explicit and audited: list pending IDs, reconcile attempts as error without
refund/cache, release stuck claims, then set a new requeue token. No paid retry occurs
without a new run/requeue; uncertain attempts still require reconciliation. Known
prefix stripping is conservative rather than full registrable-domain inference.
Target-role/JD-based ranking beyond the current title/team matching remains a design
follow-on; title matches do not establish actual HM or team ownership.

Offline verification and strict five-variant dry-run audit are complete. No live gate
was enabled. Next steps are supplied URLs for no-spend validation, then separately
bounded live acceptance after shared allocation and Google API access are established.


## Simplified input contract — November 15, 2026

Hardik rejected the 14-column entry workflow. Normal input is one LinkedIn/job/company
URL, or Full Name | Company (with an optional separate company/notes cell). The current
Sheet accepts these in C, with optional company in D; no IDs/ready/profile/cap/token
entry is needed. Advanced columns remain compatible and can be hidden by --setup-sheet
once Google authentication exists. Setup and processing use the API, not RPA.

Implemented: generated/persisted row IDs, blank-ready defaults, hash-based simple-row
versioning, one-contact default, direct person enrichment and shared guarded recovery.
LinkedIn/name requests are email-only by default; job/company discovery defaults to
Claude drafting. All defaults are centralized. Explicit row overrides remain supported.
No inferred application submission or attachment is allowed. No background schedule,
uncertain retry, live allowance change or provider call is authorized by simplifying input.
Named-person identity/current employer are checked, low/ambiguous matches are flagged,
and no broad search or second paid enrichment is used for a known person. Cache aliases
reuse resolved people across URL/ID lookups without extending the original expiry.


## First supplied row validation — November 15, 2026

Public CSV inspection of the supplied workbook works without Google authentication.
One Klaviyo row validated; its public page resolved to Software Engineer II - Flows
Experience using the existing parser on an ordinary HTTP diagnostic response. The
production pinned-IP page fetcher failed in this environment and needs investigation
before end-to-end acceptance. Google API synchronization/writes remain unconfigured,
shared allocation remains unconfirmed, and no paid lookup/draft was run.


## Bounded live acceptance — November 15, 2026

The runtime proxy/DNS fetching issue is fixed with public-IP pinning and origin TLS
validation preserved. Full suite: 751 passed. The user authorized the first Klaviyo
row run capped at one search, one enrichment and one draft. It completed with one
Apollo-verified professional email and one Opus 5.5 high draft using Full Stack facts.
Employer confirmed; actual hiring/team authority remains unconfirmed. This is live
acceptance of that single path, not proof of deliverability or ongoing account scope.

Results/checkpoints and a readable review file are in ignored local-data/exports/.
No email was sent. Google API write-back still needs credentials. Persistent
allocation_confirmed remains false; the bounded authorization was applied only in
memory for that run. General/shared allocation and broader workflow acceptance
remain open. Public Sheet input required no further user columns.


## Approved reuse policy and Git publication — November 15, 2026

Hardik approved the recommended policy: exact job/company duplicates reuse complete
results, while a different job at the same company reuses a suitable saved contact
and makes one new Claude call per recipient for that role. Canonical URL identities
preserve job IDs and ignore known tracking fields. Draft dependencies include notes,
application/attachment claims, profile/source snapshots, prompt and model settings.

Implemented locally: expiring completed-job snapshots; a confirmed-employer/email
contact pool inheriting original enrichment expiry; history restoration for existing
runs; new-job local contact re-ranking; old team certainty reset for the new role;
per-row duplicate publication, reused status and optional result provenance columns.
No job-specific hiring relationship is inferred. Ranking remains company/title based.
Expired results/unsuitable saved contacts stop for reviewed refresh without silently
paying. Failed/uncertain work stays subject to existing recovery gates.

The Sheet flow uses Google APIs only. One-time --setup-sheet appends the three reuse
columns without overwriting existing rows and expands the Results grid if needed.
Live write-back still awaits Google credentials; no background trigger is configured.
Draft wording, stronger contact discovery/ranking, Notion and runner hosting remain
separate future decisions. Persistent general live allocation remains false.

User requested pushing the project as apollo-email-scraper-agent. Restore genuine
ancestry from the original import commit, keep the friend's upstream remote, publish
privately under HardikLad10, exclude secrets/personal runtime records, and move the
inherited scanner workflow outside the active workflows directory. Parent Git and
original TeX sources must remain unchanged.


## Repository visibility — November 15, 2026

Hardik explicitly requested public access. Origin at
https://github.com/HardikLad10/apollo-email-scraper-agent is now public; anonymous
page access was verified (HTTP 200). Earlier private-publication notes are historical.
Secrets/private runtime records remain excluded; no scheduled workflow was enabled.


## Cold-email draft v2 — November 15, 2026

Hardik approved a shorter draft format: his confirmed graduation, work-authorization and
immediate-availability sentence is always the first bullet (stored only in local
`profile.md`); the job URL is always in the body; Claude reads the full JD with all eligible
profile facts and may run up to two web searches for company values/success factors to
write 1–2 fit lines; target 100–140 words. Without a job URL, a short networking draft is
written instead. Design: `docs/superpowers/specs/2026-11-15-cold-email-draft-v2-design.md`;
implemented on branch `feat/cold-email-draft-v2`, pending one paid comparison draft.


## V2 handoff review and mixed LinkedIn input — November 15, 2026

Reviewed Claude's completed v2 branch and retained its writing/format decisions.
The shared input now supports personal LinkedIn profiles (direct email-only lookup),
public post URLs (explicit personal-author resolution, then direct lookup), and job
URLs including LinkedIn jobs when readable. Company remains optional for known people.
Blocked/ambiguous/company-authored posts request the personal profile URL before any
paid call. No profile scraping, slug guessing, commenter extraction or automated sending.
Optional known-person drafts use v2 networking mode, not an invented vacancy.

Fixed v2 integration: web-search settings invalidate completed-job/per-draft reuse;
automatic completed Sheet rows detect prompt/profile/settings upgrades; failed claims
remain gated for review. Actual Claude request counts are exposed in draft flags.
The documented max_uses cap already applies across paused-turn continuations and is
preserved unchanged. Stronger company-contact targeting remains a separate limitation.

Verification: 804 passing offline tests, including nine strict dry-run variants;
real profile freshness passed without edits, with 17 eligible Full Stack facts.
No paid provider call or Sheet write occurred. Credentials/ADC are still absent and
routine live remains off. Google API setup is the remaining external dependency;
see docs/GOOGLE_SHEETS_SETUP.md and docs/reviews/2026-11-15-v2-intake-readiness.md.
Once connected, the user adds C=input URL and D=company website (optional for people);
one on-demand API sync fills Results and statuses. No automatic watcher is enabled.


## Supplied Sheet dry-run result — November 15, 2026

Four rows validated syntactically. The public-page check exposed and fixed missing
plain-HTML title/JD fallback without weakening employer-domain confirmation. Exactly
one role H1 is accepted; forms/navigation/footer are excluded from fallback JD text;
explicit placeholder-only role descriptions stop before paid work. Full suite: 810 passed.

One row is ready as entered, two need company websites in D, and the remaining row
also needs a complete JD rather than the posting's n/a content. See the ignored
local-data/reports/2026-11-15-sheet-dry-run.md receipt. Company corrections were tested
in memory only, not written to the Sheet. No provider calls, Sheet writes or quota
changes occurred. Google API authentication is still missing. After setup/corrections,
start with the three valid-JD rows under the existing three-draft run cap; hold the
incomplete posting. The user's current request authorized a dry run, not a paid run.


## Google Sheet connection verified — November 15, 2026

The service-account credential is configured locally in ignored config/service_account.json.
Actual authenticated Sheet API read AND write now work. Existing anyone-with-link edit
sharing was sufficient; no extra sharing permission was required in this workbook.
Pinned the missing PySocks dependency so httplib2 can use the runtime's HTTP proxy.
The production Sheet preview/setup commands work; input rows were preserved.

Applied the simple layout/reuse headers through the API and filled verified missing
company URLs. The Queue now shows three ready rows and one needs_context for the
incomplete job description. Stable row IDs were assigned. No paid contact lookup,
Claude draft, send, allowance change or invented result occurred. Full suite: 810 passed;
local ledger unchanged. Google authentication is no longer a blocker; next acceptance
is the bounded three-row live test. Routine/background live processing remains off.
