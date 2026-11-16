from dataclasses import replace
from types import SimpleNamespace
import json
import pytest

from outreach.models import Person, Context, Request, Candidate, Outcome
from outreach.settings import load_settings
from outreach.main import main
from outreach.store import Store
from outreach.ranking import rank_people
from outreach.drafting import DraftClient,DraftError


def test_cto_is_not_a_substring_of_director():
    context=Context('Example','example.org','Engineer',None,'',(),())
    people=[Person('wrong','Alex','Director of Marketing','example.org'),Person('right','Sam','CTO / Co-founder','example.org')]
    assert [p.apollo_id for p in rank_people(people,context,('cto',),3)]==['right']


def test_missing_export_is_readonly():
    settings=load_settings()
    assert main(['--export-run','missing'])==3
    assert not settings.state_path.parent.exists()


@pytest.mark.parametrize('prefix',['\t','\r'])
def test_csv_escapes_control_prefixes(tmp_path,prefix):
    from outreach.export import export_run
    outcome=Outcome('test','done',None,(Person('p',prefix+'value','Recruiter','example.org'),),{},())
    csv_path,_=export_run(outcome,tmp_path)
    import csv
    with csv_path.open(newline='') as stream: row=next(csv.DictReader(stream))
    assert row['name'].startswith("'"+prefix)


def test_local_draft_typeerror_is_not_uncertain():
    class Messages:
        def create(self,**kwargs): raise TypeError('local argument error')
    client=DraftClient('fake','prompt',client=SimpleNamespace(messages=Messages()))
    with pytest.raises(DraftError) as error:
        client.draft(Context('Example','example.org','Engineer',None,'',(),()),Person('p','Sam','CTO','example.org'),
                     Candidate('fullstack',('a','b','c'),(),{},'hash'),Request())
    assert error.value.uncertain is False


def test_draft_timeout_comes_from_settings(monkeypatch):
    import anthropic
    seen=[]
    def constructor(**kwargs): seen.append(kwargs); return SimpleNamespace()
    monkeypatch.setattr(anthropic,'Anthropic',constructor)
    DraftClient('fake','prompt',timeout=17)
    assert seen[0]['timeout']==17 and seen[0]['max_retries']==0


def test_malformed_manifest_is_profile_review_error(outreach_project):
    from outreach.profile import load_candidate,ProfileNeedsReview
    (outreach_project/'config/outreach_profile_sources.yaml').write_text('sources: []')
    with pytest.raises(ProfileNeedsReview):
        load_candidate('fullstack',Context('Example','example.org','Engineer',None,'',(),()),root=outreach_project)


def test_job_only_preview_checks_freshness_and_warns_allocation(outreach_project,capsys):
    (outreach_project/'fullstack.tex').write_text('Changed fictional claim')
    assert main(['--job-url','https://example.org/jobs/1','--draft-email','--dry-run'])==2
    result=json.loads(capsys.readouterr().out)
    assert any('source changed' in message.lower() for message in result['missing_context'])
    assert any('allocation' in message.lower() for message in result['warnings'])


@pytest.mark.parametrize('status,expected',[('error',4),('needs_context',4),('budget_wait',3),('done',0)])
def test_sheet_summary_exit_status(status,expected):
    from outreach.main import sheet_exit_code
    assert sheet_exit_code({'errors':int(status in ('error','needs_context')),'budget_wait':int(status=='budget_wait')})==expected
