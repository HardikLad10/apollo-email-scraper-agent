from dataclasses import replace
from pathlib import Path

import pytest

from outreach.main import parse_request, main
from outreach.context import InputError
from outreach.settings import Settings, load_settings


def test_company_requires_role():
    with pytest.raises(InputError):
        parse_request(['--company-url', 'https://example.org'])


def test_drafts_and_application_claims_are_explicit():
    request = parse_request(['--job-url', 'https://example.org/job/1'])
    assert not request.draft_email
    assert request.application_status == 'unknown'
    assert not request.resume_attached


@pytest.mark.parametrize('value', ['0', '-1', 'true', '1.5'])
def test_invalid_limit_rejected(tmp_path, value):
    config = tmp_path / 'settings.yaml'
    config.write_text('enrich_daily_limit: ' + value)
    with pytest.raises(ValueError):
        load_settings(config)


def test_unknown_settings_rejected(tmp_path):
    config = tmp_path / 'settings.yaml'
    config.write_text('typo_limit: 5')
    with pytest.raises(ValueError):
        load_settings(config)


def test_dry_run_writes_nothing_and_needs_no_keys(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('APOLLO_API_KEY', raising=False)
    assert main(['--company-url', 'https://example.org', '--target-role', 'Full Stack Engineer', '--dry-run']) == 0
    assert not list(tmp_path.iterdir())


def test_job_only_preview_reports_fetch_needed(capsys):
    assert main(['--job-url', 'https://example.org/jobs/1', '--dry-run']) == 2
    assert 'fetch' in capsys.readouterr().out.lower()
