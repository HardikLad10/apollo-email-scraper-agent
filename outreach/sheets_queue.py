"""Shared Sheet adapter; local SQLite claims, not Sheet status, prevent duplicate work."""
from dataclasses import asdict
from datetime import datetime, timezone
import json

from .context import InputError, validate_request
from .models import Request, fingerprint, outcome_from_dict
from .export import result_rows
from .intake import canonical_row,prepare_row,decode_input

INPUT_FIELDS = ('job_url','company_url','target_role','job_description','profile','contact_roles',
                'max_contacts','draft_email','application_status','resume_attached','notes')
QUEUE_HEADERS = ('row_id','ready')+INPUT_FIELDS+('requeue_token','status','processed_hash','run_id','processed_at','error')
RESULT_HEADERS = ('source_row_id','input_hash','result_id','run_id','status','job_url','job_title','company_domain',
                  'apollo_id','name','title','linkedin_url','email','email_status','email_source','employer_match',
                  'team_match','evidence','review_flags','draft_subject','draft_body','lookup_outcome',
                  'selected_profile','source_hashes','profile_hash','prompt_hash','created_at')
REUSE_RESULT_HEADERS = ('selection_reason','reuse_type','reused_from_run_id')


class QueueError(RuntimeError): pass


def boolean(value, default=False):
    if value is None or value=='': return default
    if type(value) is bool: return value
    if isinstance(value,str) and value.strip().lower() in ('true','false'):
        return value.strip().lower()=='true'
    raise InputError('Boolean cells must be TRUE/FALSE or checkboxes')


def input_hash(row):
    row=canonical_row(row)
    return fingerprint({key:row.get(key,'') for key in INPUT_FIELDS})


def row_request(row, settings):
    automatic=row.get('ready') in ('',None) or bool(row.get('_automatic')) or bool(row.get('input'))
    row=canonical_row(row)
    def text(key): return str(row.get(key) or '').strip()
    data={}
    entry=text('job_url')
    if entry: data=decode_input(entry,text('company_url'),target_role=settings.queue_target_role)
    if not entry and text('company_url') and not text('target_role'):
        data=decode_input(text('company_url'),target_role=settings.queue_target_role)
    count=row.get('max_contacts')
    if count is None or count=='': count=settings.queue_contacts_per_job
    if type(count) is bool: raise InputError('max_contacts must be an integer')
    try:
        converted=int(count)
        if str(count).strip() not in (str(converted),str(float(converted))): raise ValueError()
    except (ValueError,TypeError): raise InputError('max_contacts must be an integer') from None
    if converted>settings.max_contacts: raise InputError('max_contacts exceeds configured cap')
    direct=bool(data.get('linkedin_url') or data.get('person_name') or data.get('linkedin_post_url'))
    request=Request(job_url=data.get('job_url',text('job_url') or None),company_url=data.get('company_url',text('company_url') or None) if not data.get('company_name') else None,
                    target_role=text('target_role') or data.get('target_role'),job_description=text('job_description') or None,
                    profile=text('profile') or 'auto',max_contacts=converted,
                    contact_roles=tuple(part.strip() for part in text('contact_roles').replace(';',',').split(',')) if text('contact_roles') else Request().contact_roles,
                    application_status=text('application_status') or 'unknown',
                    resume_attached=boolean(row.get('resume_attached')),draft_email=boolean(row.get('draft_email'),default=settings.queue_default_draft_email and not direct),
                    notes=text('notes'),linkedin_url=data.get('linkedin_url'),person_name=data.get('person_name'),
                    company_name=data.get('company_name'),simple_input=automatic or direct,
                    linkedin_post_url=data.get('linkedin_post_url'))
    validate_request(request)
    return request


def preview_rows(rows,settings):
    rows=[prepare_row(row,index) for index,row in enumerate(rows,2)]
    identifiers=[str(row.get('row_id') or '').strip() for row in rows]
    if any(not key for key in identifiers) or len(set(identifiers))!=len(identifiers):
        raise QueueError('Every nonempty Queue row requires a unique stable row_id')
    summary={'mode':'sheet_preview','provider_calls':0,'writes':0,'ready_valid':0,'not_ready':0,'invalid':[]}
    for row,row_id in zip(rows,identifiers):
        try:
            if not boolean(row.get('ready')): summary['not_ready']+=1; continue
            row_request(row,settings)
            summary['ready_valid']+=1
        except InputError as error: summary['invalid'].append({'row_id':row_id,'error':str(error)})
    return summary


