"""Audit hooks run in a child process so they cannot leak into other tests."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


VARIANTS=[
    (['--company-url','https://example.com','--target-role','Software Engineer','--dry-run'],0),
    (['--company-url','https://example.com','--target-role','Software Engineer','--draft-email','--application-status','interested','--dry-run'],0),
    (['--company-url','https://example.com','--target-role','AI Software Engineer','--draft-email','--dry-run'],2),
    (['--job-url','https://boards.greenhouse.io/acme/jobs/123','--dry-run'],2),
    (['--sync-sheet','--dry-run'],0),
    (['https://linkedin.com/in/jordan-blake','--dry-run'],0),
    (['Jordan Blake | Northstar','--dry-run'],0),
    (['--setup-sheet','--dry-run'],0),
]


@pytest.mark.parametrize('arguments,expected',VARIANTS)
def test_dry_run_audit_forbids_all_network_and_filesystem_mutations(outreach_project,arguments,expected):
    script=r'''
import json,os,sys
from pathlib import Path
import outreach.main as cli
import outreach.settings as settings
import outreach.service
root=Path(sys.argv[1]); settings.ROOT=root; cli.ROOT=root
forbidden=[]
def audit(event,args):
    blocked=event in {'socket.connect','socket.getaddrinfo','os.mkdir','os.rename','os.remove','os.chmod','tempfile.mkstemp'}
    if event=='open':
        mode=args[1] or ''
        flags=args[2] or 0
        blocked=any(character in mode for character in 'wax+') or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC))
    if blocked:
        forbidden.append(event)
        raise AssertionError('Forbidden dry-run action: '+event)
sys.addaudithook(audit)
result=cli.main(json.loads(sys.argv[2]))
assert result==int(sys.argv[3]),(result,forbidden)
assert not forbidden,forbidden
assert not (root/'local-data').exists()
'''
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(Path(__file__).resolve().parents[1])}
    result=subprocess.run([sys.executable,'-c',script,str(outreach_project),json.dumps(arguments),str(expected)],
                          cwd=outreach_project,env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
