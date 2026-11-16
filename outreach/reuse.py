"""Canonical work identities; company contacts and job drafts have different scopes."""
from dataclasses import asdict
import hashlib
from urllib.parse import urlsplit, parse_qsl, urlencode

import yaml

from .context import domain, employer_domain
from .models import fingerprint, Request


def canonical_job_url(url):
    parsed = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
             if not key.lower().startswith('utm_') and key.lower() not in
             {'gclid', 'fbclid', 'msclkid', 'mc_cid', 'mc_eid'}]
    suffix = urlencode(sorted(query))
    return 'https://'+domain(url)+(parsed.path.rstrip('/') or '/')+('?' + suffix if suffix else '')


def draft_dependencies(settings, prompt):
    dependencies = {}
    try:
        root = settings.project_root
        manifest = (root/'config/outreach_profile_sources.yaml').read_bytes()
        dependencies['manifest'] = hashlib.sha256(manifest).hexdigest()
        dependencies['profile'] = hashlib.sha256((root/'profile.md').read_bytes()).hexdigest()
        config = yaml.safe_load(manifest)
        dependencies['sources'] = {name:hashlib.sha256((root/source['path']).read_bytes()).hexdigest()
                                  for name, source in config['sources'].items()}
    except (OSError, KeyError, TypeError, AttributeError, yaml.YAMLError):
        # The normal profile preflight will explain the problem without spending.
        return None
    from .drafting import MODEL, EFFORT
    dependencies.update(prompt=prompt, model=MODEL, effort=EFFORT, max_tokens=settings.max_tokens,
                        draft_web_search_max_uses=settings.draft_web_search_max_uses)
    return dependencies


def result_key(request, settings, prompt):
    if not request.job_url or request.linkedin_url or request.person_name: return None
    data = asdict(request)
    data.pop('simple_input')
    data['job_url'] = canonical_job_url(request.job_url)
    data['company_url'] = employer_domain(request.company_url) if request.company_url else None
    data['contact_roles'] = sorted(set(request.contact_roles))
    dependencies = draft_dependencies(settings,prompt) if request.draft_email else {}
    if dependencies is None: return None
    return fingerprint({'request':data, 'draft_dependencies':dependencies})


def restore_history(request, settings, prompt, store, key):
    """Index pre-upgrade completed runs using their original provider cache deadlines."""
    for saved in store.saved_runs():
        outcome = saved.get('outcome') or {}
        if outcome.get('status') != 'done': continue
        context = outcome.get('context') or {}
        if request.company_url and context.get('company_domain') != employer_domain(request.company_url): continue
        deadlines = []
        for person in outcome.get('people', []):
            enrichment_key = fingerprint({'apollo_id':person['apollo_id']})
            store.remember_contact(person,outcome['run_id'],enrichment_key)
            entry = store.cache_record('enrich',enrichment_key)
            if entry: deadlines.append(entry['expires_at'])
        if not deadlines: continue
        old = Request(**saved['request'])
        if result_key(old,settings,prompt) != key: continue
        if request.draft_email:
            metadata = outcome.get('metadata',{})
            from .drafting import MODEL, EFFORT
            if (metadata.get('prompt_hash') != fingerprint(prompt) or metadata.get('model') != MODEL or
                metadata.get('effort') != EFFORT or metadata.get('max_tokens',8192) != settings.max_tokens or
                metadata.get('draft_web_search_max_uses',0) != settings.draft_web_search_max_uses): continue
            root = settings.project_root
            if metadata.get('profile_hash') != hashlib.sha256((root/'profile.md').read_bytes()).hexdigest(): continue
            config = yaml.safe_load((root/'config/outreach_profile_sources.yaml').read_bytes())
            sources = {name:hashlib.sha256((root/source['path']).read_bytes()).hexdigest()
                       for name,source in config['sources'].items()}
            if metadata.get('source_hashes') != sources: continue
        reasons = outcome.setdefault('metadata',{}).setdefault('selection_reasons',{})
        for person in outcome.get('people',[]):
            reasons.setdefault(person['apollo_id'],
                'Previously completed company/title lookup. Specific hiring/team relationship unconfirmed.')
        store.save_cached('job_result',key,outcome,expires_at=min(deadlines))
        return
