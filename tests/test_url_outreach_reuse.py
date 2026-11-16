from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from outreach.models import Request, Person, Draft
from outreach.settings import Settings
from outreach.store import Store
from outreach.service import run
from outreach.sheets_queue import QueueProcessor


@pytest.fixture
def workflow(tmp_path, outreach_project):
    settings = Settings(outreach_project, tmp_path/'state', tmp_path/'out',
                        allocation_confirmed=True, max_contacts=1)
    clock = [datetime(2026, 11, 15, 18, tzinfo=timezone.utc)]
    store = Store(settings.state_path, settings, lambda: clock[0])

    class Apollo:
        searches = enrichments = 0
        def search(self, context, roles, page, per_page):
            self.searches += 1
            return [Person('person1', 'Jordan Blake', 'Technical Recruiter', 'example.org',
                           employer_match='confirmed')]

        def enrich(self, identifiers):
            self.enrichments += len(identifiers)
            return {'person1': Person('person1', 'Jordan Blake', 'Technical Recruiter',
                    'example.org', 'https://linkedin.com/in/jordan-blake', 'jordan@example.org',
                    'verified', team_match='confirmed')}

    class Drafter:
        prompt = 'Fictional prompt v1'
        calls = 0
        def draft(self, context, person, candidate, request):
            self.calls += 1
            return Draft(context.job_title, '- Built APIs\n- Built React\n- Used SQL')

    apollo, drafter = Apollo(), Drafter()
    fetches = []
    def fetch(url):
        fetches.append(url)
        title = 'Backend Engineer' if '/2' in url else 'Full Stack Engineer'
        return '<script type="application/ld+json">'+json.dumps({
            '@type':'JobPosting', 'title':title, 'description':'Build Python and React APIs',
            'hiringOrganization':{'name':'Example', 'url':'https://example.org'}})+'</script>'

    def execute(request, **kwargs):
        return run(request, settings=settings, store=kwargs.pop('store', store),
                   fetch=kwargs.pop('fetch', fetch), apollo=apollo, drafter=drafter, **kwargs)

    request = Request(job_url='https://example.org/jobs/1', company_url='https://example.org',
                      max_contacts=1, draft_email=True, simple_input=True)
    return settings, store, clock, apollo, drafter, fetches, execute, request


def test_tracking_duplicate_reuses_entire_result_across_restart_without_fetch(workflow):
    settings, store, clock, apollo, drafter, fetches, execute, request = workflow
    first = execute(request)
    duplicate = replace(request, job_url='https://www.example.org/jobs/1/?utm_source=linkedin#apply',
                        company_url='https://www.example.org/')
    second = execute(duplicate, store=Store(settings.state_path, settings, lambda: clock[0]),
                     fetch=lambda _: pytest.fail('Completed duplicate must not fetch its page'))
    assert second.status == 'done' and second.run_id != first.run_id
    assert second.metadata['reuse_type'] == 'job_result'
    assert second.metadata['reused_from_run_id'] == first.run_id
    assert second.metadata['counts']['provider_attempts'] == {'search':0, 'enrich':0, 'draft':0}
    assert second.people == first.people and second.drafts == first.drafts
    assert (apollo.searches, apollo.enrichments, drafter.calls) == (1, 1, 1)


def test_same_company_new_job_reuses_contact_and_drafts_for_new_role(workflow):
    _, _, _, apollo, drafter, _, execute, request = workflow
    first = execute(request)
    second = execute(replace(request, job_url='https://example.org/jobs/2'))
    assert second.status == 'done'
    assert second.drafts['person1'].subject == 'Backend Engineer'
    assert second.people[0].team_match == 'unknown'
    assert second.metadata['reuse_type'] == 'company_contacts'
    assert second.metadata['reused_from_run_id'] == first.run_id
    assert second.metadata['counts']['provider_attempts'] == {'search':0, 'enrich':0, 'draft':1}
    assert (apollo.searches, apollo.enrichments, drafter.calls) == (1, 1, 2)


@pytest.mark.parametrize('change', [
    {'notes':'Please focus on Python'}, {'application_status':'applied'}, {'resume_attached':True},
])
def test_changed_drafting_inputs_get_one_new_draft_without_apollo(workflow, change):
    _, _, _, apollo, drafter, _, execute, request = workflow
    execute(request)
    result = execute(replace(request, **change))
    assert result.status == 'done'
    assert result.metadata['counts']['provider_attempts'] == {'search':0, 'enrich':0, 'draft':1}
    assert (apollo.searches, apollo.enrichments, drafter.calls) == (1, 1, 2)


def test_contact_reuse_does_not_extend_expiry_or_automatically_refresh(workflow):
    _, _, clock, apollo, drafter, _, execute, request = workflow
    execute(request)
    clock[0] += timedelta(days=6)
    assert execute(replace(request, job_url='https://example.org/jobs/2')).status == 'done'
    clock[0] += timedelta(days=2)
    result = execute(replace(request, job_url='https://example.org/jobs/3'))
    assert result.status == 'needs_context'
    assert any('refresh' in flag.lower() for flag in result.review_flags)
    assert (apollo.searches, apollo.enrichments, drafter.calls) == (1, 1, 2)


