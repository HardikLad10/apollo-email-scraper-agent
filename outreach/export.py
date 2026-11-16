from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import io
import json
import os
import re
import tempfile

from .models import fingerprint


def result_rows(outcome):
    rows=[]
    for person in outcome.people or (None,):
        draft=outcome.drafts.get(person.apollo_id) if person else None
        rows.append({
            'result_id':fingerprint({'run':outcome.run_id,'person':person.apollo_id if person else None}),
            'run_id':outcome.run_id,'status':outcome.status,
            'job_url':outcome.context.job_url if outcome.context else '',
            'job_title':outcome.context.job_title if outcome.context else '',
            'company_domain':outcome.context.company_domain if outcome.context else '',
            'apollo_id':person.apollo_id if person else '', 'name':person.name if person else '',
            'title':person.title if person else '', 'linkedin_url':person.linkedin_url if person else '',
            'email':person.email if person else '', 'email_status':person.email_status if person else '',
            'email_source':'apollo' if person and person.email else '',
            'employer_match':person.employer_match if person else '', 'team_match':person.team_match if person else '',
            'evidence':json.dumps([asdict(e) for e in person.evidence],ensure_ascii=False) if person else '[]',
            'review_flags':'; '.join(outcome.review_flags+(tuple(draft.review_flags) if draft else ())),
            'draft_subject':draft.subject if draft else '', 'draft_body':draft.body if draft else '',
            'lookup_outcome':('found' if person.email else 'no_email') if person else outcome.status,
            'selected_profile':outcome.metadata.get('selected_profile',''),
            'source_hashes':json.dumps(outcome.metadata.get('source_hashes',{}),sort_keys=True),
            'profile_hash':outcome.metadata.get('profile_hash',''),
            'prompt_hash':outcome.metadata.get('prompt_hash',''),
            'created_at':outcome.metadata.get('created_at',''),
            'selection_reason':outcome.metadata.get('selection_reasons',{}).get(person.apollo_id,'') if person else '',
            'reuse_type':outcome.metadata.get('reuse_type',''),
            'reused_from_run_id':outcome.metadata.get('reused_from_run_id',''),
        })
    return rows


def _write(path, text):
    descriptor,temporary=tempfile.mkstemp(dir=path.parent,prefix='.export-')
    try:
        with os.fdopen(descriptor,'w',newline='') as stream: stream.write(text)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def export_run(outcome,directory):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',outcome.run_id): raise ValueError('Invalid run ID')
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    rows=result_rows(outcome)
    output=io.StringIO()
    writer=csv.DictWriter(output,fieldnames=list(rows[0])); writer.writeheader()
    for row in rows:
        writer.writerow({key: "'"+value if isinstance(value,str) and (value.startswith(('\t','\r')) or value.lstrip().startswith(('=','+','-','@'))) else value for key,value in row.items()})
    csv_path,json_path=directory/(outcome.run_id+'.csv'),directory/(outcome.run_id+'.json')
    _write(csv_path,output.getvalue())
    _write(json_path,json.dumps({'exported_at':datetime.now(timezone.utc).isoformat(),'outcome':asdict(outcome)},indent=2,ensure_ascii=False))
    return csv_path,json_path
