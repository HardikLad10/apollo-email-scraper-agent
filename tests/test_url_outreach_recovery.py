import json
import pytest

from outreach.main import main
from outreach.settings import load_settings
from outreach.store import Store, AccountingUnavailable
from outreach.sheets_queue import QueueProcessor
from tests.test_url_outreach_sheets import FakeSheet
from outreach.models import Outcome


def test_reconcile_keeps_usage_and_requires_confirmation(outreach_project):
    settings=load_settings()
    store=Store(settings.state_path,settings)
    identifier=store.reserve('enrich','fake-person')
    store.finish(identifier,'uncertain',{'private':'must-not-print'})
    with pytest.raises(ValueError): store.reconcile(identifier,confirmed=False)
    assert store.remaining('enrich')==4
    store.reconcile(identifier,confirmed=True)
    assert store.remaining('enrich')==4
    assert store.cached('enrich','fake-person') is None
    store.reserve('enrich','fake-person')
    assert store.remaining('enrich')==3
    assert store.audit_entries()[0]['previous_status']=='uncertain'
    with pytest.raises(ValueError): store.reconcile(identifier,confirmed=True)
    with pytest.raises(ValueError): store.reconcile('unknown',confirmed=True)


def test_pending_listing_is_private_and_cli_recovery_needs_no_keys(capsys):
    settings=load_settings(); store=Store(settings.state_path,settings)
    identifier=store.reserve('search','private-operation-key')
    store.claim('claim-fake',{'secret_email':'secret@example.org','token':''})
    assert main(['--list-pending'])==0
    data=json.loads(capsys.readouterr().out)
    assert data['attempts'][0]['id']==identifier
    assert data['claims'][0]['id']=='claim-fake'
    assert 'secret@example.org' not in json.dumps(data) and 'private-operation-key' not in json.dumps(data)
    assert main(['--reconcile',identifier,'--as','error'])==2
    assert main(['--reconcile',identifier,'--as','error','--confirm'])==0
    assert store.remaining('search')==4


def test_released_row_requires_new_requeue_token(tmp_path):
    from outreach.settings import Settings
    settings=Settings(tmp_path,tmp_path/'state',tmp_path/'out')
    store=Store(settings.state_path,settings); sheet=FakeSheet(); calls=[]
    base='sheet:fake:job1'
    store.claim(base,{'input_hash':'old-hash','token':''})
    with pytest.raises(ValueError): store.release_claim(base,confirmed=False)
    store.release_claim(base,confirmed=True)
    def process(request):
        calls.append(request); return Outcome('fake-run','done',None,(),{},())
    queue=QueueProcessor(sheet,store,process,settings,'fake')
    queue.sync(); assert not calls
    sheet.rows[0]['requeue_token']='reviewed-1'
    queue.sync(); assert len(calls)==1


def test_readonly_recovery_does_not_create_missing_database():
    settings=load_settings()
    with pytest.raises(AccountingUnavailable): Store.open_existing(settings.state_path,settings,read_only=True)
    assert not settings.state_path.parent.exists()


def test_stale_worker_cannot_finish_a_reclaimed_row():
    settings=load_settings(); store=Store(settings.state_path,settings)
    old={'input_hash':'old','token':'first'}
    store.claim('fake-row',old)
    store.release_claim('fake-row',confirmed=True)
    assert store.claim('fake-row',{'input_hash':'new','token':'second'})
    with pytest.raises(AccountingUnavailable): store.finish_claim('fake-row',old)
    assert store.get_claim('fake-row')[0]=='processing'
