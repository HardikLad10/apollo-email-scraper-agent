"""One request through the same budgeted pipeline, from CLI or Sheets."""
from dataclasses import asdict, replace
from pathlib import Path
from datetime import datetime, timezone
import uuid
import re

from shared.linkedin_url import normalize_linkedin_url

from .models import Outcome, Draft, Person, Context, Evidence, fingerprint, person_from_dict, outcome_from_dict
from .context import resolve_context, validate_request, NeedsContext, employer_domain
from .apollo import employer_check, ProviderError
from .drafting import MODEL, EFFORT, DraftError
from .profile import select_profile, load_candidate, ProfileNeedsReview
from .ranking import rank_people, title_matches
from .store import Store, BudgetExceeded, CachedResult, AttemptUncertain, AccountingUnavailable
from .reuse import result_key, restore_history


def _profile_url(value):
    if not isinstance(value,str): return None
    try: normalized=normalize_linkedin_url(value)
    except ValueError: return None
    return normalized if re.fullmatch(r'https://linkedin\.com/in/[^/\s]+',normalized) else None


def _dedupe_people(records):
    identifiers,urls,result=set(),set(),[]
    for record in records:
        url=_profile_url(record.get('linkedin_url'))
        if record['apollo_id'] in identifiers or (url and url in urls): continue
        identifiers.add(record['apollo_id'])
        if url: urls.add(url)
        result.append({**record,'linkedin_url':url})
    return result


def _name_key(value):
    return re.sub(r'[^\w]+','',value.casefold())


def _company_key(value):
    words=re.findall(r'\w+',value.casefold())
    while words and words[-1] in ('inc','incorporated','llc','ltd','limited','corp','corporation','company'):
        words.pop()
    return ''.join(words)


def _lookup_key(filters):
    canonical={key:(_name_key(value) if key=='name' else _company_key(value) if key=='organization_name' else value)
               for key,value in filters.items() if value}
    return fingerprint({'person_lookup':canonical})


def _direct_lookup(request,settings,store,apollo,budget):
    expected=employer_domain(request.company_url) if request.company_url else ''
    filters={'linkedin_url':request.linkedin_url} if request.linkedin_url else {'name':request.person_name}
    if expected: filters['domain']=expected
    elif request.company_name: filters['organization_name']=request.company_name
    key=_lookup_key(filters)
    def call():
        person=apollo.lookup(**filters)
        return {person.apollo_id:asdict(person)} if person else {}
    records=_paid(store,'enrich',key,call,budget)
    if len(records)>1: raise NeedsContext('Ambiguous person lookup; provide their LinkedIn URL')
    person=person_from_dict(next(iter(records.values()))) if records else None
    identity=False
    if person:
        if request.linkedin_url: identity=_profile_url(person.linkedin_url)==request.linkedin_url
        else:
            same_company=(person.company_domain==expected) if expected else bool(_company_key(request.company_name or '') and _company_key(person.company_name)==_company_key(request.company_name or ''))
            identity=_name_key(person.name)==_name_key(request.person_name or '') and same_company
        identity=identity and person.match_confidence not in ('low','none')
        if identity:
            store.alias_cache('enrich',key,fingerprint({'apollo_id':person.apollo_id}))
            if not expected: expected=person.company_domain
    title=request.target_role or settings.queue_target_role
    context=Context(request.company_name or (person.company_name if person else '') or expected,
                    expected,title,None,request.job_description or request.notes,(),
                    (Evidence('person_identity','matched' if identity else 'unverified',request.linkedin_url or 'https://api.apollo.io/api/v1/people/match',
                              'confirmed' if identity else 'unknown'),))
    return context,records,identity


class RunBudget:
    """One invocation budget shared by every row in a Sheet sync."""
    def __init__(self, settings):
        self.limits={'enrich':settings.enrich_run_limit,'draft':settings.draft_run_limit}
        self.used={'enrich':0,'draft':0,'search':0}
        self.failed={'enrich':0,'draft':0,'search':0}

    def check(self,kind):
        if kind in self.limits and self.used[kind]>=self.limits[kind]:
            raise BudgetExceeded(f'{kind} run limit exhausted')

    def count(self,kind):
        if kind in self.used: self.used[kind]+=1


