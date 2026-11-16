from dataclasses import replace
import json

import pytest

from outreach.models import Person, Request
from outreach.service import run
from outreach.settings import Settings
from outreach.sheets_queue import row_request, QueueProcessor
from outreach.store import Store
from tests.test_url_outreach_draft_v2 import client, response, text, GOOD, JOB, PERSON, CANDIDATE
from tests.test_url_outreach_reuse import workflow


def test_post_input_is_email_only_without_operational_columns(outreach_project):
    from outreach.settings import load_settings
    request = row_request({'input':'https://www.linkedin.com/posts/jordan-blake_activity-123-abc'},load_settings())
    assert request.linkedin_post_url and not request.job_url
    assert request.draft_email is False and request.max_contacts == 1


def test_post_author_resolution_uses_direct_lookup_and_reuses_profile_cache(tmp_path):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out',allocation_confirmed=True)
    store=Store(settings.state_path,settings)
    post='https://www.linkedin.com/posts/jordan-blake_activity-123-abc'
    page='<script type="application/ld+json">'+json.dumps({
        '@type':'SocialMediaPosting','author':{'@type':'Person','url':'https://www.linkedin.com/in/Jordan-Blake/'}})+'</script>'
    class Apollo:
        def __init__(self): self.lookups=[]
        def lookup(self, **filters):
            self.lookups.append(filters)
            return Person('p','Jordan Blake','Engineer','example.org',
                          'https://linkedin.com/in/jordan-blake','jordan@example.org')
        def search(self,*a,**kw): pytest.fail('A post must not trigger broad people search')
        def enrich(self,*a,**kw): pytest.fail('No second enrichment after direct lookup')
    apollo=Apollo()
    result=run(row_request({'input':post},settings),settings=settings,store=store,
               fetch=lambda _:page,apollo=apollo)
    assert result.status=='done' and result.people[0].email=='jordan@example.org'
    assert result.metadata['source_url']==post
    assert any(e.kind=='post_author' for e in result.context.evidence)
    assert not result.drafts
    result=run(row_request({'input':'https://linkedin.com/in/jordan-blake'},settings),settings=settings,
               store=store,fetch=lambda _:pytest.fail('Never scrape a personal profile'),apollo=apollo)
    assert result.status=='done' and apollo.lookups==[{'linkedin_url':'https://linkedin.com/in/jordan-blake'}]


@pytest.mark.parametrize('page',[
    '<html>Please sign in</html>',
    '<a href="https://linkedin.com/in/some-commenter">A commenter</a>',
    '<script type="application/ld+json">{"author":{"url":"https://linkedin.com/company/example"}}</script>',
    '<script type="application/ld+json">{"author":[{"url":"https://linkedin.com/in/one"},{"url":"https://linkedin.com/in/two"}]}</script>',
])
def test_post_without_unique_person_author_needs_context_before_spend(tmp_path,page):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out',allocation_confirmed=True)
    store=Store(settings.state_path,settings)
    class Apollo:
        def lookup(self,**kwargs): pytest.fail('Do not guess the post author')
    request=row_request({'input':'https://www.linkedin.com/feed/update/urn:li:activity:123'},settings)
    result=run(request,settings=settings,store=store,fetch=lambda _:page,apollo=Apollo())
    assert result.status=='needs_context'
    assert any('profile' in flag.lower() for flag in result.review_flags)
    assert store.remaining('enrich')==5


def test_continuation_preserves_turn_search_cap_and_reports_requests():
    drafter, fake=client(response(text('Researching.'),stop='pause_turn',searches=1),response(text(GOOD),searches=1))
    draft=drafter.draft(JOB,PERSON,CANDIDATE,Request())
    assert fake.calls[1]['tools'][0]['max_uses']==2
    assert 'api_requests:2' in draft.review_flags and 'web_searches:2' in draft.review_flags


def test_search_setting_invalidates_job_result_key(outreach_project):
    from outreach.models import Request
    from outreach.reuse import result_key
    settings=Settings(outreach_project,outreach_project/'db',outreach_project/'out',draft_web_search_max_uses=2)
    request=Request(job_url='https://example.org/jobs/1',company_url='https://example.org',draft_email=True)
    assert result_key(request,settings,'same prompt')!=result_key(request,replace(settings,draft_web_search_max_uses=0),'same prompt')


def test_web_search_setting_change_regenerates_draft_without_apollo(workflow):
    settings,store,_,apollo,drafter,_,execute,request=workflow
    execute(request)
    result=run(request,settings=replace(settings,draft_web_search_max_uses=0),store=store,
               fetch=lambda _: '<script type="application/ld+json">'+json.dumps({
                   '@type':'JobPosting','title':'Full Stack Engineer','description':'Build Python and React APIs',
                   'hiringOrganization':{'name':'Example','url':'https://example.org'}})+'</script>',
               apollo=apollo,drafter=drafter)
    assert result.status=='done'
    assert (apollo.searches,apollo.enrichments,drafter.calls)==(1,1,2)


