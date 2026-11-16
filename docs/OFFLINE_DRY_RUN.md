# Offline walkthrough — November 14, 2026

Status: completed a local demonstration, not a full pipeline dry run. The current CLI still has no `--dry-run` flag.
No Apollo, Anthropic, Google Sheets, job-page fetch, or other network call was made. No emails or drafts were generated.

## Existing helpers exercised

Ran the actual `input_file.parse_line` and `normalize_linkedin_url` functions on fictional text inputs. Applied the current service validation rule and an in-memory duplicate set. Did not invoke `service.run` or the CLI.

| Normalized input | Local outcome |
| --- | --- |
| `https://linkedin.com/in/outreach-demo-a` | eligible new URL (lookup not performed) |
| `https://linkedin.com/in/outreach-demo-a` | duplicate |
| `https://linkedin.com/company/outreach-demo-company` | invalid profile URL |
| `https://linkedin.com/in/outreach-demo-b` | eligible new URL (lookup not performed) |

Parsed entries: 4; eligible unique profiles: 2; duplicates: 1; invalid profiles: 1. Sheet-existing status and email availability were not checked.

## Proposed cold-email request assembled locally

Read the new prompt and profile, selected three supported facts, and assembled a request object in memory. This object was never sent. The 8192 output-token ceiling is a proposed configurable starting point, not measured usage or a live validation.

- Model: `claude-opus-5-5`; effort: `high`.
- Fictional recipient: Alex, Engineering Manager at Example Co.
- Fictional role: Backend Engineer; supplied example requirements: Python, SQL, internal tooling.
- Selected profile: `fullstack`.
- Selected fact IDs: `education.ms`, `piramal.claims`, `piramal.sql`.
- Application status: interested; resume attachment: false; format: three bullets.
- Prompt characters: 8,690; serialized case characters: 1,051. These are character counts, not API token counts.
- No BIG implementation was needed for this case; no other profile was mixed in.

## Company-row planning example

A future row containing `Example Co`, `example.com`, a job URL/description, team keyword `platform`, and personas `technical_recruiter;engineering_manager` would request a company search, evidence-based shortlist, and selected-person enrichment within the budget. No company-search function was executed here. Contacts, emails, and team membership remain unknown.

## What remains untested

XLSX/CSV import, live key access, provider billing, company discovery, team inference, daily accounting, automatic profile refresh, Claude style quality, and export/recovery are not validated by this demonstration. They require implementation and the checks in `OUTREACH_WORKFLOW_PLAN.md`.
