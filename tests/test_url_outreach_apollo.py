import pytest

from outreach.apollo import ApolloClient, ProviderError
from outreach.models import Context, Person
from outreach.ranking import rank_people


class Response:
    status_code = 200
    def __init__(self, data): self.data = data
    def json(self): return self.data


class Transport:
    def __init__(self, body): self.body, self.calls = body, []
    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return Response(self.body)


def context():
    return Context('Example', 'example.org', 'Full Stack Engineer', None, 'React APIs', (), ())


def test_search_supports_id_without_linkedin():
    transport = Transport({'people': [{'id':'fake-person-1', 'first_name':'Alex', 'title':'Technical Recruiter', 'organization': {'primary_domain':'example.org'}}]})
    client = ApolloClient('fake-key', transport, 15)
    person = client.search(context(), ('technical_recruiter',), 1, 25)[0]
    assert person.apollo_id == 'fake-person-1'
    assert person.linkedin_url is None and person.email is None
    assert transport.calls[0][1]['params']['q_organization_domains_list[]'] == ['example.org']


def test_enrichment_uses_ids_and_professional_email_only():
    transport = Transport({'matches':[{'id':'id1','name':'Alex','title':'Technical Recruiter','email':'alex@example.org','email_status':'verified','organization':{'primary_domain':'example.org'}}]})
    client = ApolloClient('fake-key', transport, 15)
    assert client.enrich(['id1'])['id1'].email == 'alex@example.org'
    payload = transport.calls[0][1]['json']
    assert payload['details'] == [{'id':'id1'}]
    assert set(payload)=={'details'}
    switches=transport.calls[0][1]['params']
    assert switches=={'reveal_personal_emails':'false','reveal_phone_number':'false','run_waterfall_email':'false','run_waterfall_phone':'false'}


def test_rank_excludes_known_mismatch():
    people = [Person('a','Alex','Technical Recruiter','other.org',employer_match='mismatch'), Person('b','Sam','Technical Recruiter','example.org')]
    assert [p.apollo_id for p in rank_people(people, context(), ('technical_recruiter',), 3)] == ['b']


def test_current_history_overrides_old_organization():
    transport = Transport({'matches':[{'id':'id1','email':'alex@example.org',
        'organization':{'id':'old','primary_domain':'example.org'},
        'employment_history':[{'current':True,'organization_id':'new','organization_name':'Other'}]}]})
    person = ApolloClient('fake',transport).enrich(['id1'])['id1']
    assert person.company_domain==''  # A different organization ID cannot confirm a domain.


@pytest.mark.parametrize('status',[401,403,429,500])
def test_errors_are_safe_and_not_retried(status):
    transport=Transport({'error':'secret-contact-body'})
    def post(url,**kwargs):
        transport.calls.append((url,kwargs))
        response=Response({'secret':'contact body'})
        response.status_code=status
        return response
    transport.post=post
    with pytest.raises(ProviderError) as error:
        ApolloClient('fake',transport).search(context(),('technical_recruiter',),1,25)
    assert len(transport.calls)==1
    assert 'contact' not in str(error.value)
