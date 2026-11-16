import pytest

from outreach.context import resolve_context,NeedsContext
from outreach.models import Request


def test_single_html_job_heading_with_company_does_not_need_manual_role():
    page='''<nav>Other openings: Designer</nav><main><h1>Software Engineer I, Data Platforms</h1>
    <div itemprop="description"><h2>Responsibilities</h2><p>Build Python data pipelines and SQL services.</p></div>
    <form>Upload resume and enter private details</form></main><footer>Unrelated links</footer>'''
    result=resolve_context(Request(job_url='https://jobs.example.net/123',company_url='https://example.org'),fetch=lambda _:page)
    assert result.job_title=='Software Engineer I, Data Platforms'
    assert result.description=='Responsibilities Build Python data pipelines and SQL services.'
    assert 'private details' not in result.description
    assert any(e.kind=='job_title' and e.value==result.job_title for e in result.evidence)


def test_html_heading_does_not_implicitly_approve_a_company_domain():
    with pytest.raises(NeedsContext,match='company'):
        resolve_context(Request(job_url='https://job-boards.greenhouse.io/example/jobs/123'),
                        fetch=lambda _: '<h1>Software Engineer</h1><p>Build APIs.</p>')


def test_multiple_different_job_headings_are_not_guessed():
    with pytest.raises(NeedsContext,match='Multiple'):
        resolve_context(Request(job_url='https://example.org/jobs',company_url='https://example.org'),
                        fetch=lambda _: '<h1>Software Engineer</h1><h1>Data Engineer</h1>')


def test_generic_careers_heading_is_not_a_role():
    with pytest.raises(NeedsContext):
        resolve_context(Request(job_url='https://example.org/careers',company_url='https://example.org'),
                        fetch=lambda _: '<h1>Current openings</h1><p>Browse the team.</p>')


def test_placeholder_description_preserves_role_and_marks_limited_context():
    page='''<main><h1>Platform Software Engineer</h1><div class="job__description">
    <p>About Example</p><p>Example builds enterprise tools for business teams.</p><p>n/a</p>
    <p>United States - Remote Pay Range</p><p>$100,000 - $120,000</p></div></main>'''
    result=resolve_context(Request(job_url='https://job-boards.greenhouse.io/example/jobs/123',company_url='https://example.org'),fetch=lambda _:page)
    assert result.job_title=='Platform Software Engineer'
    assert any(e.kind=='job_description' and e.value=='missing_role_details' for e in result.evidence)
    assert 'n/a' not in result.description


def test_role_specific_description_can_have_an_unrelated_na_field():
    page='''<h1>Software Engineer</h1><div class="job__description"><h2>Responsibilities</h2>
    <p>Build reliable Python APIs and SQL services.</p><p>Relocation allowance</p><p>n/a</p></div>'''
    result=resolve_context(Request(job_url='https://example.org/jobs/1',company_url='https://example.org'),fetch=lambda _:page)
    assert 'Python APIs' in result.description
