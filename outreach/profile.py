"""Read reviewed facts from one profile, keeping original resumes authoritative."""
from pathlib import Path
import hashlib
import os
import re
import tempfile
import yaml

from .models import Candidate


class ProfileNeedsReview(RuntimeError): pass


def active_tex_text(text):
    text = re.sub(r'(?<!\\)%[^\n]*', '', text)
    if r'\begin{document}' in text:
        text = text.split(r'\begin{document}',1)[1].split(r'\end{document}',1)[0]
    text = text.replace(r'\%', '%').replace(r'\&','&').replace(r'\_','_')
    text = re.sub(r'\\href\{[^{}]*\}', '', text)
    text = re.sub(r'\\[A-Za-z]+\*?(?:\[[^\]]*\])?', ' ', text)
    return re.sub(r'\s+', ' ', text.replace('{',' ').replace('}',' ')).strip()


def select_profile(context, override, *, automatic=False):
    if override != 'auto': return override
    title = context.job_title.lower()
    if any(term in title for term in ('accessibility','wcag')): return 'accessibility'
    swe = bool(re.search(r'\b(swe|software|full.?stack|front.?end|back.?end)\b',title))
    ai = bool(re.search(r'\b(ai|fde|machine learning|forward deployed)\b',title))
    if swe and ai and not automatic: raise ProfileNeedsReview('Overlapping AI/SWE role: select --profile explicitly')
    if ai and automatic: return 'amazon'
    if swe: return 'fullstack'
    if ai or 'application develop' in title: return 'amazon'
    if automatic: return 'fullstack'
    raise ProfileNeedsReview('Select fullstack, amazon or accessibility for this role')


def _section(text, heading):
    try: section = text.split('## '+heading+'\n',1)[1].split('\n## ',1)[0]
    except IndexError: raise ProfileNeedsReview('Reviewed profile section missing') from None
    return re.findall(r'^- (.+(?:\n(?!\n|[-#])[^\n]+)*)', section, re.M)


def _facts(text, heading):
    return [' '.join(fact.split()) for fact in _section(text,heading)]


def _atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temp = tempfile.mkstemp(dir=path.parent, prefix='.profile-')
    try:
        with os.fdopen(descriptor,'w') as stream: stream.write(text)
        os.replace(temp,path)
    finally:
        if os.path.exists(temp): os.unlink(temp)


def load_candidate(profile, context, *, root, refresh=False):
    root = Path(root)
    try:
        text = (root/'profile.md').read_text()
        config = yaml.safe_load((root/'config/outreach_profile_sources.yaml').read_text())
    except (OSError, yaml.YAMLError): raise ProfileNeedsReview('Profile or source manifest unavailable') from None
    if not isinstance(config,dict) or not isinstance(config.get('sources'),dict) or set(config['sources'])!={'fullstack','amazon','accessibility'}:
        raise ProfileNeedsReview('Malformed profile source manifest: expected three approved sources')
    for source in config['sources'].values():
        if not isinstance(source,dict) or not isinstance(source.get('path'),str) or not source['path'] or not isinstance(source.get('reviewed_active_sha256'),str) or not re.fullmatch('[a-f0-9]{64}',source['reviewed_active_sha256']):
            raise ProfileNeedsReview('Malformed profile source path/hash; review manifest')
    if profile not in ('fullstack','amazon','accessibility'): raise ProfileNeedsReview('Unknown profile')
    hashes, changed, excerpts = {}, [], []
    # Shared facts were reviewed across these originals; conservatively check all three.
    for name, source in config['sources'].items():
        try: original = (root/source['path']).read_text()
        except OSError: raise ProfileNeedsReview('An approved original resume is missing') from None
        active = active_tex_text(original)
        hashes[name] = hashlib.sha256(original.encode()).hexdigest()
        if hashlib.sha256(active.encode()).hexdigest() != source['reviewed_active_sha256']:
            changed.append(name)
            excerpts.append(f'### {name} — source changed; not approved facts\n\n{active}\n')
    if changed:
        if refresh:
            marker = '\n<!-- generated-source-review -->\n'
            update = marker+'## Source changes requiring review\n\n'+ '\n'.join(excerpts)
            _atomic_text(root/'profile.md',text.split(marker)[0]+update)
        raise ProfileNeedsReview('Resume source changed; review generated excerpts and fact bindings: '+', '.join(changed))
    shared = _facts(text,'Shared candidate facts')
    selected = _facts(text,'Profile: '+profile)
    if profile == 'accessibility':
        selected = [f for f in selected if '**big.accessibility:**' not in f and '**jobfinder.accessibility:**' not in f]
        selected += [f for f in _facts(text,'Profile: amazon') if f.startswith(('**big.','**jobfinder.'))]
    restrictions = tuple(_facts(text,'Claim restrictions for every profile'))
    # Explanatory cross-references must not be mistaken for independent candidate claims.
    selected = [f for f in selected if not f.startswith('**teaching:**') or profile=='fullstack']
    terms = set(re.findall(r'[a-z0-9+#]+',context.job_title.lower()+' '+context.description.lower()))
    relevant = sorted(shared+selected, key=lambda f:-len(terms & set(re.findall(r'[a-z0-9+#]+',f.lower()))))
    facts = relevant[:6]
    # Preserve at least one actual selected-profile implementation when relevant facts tie.
    chosen_big = next((f for f in selected if '**big.' in f and '**big.role:**' not in f),None)
    if chosen_big and chosen_big not in facts: facts[-1] = chosen_big
    if len(facts)<3: raise ProfileNeedsReview('At least three supported facts required')
    return Candidate(profile,tuple(facts),restrictions,hashes,hashlib.sha256(text.encode()).hexdigest())
