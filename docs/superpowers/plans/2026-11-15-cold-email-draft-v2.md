# Cold-email draft v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shorter, scannable job cold emails that always carry the job link, open with the confirmed graduation/authorization/availability line, use the most JD-relevant profile facts, and include 1–2 grounded fit lines.

**Architecture:** `profile.py` sends every eligible fact; `drafting.py` derives the required first bullet from the `work_authorization` fact, adds the Claude web search server tool, continues one `pause_turn`, and enforces link/first-bullet/bullet-count checks; a new `claude_cold_email_prompt_v2.md` carries the format. One new setting controls search.

**Tech Stack:** Python 3.12, Anthropic SDK (Messages API, `web_search_20250305`), pytest with fake clients.

Spec: `docs/superpowers/specs/2026-11-15-cold-email-draft-v2-design.md`.

## Global Constraints

- Model `claude-opus-5-5`, effort `high`, `max_retries=0`; no automatic retry.
- Web search tool: `{"type": "web_search_20250305", "name": "web_search", "max_uses": N}`; setting `draft_web_search_max_uses`, default 2, allowed 0–5, 0 omits the tool.
- The exact authorization sentence lives only in gitignored `profile.md` as `- **work_authorization:** <sentence>`. Committed files (code, prompt, tests, docs) use fictional text. The repository is public.
- Body target 100–140 words; over 150 words adds flag `over_length` (draft kept).
- Hard failures: job URL missing from body; first bullet differs from the `work_authorization` sentence (when that fact exists); bullet count not 3 (job URL given) or 2 (no job URL).
- Review flags for search: `web_searches:<n>` and `source:<url>` (cited URLs only, no page text).
- No live API calls in tests. `allocation_confirmed` stays `false`. `CHANGELOG.md` append-only.
- Do not commit `CHANGELOG.md`/`scope.md` on this branch: they contain Codex's pending uncommitted note.

---

### Task 1: Send all eligible profile facts

**Files:**
- Modify: `outreach/profile.py:95-100`
- Modify (gitignored, local): `profile.md`
- Test: `tests/test_url_outreach_draft_v2.py`

**Interfaces:**
- Produces: `load_candidate(...)` returns `Candidate.facts == tuple(shared + selected)` in profile order (accessibility/teaching adjustments unchanged).

- [ ] **Step 1: Failing test**

```python
def test_all_eligible_facts_are_sent(outreach_project):
    candidate = load_candidate('fullstack', NETWORK, root=outreach_project)
    assert len(candidate.facts) == 7
    assert any('Docker and AWS' in f for f in candidate.facts)
```

- [ ] **Step 2:** `pytest tests/test_url_outreach_draft_v2.py -k all_eligible` → FAIL (6 facts).
- [ ] **Step 3: Implement** — replace the keyword ranking and `chosen_big` swap with:

```python
    facts = shared+selected
    if len(facts)<3: raise ProfileNeedsReview('At least three supported facts required')
```

- [ ] **Step 4: `profile.md`** — in Shared facts add `- **work_authorization:** <confirmed sentence>`; drop "work authorization" and "start date" from the identity do-not-infer list; point writing instructions to v2; add a claim restriction: use the `work_authorization` sentence exactly, never state visa type or sponsorship need, no start date other than immediately (confirmed by Hardik, November 15, 2026).
- [ ] **Step 5:** Run test → PASS; full suite green.

### Task 2: Drafting rules, web search and checks

**Files:**
- Modify: `outreach/drafting.py`
- Modify: `tests/test_url_outreach_drafting.py`, `tests/test_url_outreach_acceptance.py` (job URL in fixture email/context)
- Test: `tests/test_url_outreach_draft_v2.py`

**Interfaces:**
- Produces: `required_first_bullet(candidate) -> str` ('' when absent); `parse_draft(text, bullets=3) -> Draft`; `check_draft(draft, context, candidate) -> tuple[str, ...]`; `DraftClient(api_key, prompt, max_tokens=8192, *, client=None, timeout=60, web_search_max_uses=0)`.
- `build_message` adds `job_url`, `email_mode` (`job`/`networking`), `required_first_bullet` (or `None`), `format` (`three_hyphen_bullets`/`two_hyphen_bullets`), mode-specific `ask`.

