from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from outreach.settings import Settings
from outreach.store import Store, BudgetExceeded, AttemptUncertain, AccountingUnavailable


def configured(tmp_path, **kwargs):
    return Settings(project_root=tmp_path, state_path=tmp_path/'state.db', output_dir=tmp_path/'exports', allocation_confirmed=True, **kwargs)


def test_pending_attempt_survives_restart(tmp_path):
    settings = configured(tmp_path)
    clock = lambda: datetime(2026, 11, 15, 18, tzinfo=timezone.utc)
    Store(settings.state_path, settings, clock).reserve('enrich', 'person1')
    reopened = Store(settings.state_path, settings, clock)
    assert reopened.remaining('enrich') == 4
    with pytest.raises(AttemptUncertain):
        reopened.reserve('enrich', 'person1')


def test_two_connections_cannot_exceed_limit(tmp_path):
    settings = configured(tmp_path, enrich_daily_limit=1)
    Store(settings.state_path, settings)
    def attempt(key):
        try:
            Store(settings.state_path, settings).reserve('enrich', key)
            return True
        except BudgetExceeded:
            return False
    with ThreadPoolExecutor(2) as pool:
        assert sum(pool.map(attempt, ['a', 'b'])) == 1


def test_cache_expiration_and_day_rollover(tmp_path):
    settings = configured(tmp_path)
    today = datetime(2026, 11, 15, 18, tzinfo=timezone.utc)
    store = Store(settings.state_path, settings, lambda: today)
    attempt = store.reserve('enrich', 'a')
    store.finish(attempt, 'done', {'email': 'fake@example.org'})
    assert store.cached('enrich', 'a')['email'] == 'fake@example.org'
    tomorrow = Store(settings.state_path, settings, lambda: today + timedelta(days=1))
    assert tomorrow.remaining('enrich') == 5
    expired = Store(settings.state_path, settings, lambda: today + timedelta(days=8))
    assert expired.cached('enrich', 'a') is None


def test_corrupt_accounting_fails_closed(tmp_path):
    settings = configured(tmp_path)
    settings.state_path.write_bytes(b'not a sqlite database')
    with pytest.raises(AccountingUnavailable):
        Store(settings.state_path, settings)


def test_dst_repeated_hour_does_not_reset_budget(tmp_path):
    settings=configured(tmp_path,enrich_daily_limit=1)
    first=datetime(2026,11,1,6,30,tzinfo=timezone.utc)
    store=Store(settings.state_path,settings,lambda:first)
    store.reserve('enrich','one')
    repeated=Store(settings.state_path,settings,lambda:first+timedelta(hours=1))
    assert repeated.remaining('enrich')==0
    with pytest.raises(BudgetExceeded): repeated.reserve('enrich','two')


def test_uncertain_attempt_cannot_be_repeated_after_midnight(tmp_path):
    settings=configured(tmp_path)
    today=datetime(2026,11,15,18,tzinfo=timezone.utc)
    Store(settings.state_path,settings,lambda:today).reserve('enrich','one')
    tomorrow=Store(settings.state_path,settings,lambda:today+timedelta(days=1))
    with pytest.raises(AttemptUncertain): tomorrow.reserve('enrich','one')
