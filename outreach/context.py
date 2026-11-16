"""Public URL fetching with pinned public DNS destinations and job context parsing."""
import http.client
import ipaddress
import json
import re
import socket
from urllib.parse import urlsplit, urljoin
from urllib.request import getproxies, proxy_bypass

import requests

from bs4 import BeautifulSoup

from .models import Request, Context, Evidence

ROLES = {'hiring_manager', 'technical_recruiter', 'engineering_manager', 'cto', 'ceo'}
ATS_HOSTS = ('greenhouse.io', 'lever.co', 'ashbyhq.com', 'myworkdayjobs.com', 'workday.com', 'smartrecruiters.com', 'workable.com')
THIRD_PARTY_HOSTS = ATS_HOSTS + ('linkedin.com', 'facebook.com', 'fb.com', 'x.com', 'twitter.com',
                               'instagram.com', 'glassdoor.com', 'indeed.com')


class InputError(ValueError): pass
class NeedsContext(InputError): pass


def domain(url: str) -> str:
    parsed = urlsplit(url)
    host = (parsed.hostname or '').lower().removeprefix('www.').rstrip('.')
    if parsed.scheme not in ('http', 'https') or not host or parsed.username or parsed.password:
        raise InputError('Use a public HTTP(S) URL without embedded credentials')
    try:
        if not ipaddress.ip_address(host).is_global:
            raise InputError('Local/private addresses are not supported')
    except ValueError as error:
        if isinstance(error, InputError): raise
        if '.' not in host or host.endswith(('.local', '.localhost', '.internal')):
            raise InputError('Use a public hostname') from None
    try:
        if parsed.port not in (None, 80, 443): raise InputError('Only standard HTTP(S) ports supported')
    except ValueError: raise InputError('Invalid URL port') from None
    return host


def employer_domain(url: str) -> str:
    """Conservative host normalization, not a public-suffix/registrable-domain parser."""
    host = domain(url)
    if any(host == blocked or host.endswith('.'+blocked) for blocked in THIRD_PARTY_HOSTS):
        raise NeedsContext('Provide --company-url for the employer website, not a social or ATS page')
    labels = host.split('.')
    while len(labels) > 2 and labels[0] in ('www', 'jobs', 'careers', 'career', 'apply'):
        labels.pop(0)
    return '.'.join(labels)


def _organization_domain(organization):
    for field in ('url', 'sameAs'):
        values = organization.get(field) or []
        if isinstance(values, str): values = [values]
        if not isinstance(values, list): continue
        candidates = set()
        for value in values:
            if not isinstance(value, str): continue
            try: candidates.add(employer_domain(value))
            except InputError: continue
        if len(candidates) > 1: raise NeedsContext('Ambiguous employer websites; provide --company-url')
        if candidates: return candidates.pop()
    return ''


def validate_request(request: Request) -> None:
    direct=bool(request.linkedin_url or request.person_name)
    if request.linkedin_url:
        from shared.linkedin_url import normalize_linkedin_url
        if not re.fullmatch(r'https://linkedin\.com/in/[^/\s]+',normalize_linkedin_url(request.linkedin_url)):
            raise InputError('Use a personal LinkedIn /in/ URL')
    if request.person_name and not (request.company_name or request.company_url):
        raise InputError('A person name needs a company')
    if not direct and not request.job_url and not (request.company_url and request.target_role):
        raise InputError('Provide job URL, or company URL plus target role')
    for url in (request.job_url, request.company_url):
        if url: domain(url)
    if request.company_url: employer_domain(request.company_url)
    if type(request.max_contacts) is not int or request.max_contacts < 1:
        raise InputError('max_contacts must be positive')
    if not request.contact_roles or set(request.contact_roles) - ROLES:
        raise InputError('Unknown contact roles')
    if request.profile not in ('auto', 'fullstack', 'amazon', 'accessibility'):
        raise InputError('Unknown resume profile')
    if request.application_status not in ('unknown', 'interested', 'applied'):
        raise InputError('Invalid application status')


def _public_addresses(host, port, proxy):
    try:
        addresses = {entry[4][0] for entry in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)}
    except socket.gaierror:
        if not proxy: raise
        # Some managed runtimes expose DNS only through their HTTP proxy. Resolve
        # over authenticated HTTPS, then CONNECT to the checked IP, not the hostname.
        addresses = set()
        for record_type in ('A', 'AAAA'):
            response = None
            try:
                response = requests.get('https://dns.google/resolve',
                    params={'name':host, 'type':record_type}, headers={'Accept':'application/dns-json'},
                    timeout=15, allow_redirects=False, stream=True)
                if response.status_code != 200: raise ValueError()
                body = response.raw.read(65_537, decode_content=True)
                if len(body) > 65_536: raise ValueError()
                data = json.loads(body)
                if not isinstance(data, dict) or data.get('Status') != 0: raise ValueError()
                addresses = {entry['data'] for entry in data.get('Answer', []) if entry.get('type') in (1, 28)}
            except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError, OSError):
                raise NeedsContext('Public DNS resolution through proxy failed') from None
            finally:
                if response is not None: response.close()
            if addresses: break
    try:
        public = bool(addresses) and all(ipaddress.ip_address(ip).is_global for ip in addresses)
    except ValueError: public = False
    if not public: raise NeedsContext('URL resolves to a non-public destination')
    return addresses


