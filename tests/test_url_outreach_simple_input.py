from dataclasses import replace
from types import SimpleNamespace

import pytest

from outreach.context import InputError
from outreach.main import parse_request
from outreach.models import Person, Request, Outcome
from outreach.settings import load_settings, Settings
from outreach.sheets_queue import row_request, preview_rows, QueueProcessor
from outreach.service import run
from outreach.store import Store


def test_paste_only_job_url_uses_defaults():
    request=row_request({'job_url':'https://example.org/jobs/123'},load_settings())
    assert request.max_contacts==1 and request.draft_email is True
    assert request.simple_input is True


def test_paste_only_linkedin_url_needs_no_other_fields():
    request=row_request({'job_url':'https://www.linkedin.com/in/Jordan-Blake/'},load_settings())
    assert request.linkedin_url=='https://linkedin.com/in/jordan-blake'
    assert request.job_url is None and request.draft_email is False


@pytest.mark.parametrize('row',[
    {'job_url':'Jordan Blake | Northstar'},
    {'input':'Jordan Blake','company':'Northstar'},
    {'job_url':'Jordan Blake','company_url':'Northstar'},
])
def test_name_company_needs_no_operational_columns(row):
    request=row_request(row,load_settings())
    assert request.person_name=='Jordan Blake' and request.company_name=='Northstar'
    assert request.draft_email is False


def test_name_only_asks_only_for_company():
    with pytest.raises(InputError,match='company'):
        row_request({'job_url':'Jordan Blake'},load_settings())


def test_company_website_has_default_target_role():
    request=row_request({'job_url':'https://example.org'},load_settings())
    assert request.company_url=='https://example.org' and request.target_role=='Software Engineer'


def test_positional_cli_accepts_linkedin_or_name_company():
    assert parse_request(['https://linkedin.com/in/jordan-blake']).linkedin_url
    assert parse_request(['Jordan Blake | Northstar']).person_name=='Jordan Blake'


def test_minimal_rows_are_ready_without_ids_or_flags():
    summary=preview_rows([{'job_url':'https://example.org/jobs/123'}],load_settings())
    assert summary['ready_valid']==1 and not summary['invalid']


def test_explicit_false_still_holds_a_row():
    summary=preview_rows([{'job_url':'https://example.org/jobs/123','ready':False}],load_settings())
    assert summary['not_ready']==1


def test_person_url_is_one_budgeted_lookup_not_people_search(tmp_path):
    settings=Settings(tmp_path,tmp_path/'state',tmp_path/'out',allocation_confirmed=True)
    store=Store(settings.state_path,settings)
    request=row_request({'job_url':'https://linkedin.com/in/jordan-blake'},settings)
    class Apollo:
        calls=0
        def lookup(self,**kwargs):
            self.calls+=1
            return Person('person1','Jordan Blake','Staff Engineer','northstar.example',
                          'https://linkedin.com/in/jordan-blake','jordan@northstar.example',company_name='Northstar')
        def search(self,*args): pytest.fail('Known person must not trigger a broad search')
        def enrich(self,*args): pytest.fail('Do not pay twice for the same resolved person')
    apollo=Apollo()
    for _ in range(2):
        result=run(request,settings=settings,store=store,fetch=lambda _:pytest.fail('No LinkedIn scraping'),apollo=apollo)
        assert result.people[0].email=='jordan@northstar.example'
    assert apollo.calls==1 and store.remaining('enrich')==4 and store.remaining('search')==5


def test_minimal_sheet_edit_requeues_without_internal_token(tmp_path):
    settings=Settings(tmp_path,tmp_path/'state',tmp_path/'out'); store=Store(settings.state_path,settings)
    class Sheet:
        row={'job_url':'https://example.org/jobs/1'}
        def read_queue(self): return [dict(self.row)]
        def write_status(self,row_id,hashed,values):
            if 'row_id' in values: self.row['row_id']=values['row_id']
        def write_results(self,rows): pass
    sheet=Sheet(); calls=[]
    def process(request):
        calls.append(request)
        return Outcome('run'+str(len(calls)),'done',None,(),{},())
    queue=QueueProcessor(sheet,store,process,settings,'fake')
    queue.sync(); queue.sync(); assert len(calls)==1
    sheet.row['job_url']='https://example.org/jobs/2'
    queue.sync(); assert len(calls)==2