class QueueProcessor:
    def __init__(self,sheet,store,process,settings,sheet_id):
        self.sheet,self.store,self.process,self.settings,self.sheet_id=sheet,store,process,settings,sheet_id

    def _publish(self,row_id,hashed,payload):
        outcome=outcome_from_dict(payload['outcome'])
        rows=[{**row,'source_row_id':row_id,'input_hash':hashed} for row in result_rows(outcome)]
        self.sheet.write_results(rows)
        status = 'reused' if outcome.status=='done' and outcome.metadata.get('reuse_type')=='job_result' else outcome.status
        self.sheet.write_status(row_id,hashed,{'status':status,'processed_hash':hashed,'run_id':outcome.run_id,
                     'processed_at':payload['processed_at'],'error':'; '.join(outcome.review_flags) if outcome.status!='done' else ''})

    def _status(self,row_id,hashed,values):
        try:
            return self.sheet.write_status(row_id,hashed,values) is not False
        except Exception:
            return False

    def sync(self):
        rows=[prepare_row(row,index) for index,row in enumerate(self.sheet.read_queue(),2)]
        identifiers=[str(row.get('row_id') or '').strip() for row in rows]
        if any(not key for key in identifiers) or len(set(identifiers))!=len(identifiers):
            raise QueueError('Every nonempty Queue row requires a unique stable row_id')
        summary={'processed':0,'unchanged':0,'not_ready':0,'changed':0,'errors':0,'budget_wait':0}
        for row,row_id in zip(rows,identifiers):
            hashed=input_hash(row)
            try:
                if not boolean(row.get('ready')):
                    summary['not_ready']+=1; continue
                request=row_request(row,self.settings)
            except InputError as error:
                self._status(row_id,hashed,{'status':'needs_context','error':str(error)})
                summary['errors']+=1; continue
            token=str(row.get('requeue_token') or '')
            if request.simple_input and not token: token='auto:'+hashed
            input_token=token
            if request.simple_input and not row.get('requeue_token') and request.draft_email:
                from .reuse import draft_dependencies
                try: prompt=(self.settings.project_root/'claude_cold_email_prompt_v2.md').read_text()
                except OSError: prompt=''
                signature=draft_dependencies(self.settings,prompt)
                if signature is not None: token+=':draft:'+fingerprint(signature)
            base='sheet:'+self.sheet_id+':'+row_id
            previous=self.store.get_claim(base)
            if previous:
                if previous[0]=='processing':
                    self._status(row_id,hashed,{'status':'error','error':'Interrupted or active local row claim requires reconciliation'})
                    summary['errors']+=1; continue
                saved=previous[1]
                if previous[0] in ('released','error') or saved.get('outcome',{}).get('status')=='error':
                    if not input_token or input_token==saved.get('input_token',saved.get('token','')):
                        self._status(row_id,hashed,{'status':'changed','error':'Set a new requeue_token after reviewing the failed/released claim'})
                        if saved.get('outcome',{}).get('status')=='error': summary['errors']+=1
                        summary['changed']+=1; continue
                elif saved['input_hash']==hashed and saved['token']==token:
                    self._publish(row_id,hashed,saved)
                    if saved['outcome']['status']=='budget_wait': summary['budget_wait']+=1
                    elif saved['outcome']['status']!='done': summary['errors']+=1
                    summary['unchanged']+=1; continue
                if token==saved['token']:
                    self._status(row_id,hashed,{'status':'changed','error':'Review edit, then change requeue_token to explicitly reprocess'})
                    summary['changed']+=1; continue
            operation=base+':'+fingerprint({'input':hashed,'token':token})
            payload={'input_hash':hashed,'token':token,'input_token':input_token,'base_claim':base,'created_at':datetime.now(timezone.utc).isoformat()}
            # Do not acquire durable claims if even the pre-processing status write fails.
            if not self._status(row_id,hashed,{'status':'processing','error':'',**({'row_id':row_id} if row.get('_generated_id') else {})}):
                summary['errors']+=1; continue
            if not self.store.claim(base,payload):
                summary['errors']+=1; continue
            if not self.store.claim(operation,payload):
                self.store.finish_claim(base,payload,status='error')
                self._status(row_id,hashed,{'status':'error','error':'Existing operation claim requires reconciliation'})
                summary['errors']+=1; continue
            try:
                outcome=self.process(request)
            except Exception as error:
                message=str(error) if isinstance(error,InputError) else 'Processing failed: '+type(error).__name__
                failure={**payload,'error':message}
                # If accounting itself is unavailable, fail closed and leave an explicit
                # recoverable claim; never start additional paid work without a ledger.
                self.store.finish_claim(operation,failure,status='error')
                self.store.finish_claim(base,failure,status='error')
                self._status(row_id,hashed,{'status':'needs_context' if isinstance(error,InputError) else 'error','error':message})
                summary['errors']+=1; continue
            payload={'input_hash':hashed,'token':token,'input_token':input_token,'outcome':asdict(outcome),
                     'processed_at':datetime.now(timezone.utc).isoformat()}
            # Both claims are saved before any Results append. An ambiguous write can
            # be reconciled by result_id on the next sync without provider calls.
            self.store.finish_claim(operation,payload)
            self.store.finish_claim(base,payload)
            self._publish(row_id,hashed,payload)
            summary['processed']+=1
            if outcome.status=='budget_wait': summary['budget_wait']+=1
            elif outcome.status!='done': summary['errors']+=1
        return summary