def _proxy_socket(proxy, address, port, timeout):
    parsed = urlsplit(proxy)
    if parsed.scheme != 'http' or not parsed.hostname or parsed.username or parsed.password:
        raise NeedsContext('Page fetching requires an HTTP proxy without embedded credentials')
    tunnel = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=timeout)
    try:
        tunnel.set_tunnel(address, port)
        tunnel.connect()
        return tunnel.sock
    except BaseException:
        tunnel.close()
        raise


def fetch_public_text(url: str) -> str:
    for _ in range(4):
        domain(url)
        parsed = urlsplit(url)
        host, port = parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80)
        try:
            proxies = getproxies()
            proxy = None if proxy_bypass(host) else proxies.get(parsed.scheme) or proxies.get('all')
            addresses = _public_addresses(host, port, proxy)
            address = min(addresses,key=lambda ip:(ipaddress.ip_address(ip).version,ip))
            cls = http.client.HTTPSConnection if parsed.scheme == 'https' else http.client.HTTPConnection
            connection = cls(host, port, timeout=15)
            # Pin the checked IP; HTTPS still validates certificate/SNI against original host.
            connection._create_connection = lambda endpoint, timeout, *a, **kw: (
                _proxy_socket(proxy, address, port, timeout) if proxy else socket.create_connection((address, port), timeout))
            try:
                path = parsed.path or '/'
                if parsed.query: path += '?' + parsed.query
                connection.request('GET', path, headers={'User-Agent':'JobOutreachPilot/1.0', 'Accept':'text/html,application/json'})
                response = connection.getresponse()
                if response.status in (301, 302, 303, 307, 308):
                    location = response.getheader('Location')
                    if not location: raise NeedsContext('Invalid redirect')
                    url = urljoin(url, location)
                    continue
                if response.status != 200: raise NeedsContext(f'Job/company page unavailable: HTTP {response.status}')
                body = response.read(2_000_001)
                if len(body) > 2_000_000: raise NeedsContext('Page too large; provide JD text')
                return body.decode('utf-8', errors='replace')
            finally: connection.close()
        except (OSError, http.client.HTTPException):
            raise NeedsContext('Page fetch failed; supply JD, company URL and role') from None
    raise NeedsContext('Too many redirects; provide JD text')


def _jobs(value):
    if isinstance(value, list):
        for entry in value: yield from _jobs(entry)
    elif isinstance(value, dict):
        types = value.get('@type', [])
        if 'JobPosting' in (types if isinstance(types, list) else [types]): yield value
        if '@graph' in value: yield from _jobs(value['@graph'])


def resolve_context(request: Request, *, fetch=fetch_public_text) -> Context:
    validate_request(request)
    page = ''
    if not (request.job_description and request.company_url and request.target_role):
        try: page = fetch(request.job_url or request.company_url)
        except NeedsContext:
            if request.job_url and not request.job_description:
                raise NeedsContext('Job page unavailable; provide JD text, company URL and target role') from None
            if not (request.company_url and request.target_role): raise
    soup = BeautifulSoup(page, 'html.parser')
    jobs = []
    for script in soup.find_all('script', type='application/ld+json'):
        try: jobs.extend(_jobs(json.loads(script.string or script.get_text())))
        except (ValueError, TypeError): continue
    if len(jobs) > 1: raise NeedsContext('Multiple jobs on page; provide a single-job URL or explicit JD/context')
    job = jobs[0] if jobs else {}
    organization = job.get('hiringOrganization') or {}
    if isinstance(organization, list): organization = organization[0] if len(organization) == 1 else {}
    if not isinstance(organization, dict): organization = {}
    employer = _organization_domain(organization)
    expected = employer_domain(request.company_url) if request.company_url else ''
    if expected and employer and employer != expected:
        raise NeedsContext('Explicit company conflicts with job employer; confirm employer URL')
    company_domain = expected or employer
    if not company_domain and request.job_url:
        host = domain(request.job_url)
        if not any(host == ats or host.endswith('.'+ats) for ats in ATS_HOSTS):
            # Generic job hosts cannot safely be presumed to be the employer.
            raise NeedsContext('Confirm company URL; page did not identify hiring organization domain')
    title = request.target_role or job.get('title')
    if not company_domain or not isinstance(title, str) or not title.strip():
        raise NeedsContext('Missing company URL/domain or target role; provide overrides and JD')
    for tag in soup(['script', 'style', 'noscript', 'template', 'svg']): tag.decompose()
    description = request.job_description or BeautifulSoup(str(job.get('description') or ''), 'html.parser').get_text(' ', strip=True) or soup.get_text(' ', strip=True)
    source = request.job_url or request.company_url
    evidence = (Evidence('employer_domain', company_domain, source, 'confirmed' if expected or employer else 'unknown'),)
    terms = tuple(dict.fromkeys(re.findall(r'(?i)\b(?:team|platform|product)\s+([A-Za-z][A-Za-z0-9 -]{1,45})', description)))[:5]
    return Context(str(organization.get('name') or company_domain), company_domain, title.strip(), request.job_url,
                   description[:20000], terms, evidence)
