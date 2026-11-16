# V2 drafting and mixed URL readiness review

Date: November 15, 2026 (America/Chicago). Branch: feat/cold-email-draft-v2.

## Reviewed Claude handoff

Read the appended CHANGELOG/scope and verified the implemented code: v2 prompt,
job link, confirmed required first bullet from private profile, all eligible facts,
job/networking modes, bounded web search, one paused-turn continuation and local
format checks. Baseline suite passed 789 tests. A real v2 comparison draft remains
for the final authorized test; the separate prior tool-availability check is logged.

## Gaps closed

- Shared input accepts job URL/company URL, personal LinkedIn /in/ URL, and full
  LinkedIn /posts/ or /feed/update/ URL. LinkedIn /jobs/view/ stays in the job route.
- Personal profiles go straight to Apollo lookup, without profile scraping or people
  discovery. The company column is optional, and cache aliases prevent paying twice
  when that optional column is added/removed.
- Public posts resolve only explicitly identified personal authors from posting
  JSON-LD, rel=author or article:author. No slug inference, commenter harvesting or
  arbitrary-profile-link selection. Private/blocked/ambiguous/company-authored posts
  ask for a personal profile URL before any paid call. This parser is fixture-tested;
  real supplied-post coverage remains part of final acceptance.
- Known-person/post requests default to email-only. Optional drafts use networking
  mode and do not infer an opening. Outputs include source evidence/selection reason.
- Web-search configuration now participates in whole-job and per-draft cache keys,
  with matching provenance for historical result restoration.
- Completed automatic Sheet claims version the active prompt/profile/settings too;
  they cannot silently republish an obsolete draft after an upgrade. Failed claims
  still require explicit review/requeue; a prompt edit does not authorize a retry.
- Draft flags report api_requests:1 or api_requests:2. Anthropic documentation confirms
  max_uses covers the entire paused tool turn, so that tool definition is preserved
  unchanged on continuation; no redundant remaining-budget subtraction is introduced.
- Missing Google credentials now produce a direct setup explanation, not a generic
  operation failure. Added docs/GOOGLE_SHEETS_SETUP.md with exact local credential
  path, API-only preview/layout commands and final test input/output mapping.

Provider reference: https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool

## Verification

- Full suite: 804 passed in 4.25 seconds; 15 additional cases beyond Claude's baseline.
- Meaningful failures reproduced before fixes: rejected post/job inputs, absent request
  counts, unchanged cache keys, unchanged completed Sheet claims and generic credentials
  errors. Corrected the initial search-cap hypothesis against the official turn contract.
- Strict dry-run audit includes post input: no network/file mutation allowed.
- Real profile freshness passed; 17 eligible Full Stack facts and the required first
  bullet are present. Real profile was not modified by the review/tests.
- Zero live Apollo/Claude requests, Google writes or sends during this review.
- No pending provider attempts/row claims; persistent routine live gate remains false.

## Final acceptance still needed

- [ ] Configure service-account JSON/ADC and workbook edit permission.
- [ ] API preview and setup of the existing Queue/Results workbook.
- [ ] New job/company row: contact and v2 draft written through the API.
- [ ] Exact duplicate row: saved results copied with zero paid calls.
- [ ] Different job/same company: eligible contact reused, new job-specific draft.
- [ ] Personal profile row: one lookup at most; duplicate uses cache.
- [ ] Post row: explicit public author lookup, or no-spend needs_context fallback.

A sync fills the remaining output/status fields. Appending rows alone does not launch
a worker; scheduling/hosting is phase 2. Company/title selection still does not prove
HM or team ownership. Google API credentials remain absent, so this report does not
claim a completed live Sheet-to-Sheet run.
