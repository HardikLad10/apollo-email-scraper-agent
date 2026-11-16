from pathlib import Path

import pytest

from outreach.sheets_queue import QueueProcessor, QueueError
from outreach.models import Outcome
from outreach.settings import Settings
from outreach.store import Store


class FakeSheet:
    def __init__(self):
        self.rows=[{'row_id':'job1','ready':True,'company_url':'https://example.org','target_role':'Full Stack Engineer'}]
        self.results=[]
        self.statuses=[]
    def read_queue(self): return [dict(row) for row in self.rows]
    def write_status(self,row_id,input_hash,values): self.statuses.append(values)
    def write_results(self,rows):
        existing={r['result_id'] for r in self.results}
        self.results.extend(row for row in rows if row['result_id'] not in existing)


def test_only_ready_rows_and_no_repeat_paid_work(tmp_path):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out',allocation_confirmed=True)
    store=Store(settings.state_path,settings)
    sheet=FakeSheet()
    sheet.rows += [{'row_id':'job2','ready':False}]
    calls=[]
    def process(request):
        calls.append(request)
        return Outcome('run1','done',None,(),{},())
    queue=QueueProcessor(sheet,store,process,settings,sheet_id='fake-sheet')
    queue.sync()
    queue.sync()
    assert len(calls)==1 and len(sheet.results)==1
    sheet.rows[0]['target_role']='Backend Engineer'
    queue.sync()
    assert len(calls)==1 and sheet.statuses[-1]['status']=='changed'
    sheet.rows[0]['requeue_token']='reviewed-edit-1'
    queue.sync()
    assert len(calls)==2


def test_duplicate_row_ids_fail_before_processing(tmp_path):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out')
    sheet=FakeSheet(); sheet.rows += [dict(sheet.rows[0])]
    queue=QueueProcessor(sheet,Store(settings.state_path,settings),lambda _:pytest.fail('must not process'),settings,'fake')
    with pytest.raises(QueueError): queue.sync()


def test_ambiguous_sheet_write_reconciles_without_reprocessing(tmp_path):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out')
    sheet=FakeSheet()
    calls=[]
    original=sheet.write_results
    def fail_after_append(rows):
        original(rows)
        sheet.write_results=original
        raise QueueError('timeout after append')
    sheet.write_results=fail_after_append
    def process(request):
        calls.append(request)
        return Outcome('run1','done',None,(),{},())
    queue=QueueProcessor(sheet,Store(settings.state_path,settings),process,settings,'fake')
    with pytest.raises(QueueError): queue.sync()
    queue.sync()
    assert len(calls)==1 and len(sheet.results)==1


def test_interrupted_row_claim_does_not_run_again(tmp_path):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out')
    store=Store(settings.state_path,settings)
    sheet=FakeSheet()
    store.claim('sheet:fake:job1',{'input_hash':'old-hash','token':''})
    queue=QueueProcessor(sheet,store,lambda _:pytest.fail('interrupted row must be held'),settings,'fake')
    queue.sync()
    assert sheet.statuses[-1]['status']=='error'


def test_status_relocates_sorted_row_and_holds_changed_inputs():
    from outreach.sheets_queue import GoogleQueue, input_hash
    writes=[]
    class API:
        def spreadsheets(self): return self
        def values(self): return self
        def batchUpdate(self,**kwargs): writes.append(kwargs); return self
        def execute(self,**kwargs): return {}
    queue=GoogleQueue('fake',service=API())
    row={'row_id':'job1','ready':True,'company_url':'https://example.org','target_role':'Engineer'}
    headers=list(row)+['status']
    original_hash=input_hash(row)
    queue._read=lambda tab:[headers,['job2',True,'https://other.org','Engineer',''],[row[k] for k in row]+['']]
    queue.write_status('job1',original_hash,{'status':'done'})
    assert writes[0]['body']['data'][0]['range']=="'Queue'!E3"
    row['target_role']='Changed Engineer'
    queue.write_status('job1',original_hash,{'status':'done'})
    assert len(writes)==1


def test_sheet_preview_validates_without_processing_or_writing(tmp_path):
    from outreach.sheets_queue import preview_rows
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out')
    rows=FakeSheet().read_queue()+[{'row_id':'draft','ready':False}]
    summary=preview_rows(rows,settings)
    assert summary['ready_valid']==1 and summary['not_ready']==1
    assert not list(tmp_path.iterdir())


def test_unexpected_process_error_finishes_claims_and_continues(tmp_path):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out')
    store=Store(settings.state_path,settings); sheet=FakeSheet(); calls=[]
    sheet.rows.append({**sheet.rows[0],'row_id':'job2'})
    def process(request):
        calls.append(request)
        if len(calls)==1: raise RuntimeError('private secret@example.org error')
        return Outcome('run2','done',None,(),{},())
    queue=QueueProcessor(sheet,store,process,settings,'fake')
    summary=queue.sync()
    assert len(calls)==2 and summary['errors']==1
    assert not store.list_pending()['claims']
    assert store.get_claim('sheet:fake:job1')[0]=='error'
    assert 'secret@example.org' not in str(sheet.statuses)
    queue.sync()
    assert len(calls)==2  # No automatic retry of the errored row.


def test_status_failure_before_processing_creates_no_claims(tmp_path):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out')
    store=Store(settings.state_path,settings); sheet=FakeSheet()
    def fail(*args): raise QueueError('write failed')
    sheet.write_status=fail
    queue=QueueProcessor(sheet,store,lambda _:pytest.fail('must not process'),settings,'fake')
    summary=queue.sync()
    assert summary['errors']==1 and not store.list_pending()['claims']


def test_cached_row_error_stays_visible_in_summary(tmp_path):
    settings=Settings(tmp_path,tmp_path/'db',tmp_path/'out'); store=Store(settings.state_path,settings)
    queue=QueueProcessor(FakeSheet(),store,lambda _:Outcome('run1','error',None,(),{},('safe error',)),settings,'fake')
    assert queue.sync()['errors']==1
    assert queue.sync()['errors']==1