def test_name_company_lookup_retains_identity_and_avoids_search(tmp_path):
    settings=Settings(tmp_path,tmp_path/'state',tmp_path/'out',allocation_confirmed=True)
    store=Store(settings.state_path,settings); seen=[]
    class Apollo:
        def lookup(self,**kwargs):
            seen.append(kwargs)
            return Person('person1','Jordan Blake','Staff Engineer','northstar.example',email='jordan@northstar.example',company_name='Northstar, Inc.')
        def search(self,*args): pytest.fail('No broad search for a named person')
        def enrich(self,*args): pytest.fail('No duplicate paid enrichment')
    result=run(row_request({'job_url':'Jordan Blake | Northstar'},settings),settings=settings,
               store=store,fetch=lambda _:pytest.fail('No page fetch needed'),apollo=Apollo())
    assert seen==[{'name':'Jordan Blake','organization_name':'Northstar'}]
    assert result.metadata['identity_match'] is True
    assert result.people[0].email=='jordan@northstar.example'


def test_simple_lookup_request_parameters_are_exact():
    from outreach.apollo import ApolloClient
    from tests.test_url_outreach_apollo import Transport
    transport=Transport({'person':{'id':'person1','name':'Jordan Blake','email':'jordan@northstar.example',
        'organization':{'name':'Northstar','primary_domain':'northstar.example'}},'match_confidence':'high'})
    result=ApolloClient('fake',transport).lookup(name='Jordan Blake',organization_name='Northstar')
    assert result.match_confidence=='high'
    url,arguments=transport.calls[0]
    assert url.endswith('/people/match') and arguments['json'] is None
    assert arguments['params']['organization_name']=='Northstar'
    assert arguments['params']['reveal_personal_emails']=='false'


def test_google_status_write_can_assign_an_automatic_id():
    from outreach.sheets_queue import GoogleQueue,QUEUE_HEADERS,input_hash
    from outreach.intake import prepare_row
    writes=[]
    class API:
        def spreadsheets(self): return self
        def values(self): return self
        def batchUpdate(self,**kwargs): writes.append(kwargs); return self
        def execute(self,**kwargs): return {}
    raw={key:'' for key in QUEUE_HEADERS}; raw['job_url']='https://example.org/jobs/1'
    row=prepare_row(raw,2)
    queue=GoogleQueue('fake',service=API())
    queue._read=lambda _: [list(QUEUE_HEADERS),[raw[key] for key in QUEUE_HEADERS]]
    queue.write_status(row['row_id'],input_hash(row),{'row_id':row['row_id'],'status':'processing'})
    assert writes[0]['body']['data'][0]['range']=="'Queue'!A2"


def test_simple_ai_role_selects_profile_without_another_input(outreach_project):
    from outreach.profile import select_profile
    from outreach.models import Context
    context=Context('Example','example.org','AI Software Engineer',None,'',(),())
    assert select_profile(context,'auto',automatic=True)=='amazon'


def test_sheet_setup_uses_api_and_keeps_input_columns_only():
    from outreach.sheets_queue import GoogleQueue,QUEUE_HEADERS
    calls=[]
    class API:
        def spreadsheets(self): return self
        def get(self,**kwargs): self.action='get'; return self
        def batchUpdate(self,**kwargs): calls.append(kwargs); self.action='update'; return self
        def execute(self,**kwargs):
            return {'sheets':[{'properties':{'sheetId':0,'title':'Queue'}}]} if self.action=='get' else {}
    queue=GoogleQueue('fake',service=API()); queue._read=lambda _: [list(QUEUE_HEADERS)]
    queue.setup_simple_layout()
    requests=calls[0]['body']['requests']
    headers=requests[0]['updateCells']['rows'][0]['values']
    assert headers[2]['userEnteredValue']['stringValue']=='input'
    assert headers[3]['userEnteredValue']['stringValue']=='company'
    assert any(r.get('updateDimensionProperties',{}).get('properties',{}).get('hiddenByUser') is True for r in requests)
    assert not any('delete' in str(r).lower() for r in requests)


def test_explicit_zero_contact_cap_is_not_replaced_with_default():
    with pytest.raises(InputError):
        parse_request(['--job-url','https://example.org/jobs/1','--max-contacts','0'])


def test_changed_row_before_status_write_does_not_spend(tmp_path):
    settings=Settings(tmp_path,tmp_path/'state',tmp_path/'out'); store=Store(settings.state_path,settings)
    class Sheet:
        def read_queue(self): return [{'job_url':'https://example.org/jobs/1'}]
        def write_status(self,*args): return False
    queue=QueueProcessor(Sheet(),store,lambda _:pytest.fail('Changed input must not be processed'),settings,'fake')
    assert queue.sync()['errors']==1
    assert not store.list_pending()['claims']
