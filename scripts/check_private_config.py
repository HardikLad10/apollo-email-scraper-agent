"""Reject private configuration in the staged index without printing its values."""
from pathlib import Path
import json
import os
import re
import subprocess

from dotenv import dotenv_values


def main():
    root=Path(subprocess.check_output(['git','rev-parse','--show-toplevel']).decode().strip())
    config={**dotenv_values(root/'.env'),**os.environ}
    private=[value.encode() for name,value in config.items() if isinstance(value,str) and len(value)>=10 and
             (name=='SHEET_ID' or name.endswith(('API_KEY','PASSWORD','PRIVATE_KEY')))]
    files=subprocess.check_output(['git','diff','--cached','--name-only','--diff-filter=ACMR','-z']).decode().split('\0')
    failed=[]
    placeholders={b'YOUR_SHEET_ID',b'SHEET_ID',b'SPREADSHEET_ID',b'EXAMPLE_SHEET_ID'}
    for name in filter(None,files):
        content=subprocess.check_output(['git','show',':'+name])
        ids=re.findall(rb'docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)',content)
        bad=any(value in content for value in private) or any(value not in placeholders for value in ids)
        if name.endswith('.json'):
            try:
                data=json.loads(content)
                bad=bad or (isinstance(data,dict) and data.get('type')=='service_account' and bool(data.get('private_key')))
            except (ValueError,UnicodeError): pass
        if bad: failed.append(name)
    if failed:
        print('Commit blocked: private configuration/workbook reference in '+', '.join(failed))
        print('Use environment variables and placeholder examples; keep private data in ignored local files.')
        return 1
    return 0


if __name__=='__main__': raise SystemExit(main())
