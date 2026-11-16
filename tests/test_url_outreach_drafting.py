from types import SimpleNamespace
import pytest

from outreach.drafting import DraftClient, parse_draft, DraftError
from outreach.models import Context, Candidate, Person, Request


EMAIL = 'Subject: Full Stack Engineer at Example\n\nHi Alex,\n\nA few reasons I would fit:\n- Built React apps.\n- Built APIs.\n- Improved SQL queries.\n\nWould you be open to a conversation?\n\nThank you,\nHardik Lad'


def test_parses_three_bullets():
    assert parse_draft(EMAIL).subject == 'Full Stack Engineer at Example'


@pytest.mark.parametrize('text', ['NEEDS_CONTEXT: Missing role', 'Subject: Test\n\nOne paragraph', ''])
def test_rejects_incomplete_output(text):
    with pytest.raises(DraftError): parse_draft(text)


def test_one_request_correct_model_and_effort():
    calls = []
    class Messages:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(stop_reason='end_turn', content=[SimpleNamespace(type='text', text=EMAIL)])
    client = DraftClient('fake', 'FULL STYLE AND EXAMPLES', 8192, client=SimpleNamespace(messages=Messages()))
    context = Context('Example','example.org','Full Stack Engineer',None,'React APIs',(),())
    candidate = Candidate('fullstack',('Built React apps','Built APIs','Improved SQL'),('No invented metrics',),{},'hash')
    client.draft(context, Person('p','Alex','Recruiter','example.org'), candidate, Request())
    assert len(calls) == 1
    assert calls[0]['model'] == 'claude-opus-5-5'
    assert calls[0]['output_config'] == {'effort':'high'}
    assert calls[0]['system'] == 'FULL STYLE AND EXAMPLES'
