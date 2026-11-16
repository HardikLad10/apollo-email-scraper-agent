# Cold-email draft v2 — design

Date: November 15, 2026 (America/Chicago). Status: approved in conversation, awaiting
written-spec review. Not implemented.

## Why

The first live draft (Klaviyo run `633ebbc6…`) was 176 words, had no job link, no graduation
or availability line, and bullets without outcomes. Claude received the full job description
but only six profile facts pre-selected by a local keyword counter, so it could not pick the
strongest proof (for example, the Piramal 40% and 3x results were not offered).

Research summary (sources below): job cold emails that get replies are short (roughly
100–150 words at most), name the role and link it, state who the sender is and their
availability, give one or two concrete proof points, connect to something specific about the
company, and end with one small ask. Work-authorization guidance: state it plainly and
positively; never invent sponsorship claims.

## Decisions (confirmed by Hardik)

1. First bullet, always, verbatim: Hardik's confirmed graduation, work-authorization and
   immediate-availability sentence, stored only in the gitignored `profile.md` as the
   `work_authorization` fact (the repository is public). No visa type or sponsorship
   mention.
2. Every draft with a job URL includes that URL in the body.
3. Claude receives the full JD and all eligible profile facts, and picks the relevant ones.
4. The email includes one or two lines on why Hardik fits the role, mapping specific JD or
   company points to his experience. Claude may use the JD plus web search for the company's
   values and success factors.
5. If no job URL is supplied, still write a draft: a shorter networking email with no job
   link and no claims about a specific opening.

## Email format (prompt v2)

New file `claude_cold_email_prompt_v2.md`. `claude_cold_email_prompt_v1.md` stays unchanged
as history. Target 100–140 words in the body.

```
Subject: <Role> at <Company>

Hi <first name>,

I'm interested in the <Role> role at <Company>: <job URL>
A few reasons I'd be a strong fit:

- <work_authorization sentence, verbatim>
- <Most JD-relevant proof, one sentence, leading with the outcome or number>
- <Second proof, one sentence, leading with the outcome or number>

<1–2 sentences mapping one specific JD requirement or company value/success factor to
Hardik's experience. Grounded in the JD or a cited search source.>

Would you be open to a brief conversation about the role?

Thanks,
Hardik Lad
```

Prompt rules carried over from v1: voice and banned-phrase list, no em dashes, no
"not just X but Y", application/attachment wording only when confirmed, no invented
relationships or team membership, `NEEDS_CONTEXT:` when essential input is missing.

Prompt rules added or changed:

- The first bullet is the verbatim line above; do not rephrase it.
- Bullets 2–3 are the two facts most relevant to the JD; each one sentence, outcome first,
  using exact supplied metrics only.
- The fit lines must reference something specific from the JD or a search result, never
  generic praise. If search finds nothing reliable, use the JD only.
- Do not state company facts that are not in the JD or a cited search result. Prefer the
  company's own site and official pages over third-party pages.
- Remove the separate company-hook paragraph from v1; the fit lines replace it.
- Style examples are rewritten to the v2 format with fictional companies so Claude does not
  copy the old long shape. The voice examples' facts are never used as candidate facts.

No job URL: same greeting, first bullet, one proof bullet, one fit line from search or the
supplied company/role, and the ask "Would you be open to a brief conversation about roles on
your team?". No link and no claim that an opening exists. Target 70–110 words.

## Components

### `profile.md`

- Add shared fact `work_authorization`: the verbatim first-bullet text only (the loader
  uses everything after the label as the required bullet). Record "confirmed by Hardik on
  November 15, 2026" in the claim restrictions, not in the fact.
- Replace the "do not infer work authorization" wording in Shared facts with a rule that only
  this exact confirmed line may be used. Keep the restriction against claiming any
  sponsorship status (needed or not needed) and against inferring start dates beyond
  "immediately".
- The profile freshness guard reads `profile.md` text; changing it does not change the
  resume-source hashes, so no re-review of resume sources is triggered.

### `outreach/profile.py` — fact selection

- Send all shared facts plus all facts of the selected profile (with the existing
  accessibility and teaching adjustments), instead of the top six by keyword overlap.
