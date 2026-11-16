"""Public fetches retain destination pinning when the runtime requires a proxy."""
import io
import json
import socket

import pytest

from outreach import context


@pytest.fixture
def proxy_transport(monkeypatch):
    events = []
    monkeypatch.setattr(context, 'getproxies', lambda: {'https': 'http://127.0.0.1:8123'}, raising=False)
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *a, **kw: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))])

    class Tunnel:
        def __init__(self, host, port, **kwargs):
            events.append(('proxy', host, port))
            self.sock = object()

        def set_tunnel(self, host, port): events.append(('tunnel', host, port))
        def connect(self): events.append(('connect',))
        def close(self): events.append(('close_tunnel',))

    class Page:
        status = 200
        def read(self, limit): return b'public job page'

    class Origin:
        def __init__(self, host, port, **kwargs):
            self.host, self.port = host, port
            events.append(('tls_origin', host, port))

        def request(self, *args, **kwargs):
            # HTTPSConnection wraps this socket with TLS/SNI for self.host.
            self._create_connection((self.host, self.port), 15)

        def getresponse(self): return Page()
        def close(self): events.append(('close_origin',))

    monkeypatch.setattr(context.http.client, 'HTTPConnection', Tunnel)
    monkeypatch.setattr(context.http.client, 'HTTPSConnection', Origin)
    return events


def test_proxy_connects_to_checked_ip_and_keeps_original_tls_hostname(proxy_transport):
    assert context.fetch_public_text('https://employer.example/jobs/1') == 'public job page'
    assert ('proxy', '127.0.0.1', 8123) in proxy_transport
    assert ('tunnel', '8.8.8.8', 443) in proxy_transport
    assert ('tls_origin', 'employer.example', 443) in proxy_transport


def dns_response(monkeypatch, addresses):
    def get(url, **kwargs):
        assert url == 'https://dns.google/resolve'
        assert kwargs['params'] == {'name': 'employer.example', 'type': 'A'}
        assert kwargs['allow_redirects'] is False
        body = json.dumps({'Status': 0, 'Answer': [
            {'type': 1, 'data': address} for address in addresses]}).encode()
        class Response:
            status_code = 200
            class Body(io.BytesIO):
                def read(self, size, **kwargs): return super().read(size)
            raw = Body(body)
            def close(self): pass
        return Response()
    import requests
    monkeypatch.setattr(requests, 'get', get)
    def unavailable(*args, **kwargs): raise socket.gaierror('runtime has no local DNS')
    monkeypatch.setattr(socket, 'getaddrinfo', unavailable)


def test_proxy_resolves_over_https_when_system_dns_is_unavailable(monkeypatch, proxy_transport):
    dns_response(monkeypatch, ['8.8.4.4'])
    assert context.fetch_public_text('https://employer.example/jobs/1') == 'public job page'
    assert ('tunnel', '8.8.4.4', 443) in proxy_transport


@pytest.mark.parametrize('addresses', [['127.0.0.1'], ['8.8.8.8', '10.0.0.1']])
def test_remote_dns_private_answers_never_connect(monkeypatch, proxy_transport, addresses):
    dns_response(monkeypatch, addresses)
    with pytest.raises(context.NeedsContext):
        context.fetch_public_text('https://employer.example/jobs/1')
    assert not any(event[0] in ('proxy', 'connect') for event in proxy_transport)


def test_proxy_failure_never_falls_back_to_direct_connection(monkeypatch, proxy_transport):
    def unavailable(self): raise OSError('proxy unavailable')
    monkeypatch.setattr(context.http.client.HTTPConnection, 'connect', unavailable)
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **kw: pytest.fail('direct fallback forbidden'))
    with pytest.raises(context.NeedsContext):
        context.fetch_public_text('https://employer.example/jobs/1')
    assert ('close_tunnel',) in proxy_transport


def test_missing_local_dns_without_proxy_does_not_contact_resolver(monkeypatch):
    import requests
    monkeypatch.setattr(context, 'getproxies', lambda: {}, raising=False)
    def unavailable(*args, **kwargs): raise socket.gaierror('no DNS')
    monkeypatch.setattr(socket, 'getaddrinfo', unavailable)
    monkeypatch.setattr(requests, 'get', lambda *a, **kw: pytest.fail('no implicit remote DNS'))
    with pytest.raises(context.NeedsContext):
        context.fetch_public_text('https://employer.example/jobs/1')
