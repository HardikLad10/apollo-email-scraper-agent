"""Hermetic project inputs for the URL route; legacy fixtures stay unchanged."""
import hashlib
from pathlib import Path

import pytest
import yaml


REAL_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='session', autouse=True)
def personal_profile_is_unchanged():
    path = REAL_ROOT/'profile.md'
    before = hashlib.sha256(path.read_bytes()).digest() if path.exists() else None
    yield
    after = hashlib.sha256(path.read_bytes()).digest() if path.exists() else None
    assert after == before, 'Test suite changed the personal profile.md'


@pytest.fixture
def outreach_project(tmp_path_factory):
    from outreach.profile import active_tex_text
    root = tmp_path_factory.mktemp('fictional_outreach_project')
    (root/'config').mkdir()
    (root/'outreach').mkdir()
    sources = {}
    for name in ('fullstack', 'amazon', 'accessibility'):
        source = root/(name+'.tex')
        source.write_text('\\begin{document}Fictional '+name+' experience\\end{document}')
        sources[name] = {'path':source.name, 'reviewed_active_sha256':hashlib.sha256(active_tex_text(source.read_text()).encode()).hexdigest()}
    (root/'config/outreach_profile_sources.yaml').write_text(yaml.safe_dump({'sources':sources}))
    (root/'profile.md').write_text('''# Fictional test candidate
## Shared candidate facts
- **identity:** Test Candidate.
- **education:** Studied software engineering.
- **apis:** Built Python REST APIs.
- **sql:** Improved SQL queries.
- **react:** Built React applications.
## Profile: fullstack
- **big.fullstack.retrieval:** Built ChromaDB retrieval with Dialogflow CX.
- **deployment:** Used Docker and AWS.
## Profile: amazon
- **big.amazon.application:** Built a Next.js and Drizzle application.
- **streaming:** Used SSE streaming.
## Profile: accessibility
- **accessibility:** Remediated fictional course documents.
## Claim restrictions for every profile
- Do not invent metrics or employment relationships.
- Do not combine the two BIG implementations.
''')
    (root/'outreach/settings.yaml').write_text(yaml.safe_dump({
        'state_path':str(root/'local-data/state.sqlite3'), 'output_dir':str(root/'local-data/exports'),
        'allocation_confirmed':False,
    }))
    for prompt in ('claude_cold_email_prompt_v1.md','claude_cold_email_prompt_v2.md'):
        (root/prompt).write_text((REAL_ROOT/prompt).read_text())
    return root


@pytest.fixture(autouse=True)
def isolate_url_route(request, monkeypatch):
    if not request.node.path.name.startswith('test_url_outreach_'):
        return
    root = request.getfixturevalue('outreach_project')
    import outreach.main
    import outreach.settings
    monkeypatch.setattr(outreach.main, 'ROOT', root)
    monkeypatch.setattr(outreach.settings, 'ROOT', root)
