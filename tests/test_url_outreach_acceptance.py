import json
import socket
from pathlib import Path

import pytest

from outreach.drafting import DraftClient
from outreach.models import Context, Person, Candidate, Request
from tests.test_url_outreach_drafting import EMAIL


def test_real_sdk_accepts_opus_effort_without_network(monkeypatch,outreach_project):
    import httpx2
    from anthropic import Anthropic
    monkeypatch.setattr(socket,'create_connection',lambda *a,**kw:pytest.fail('network forbidden'))
    calls=[]
    def respond(request):
        calls.append(json.loads(request.content))
        return httpx2.Response(200,json={'id':'msg_fake','type':'message','role':'assistant','model':'claude-opus-5-5',
            'content':[{'type':'text','text':EMAIL}],'stop_reason':'end_turn','stop_sequence':None,
            'usage':{'input_tokens':100,'output_tokens':100}})
    with httpx2.Client(transport=httpx2.MockTransport(respond)) as http:
        sdk=Anthropic(api_key='fake-not-a-secret',max_retries=0,http_client=http)
        prompt=(outreach_project/'claude_cold_email_prompt_v1.md').read_text()
        client=DraftClient('fake',prompt,8192,client=sdk)
        context=Context('Example','example.org','Full Stack Engineer','https://example.org/jobs/1','React',(),())
        candidate=Candidate('fullstack',('React','APIs','SQL'),(),{},'hash')
        assert client.draft(context,Person('p','Alex','Recruiter','example.org'),candidate,Request()).subject
    assert len(calls)==1
    assert calls[0]['model']=='claude-opus-5-5' and calls[0]['output_config']=={'effort':'high'}
    assert calls[0]['system'].count('<example format=')==2


def test_preview_does_not_make_network_calls_or_write(tmp_path,monkeypatch):
    from outreach.main import main
    monkeypatch.setattr(socket,'create_connection',lambda *a,**kw:pytest.fail('network forbidden'))
    monkeypatch.chdir(tmp_path)
    assert main(['--company-url','https://example.org','--target-role','Full Stack Engineer','--draft-email','--dry-run'])==0
    assert not list(tmp_path.iterdir())
