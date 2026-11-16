# URL outreach review resolution — November 15, 2026

Original review: `2026-11-15-url-outreach-code-review.md` (preserved).
Status: all five important findings and actionable minors fixed offline. No live gate
enabled, no provider/job/Sheets API request, no messages or Git mutations.

| Finding | Resolution | Regression evidence |
| --- | --- | --- |
| 5: real profile can be rewritten by tests | Fictional temporary projects, redirected CLI roots, session hash guard | `tests/conftest.py`, service/profile/acceptance tests; original assertion failed before fix |
| 1: social/ATS domain confirmed as employer | URL preference, string/list sameAs, third-party rejection, known-prefix normalization and safe overrides | `test_url_outreach_context.py`: seven new metadata/override cases |
| 2: permanently blocked attempts/claims | Explicit confirmed local recovery, unchanged usage, no invented cache, audited state changes, new-token gate | `test_url_outreach_recovery.py`: listing privacy, confirmation, invalid state, release/retry, stale completion |
| 3: exceptions strand Sheet claims | Pre-status before claims, base re-acquisition, terminal caught errors, continued rows; stop if ledger unavailable | `test_url_outreach_sheets.py`: runtime failure, failed status write, repeat error summary |
| 4: incomplete dedup/email flags | Normalize personal LinkedIn aliases before enrichment; persist email fingerprints/IDs and flag independently of drafting | `test_url_outreach_dedup.py`: one lookup for URL aliases; duplicate flags without drafts/across restart |

## Minor findings

- Titles match word boundaries; Director is not CTO. Persona mismatch checks title
  separately from employer eligibility.
- URL summaries persist and print attempted/found/not-found/failed/skipped/remaining
  counts, with per-operation attempt counts. Sync returns nonzero for row errors,
  budget waits or changed rows; cached error outcomes remain visible on repeated sync.
- Export reads existing state without creating a database. Preview connections close.
- Claude timeout is configurable; local TypeError is not an uncertain network outcome.
- CSV escapes tab/carriage-return prefixes as well as formula-leading characters.
- Drafting previews check source freshness even without a fetched role; disabled
  allocation is a warning; malformed source manifests raise ProfileNeedsReview.
- Apollo's current official documentation confirms query parameters for search filters
  and enrichment reveal/waterfall switches. Client uses query arrays with brackets and
  lowercase false switches; only enrichment details are in the JSON body.
- Employment fixtures now use documented organization IDs. Missing/conflicting current
  organization evidence fails safe. Explicit `has_email: false` avoids a paid lookup.
- Public fetching prefers IPv4 while keeping public-address validation and DNS pinning.
- Five subprocess audit-hook dry runs forbid network lookup/connect and filesystem
  writes anywhere, rather than checking only an empty working directory.

Sources checked (documentation only, no API execution):

- https://docs.apollo.io/reference/bulk-people-enrichment
- https://docs.apollo.io/reference/people-api-search

## Deliberate limits and follow-on work

- Recovery v1 offers `--as error`, not success/cache import without a verified payload.
  Usage is never refunded. Stop active workers before recovery; an old completion is
  rejected if a newer token/input owns the row.
- Employer normalization strips known prefixes; it does not guess arbitrary registrable
  domains or add a public-suffix dependency. Supply a canonical company URL when needed.
- A permanently unavailable/corrupt ledger still stops the sync. Once restored, explicit
  release/reconciliation can resolve pending state; the tool never spends around it.
- Hiring-manager/engineering-manager title sets remain identical candidate categories.
  More job/team-specific ranking is a future design improvement, with no extra default
  Claude calls and no guarantee of exact hiring ownership.
- Shared workbook formatting is verified in-browser. Google API authentication, actual
  provider permissions/allowance, deliverability and real-draft calibration remain open.

## Verification

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider`
passed **723 tests**, including five isolated dry-run audit variants and the real-profile
hash guard. Each important issue had a failing test before its fix; the full suite was
run after each coherent fix. Final checks and exact results are appended to CHANGELOG.
