from dataclasses import replace

from outreach.models import Request, Person
from outreach.settings import Settings
from outreach.store import Store
from outreach.service import run


class Apollo:
    def __init__(self,people): self.people,self.enriched=people,[]
    def search(self,*args): return self.people
    def enrich(self,ids):
        self.enriched.extend(ids)
        return {p.apollo_id:replace(p,email='SHARED@example.org') for p in self.people if p.apollo_id in ids}


def execute(tmp_path,people,store=None,roles=Request().contact_roles):
    settings=Settings(tmp_path,tmp_path/'state',tmp_path/'out',allocation_confirmed=True)
    store=store or Store(settings.state_path,settings)
    apollo=Apollo(people)
    result=run(Request(company_url='https://example.org',target_role='Software Engineer',contact_roles=roles),
               settings=settings,store=store,fetch=lambda _: '',apollo=apollo)
    return result,apollo,store


def test_linkedin_aliases_consume_one_lookup(tmp_path):
    people=[Person('a','Alex','Technical Recruiter','example.org','https://www.linkedin.com/in/alex/'),
            Person('b','Alex','Technical Recruiter','example.org','http://linkedin.com/in/Alex')]
    result,apollo,store=execute(tmp_path,people)
    assert len(apollo.enriched)==1 and store.remaining('enrich')==4
    assert result.people[0].linkedin_url=='https://linkedin.com/in/alex'


def test_duplicate_email_flagged_without_drafting(tmp_path):
    people=[Person(identifier,'Alex','Technical Recruiter','example.org') for identifier in ('a','b')]
    result,_,_=execute(tmp_path,people)
    assert 'b:duplicate_email' in result.review_flags


def test_duplicate_email_flag_survives_restart(tmp_path):
    first,_,store=execute(tmp_path,[Person('a','Alex','Technical Recruiter','example.org')])
    reopened=Store(store.path,store.settings)
    second,_,_=execute(tmp_path,[Person('b','Alex','Technical Recruiter','example.org')],reopened,('technical_recruiter',))
    assert 'b:duplicate_email' in second.review_flags
    assert b'SHARED@example.org' not in b''.join(str(row).encode() for row in store.email_identities())


def test_explicit_has_email_false_avoids_paid_enrichment(tmp_path):
    people=[Person('a','Alex','Technical Recruiter','example.org',email_available=False)]
    result,apollo,store=execute(tmp_path,people)
    assert not apollo.enriched and store.remaining('enrich')==5
    assert len(result.people)==1 and 'a:no_email' in result.review_flags