def test_sheet_rechecks_completed_row_after_prompt_changes(outreach_project,tmp_path):
    from outreach.models import Outcome
    settings=Settings(outreach_project,tmp_path/'db',tmp_path/'out')
    store=Store(settings.state_path,settings)
    calls=[]
    class Sheet:
        def read_queue(self): return [{'input':'https://example.org/jobs/1','company':'https://example.org'}]
        def write_status(self,*args): pass
        def write_results(self,*args): pass
    def process(request):
        calls.append(request)
        return Outcome('run'+str(len(calls)),'done',None,(),{},())
    queue=QueueProcessor(Sheet(),store,process,settings,'test')
    queue.sync();queue.sync();assert len(calls)==1
    prompt=outreach_project/'claude_cold_email_prompt_v2.md'
    prompt.write_text(prompt.read_text()+'\nUpdated style instruction.\n')
    queue.sync();queue.sync()
    assert len(calls)==2


def test_prompt_change_does_not_retry_failed_sheet_claim(outreach_project,tmp_path):
    from outreach.models import Outcome
    settings=Settings(outreach_project,tmp_path/'db',tmp_path/'out')
    store=Store(settings.state_path,settings);calls=[]
    class Sheet:
        def read_queue(self): return [{'input':'https://example.org/jobs/1','company':'https://example.org'}]
        def write_status(self,*args): pass
        def write_results(self,*args): pass
    def process(request):
        calls.append(request)
        raise RuntimeError('simulated interrupted operation')
    queue=QueueProcessor(Sheet(),store,process,settings,'test');queue.sync()
    prompt=outreach_project/'claude_cold_email_prompt_v2.md'
    prompt.write_text(prompt.read_text()+'\nUpdated style instruction.\n')
    queue.sync()
    assert len(calls)==1


def test_linkedin_job_link_remains_a_job_input(tmp_path):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out')
    url='https://www.linkedin.com/jobs/view/123456789'
    request=row_request({'input':url,'company':'https://example.org'},settings)
    assert request.job_url==url and request.draft_email is True
    assert request.linkedin_url is None and request.linkedin_post_url is None


def test_missing_google_credentials_explain_the_next_setup_step(monkeypatch):
    from google.auth.exceptions import DefaultCredentialsError
    from outreach.sheets_queue import GoogleQueue,QueueError
    import shared.sheets
    def missing(): raise DefaultCredentialsError('credentials missing')
    monkeypatch.setattr(shared.sheets,'_service',missing)
    with pytest.raises(QueueError,match='GOOGLE_APPLICATION_CREDENTIALS'):
        GoogleQueue('fictional-sheet')


def test_profile_lookup_cache_is_shared_with_optional_company_column(tmp_path):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out',allocation_confirmed=True)
    store=Store(settings.state_path,settings)
    class Apollo:
        def __init__(self): self.calls=0
        def lookup(self,**kwargs):
            self.calls+=1
            return Person('p','Jordan Blake','Engineer','example.org',
                          'https://linkedin.com/in/jordan-blake','jordan@example.org')
    apollo=Apollo()
    for company in ('https://example.org',''):
        result=run(row_request({'input':'https://linkedin.com/in/jordan-blake','company':company},settings),
                   settings=settings,store=store,fetch=lambda _:pytest.fail('Do not scrape a profile'),apollo=apollo)
        assert result.status=='done' and result.people[0].email
    assert apollo.calls==1 and store.remaining('enrich')==4


def test_missing_jd_does_not_block_email_lookup_and_draft(workflow):
    settings,store,_,apollo,drafter,_,_,request=workflow
    page='<h1>Full Stack Engineer</h1><div class="job__description"><p>About Example</p><p>We build developer tools.</p><p>n/a</p></div>'
    result=run(request,settings=settings,store=store,fetch=lambda _:page,apollo=apollo,drafter=drafter)
    assert result.status=='done' and result.people[0].email and len(result.drafts)==1
    assert 'job_description_missing' in result.review_flags
    assert result.metadata['job_description_status']=='missing'


def test_draft_payload_labels_missing_jd_instead_of_inventing_requirements():
    from outreach.drafting import build_message
    from outreach.models import Evidence
    context=replace(JOB,description='Example builds developer tools.',evidence=(Evidence('job_description','missing_role_details',JOB.job_url,'unknown'),))
    payload=json.loads(build_message(context,PERSON,CANDIDATE,Request()).split('\n',1)[1])
    assert payload['job_description_status']=='missing'
    assert 'do not infer' in payload['context_limitations'].lower()
