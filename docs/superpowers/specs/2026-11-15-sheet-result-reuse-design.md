# Company contact and job result reuse

Approved direction: Hardik selected company-contact reuse plus one fresh Claude call
for a different job, and requested publication as apollo-email-scraper-agent.

## Contract

- Inputs remain job URL and company URL; row IDs/defaults stay automatic.
- Canonical company domain groups saved contacts. Canonical job URL retains job IDs,
  ignores known tracking parameters and fragments, and distinguishes different roles.
- An exact completed job with unchanged drafting inputs/profile/prompt reuses its
  complete outcome without website, Apollo or Claude calls. Each new Queue row gets
  its own result/run identity and an explicit reuse source.
- A different job at the same company uses fresh, confirmed-employer saved contacts
  matching the requested personas. It re-ranks locally, resets old team certainty,
  and drafts for the new role. One recipient means at most one new Claude call.
- Contact validity inherits the original enrichment expiry; reuse never extends it.
  Missing emails, employer mismatches and expired contacts are ineligible.
- Known expired job results or company contacts needing refresh are marked for review;
  there is no automatic paid refresh. Failed/uncertain work is never treated as complete.
- Changed notes, application/attachment claims, profile or prompt invalidate draft reuse.
- Existing quota, interruption and Sheet write reconciliation safeguards remain.
- Sheets API writes continue through GoogleQueue; no UI or new scheduler is introduced.
  Optional result columns expose selection/reuse reasoning; original columns still work.
- Draft wording, stronger contact discovery/ranking, Notion and hosting are deferred.

## Boundaries and verification

`outreach/reuse.py` owns canonical identities and input/profile/prompt signatures.
`Store` owns expiring outcome snapshots and contact records with source provenance.
`service.run` decides reuse before network work, then uses the existing guarded pipeline.
`QueueProcessor` marks reused results and publishes each appended row independently.

Tests use fictional candidates/providers and temporary ledgers. Verify same-job tracker
variants across restarts, new-job contact reuse, TTL preservation, changed drafting
inputs, no reuse of invalid contacts, duplicate Sheet rows, and ambiguous write recovery.
No live provider call or new live allowance is needed for this implementation.

## Git publication

Restore the original import commit's genuine upstream history in a nested repository.
Publish on main to a new private HardikLad10/apollo-email-scraper-agent repository.
Exclude secrets/private records and disable inherited workflow discovery before push.
Keep the parent repository and source TeX resumes untouched.
