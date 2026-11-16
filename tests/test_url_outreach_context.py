import pytest

from outreach.context import resolve_context, InputError, NeedsContext, validate_request
from outreach.models import Request


def test_ats_host_is_not_employer():
    page = '''<script type="application/ld+json">{"@type":"JobPosting","title":"Full Stack Engineer","description":"React services","hiringOrganization":{"name":"Example","sameAs":"https://example.org"}}</script>'''
    context = resolve_context(Request(job_url='https://boards.example.net/job/1'), fetch=lambda _: page)
    assert context.company_domain == 'example.org'
    assert context.job_title == 'Full Stack Engineer'


def test_blocked_page_requires_context():
    with pytest.raises(NeedsContext):
        resolve_context(Request(job_url='https://boards.example.net/job/1'), fetch=lambda _: '<html>Enable javascript</html>')


@pytest.mark.parametrize('url', ['file:///etc/passwd', 'http://127.0.0.1/x', 'http://user:pass@example.org', 'http://[::1]/'])
def test_invalid_or_local_url(url):
    with pytest.raises(InputError):
        validate_request(Request(job_url=url))


def test_company_and_pasted_description():
    request = Request(company_url='https://example.org', target_role='Backend Engineer', job_description='Build Python APIs')
    context = resolve_context(request, fetch=lambda _: '<p>Example builds developer tools.</p>')
    assert context.description == 'Build Python APIs'
    assert context.company_domain == 'example.org'


def test_dns_private_destination_rejected_without_connect(monkeypatch):
    import socket
    from outreach.context import fetch_public_text
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))])
    monkeypatch.setattr(socket,'create_connection',lambda *a,**kw:pytest.fail('private connection forbidden'))
    with pytest.raises(NeedsContext): fetch_public_text('https://example.org')


def test_conflicting_employer_requires_review():
    page='''<script type="application/ld+json">{"@type":"JobPosting","title":"Engineer","hiringOrganization":{"sameAs":"https://other.org"}}</script>'''
    with pytest.raises(NeedsContext):
        resolve_context(Request(job_url='https://example.org/jobs/1',company_url='https://example.org'),fetch=lambda _:page)


@pytest.mark.parametrize('organization',[
    {'sameAs':'https://www.linkedin.com/company/acme'},
    {'url':'https://boards.greenhouse.io/acme'},
    {'sameAs':['https://facebook.com/acme','https://indeed.com/acme']},
])
def test_third_party_employer_links_require_real_domain(organization):
    import json
    page='<script type="application/ld+json">'+json.dumps({'@type':'JobPosting','title':'Engineer','hiringOrganization':organization})+'</script>'
    with pytest.raises(NeedsContext):
        resolve_context(Request(job_url='https://boards.greenhouse.io/acme/jobs/1'),fetch=lambda _:page)
    result=resolve_context(Request(job_url='https://boards.greenhouse.io/acme/jobs/1',company_url='https://acme.com'),fetch=lambda _:page)
    assert result.company_domain=='acme.com'


@pytest.mark.parametrize('organization',[
    {'url':'https://careers.acme.com','sameAs':'https://linkedin.com/company/acme'},
    {'sameAs':['https://linkedin.com/company/acme','https://www.acme.com']},
    {'url':'https://boards.greenhouse.io/acme','sameAs':'https://acme.com'},
])
def test_real_employer_urls_and_lists_normalize(organization):
    import json
    page='<script type="application/ld+json">'+json.dumps({'@type':'JobPosting','title':'Engineer','hiringOrganization':organization})+'</script>'
    result=resolve_context(Request(job_url='https://boards.greenhouse.io/acme/jobs/1',company_url='https://jobs.acme.com'),fetch=lambda _:page)
    assert result.company_domain=='acme.com'


def test_explicit_social_company_url_is_not_an_employer():
    with pytest.raises(NeedsContext):
        resolve_context(Request(company_url='https://linkedin.com/company/acme',target_role='Engineer'),fetch=lambda _: '')


def test_fetch_prefers_public_ipv4(monkeypatch):
    import socket,http.client
    import outreach.context
    from outreach.context import fetch_public_text
    monkeypatch.setattr(outreach.context, 'getproxies', lambda: {})
    connected=[]
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[
        (socket.AF_INET6,socket.SOCK_STREAM,6,'',('2001:4860:4860::8888',443,0,0)),
        (socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))])
    monkeypatch.setattr(socket,'create_connection',lambda address,*a,**kw:connected.append(address))
    class Response:
        status=200
        def read(self,*args): return b'public page'
    class Connection:
        def __init__(self,host,port,**kwargs): self.host,self.port=host,port
        def request(self,*args,**kwargs): self._create_connection((self.host,self.port),1)
        def getresponse(self): return Response()
        def close(self): pass
    monkeypatch.setattr(http.client,'HTTPSConnection',Connection)
    assert fetch_public_text('https://example.org')=='public page'
    assert connected[0][0]=='8.8.8.8'
