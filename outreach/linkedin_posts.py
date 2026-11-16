"""Resolve a public post's explicitly identified author; never infer authors from slugs."""
import json
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from shared.linkedin_url import normalize_linkedin_url
from .context import domain, InputError, NeedsContext
from .models import Evidence


def post_url(value):
    host = domain(value)
    parsed = urlsplit(value)
    if host != 'linkedin.com' and not host.endswith('.linkedin.com'):
        raise InputError('Use a LinkedIn post URL')
    if not (parsed.path.startswith('/posts/') or parsed.path.startswith('/feed/update/')):
        raise InputError('Use a personal LinkedIn profile or a LinkedIn post URL')
    return urlunsplit(('https','www.linkedin.com',parsed.path.rstrip('/'),'', ''))


def _profile(value):
    if not isinstance(value,str): return None
    value = urljoin('https://www.linkedin.com',value)
    try:
        host = domain(value)
        if host != 'linkedin.com' and not host.endswith('.linkedin.com'): return None
        result = normalize_linkedin_url(value)
    except (InputError,ValueError): return None
    return result if re.fullmatch(r'https://linkedin\.com/in/[^/\s]+',result) else None


def resolve_post_author(value, *, fetch):
    url = post_url(value)
    try: page = fetch(url)
    except NeedsContext:
        raise NeedsContext('LinkedIn post is not publicly readable; paste the author\'s personal LinkedIn profile URL instead') from None
    soup = BeautifulSoup(page,'html.parser')
    authors = set()
    def author(value):
        if isinstance(value,list):
            for entry in value: author(entry)
        elif isinstance(value,dict):
            for key in ('url','sameAs','@id'):
                if key in value: author(value[key])
        else:
            profile = _profile(value)
            if profile: authors.add(profile)
    def posting(value):
        if isinstance(value,list):
            for entry in value: posting(entry)
        elif isinstance(value,dict):
            types = value.get('@type',[])
            if isinstance(types,str): types=[types]
            if any(kind in types for kind in ('SocialMediaPosting','BlogPosting','Article','DiscussionForumPosting')):
                author(value.get('author'))
            posting(value.get('@graph',[]))
    for script in soup.find_all('script',type='application/ld+json'):
        try: posting(json.loads(script.string or script.get_text()))
        except (ValueError,TypeError): continue
    for tag in soup.select('a[rel~="author"], link[rel~="author"]'):
        author(tag.get('href'))
    for tag in soup.select('meta[property="article:author"]'):
        author(tag.get('content'))
    if len(authors) != 1:
        raise NeedsContext('LinkedIn post has no unique personal author profile; paste the author\'s LinkedIn /in/ URL instead')
    profile = authors.pop()
    return profile, Evidence('post_author',profile,url,'confirmed')