def test_expired_exact_result_does_not_trigger_automatic_paid_refresh(workflow):
    _, _, clock, apollo, drafter, _, execute, request = workflow
    execute(request)
    clock[0] += timedelta(days=8)
    result = execute(request)
    assert result.status == 'needs_context'
    assert (apollo.searches, apollo.enrichments, drafter.calls) == (1, 1, 1)


def test_duplicate_appended_sheet_rows_both_receive_results(workflow):
    settings, store, _, apollo, drafter, _, execute, _ = workflow
    class Sheet:
        def __init__(self): self.results = []; self.statuses = []
        def read_queue(self): return [
            {'input':'https://example.org/jobs/1', 'company':'https://example.org'},
            {'input':'https://example.org/jobs/1?utm_source=email', 'company':'https://www.example.org/'}]
        def write_status(self, row_id, hashed, values): self.statuses.append(values)
        def write_results(self, rows):
            seen = {r['result_id'] for r in self.results}
            self.results.extend(r for r in rows if r['result_id'] not in seen)
    sheet = Sheet()
    queue = QueueProcessor(sheet, store, execute, settings, 'fictional-sheet')
    queue.sync()
    assert len(sheet.results) == 2
    assert len({r['source_row_id'] for r in sheet.results}) == 2
    assert sheet.statuses[-1]['status'] == 'reused'
    queue.sync()
    assert len(sheet.results) == 2
    assert (apollo.searches, apollo.enrichments, drafter.calls) == (1, 1, 1)


def test_preexisting_completed_run_is_reused_without_new_network(workflow):
    settings, store, _, apollo, drafter, _, execute, request = workflow
    first = execute(request)
    # Simulate an older ledger: provider caches/runs exist, new reuse indexes do not.
    with store._db() as db:
        db.execute("DELETE FROM cache WHERE kind='job_result'")
        db.execute('DELETE FROM company_contacts')
    second = execute(request, fetch=lambda _:pytest.fail('Old completed run should be restored locally'))
    assert second.metadata['reused_from_run_id'] == first.run_id
    third = execute(replace(request,job_url='https://example.org/jobs/2'))
    assert third.metadata['reuse_type'] == 'company_contacts'
    assert (apollo.searches, apollo.enrichments, drafter.calls) == (1, 1, 2)


def test_new_prompt_invalidates_old_draft_but_not_contact(workflow):
    _, _, _, apollo, drafter, _, execute, request = workflow
    execute(request)
    drafter.prompt = 'Fictional prompt v2'
    result = execute(request)
    assert result.status == 'done'
    assert (apollo.searches, apollo.enrichments, drafter.calls) == (1, 1, 2)


def test_export_contains_contact_selection_and_reuse_provenance(workflow):
    from outreach.export import result_rows
    _, _, _, _, _, _, execute, request = workflow
    first = execute(request)
    result = execute(replace(request, job_url='https://example.org/jobs/2'))
    row = result_rows(result)[0]
    assert row['reuse_type'] == 'company_contacts'
    assert row['reused_from_run_id'] == first.run_id
    assert 'unconfirmed' in row['selection_reason'].lower()


def test_sheet_setup_adds_reuse_headers_without_overwriting_results():
    from outreach.sheets_queue import GoogleQueue, QUEUE_HEADERS, RESULT_HEADERS
    calls = []
    class API:
        def spreadsheets(self): return self
        def get(self, **kwargs): self.action='get'; return self
        def batchUpdate(self, **kwargs): calls.append(kwargs); self.action='write'; return self
        def execute(self, **kwargs):
            return {'sheets':[{'properties':{'sheetId':0,'title':'Queue'}},
                              {'properties':{'sheetId':9,'title':'Results','gridProperties':{'columnCount':27}}}]} if self.action=='get' else {}
    queue = GoogleQueue('fictional',service=API())
    queue._read = lambda tab: [list(QUEUE_HEADERS if tab=='Queue' else RESULT_HEADERS)]
    queue.setup_simple_layout()
    updates = [r['updateCells'] for r in calls[0]['body']['requests'] if 'updateCells' in r]
    results = [r for r in updates if r['range']['sheetId']==9]
    assert len(results)==1
    assert results[0]['range']['startRowIndex']==0 and results[0]['range']['endRowIndex']==1
    assert results[0]['range']['startColumnIndex']==27
    assert [c['userEnteredValue']['stringValue'] for c in results[0]['rows'][0]['values']] == [
        'selection_reason', 'reuse_type', 'reused_from_run_id']
    assert {'appendDimension':{'sheetId':9,'dimension':'COLUMNS','length':3}} in calls[0]['body']['requests']


def test_changed_profile_sources_block_before_any_more_spending(workflow):
    settings, _, _, apollo, drafter, _, execute, request = workflow
    execute(request)
    source = settings.project_root/'fullstack.tex'
    source.write_text(source.read_text().replace('experience','changed factual experience'))
    result = execute(request)
    assert result.status == 'needs_context'
    assert (apollo.searches, apollo.enrichments, drafter.calls) == (1, 1, 1)


def test_distinct_query_job_ids_are_not_collapsed(workflow):
    _, _, _, apollo, drafter, _, execute, request = workflow
    execute(replace(request,job_url='https://example.org/careers?jobId=101&utm_source=mail'))
    second = execute(replace(request,job_url='https://example.org/careers?jobId=202'))
    assert second.metadata['reuse_type'] == 'company_contacts'
    assert (apollo.searches, apollo.enrichments, drafter.calls) == (1, 1, 2)
