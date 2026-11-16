import re

TITLE_SETS = {
    'technical_recruiter': ('technical recruiter', 'technical sourcer', 'talent acquisition'),
    'hiring_manager': ('engineering manager', 'software engineering manager', 'director of engineering'),
    'engineering_manager': ('engineering manager', 'software engineering manager', 'director of engineering'),
    'cto': ('cto', 'chief technology officer'),
    'ceo': ('ceo', 'chief executive officer', 'founder'),
}


def title_matches(title,roles):
    return any(re.search(r'\b'+re.escape(term)+r'\b',title,re.I)
               for role in roles for term in TITLE_SETS[role])


def rank_people(people, context, roles, limit):
    titles = tuple(title for role in roles for title in TITLE_SETS[role])
    def score(person):
        return (person.employer_match == 'confirmed',
                title_matches(person.title,roles),
                sum(term.lower() in person.title.lower() for term in context.team_terms))
    eligible = [p for p in people if p.employer_match != 'mismatch' and
                title_matches(p.title,roles)]
    return sorted(sorted(eligible, key=lambda p:p.apollo_id), key=score, reverse=True)[:limit]
