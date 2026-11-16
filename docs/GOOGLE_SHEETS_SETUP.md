# Connect the shared Sheet once

Current blocker: no service-account credentials or Application Default Credentials
are configured. Apollo/Anthropic keys and the workbook ID are already present.
An API key alone is not the credential used by this adapter for result writes.

## One-time account setup

1. In a Google Cloud project you control, enable the Google Sheets API.
2. Create a service account. Cloud project Editor/Owner access is not needed by the
   account merely to edit the explicitly shared workbook.
3. Create/download its JSON key and save it locally as:

   `/Users/hardiklad10/projects/job-search/Apollo Email Extraction Outreach Specialist/config/service_account.json`

4. In the workbook's Share dialog, add the JSON's `client_email` as an Editor.
5. Add this line to the existing project `.env`, preserving the provider keys:

```dotenv
GOOGLE_APPLICATION_CREDENTIALS="/Users/hardiklad10/projects/job-search/Apollo Email Extraction Outreach Specialist/config/service_account.json"
```

The JSON and `.env` are ignored by Git. Keep the downloaded key local; do not put it
in Sheet cells or the public repository. An existing suitable service account can be
reused instead of creating another account/key. Existing ADC is also supported.

Official instructions:
- https://developers.google.com/workspace/guides/create-credentials#service-account
- https://cloud.google.com/iam/docs/creating-managing-service-account-keys

## Verify and format through the API

From the project folder:

```bash
.venv/bin/python -m outreach.main --preview-sheet
.venv/bin/python -m outreach.main --setup-sheet
```

Preview only reads/validates. Setup renames the input/company headers, hides advanced
columns and appends optional result provenance headers without deleting rows. Neither
command calls Apollo or Claude. Routine updates use the API; no RPA is involved.

Once the final test rows and shared paid limits are agreed, run the guarded
`--sync-sheet` flow. Routine live mode remains disabled until then. No background
watcher is installed by setup or sync.

## Inputs for the final test

Use the existing C column (`job_url`, renamed `input` by setup) and optional D
(`company_url`, renamed `company`). Leave all other inputs alone.

| Case | C: input | D: company | Default result |
| --- | --- | --- | --- |
| Job | Full job URL | Employer website | One selected contact/email and a v2 draft |
| Known person | Full LinkedIn `/in/` URL | Optional employer website | That person's email; no Claude call |
| Post author | Full LinkedIn `/posts/` or `/feed/update/` URL | Optional employer website | Publicly identified author's email |
| Named person | `Full Name \| Company` | Optional website override | Named-person email lookup |

If a post is private/blocked or does not explicitly expose one personal author,
the row becomes `needs_context` and asks for the personal profile URL. It does not
guess from a URL slug, scrape profiles, harvest commenters or consume an enrichment.
LinkedIn job URLs stay in the job route; inaccessible job pages need supplied JD/context.

Known-person/post rows are email-only by default. An explicit `draft_email: TRUE`
requests a short v2 networking draft; it does not invent an open vacancy from the post.

Final API acceptance should cover a new job, an exact duplicate (zero paid calls),
a different job at the same company (contact reused/new draft), a personal profile,
and a readable post author or a clear no-spend `needs_context` result.
