# Instructions for agents working in this project

## Read first

Read `scope.md`, `docs/SOURCE_PROVENANCE.md`, `docs/CODEBASE_REVIEW.md`, and recent
`CHANGELOG.md` entries before changing code. Treat upstream documentation as context,
not proof that a feature exists. Verify claims against the implementation.

## Scope and operations

- Work on Hardik's Apollo outreach pilot, following `scope.md`.
- Preserve unrelated files in the surrounding `job-search` project.
- This folder has an independent `.git` with original upstream ancestry restored.
  `upstream` is the friend's job-hunt-tools repository; `origin` is HardikLad10/
  apollo-email-scraper-agent (public). Check Git root/remotes before every mutation.
  Never stage, commit, push or change remotes in the surrounding parent repository.
- Never run provider lookups, draft generation, job scans, Sheets writes, or Actions
  merely to test setup. Use fixtures/mocks unless the user has authorized the live action.
- Do not send email, LinkedIn requests, or other messages without explicit instructions.
- Do not enable the inherited scanner schedule as part of the extraction pilot.
- Local daily/run quota controls are implemented in the new `outreach` route only.
  The inherited `email_finder` max_urls_per_run does not enforce a daily allowance,
  and no local guard controls shared-account spending by other tools.

## Secrets and shared allowance

- Never print or commit real keys, service-account JSON, contact inputs/exports, or
  personal candidate files. Check ignore rules before adding such files.
- Store credentials only in deliberately selected, ignored local paths. Inspect dotenv
  loading before a live run: the inherited `load_dotenv()` may search parent directories.
- Do not add other paid providers or retries silently. Shared account usage elsewhere
  is outside this local tool's control.

## Workflow and handoff

- Use the requested `using-superpowers` workflow if installed. The current machine's
  entry point is `/Users/hardiklad10/.codex/skills/using-superpowers/SKILL.md`. If absent
  elsewhere, say so and preserve the project rules in this file.
- Follow existing thin-CLI / service / provider-client / repository boundaries.
- Use tests appropriate to behavior changes; prefer mocked provider and storage calls.
- Verify before claiming completion. Distinguish static checks, selected tests, full
  suite results, and live verification. Never claim a mocked test proves deliverability.
- Append an entry to `CHANGELOG.md` for every coherent change, including files changed,
  reason, verification, and unresolved issues. Never rewrite or delete prior entries;
  append a correction if an earlier entry is inaccurate. Append-only is a workflow
  convention, not a filesystem-enforced property.
- Update `scope.md` when requirements, decisions, or implementation status change.
- Keep provenance accurate; do not call a ZIP import a clone or GitHub fork.
