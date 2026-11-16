from dataclasses import dataclass, fields
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import yaml

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    project_root: Path
    state_path: Path
    output_dir: Path
    timezone: str = 'America/Chicago'
    enrich_daily_limit: int = 5
    enrich_run_limit: int = 5
    max_contacts: int = 3
    search_pages_per_job: int = 1
    search_page_size: int = 25
    search_daily_limit: int = 5
    draft_run_limit: int = 3
    draft_daily_limit: int = 5
    allocation_confirmed: bool = False
    cache_ttl_days: int = 7
    timeout_seconds: float = 15
    draft_timeout_seconds: float = 60
    max_tokens: int = 8192
    draft_web_search_max_uses: int = 2
    default_application_status: str = 'applied'
    queue_contacts_per_job: int = 1
    queue_default_draft_email: bool = True
    queue_target_role: str = 'Software Engineer'


def load_settings(path: Path | None = None) -> Settings:
    try:
        data = yaml.safe_load((path or ROOT/'outreach/settings.yaml').read_text()) or {}
    except (OSError, yaml.YAMLError):
        raise ValueError('Cannot read settings YAML') from None
    allowed = {f.name for f in fields(Settings)} - {'project_root'}
    if not isinstance(data, dict) or set(data) - allowed:
        raise ValueError('Unknown configuration fields')
    for key, value in data.items():
        if key in {'timezone', 'state_path', 'output_dir','queue_target_role'}:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'Invalid {key}')
        elif key in ('allocation_confirmed','queue_default_draft_email'):
            if type(value) is not bool: raise ValueError('allocation_confirmed must be boolean')
        elif key == 'default_application_status':
            if value not in ('unknown','interested','applied'): raise ValueError('default_application_status must be unknown, interested or applied')
        elif key == 'draft_web_search_max_uses':
            if type(value) is not int or not 0 <= value <= 5: raise ValueError('draft_web_search_max_uses must be 0-5')
        elif type(value) not in ((int, float) if key in ('timeout_seconds','draft_timeout_seconds') else (int,)) or value <= 0:
            raise ValueError(f'Invalid positive limit: {key}')
    for field, default in [('state_path', 'local-data/state.sqlite3'), ('output_dir', 'local-data/exports')]:
        value = Path(data.get(field, default)).expanduser()
        data[field] = value if value.is_absolute() else ROOT/value
    result = Settings(project_root=ROOT, **data)
    try: ZoneInfo(result.timezone)
    except (ZoneInfoNotFoundError, ValueError): raise ValueError('Invalid timezone') from None
    if result.search_page_size > 100 or result.max_contacts > result.enrich_run_limit:
        raise ValueError('Selection/page cap exceeds configured run/provider limit')
    if result.queue_contacts_per_job>result.max_contacts:
        raise ValueError('Queue contact default exceeds global selection cap')
    return result
