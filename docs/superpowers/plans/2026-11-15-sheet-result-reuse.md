# Sheet Result Reuse Implementation Plan

> **For agentic workers:** Execute inline with checkpoints; implementation is already
> authorized. Use executing-plans and test-driven-development, with no delegation needed.

**Goal:** Reuse completed job results and suitable company contacts, then publish the project privately.

**Architecture:** Canonical request identities index completed local outcomes. A separate
contact pool inherits enrichment expiry. The existing service, ledger and API Sheet
adapter handle new work, row publication and recovery.

**Tech Stack:** Python 3.12+, SQLite, requests, pytest, existing Google/Anthropic clients.

**Spec:** `docs/superpowers/specs/2026-11-15-sheet-result-reuse-design.md`

## Global constraints

No secrets/private contact data in Git. No sender, scheduler, new paid test or profile
fact changes. Preserve daily limits and uncertain-request recovery. Original TeX files
stay in the parent folder. Exact duplicates make no paid calls; new jobs never inherit
an old job's draft. Reuse does not extend enrichment lifetime.

### 1. Reuse identities and expiring storage

Files: create `outreach/reuse.py`; modify `outreach/store.py`; create
`tests/test_url_outreach_reuse.py`.

- [x] Write/run failing tests for canonical duplicates, new-job reuse and expiry.
- [x] Add `canonical_job_url(url)` and `result_key(request, settings, prompt)`.
  The key fingerprints canonical inputs plus draft dependencies; retain query job IDs.
- [x] Add `Store.cache_record`, `Store.save_cached`, `Store.remember_contact` and
  `Store.saved_contacts`. Contacts copy expiry from completed enrichment entries.
- [x] Run the focused tests with bytecode/cache disabled.

Core acceptance assertion:
```python
assert second.metadata['counts']['provider_attempts'] == {'search': 0, 'enrich': 0, 'draft': 0}
assert second.metadata['reused_from_run_id'] == first.run_id
```

### 2. Service and Queue integration

Files: modify `outreach/service.py`, `outreach/sheets_queue.py`, `outreach/export.py`;
extend reuse tests and Sheet tests.

- [x] Snapshot only completed outcomes; restore exact matches before fetching pages.
- [x] Re-rank fresh company contacts before search and reuse their enrichment directly.
- [x] Draft for a new job through the existing quota-protected call; invalidate changed
  instructions/profile/prompt. Record original source IDs and selection uncertainty.
- [x] Publish duplicate appended rows with unique result IDs; mark status reused and
  keep repeated/ambiguous publications idempotent.
- [x] Add optional output columns and non-destructive API header setup.
- [x] Run focused tests, then the complete suite and strict dry-run audits.

### 3. Handoff and private GitHub publication

Files: update README, guide, scope, provenance, AGENTS/CLAUDE and append CHANGELOG;
move inherited scanner workflow out of `.github/workflows`.

- [x] Restore original upstream Git ancestry in this folder only.
- [x] Document current implemented behavior, limits and pending Google authentication.
- [x] Audit staged file names/content and exact dotenv values without printing secrets.
- [ ] Commit on main, create the private requested repository, and push only main.
- [ ] Verify remote commit, privacy, no active workflows and no private files tracked.
