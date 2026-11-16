from dataclasses import replace
from pathlib import Path

from outreach.models import Request, Person, Draft
from outreach.settings import Settings
from outreach.store import Store
from outreach.service import run
from outreach.export import export_run


def test_three_outcomes_one_draft_and_cached_repeat(tmp_path,monkeypatch,outreach_project):
    settings = Settings(project_root=outreach_project,state_path=tmp_path/'state.db',output_dir=tmp_path/'out',allocation_confirmed=True)
    assert settings.project_root != Path(__file__).resolve().parents[1], 'Tests must not use the personal profile root'
    store = Store(settings.state_path,settings)
    class Apollo:
        searches = enrichments = 0
        def search(self, context, roles, page, per_page):
            self.searches += 1
            return [Person(str(i),'Alex','Technical Recruiter','example.org') for i in range(3)]
        def enrich(self, ids):
            self.enrichments += len(ids)
            identifier = ids[0]
            return {identifier:Person(identifier,'Alex','Technical Recruiter', 'other.org' if identifier=='2' else 'example.org',
                                     email=None if identifier=='1' else 'alex@example.org',email_status='verified')}
    class Drafter:
        prompt = 'fake full prompt'
        calls = 0
        def draft(self,*args):
            self.calls += 1
            return Draft('Test','- one\n- two\n- three')
    apollo,drafter = Apollo(),Drafter()
    request = Request(company_url='https://example.org',target_role='Full Stack Engineer',draft_email=True)
    fetch = lambda _: '<p>Example builds React developer tools.</p>'
    first = run(request,settings=settings,store=store,fetch=fetch,apollo=apollo,drafter=drafter)
    assert len(first.people)==3 and len(first.drafts)==1
    assert (store.remaining('search'),store.remaining('enrich'),store.remaining('draft')) == (4,2,4)
    assert first.metadata['counts']['provider_attempts']=={'search':1,'enrich':3,'draft':1}
    assert first.metadata['counts']['found']==2 and first.metadata['counts']['not_found']==1
    assert first.metadata['counts']['failed']==0 and first.metadata['counts']['remaining']['enrich']==2
    assert not any(flag=='2:persona_mismatch' for flag in first.review_flags)
    import pytest
    from outreach import export as output
    with monkeypatch.context() as patch:
        def fail_write(*args): raise OSError('simulated export failure')
        patch.setattr(output,'_write',fail_write)
        with pytest.raises(OSError): export_run(first,settings.output_dir)
    second = run(request,settings=settings,store=store,fetch=fetch,apollo=apollo,drafter=drafter)
    assert len(second.drafts)==1
    assert (apollo.searches,apollo.enrichments,drafter.calls)==(1,3,1)
    csv_path,json_path = export_run(first,settings.output_dir)
    assert csv_path.exists() and json_path.exists()
    import json
    assert json.loads(json_path.read_text())['outcome']['metadata']['selected_profile']=='fullstack'
    another_job=replace(request,target_role='Backend Engineer')
    third=run(another_job,settings=settings,store=store,fetch=fetch,apollo=apollo,drafter=drafter)
    assert len(third.drafts)==1
    assert (apollo.searches,apollo.enrichments,drafter.calls)==(1,3,2)


def test_export_does_not_execute_spreadsheet_formulas(tmp_path):
    from outreach.models import Outcome
    outcome=Outcome('run1','done',None,(Person('p','=HYPERLINK("evil")','Recruiter','example.org'),),{},())
    csv_path,json_path=export_run(outcome,tmp_path)
    assert "'=HYPERLINK" in csv_path.read_text()
    assert '=HYPERLINK' in json_path.read_text()


def test_shared_run_budget_applies_across_requests(tmp_path):
    from outreach.service import RunBudget, _paid
    from outreach.store import BudgetExceeded
    import pytest
    settings=Settings(tmp_path,tmp_path/'state',tmp_path/'out',enrich_run_limit=1)
    store=Store(settings.state_path,settings)
    budget=RunBudget(settings)
    assert _paid(store,'enrich','one',lambda:{'found':True},budget)=={'found':True}
    assert _paid(store,'enrich','one',lambda:pytest.fail('cached'),budget)=={'found':True}
    with pytest.raises(BudgetExceeded):
        _paid(store,'enrich','two',lambda:pytest.fail('over run cap'),budget)
    assert store.remaining('enrich')==4


def test_provider_timeout_is_not_retried_on_next_run(tmp_path):
    from outreach.service import _paid
    from outreach.apollo import ProviderError
    from outreach.store import AttemptUncertain
    import pytest
    settings=Settings(tmp_path,tmp_path/'state',tmp_path/'out')
    store=Store(settings.state_path,settings)
    def fail(): raise ProviderError('timeout',uncertain=True)
    with pytest.raises(ProviderError): _paid(store,'enrich','one',fail)
    with pytest.raises(AttemptUncertain): _paid(store,'enrich','one',lambda:pytest.fail('must not retry'))
    assert store.remaining('enrich')==4