- `work_authorization` and `education.ms` are always included and marked as required.
- Claim restrictions still go with every request. The three-fact minimum stays.
- Expected size: roughly 15–20 short facts; still one Claude call.

### `outreach/drafting.py`

- `build_message`: add `job_url` and `required_first_bullet` as explicit fields; when there
  is no job URL, set `email_mode: networking`.
- `DraftClient.draft`: add the server tool
  `{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}`. Controlled by a
  new setting `draft_web_search_max_uses` (default 2; 0 disables the tool).
- `pause_turn`: send the paused assistant content back once, unchanged, as the
  continuation of the same logical draft. A second pause, or any other stop reason except
  `end_turn`, is a draft failure. No automatic retry.
- Response text: concatenate text blocks without inserting newlines (cited text arrives in
  fragments), then parse.
- Record cited source URLs in the draft's `review_flags` as `source:<url>` entries (URLs
  only, no page text) and the web search request count as a `web_searches:<n>` flag, for
  review and cost.
- Web search disabled for the organization returns HTTP 400; surface it as a clear
  non-uncertain `DraftError` ("web search not enabled; set draft_web_search_max_uses: 0").

### Local checks after drafting (`parse_draft` / `DraftClient.draft`)

Hard failures (draft rejected, attempt recorded as error, no retry):

- Job URL supplied but not present verbatim in the body.
- First bullet is not the verbatim authorization line.
- Not exactly three hyphen bullets (job mode) or two (networking mode).

Review flags (draft kept):

- Body over 150 words: `over_length`.
- Existing application/attachment wording flags.

## Data flow

Job URL → context (JD text) → Apollo search/enrich (unchanged) → for each eligible contact:
build message (recipient, full JD, all eligible facts, restrictions, job URL, required first
bullet) → one Opus 5.5 high call with up to two web searches → checks → stored draft and
flags → CSV/JSON export (unchanged).

## Cost and time

Per draft: the existing Opus call, plus at most 2 searches ($0.02) and the search result
tokens (estimated a few thousand to tens of thousands of input tokens). Expect roughly
10–30 extra seconds per draft. Daily and per-run draft limits are unchanged. Changing the
prompt changes its hash, so previously cached drafts are not reused; redrafting an existing
contact costs one new draft call.

## Testing (offline only)

Fake Anthropic client and temporary project fixtures; no live calls.

- All eligible facts sent; `work_authorization` and `education.ms` always present.
- Message includes job URL, required first bullet, and networking mode when no URL.
- Request includes the web search tool with `max_uses` from settings; omitted when 0.
- `pause_turn` continued once; second pause fails; other stop reasons fail.
- Fragmented text blocks joined correctly; cited URLs recorded as flags.
- Missing job URL in body fails; wrong first bullet fails; wrong bullet count fails.
- Over 150 words flags but keeps the draft.
- HTTP 400 web-search-disabled maps to a clear error.
- Real-profile hash guard still passes.

## Files touched and coordination

Touched: `claude_cold_email_prompt_v2.md` (new), `profile.md`, `outreach/profile.py`,
`outreach/drafting.py`, `outreach/settings.py` and `outreach/settings.yaml` (one new
setting), one line in `outreach/main.py` (prompt file name), tests for drafting and
profile, `CHANGELOG.md` and `scope.md` (append only).

Codex is currently editing `service.py`, `models.py`, `export.py`, `sheets_queue.py`,
`store.py`, `context.py` and pushing to GitHub. Implement after Codex's push, on a separate
branch. `settings.py`, `settings.yaml` and `main.py` are shared files: re-read them
immediately before editing.

## Out of scope

Sending email, follow-ups, LinkedIn/resume links in the signature, recipient-specific
variants (recruiter vs. engineering manager vs. CTO), and fetching company pages directly.

## Sources

- Cold email length and structure: https://www.gong.io/blog/does-cold-email-even-work-any-more-heres-what-the-data-says,
  https://www.tamozo.com/blog/cold-email-length, https://studojo.com/blog/cold-email-for-software-engineer-job,
  https://interviewchamp.ai/learn/cold-email-recruiter-cs-new-grad-2026
- Work authorization in outreach: a visa-specific guide, not linked here because the repository is public.
- Claude web search tool: https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool
