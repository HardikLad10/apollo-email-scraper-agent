import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from outreach.drafting import DraftClient, DraftError, build_message, parse_draft
from outreach.models import Candidate, Context, Person, Request
from outreach.profile import load_candidate

REAL_ROOT = Path(__file__).resolve().parents[1]
URL = 'https://example.org/jobs/1'
AUTH = 'Graduated in May with an MS in Testing; authorized to work in the U.S. and available to start immediately.'
CANDIDATE = Candidate('fullstack',('**work_authorization:** '+AUTH,'Built React apps','Built APIs'),(),{},'hash')
JOB = Context('Example','example.org','Full Stack Engineer',URL,'React APIs',(),())
NETWORK = Context('Example','example.org','Full Stack Engineer',None,'React APIs',(),())
PERSON = Person('p','Alex','Recruiter','example.org')


def email(*bullets, link=URL, filler=''):
    opener = f"I'm interested in the Full Stack Engineer role at Example: {link}\n" if link else "I'm reaching out about engineering roles at Example.\n"
    return ('Subject: Full Stack Engineer at Example\n\nHi Alex,\n\n'+opener+'A few reasons I would fit:\n\n'
            +'\n'.join('- '+bullet for bullet in bullets)+'\n\n'+filler
            +'Would you be open to a brief conversation about the role?\n\nThanks,\nHardik Lad')


GOOD = email(AUTH,'Cut manual tracking 40% with React tools.','Made SQL queries 3x faster.')


def text(value, **extra): return SimpleNamespace(type='text', text=value, **extra)


def response(*blocks, stop='end_turn', searches=0):
    return SimpleNamespace(stop_reason=stop, content=list(blocks),
                           usage=SimpleNamespace(server_tool_use=SimpleNamespace(web_search_requests=searches)))


class Fake:
    def __init__(self, *responses): self.responses, self.calls = list(responses), []
    def create(self, **kwargs):
        self.calls.append(kwargs)
        result = self.responses.pop(0)
        if isinstance(result, Exception): raise result
        return result


def client(*responses, uses=2):
    fake = Fake(*responses)
    return DraftClient('fake','PROMPT',client=SimpleNamespace(messages=fake),web_search_max_uses=uses), fake


def message_data(context, candidate=CANDIDATE):
    return json.loads(build_message(context, PERSON, candidate, Request()).split('\n',1)[1])


def test_all_eligible_facts_are_sent(outreach_project):
    candidate = load_candidate('fullstack', NETWORK, root=outreach_project)
    assert len(candidate.facts) == 7
    assert any('Docker and AWS' in fact for fact in candidate.facts)


def test_job_message_fields():
    data = message_data(JOB)
    assert data['job_url'] == URL and data['email_mode'] == 'job'
    assert data['required_first_bullet'] == AUTH and data['format'] == 'three_hyphen_bullets'


def test_networking_message_fields():
    data = message_data(NETWORK, Candidate('fullstack',('a','b','c'),(),{},'hash'))
    assert data['job_url'] is None and data['email_mode'] == 'networking'
    assert data['required_first_bullet'] is None and data['format'] == 'two_hyphen_bullets'
    assert data['ask_kind'] == 'recruiter' and 'open engineering roles' in data['ask']


def test_web_search_tool_uses_setting():
    drafter, fake = client(response(text(GOOD)), uses=2)
    drafter.draft(JOB, PERSON, CANDIDATE, Request())
    assert fake.calls[0]['tools'] == [{'type':'web_search_20250305','name':'web_search','max_uses':2}]


def test_web_search_tool_omitted_when_disabled():
    drafter, fake = client(response(text(GOOD)), uses=0)
    drafter.draft(JOB, PERSON, CANDIDATE, Request())
    assert 'tools' not in fake.calls[0]


def test_pause_turn_continued_once():
    paused = response(text("I'll check the company."), stop='pause_turn', searches=1)
    drafter, fake = client(paused, response(text(GOOD), searches=1))
    draft = drafter.draft(JOB, PERSON, CANDIDATE, Request())
    assert len(fake.calls) == 2
    assert fake.calls[1]['messages'][1] == {'role':'assistant','content':paused.content}
    assert 'web_searches:2' in draft.review_flags and draft.body.startswith('Hi Alex')


def test_second_pause_fails():
    drafter, _ = client(response(stop='pause_turn'), response(stop='pause_turn'))
    with pytest.raises(DraftError, match='incomplete'): drafter.draft(JOB, PERSON, CANDIDATE, Request())


def test_other_stop_reason_fails():
    drafter, fake = client(response(text(GOOD), stop='max_tokens'))
    with pytest.raises(DraftError, match='incomplete'): drafter.draft(JOB, PERSON, CANDIDATE, Request())
    assert len(fake.calls) == 1


def test_fragmented_blocks_and_cited_sources():
    cut = GOOD.index('Cut manual')
    blocks = [text('Let me look up their values.'), text(GOOD[:cut]),
              text(GOOD[cut:cut+20], citations=[SimpleNamespace(url='https://example.org/values')]), text(GOOD[cut+20:])]
    drafter, _ = client(response(*blocks, searches=1))
    draft = drafter.draft(JOB, PERSON, CANDIDATE, Request())
    expected = parse_draft(GOOD)
    assert (draft.subject, draft.body) == (expected.subject, expected.body)
    assert 'source:https://example.org/values' in draft.review_flags and 'web_searches:1' in draft.review_flags


def test_missing_job_url_fails():
    drafter, _ = client(response(text(email(AUTH,'One.','Two.', link=None))))
    with pytest.raises(DraftError, match='job URL'): drafter.draft(JOB, PERSON, CANDIDATE, Request())


def test_wrong_first_bullet_fails():
    drafter, _ = client(response(text(email('Built React apps.', AUTH, 'Two.'))))
    with pytest.raises(DraftError, match='work-authorization'): drafter.draft(JOB, PERSON, CANDIDATE, Request())


def test_networking_requires_two_bullets():
    three = email(AUTH,'One.','Two.', link=None)
    drafter, _ = client(response(text(three)))
    with pytest.raises(DraftError, match='exactly 2'): drafter.draft(NETWORK, PERSON, CANDIDATE, Request())
    drafter, _ = client(response(text(email(AUTH,'One.', link=None))))
    assert drafter.draft(NETWORK, PERSON, CANDIDATE, Request()).subject


def test_over_length_is_flagged_not_rejected():
    drafter, _ = client(response(text(email(AUTH,'One.','Two.', filler='word '*120+'\n\n'))))
    assert 'over_length' in drafter.draft(JOB, PERSON, CANDIDATE, Request()).review_flags
    drafter, _ = client(response(text(GOOD)))
    assert 'over_length' not in drafter.draft(JOB, PERSON, CANDIDATE, Request()).review_flags


def test_http_400_explains_web_search_setting():
    class Rejected(Exception): status_code = 400
    drafter, _ = client(Rejected('request body'))
    with pytest.raises(DraftError, match='draft_web_search_max_uses: 0') as error:
        drafter.draft(JOB, PERSON, CANDIDATE, Request())
    assert error.value.uncertain is False and 'request body' not in str(error.value)


@pytest.mark.parametrize('value,ok', [(0,True),(2,True),(5,True),(-1,False),(6,False),(True,False)])
def test_web_search_setting_validation(tmp_path, value, ok):
    from outreach.settings import load_settings
    path = tmp_path/'settings.yaml'
    path.write_text(yaml.safe_dump({'draft_web_search_max_uses':value}))
    if ok: assert load_settings(path).draft_web_search_max_uses == value
    else:
        with pytest.raises(ValueError): load_settings(path)


def test_default_web_search_setting_is_two(tmp_path):
    from outreach.settings import load_settings
    path = tmp_path/'settings.yaml'
    path.write_text('{}')
    assert load_settings(path).draft_web_search_max_uses == 2


def test_prompt_v2_examples_satisfy_parser():
    prompt = (REAL_ROOT/'claude_cold_email_prompt_v2.md').read_text()
    job, networking = re.findall(r'<example[^>]*>\n(.+?)\n</example>', prompt, re.S)
    assert len(parse_draft(job).body.split()) <= 150
    assert 'https://' in job and 'https://' not in networking
    parse_draft(networking, bullets=2)
    assert 'required_first_bullet' in prompt


def test_main_uses_prompt_v2_and_search_setting():
    source = (REAL_ROOT/'outreach/main.py').read_text()
    assert 'claude_cold_email_prompt_v2.md' in source
    assert 'web_search_max_uses=settings.draft_web_search_max_uses' in source


def test_real_profile_has_single_sentence_authorization_fact():
    path = REAL_ROOT/'profile.md'
    if not path.exists(): pytest.skip('personal profile is local only')
    from outreach.profile import _facts
    facts = [f for f in _facts(path.read_text(),'Shared candidate facts') if f.startswith('**work_authorization:**')]
    assert len(facts) == 1 and not re.search(r'\.\s+[A-Z]', facts[0]) and facts[0].endswith('.')


@pytest.mark.parametrize('title,kind', [
    ('Senior Technical Recruiter','recruiter'), ('Talent Acquisition Partner','recruiter'),
    ('Engineering Manager','manager'), ('Director of Engineering','manager'), ('Head of Platform','manager'),
    ('Software Engineer II','engineer'), ('Staff Developer','engineer'),
    ('CTO','executive'), ('Co-Founder & CEO','executive'), ('VP of Engineering','executive'),
    ('Account Executive','routing'), ('Sales Director','routing'), ('Hiring Manager','manager'), ('Marketing Lead','routing'), ('','routing')])
def test_ask_kind_from_title(title, kind):
    from outreach.drafting import ask_kind
    assert ask_kind(title) == kind


def test_ask_depends_on_recipient_status_and_mode():
    recruiter = Person('p','Alex','Technical Recruiter','example.org')
    applied = json.loads(build_message(JOB, recruiter, CANDIDATE, Request(application_status='applied')).split('\n',1)[1])
    assert applied['ask_kind'] == 'recruiter' and 'my application' in applied['ask']
    unknown = json.loads(build_message(JOB, recruiter, CANDIDATE, Request()).split('\n',1)[1])
    assert 'my application' not in unknown['ask']
    engineer = json.loads(build_message(JOB, Person('p','Sam','Software Engineer','example.org'), CANDIDATE, Request()).split('\n',1)[1])
    assert 'referring me' in engineer['ask']
    other = json.loads(build_message(NETWORK, Person('p','Kim','Sales Director','example.org'), CANDIDATE, Request()).split('\n',1)[1])
    assert other['ask_kind'] == 'routing' and 'right person' in other['ask']


def test_draft_flags_ask_kind_and_modified_ask():
    from outreach.drafting import ASKS
    exact = GOOD.replace('Would you be open to a brief conversation about the role?', ASKS[('manager','job')])
    drafter, _ = client(response(text(exact)))
    flags = drafter.draft(JOB, Person('p','Alex','Engineering Manager','example.org'), CANDIDATE, Request()).review_flags
    assert 'ask:manager' in flags and 'ask_modified' not in flags
    drafter, _ = client(response(text(GOOD)))
    flags = drafter.draft(JOB, Person('p','Alex','Engineering Manager','example.org'), CANDIDATE, Request()).review_flags
    assert 'ask_modified' in flags


def test_application_status_default_comes_from_settings(tmp_path):
    from outreach.main import parse_request
    assert parse_request(['--job-url', URL]).application_status == 'applied'
    assert parse_request(['--job-url', URL, '--application-status', 'interested']).application_status == 'interested'
    from outreach.sheets_queue import row_request
    from outreach.settings import load_settings
    path = tmp_path/'settings.yaml'
    path.write_text(yaml.safe_dump({'default_application_status':'unknown'}))
    assert row_request({'job_url':URL}, load_settings(path)).application_status == 'unknown'
    path.write_text(yaml.safe_dump({'default_application_status':'maybe'}))
    with pytest.raises(ValueError): load_settings(path)
