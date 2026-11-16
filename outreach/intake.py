"""Small user inputs; operational fields are generated locally."""
import re
from urllib.parse import urlsplit

from shared.linkedin_url import normalize_linkedin_url
from .context import InputError, domain
from .models import fingerprint


def url_value(text):
    text=text.strip()
    if re.match(r'^https?://',text,re.I): return text
    if re.match(r'^(?:[\w-]+\.)+[A-Za-z]{2,}(?:[/?:#]|$)',text): return 'https://'+text
    return None


def canonical_row(row):
    row=dict(row)
    if row.get('input') not in ('',None): row['job_url']=row['input']
    if row.get('company') not in ('',None): row['company_url']=row['company']
    return row


def prepare_row(row,number=2):
    row=canonical_row(row)
    number=row.get('_sheet_row',number)
    if not str(row.get('row_id') or '').strip():
        row['row_id']='auto-'+fingerprint({'input':row.get('job_url',''),'company':row.get('company_url',''),'row':number})[:20]
        row['_generated_id']=True
    row['_automatic']=bool(row.get('_automatic')) or row.get('ready') in ('',None) or bool(row.get('input'))
    if row.get('ready') in ('',None): row['ready']=True
    return row


def decode_input(entry,company='',*,target_role='Software Engineer'):
    entry=str(entry or '').strip(); company=str(company or '').strip()
    if not entry: raise InputError('Paste a URL, or a person name with their company')
    url=url_value(entry)
    if url:
        host=domain(url)
        if host=='linkedin.com' or host.endswith('.linkedin.com'):
            normalized=normalize_linkedin_url(url)
            if not re.fullmatch(r'https://linkedin\.com/in/[^/\s]+',normalized):
                raise InputError('Use a personal LinkedIn /in/ URL')
            data={'linkedin_url':normalized,'job_url':None}
        elif urlsplit(url).path in ('','/') and not urlsplit(url).query:
            data={'company_url':url,'target_role':target_role,'job_url':None}
        else: data={'job_url':url}
    else:
        parts=re.split(r'\s*\|\s*|\s+at\s+',entry,maxsplit=1,flags=re.I)
        name=parts[0].strip()
        company=company or (parts[1].strip() if len(parts)>1 else '')
        if len(name.split())<2 or not company:
            raise InputError('For a person lookup, provide full name and company: Jordan Blake | Northstar')
        data={'person_name':name,'job_url':None}
    if company:
        website=url_value(company)
        data['company_url' if website else 'company_name']=website or company
    return data
