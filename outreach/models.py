from dataclasses import dataclass, asdict, field
import hashlib
import json


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class Evidence:
    kind: str
    value: str
    source_url: str
    confidence: str


@dataclass(frozen=True)
class Request:
    job_url: str | None = None
    company_url: str | None = None
    target_role: str | None = None
    job_description: str | None = None
    profile: str = 'auto'
    max_contacts: int = 3
    contact_roles: tuple[str, ...] = ('hiring_manager', 'technical_recruiter', 'engineering_manager')
    application_status: str = 'unknown'
    resume_attached: bool = False
    draft_email: bool = False
    notes: str = ''
    linkedin_url: str | None = None
    person_name: str | None = None
    company_name: str | None = None
    simple_input: bool = False


@dataclass(frozen=True)
class Context:
    company_name: str
    company_domain: str
    job_title: str
    job_url: str | None
    description: str
    team_terms: tuple[str, ...]
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class Person:
    apollo_id: str
    name: str
    title: str
    company_domain: str
    linkedin_url: str | None = None
    email: str | None = None
    email_status: str = 'unknown'
    employer_match: str = 'unknown'
    team_match: str = 'unknown'
    evidence: tuple[Evidence, ...] = ()
    email_available: bool | None = None
    company_name: str = ''
    match_confidence: str = 'unknown'


@dataclass(frozen=True)
class Candidate:
    profile: str
    facts: tuple[str, ...]
    restrictions: tuple[str, ...]
    source_hashes: dict[str, str]
    profile_hash: str


@dataclass(frozen=True)
class Draft:
    subject: str
    body: str
    review_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Outcome:
    run_id: str
    status: str
    context: Context | None
    people: tuple[Person, ...]
    drafts: dict[str, Draft]
    review_flags: tuple[str, ...]
    metadata: dict = field(default_factory=dict)


def person_from_dict(data: dict) -> Person:
    return Person(**{**data, 'evidence': tuple(Evidence(**e) for e in data.get('evidence', []))})


def outcome_from_dict(data: dict) -> Outcome:
    context = data.get('context')
    if context:
        context = Context(**{**context, 'team_terms': tuple(context['team_terms']),
                             'evidence': tuple(Evidence(**e) for e in context['evidence'])})
    return Outcome(data['run_id'], data['status'], context,
                   tuple(person_from_dict(p) for p in data['people']),
                   {k: Draft(**{**v,'review_flags':tuple(v.get('review_flags',()))}) for k, v in data['drafts'].items()},
                   tuple(data['review_flags']),data.get('metadata',{}))
