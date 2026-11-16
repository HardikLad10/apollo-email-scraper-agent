"""Apollo search and professional-email enrichment, without retries or fallback."""
from dataclasses import replace
from urllib.parse import urlsplit
import requests

from .models import Person, Evidence
from .ranking import TITLE_SETS
from .context import employer_domain, InputError

BASE = 'https://api.apollo.io/api/v1/'


class ProviderError(RuntimeError):
    def __init__(self, message, uncertain=False):
        super().__init__(message)
        self.uncertain = uncertain


def _domain(value):
    if not isinstance(value, str): return ''
    try: return employer_domain(value if '://' in value else 'https://'+value)
    except InputError: return ''


def _person(record):
    if not isinstance(record, dict) or not record.get('id'): raise ProviderError('Malformed Apollo person')
    org = record.get('organization') or {}
    if not isinstance(org,dict): org = {}
    employer = _domain(org.get('primary_domain') or org.get('website_url') or '')
    history=record.get('employment_history') or []
    if isinstance(history,list):
        current=[entry for entry in history if isinstance(entry,dict) and entry.get('current') is True]
        if current:
            current_ids={entry['organization_id'] for entry in current if entry.get('organization_id')}
            if len(current_ids)>1 or (org.get('id') and current_ids and org['id'] not in current_ids): employer=''
        elif org.get('id') and any(isinstance(entry,dict) and entry.get('organization_id')==org['id'] and entry.get('current') is False for entry in history):
            employer=''
    email = record.get('email')
    if not isinstance(email,str) or '@' not in email or email.startswith('email_not_unlocked') or record.get('revealed_for_current_team') is False:
        email = None
    name = record.get('name') or ' '.join(str(record.get(k) or '') for k in ('first_name','last_name')).strip()
    if not all(isinstance(v,str) for v in (name, record.get('title') or '')): raise ProviderError('Malformed Apollo identity')
    evidence = (Evidence('current_organization',employer,BASE+'people/bulk_match','confirmed'),) if employer else ()
    return Person(str(record['id']),name,record.get('title') or '',employer,
                  record.get('linkedin_url'),email,str(record.get('email_status') or 'unknown').lower(),
                  evidence=evidence,email_available=record.get('has_email') if type(record.get('has_email')) is bool else None,
                  company_name=org.get('name') if isinstance(org.get('name'),str) else '',
                  match_confidence=str(record.get('match_confidence') or 'unknown').lower())


def employer_check(person, expected_domain):
    status = 'unknown' if not person.company_domain or not expected_domain else ('confirmed' if person.company_domain == expected_domain else 'mismatch')
    return replace(person, employer_match=status)


class ApolloClient:
    def __init__(self, api_key, transport=None, timeout=15):
        self.key, self.transport, self.timeout = api_key, transport or requests.Session(), timeout

    def _post(self, endpoint, payload=None, *, params=None):
        try:
            response = self.transport.post(BASE+endpoint, headers={'x-api-key':self.key}, json=payload, params=params, timeout=self.timeout, allow_redirects=False)
        except requests.RequestException:
            raise ProviderError('Apollo transport failure; outcome uncertain', uncertain=True) from None
        if response.status_code != 200:
            raise ProviderError(f'Apollo HTTP {response.status_code}', uncertain=response.status_code >= 500)
        try: body = response.json()
        except (ValueError, TypeError): raise ProviderError('Malformed Apollo response', uncertain=True) from None
        if not isinstance(body, dict): raise ProviderError('Malformed Apollo response', uncertain=True)
        return body

    def search(self, context, roles, page, per_page):
        payload = {'q_organization_domains_list[]':[context.company_domain],
                   'person_titles[]':sorted({title for role in roles for title in TITLE_SETS[role]}),
                   'page':page,'per_page':per_page}
        records = self._post('mixed_people/api_search',params=payload).get('people')
        if not isinstance(records,list): raise ProviderError('Missing Apollo people list', uncertain=True)
        # Search identities may be obfuscated; do not invent missing last names or email.
        return [employer_check(replace(_person(p),email=None),context.company_domain) for p in records]

    def enrich(self, ids):
        if not ids: return {}
        if len(ids)>10: raise ValueError('Apollo batch maximum is 10')
        payload = {'details':[{'id':identifier} for identifier in ids]}
        # Apollo documents these as query parameters, not JSON body fields.
        params={key:'false' for key in ('reveal_personal_emails','reveal_phone_number','run_waterfall_email','run_waterfall_phone')}
        records = self._post('people/bulk_match',payload,params=params).get('matches')
        if not isinstance(records,list): raise ProviderError('Missing Apollo matches', uncertain=True)
        result = {}
        for record in records:
            if record is None: continue
            person = _person(record)
            if person.apollo_id not in ids: raise ProviderError('Unexpected Apollo person ID', uncertain=True)
            result[person.apollo_id] = person
        return result

    def lookup(self,*,linkedin_url=None,name=None,organization_name=None,domain=None):
        params={key:value for key,value in {'linkedin_url':linkedin_url,'name':name,
                'organization_name':organization_name,'domain':domain}.items() if value}
        if not linkedin_url and not (name and (organization_name or domain)):
            raise ValueError('Person lookup requires LinkedIn URL or name and company')
        params.update({key:'false' for key in ('reveal_personal_emails','reveal_phone_number','run_waterfall_email','run_waterfall_phone')})
        body=self._post('people/match',params=params)
        record=body.get('person')
        if record is None: return None
        if not isinstance(record,dict): raise ProviderError('Malformed Apollo person lookup',uncertain=True)
        return _person({**record,'match_confidence':record.get('match_confidence') or body.get('match_confidence') or 'unknown'})