def _paid(store,kind,key,call,budget=None):
    cached = store.cached(kind,key)
    if cached is not None: return cached
    if budget: budget.check(kind)
    try: attempt = store.reserve(kind,key)
    except CachedResult as result: return result.payload
    if budget: budget.count(kind)
    try: payload = call()
    except (ProviderError,DraftError) as error:
        if budget: budget.failed[kind]+=1
        store.finish(attempt,'uncertain' if error.uncertain else 'error',{'error':str(error)})
        raise
    except Exception:
        if budget: budget.failed[kind]+=1
        store.finish(attempt,'uncertain',{'error':'Unexpected operation failure'})
        raise AttemptUncertain('Unexpected provider failure; review pending operation') from None
    store.finish(attempt,'done',payload)
    return payload


def run(request, *, settings, store, fetch, apollo, drafter=None, budget=None):
    validate_request(request)
    if not settings.allocation_confirmed: raise AccountingUnavailable('Confirm shared allocation in settings before live mode')
    if request.max_contacts > settings.max_contacts: raise ValueError('Requested contact count exceeds settings')
    identifier = uuid.uuid4().hex
    budget=budget or RunBudget(settings)
    context,people,drafts,flags = None,[],{},[]
    metadata={'created_at':datetime.now(timezone.utc).isoformat()}
    direct=bool(request.linkedin_url or request.person_name)
    start_used=dict(budget.used)
    start_failed=dict(budget.failed)
    shortlist=[]
    job_key = result_key(request, settings, drafter.prompt if drafter else '')
    reused_records = {}
    contact_deadlines = []
    state = {'request':asdict(request)}
    def save(status):
        metadata['counts']={'attempted':budget.used['enrich']-start_used['enrich'],
                            'found':sum(bool(p.email) for p in people),
                            'not_found':sum(not p.email for p in people)+metadata.get('no_match_inputs',0),
                            'failed':sum(budget.failed[k]-start_failed[k] for k in budget.failed),
                            'skipped':metadata.get('deduplicated_profiles',0)+metadata.get('unavailable_email_profiles',0)+max(0,len(shortlist)-len(people)),
                            'provider_attempts':{k:budget.used[k]-start_used[k] for k in budget.used},
                            'remaining':{k:store.remaining(k) for k in ('search','enrich','draft')}}
        result = Outcome(identifier,status,context,tuple(people),dict(drafts),tuple(flags),dict(metadata))
        store.save_run(identifier,{**state,'outcome':asdict(result)})
        if status == 'done' and job_key and metadata.get('reuse_type') != 'job_result':
            store.save_cached('job_result',job_key,asdict(result),
                              expires_at=min(contact_deadlines) if contact_deadlines else None)
        return result
    save('processing')
    try:
        previous = store.cache_record('job_result',job_key) if job_key else None
        if job_key and previous is None:
            restore_history(request,settings,drafter.prompt if drafter else '',store,job_key)
            previous = store.cache_record('job_result',job_key)
        if previous:
            saved = outcome_from_dict(previous['payload'])
            context = saved.context
            if previous['expires_at'] <= store.now().isoformat():
                raise NeedsContext('Saved job result expired; review and explicitly refresh before new paid calls')
            people, drafts, flags = list(saved.people), dict(saved.drafts), list(saved.review_flags)
            metadata.update({key:value for key,value in saved.metadata.items() if key not in ('created_at','counts')})
            metadata.update(reuse_type='job_result',reused_from_run_id=saved.run_id)
            return save('done')
        direct_records={}
        if direct:
            if request.draft_email:
                # Check source freshness before spending on a lookup, even though
                # recipient context will only be available after enrichment.
                preflight=Context('','',request.target_role or settings.queue_target_role,None,request.job_description or '',(),())
                load_candidate(select_profile(preflight,request.profile,automatic=request.simple_input),preflight,root=settings.project_root,refresh=True)
            context,direct_records,identity=_direct_lookup(request,settings,store,apollo,budget)
            metadata.update(input_mode='person',identity_match=identity)
            if not direct_records:
                metadata['no_match_inputs']=1
                flags.append('no_match')
            elif not identity: flags.append('person_identity_unverified')
        else: context = resolve_context(request,fetch=fetch)
        candidate = None
        if request.draft_email:
            if drafter is None: raise DraftError('Drafting requested without configured client')
            candidate = load_candidate(select_profile(context,request.profile,automatic=request.simple_input),context,root=settings.project_root,refresh=True)
            metadata.update(selected_profile=candidate.profile,source_hashes=candidate.source_hashes,profile_hash=candidate.profile_hash,
                            prompt_hash=fingerprint(drafter.prompt),model=MODEL,effort=EFFORT,max_tokens=settings.max_tokens)
        save('context_ready')
        if not direct:
            saved_contacts = store.saved_contacts(context.company_domain)
            reusable = [replace(person_from_dict(entry['person']),team_match='unknown') for entry in saved_contacts]
            reusable = [p for p in reusable if p.email and p.employer_match=='confirmed' and p.company_domain==context.company_domain]
            reusable = rank_people(reusable,context,request.contact_roles,min(request.max_contacts,settings.max_contacts))
            if len(reusable) >= min(request.max_contacts,settings.max_contacts):
                reused_records = {p.apollo_id:asdict(p) for p in reusable}
                sources = [entry for entry in saved_contacts if entry['person']['apollo_id'] in reused_records]
                contact_deadlines.extend(entry['expires_at'] for entry in sources)
                metadata.update(reuse_type='company_contacts',
                                reused_from_run_id=sources[0]['source_run_id'],
                                reused_contact_sources={entry['person']['apollo_id']:entry['source_run_id'] for entry in sources})
            elif not reusable and store.saved_contacts(context.company_domain,include_expired=True):
                raise NeedsContext('Saved company contacts need refresh or a matching persona; no automatic Apollo refresh')
        records=list(direct_records.values())
        records.extend(reused_records.values())
        for page in (() if direct or reused_records else range(1,settings.search_pages_per_job+1)):
            search_key = fingerprint({'domain':context.company_domain,'roles':sorted(request.contact_roles),
                                      'page':page,'per_page':settings.search_page_size})
            page_records = _paid(store,'search',search_key,
                            lambda page=page: [asdict(p) for p in apollo.search(context,request.contact_roles,page,settings.search_page_size)],budget)
            records.extend(page_records)
            if len(page_records)<settings.search_page_size: break
        unique_records=_dedupe_people(records)
        metadata['deduplicated_profiles']=len(records)-len(unique_records)
        records=unique_records
        shortlist = [person_from_dict(p) for p in records] if direct else rank_people([person_from_dict(p) for p in records],context,request.contact_roles,
                                min(request.max_contacts,settings.max_contacts))
        attempted_enrich,attempted_draft = 0,0
        drafted_addresses=set()
        email_owners={}
        for selected in shortlist:
            if selected.email_available is False and not direct:
                people.append(selected)
                flags.extend((f'{selected.apollo_id}:no_email',f'{selected.apollo_id}:provider_reports_no_email'))
                metadata['unavailable_email_profiles']=metadata.get('unavailable_email_profiles',0)+1
                save('enriched')
                continue
            key = fingerprint({'apollo_id':selected.apollo_id})
            cached = direct_records if direct else reused_records if reused_records else store.cached('enrich',key)
            if cached is None:
                if attempted_enrich >= settings.enrich_run_limit: raise BudgetExceeded('Enrichment run limit exhausted')
                attempted_enrich += 1
            enriched = direct_records if direct else reused_records if reused_records else _paid(store,'enrich',key,lambda p=selected:{k:asdict(v) for k,v in apollo.enrich([p.apollo_id]).items()},budget)
            raw = enriched.get(selected.apollo_id)
            # Missing match cannot inherit apparently confirmed employment from search.
            person = employer_check(person_from_dict(raw),context.company_domain) if raw else replace(selected,email=None,employer_match='unknown')
            person=replace(person,linkedin_url=_profile_url(person.linkedin_url))
            if not direct and person.linkedin_url:
                store.alias_cache('enrich',key,_lookup_key({'linkedin_url':person.linkedin_url}))
            people.append(person)
            if not direct:
                store.remember_contact(asdict(person),identifier,key)
                entry = store.cache_record('enrich',key)
                if entry: contact_deadlines.append(entry['expires_at'])
            metadata.setdefault('selection_reasons',{})[person.apollo_id] = (
                'Previously enriched company contact; requested title matches. Specific hiring/team relationship unconfirmed.'
                if reused_records else 'Company/title match selected by local rules. Specific hiring/team relationship unconfirmed.')
            if person.email:
                email_key=person.email.strip().casefold()
                owners=email_owners.setdefault(email_key,set())
                duplicate=store.observe_email(person.email,person.apollo_id)
                owners.add(person.apollo_id)
                if duplicate or len(owners)>1:
                    for owner in sorted(owners):
                        flag=f'{owner}:duplicate_email'
                        if flag not in flags: flags.append(flag)
            if not person.email: flags.append(f'{person.apollo_id}:no_email')
            if person.employer_match != 'confirmed': flags.append(f'{person.apollo_id}:employer_{person.employer_match}')
            if person.team_match != 'confirmed': flags.append(f'{person.apollo_id}:hiring_relationship_unconfirmed')
            save('enriched')
            persona_match=direct or title_matches(person.title,request.contact_roles)
            if not persona_match: flags.append(f'{person.apollo_id}:persona_mismatch')
            if not (request.draft_email and person.email and person.employer_match=='confirmed' and persona_match): continue
            if direct and not metadata['identity_match']: continue
            if person.email.lower() in drafted_addresses:
                flags.append(f'{person.apollo_id}:duplicate_email'); continue
            drafted_addresses.add(person.email.lower())
            prompt_hash = fingerprint(drafter.prompt)
            draft_key = fingerprint({'person':asdict(person),'context':asdict(context),'candidate':asdict(candidate),
                                     'request':asdict(request),'prompt':prompt_hash,'model':MODEL,'effort':EFFORT,
                                     'max_tokens':settings.max_tokens})
            if store.cached('draft',draft_key) is None:
                if attempted_draft >= settings.draft_run_limit: raise BudgetExceeded('Draft run limit exhausted')
                attempted_draft += 1
            draft_data = _paid(store,'draft',draft_key,lambda:asdict(drafter.draft(context,person,candidate,request)),budget)
            drafts[person.apollo_id] = Draft(**draft_data)
            flags.extend(f'{person.apollo_id}:{flag}' for flag in drafts[person.apollo_id].review_flags)
            state['profile'] = asdict(candidate)
            state['prompt_hash'] = prompt_hash
            save('drafted')
        return save('done')
    except BudgetExceeded as error:
        flags.append(str(error)); return save('budget_wait')
    except (NeedsContext,ProfileNeedsReview) as error:
        flags.append(str(error)); return save('needs_context')
    except (ProviderError,DraftError,AttemptUncertain) as error:
        flags.append(str(error)); return save('error')