class GoogleQueue:
    def __init__(self,sheet_id,*,service=None):
        if service is None:
            from shared.sheets import _service
            from google.auth.exceptions import DefaultCredentialsError
            try: service=_service()
            except DefaultCredentialsError:
                raise QueueError('Google Sheets API credentials are missing. Set GOOGLE_APPLICATION_CREDENTIALS to the local service-account JSON and share the Sheet with its client_email, or configure Application Default Credentials. See docs/GOOGLE_SHEETS_SETUP.md.') from None
        self.service,self.sheet_id=service,sheet_id

    def _read(self,tab):
        try:
            result=self.service.spreadsheets().values().get(spreadsheetId=self.sheet_id,range=f"'{tab}'!A:AZ",
                                      valueRenderOption='UNFORMATTED_VALUE').execute(num_retries=0)
        except Exception: raise QueueError('Cannot read selected workbook/tab; check sharing and headers') from None
        return result.get('values',[])

    def setup_simple_layout(self):
        """One-time API layout; keep data and advanced columns, hide operational inputs."""
        raw=self._read('Queue')
        headers,_=self._rows(raw,('row_id','status'))
        renamed=[('input' if name=='job_url' and 'input' not in headers else
                  'company' if name=='company_url' and 'company' not in headers else name) for name in headers]
        try:
            workbook=self.service.spreadsheets().get(spreadsheetId=self.sheet_id,
                         fields='sheets(properties(sheetId,title,gridProperties(columnCount)))').execute(num_retries=0)
            sheets=[sheet['properties'] for sheet in workbook.get('sheets',[]) if sheet.get('properties',{}).get('title')=='Queue']
            if len(sheets)!=1: raise QueueError('Queue tab is missing or ambiguous')
            identifier=sheets[0]['sheetId']
            requests=[{'updateCells':{'range':{'sheetId':identifier,'startRowIndex':0,'endRowIndex':1,
                         'startColumnIndex':0,'endColumnIndex':len(renamed)},
                         'rows':[{'values':[{'userEnteredValue':{'stringValue':name}} for name in renamed]}],
                         'fields':'userEnteredValue'}}]
            visible={'input':400,'company':200,'notes':240,'status':140}
            known=set(QUEUE_HEADERS)|set(visible)
            for index,name in enumerate(renamed):
                if name not in known: continue  # Preserve unrelated custom columns.
                properties={'hiddenByUser':name not in visible}
                if name in visible: properties['pixelSize']=visible[name]
                requests.append({'updateDimensionProperties':{'range':{'sheetId':identifier,'dimension':'COLUMNS',
                    'startIndex':index,'endIndex':index+1},'properties':properties,'fields':','.join(properties)}})
            requests.append({'updateSheetProperties':{'properties':{'sheetId':identifier,'gridProperties':{'frozenRowCount':1}},
                                                     'fields':'gridProperties.frozenRowCount'}})
            results = [sheet['properties'] for sheet in workbook.get('sheets',[])
                       if sheet.get('properties',{}).get('title')=='Results']
            if len(results)==1:
                result_headers,_ = self._rows(self._read('Results'),RESULT_HEADERS)
                missing = [key for key in REUSE_RESULT_HEADERS if key not in result_headers]
                if missing:
                    needed = len(result_headers)+len(missing)
                    current = results[0].get('gridProperties',{}).get('columnCount',needed)
                    if current < needed:
                        requests.append({'appendDimension':{'sheetId':results[0]['sheetId'],
                                         'dimension':'COLUMNS','length':needed-current}})
                    requests.append({'updateCells':{'range':{'sheetId':results[0]['sheetId'],
                        'startRowIndex':0,'endRowIndex':1,'startColumnIndex':len(result_headers),
                        'endColumnIndex':len(result_headers)+len(missing)},
                        'rows':[{'values':[{'userEnteredValue':{'stringValue':key}} for key in missing]}],
                        'fields':'userEnteredValue'}})
            self.service.spreadsheets().batchUpdate(spreadsheetId=self.sheet_id,body={'requests':requests}).execute(num_retries=0)
        except QueueError: raise
        except Exception: raise QueueError('Sheet layout setup failed; no processing was started') from None
        return {'visible_columns':list(visible),'data_rows_preserved':True,'provider_calls':0}

    @staticmethod
    def _rows(values,required):
        if not values: raise QueueError('Missing header row')
        headers=[str(value).strip().lower() for value in values[0]]
        if len(set(headers))!=len(headers) or any(not key for key in headers): raise QueueError('Duplicate/empty headers')
        if set(required)-set(headers): raise QueueError('Required headers missing: '+', '.join(sorted(set(required)-set(headers))))
        return headers,[{key:row[index] if index<len(row) else '' for index,key in enumerate(headers)}
                        for row in values[1:] if any(value not in ('',None) for value in row)]

    def read_queue(self):
        # Validate both tabs before any row can trigger provider work.
        self._rows(self._read('Results'),RESULT_HEADERS)
        raw=self._read('Queue')
        headers,_=self._rows(raw,('row_id','ready','status','processed_hash','run_id','processed_at','error'))
        return [prepare_row({**{key:cells[index] if index<len(cells) else '' for index,key in enumerate(headers)},'_sheet_row':number},number)
                for number,cells in enumerate(raw[1:],2) if any(value not in ('',None) for value in cells)]

    def write_status(self,row_id,expected_hash,values):
        raw=self._read('Queue')
        headers,_=self._rows(raw,('row_id',)+tuple(values))
        matches=[]
        for number,cells in enumerate(raw[1:],2):
            row=prepare_row({key:cells[index] if index<len(cells) else '' for index,key in enumerate(headers)},number)
            if str(row.get('row_id') or '').strip()==row_id: matches.append((number,row))
        if len(matches)!=1: raise QueueError('Queue row moved/deleted/duplicated; no status written')
        number,row=matches[0]
        if input_hash(row)!=expected_hash: return False  # Newer user edit remains untouched.
        def letter(index):
            result=''; index+=1
            while index: index,remainder=divmod(index-1,26); result=chr(65+remainder)+result
            return result
        data=[{'range':f"'Queue'!{letter(headers.index(key))}{number}",'values':[[value]]} for key,value in values.items()]
        try:
            self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.sheet_id,
                        body={'valueInputOption':'RAW','data':data}).execute(num_retries=0)
        except Exception: raise QueueError('Status write failed; local state retained') from None
        return True

    def write_results(self,rows):
        headers,existing=self._rows(self._read('Results'),RESULT_HEADERS)
        seen={str(row['result_id']) for row in existing}
        new=[row for row in rows if row['result_id'] not in seen]
        if not new: return
        try:
            self.service.spreadsheets().values().append(spreadsheetId=self.sheet_id,range="'Results'!A1",
                valueInputOption='RAW',insertDataOption='INSERT_ROWS',
                body={'values':[[row.get(key,'') for key in headers] for row in new]}).execute(num_retries=0)
        except Exception: raise QueueError('Results write outcome uncertain; sync again to reconcile saved result IDs') from None
