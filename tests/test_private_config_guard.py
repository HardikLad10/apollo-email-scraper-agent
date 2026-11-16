from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def setup_repo(tmp_path):
    subprocess.run(['git','init','-q',str(tmp_path)],check=True)
    (tmp_path/'.env').write_text('SHEET_ID=private-workbook-id-for-this-test\n')
    return tmp_path/'README.md'


def check(tmp_path):
    return subprocess.run([sys.executable,str(ROOT/'scripts/check_private_config.py')],cwd=tmp_path,
                          text=True,capture_output=True)


def test_private_workbook_identifier_in_staged_document_is_blocked(tmp_path):
    p=setup_repo(tmp_path);p.write_text('Workbook: private-workbook-id-for-this-test')
    subprocess.run(['git','add','README.md'],cwd=tmp_path,check=True)
    result=check(tmp_path)
    assert result.returncode==1 and 'README.md' in result.stdout
    assert 'private-workbook-id-for-this-test' not in result.stdout+result.stderr


def test_placeholder_url_is_safe_to_commit(tmp_path):
    p=setup_repo(tmp_path);p.write_text('https://docs.google.com/'+'spreadsheets/d/YOUR_SHEET_ID/edit')
    subprocess.run(['git','add','README.md'],cwd=tmp_path,check=True)
    assert check(tmp_path).returncode==0


def test_unstaged_private_text_does_not_replace_staged_content(tmp_path):
    p=setup_repo(tmp_path);p.write_text('Safe staged version')
    subprocess.run(['git','add','README.md'],cwd=tmp_path,check=True)
    p.write_text('Unstaged private-workbook-id-for-this-test')
    assert check(tmp_path).returncode==0