def preview(request, *, settings):
    validate_request(request)
    missing = []
    if request.job_url and not (request.company_url and request.target_role):
        missing.append('Job URL needs fetch to resolve employer/title; provide company/role overrides for offline validation')
    if request.draft_email:
        try:
            context = Context('','',request.target_role or '',request.job_url,request.job_description or '',(),())
            # Freshness covers all originals even while the job role is unresolved.
            selected=select_profile(context,request.profile,automatic=request.simple_input) if request.target_role else (request.profile if request.profile!='auto' else 'fullstack')
            load_candidate(selected,context,root=settings.project_root,refresh=False)
        except (ProfileNeedsReview,NeedsContext) as error: missing.append(str(error))
    return {'mode':'dry_run','network_calls':0,'writes':0,
            'remaining':Store.preview(settings.state_path,settings),
            'planned_max_contacts':min(request.max_contacts,settings.max_contacts),
            'draft_email':request.draft_email,'allocation_confirmed':settings.allocation_confirmed,
            'missing_context':missing,
            'warnings':[] if settings.allocation_confirmed else ['Live processing is disabled until shared allocation is confirmed'],
            'stages':(['enrich'] if request.linkedin_url or request.person_name else ['resolve_context','search','enrich'])+(['draft'] if request.draft_email else [])}