- [ ] **Step 1: Failing tests** (fake SDK: `Fake.create` records kwargs and pops queued responses)

```python
def test_job_message_fields():
    data = json.loads(build_message(JOB, PERSON, CANDIDATE, Request()).split('\n',1)[1])
    assert data['job_url'] == URL and data['email_mode'] == 'job'
    assert data['required_first_bullet'] == AUTH and data['format'] == 'three_hyphen_bullets'

def test_pause_turn_continued_once():
    drafter, fake = client(response(text("I'll check."), stop='pause_turn', searches=1), response(text(GOOD), searches=1))
    draft = drafter.draft(JOB, PERSON, CANDIDATE, Request())
    assert len(fake.calls) == 2 and fake.calls[1]['messages'][1]['role'] == 'assistant'
    assert 'web_searches:2' in draft.review_flags

def test_missing_url_fails():
    drafter, _ = client(response(text(email(AUTH,'One.','Two.', link=None))))
    with pytest.raises(DraftError, match='job URL'): drafter.draft(JOB, PERSON, CANDIDATE, Request())
```

Plus: networking fields/two bullets, tool present with `max_uses` and omitted at 0, second pause fails, `max_tokens` stop fails, fragmented blocks with preamble parse and `source:` flags, wrong first bullet fails, three bullets in networking fails, over-length flag, HTTP 400 hint and `uncertain is False`.

- [ ] **Step 2:** Run → FAIL (`build_message` lacks fields, no `web_search_max_uses`).
- [ ] **Step 3: Implement** `drafting.py` (see final file in the branch): `_create(messages)` wraps `messages.create` with optional `tools`; one continuation on `pause_turn` with `{'role':'assistant','content':result.content}`; join text blocks with `''`; `parse_draft` drops text before the first `Subject:`/`NEEDS_CONTEXT:`; `check_draft` enforces URL/first bullet and returns `over_length`; HTTP 400 with search enabled appends "if web search is disabled for the organization, set draft_web_search_max_uses: 0".
- [ ] **Step 4:** Update existing tests' `EMAIL` to include `https://example.org/jobs/1` and use that `job_url` in their contexts.
- [ ] **Step 5:** Run → PASS; full suite green.

### Task 3: Prompt v2, setting and wiring

**Files:**
- Create: `claude_cold_email_prompt_v2.md` (v1 unchanged)
- Modify: `outreach/settings.py`, `outreach/settings.yaml`, `outreach/main.py:140`, `tests/conftest.py`
- Test: `tests/test_url_outreach_draft_v2.py`

**Interfaces:**
- Consumes: `DraftClient(..., web_search_max_uses=settings.draft_web_search_max_uses)`.
- Produces: `Settings.draft_web_search_max_uses: int = 2`.

- [ ] **Step 1: Failing tests**

```python
@pytest.mark.parametrize('value,ok', [(0,True),(2,True),(5,True),(-1,False),(6,False),(True,False)])
def test_web_search_setting(tmp_path, value, ok): ...

def test_prompt_v2_examples_satisfy_parser():
    prompt = (REAL_ROOT/'claude_cold_email_prompt_v2.md').read_text()
    job, networking = re.findall(r'<example[^>]*>\n(.+?)\n</example>', prompt, re.S)
    assert len(parse_draft(job).body.split()) <= 150
    parse_draft(networking, bullets=2)
```

- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Add the setting (validated as int 0–5, not bool) and `draft_web_search_max_uses: 2` to YAML; `main.py` loads `claude_cold_email_prompt_v2.md` and passes the setting; `conftest.py` also copies v2 into the fictional project; write prompt v2 (format, carried-over voice rules, fit-line and search rules, fictional examples for job and networking modes).
- [ ] **Step 4:** Run → PASS; full suite green; `--dry-run` preview still makes no network calls.
- [ ] **Step 5:** Commit code, prompt, tests, spec and plan on `feat/cold-email-draft-v2`; append `CHANGELOG.md` and `scope.md` entries uncommitted.
