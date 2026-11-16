"""python -m outreach.main --help"""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path

from .context import InputError, NeedsContext, validate_request, fetch_public_text
from .models import Request, outcome_from_dict
from .settings import ROOT, load_settings
from .store import Store, AccountingUnavailable, RecoveryError
from .sheets_queue import QueueError


def _parser():
    parser=argparse.ArgumentParser(description='Budgeted Apollo discovery and review-only cold-email drafts')
    parser.add_argument('input',nargs='?',help='LinkedIn/job/company URL, or "Full Name | Company"')
    parser.add_argument('--company',help='Company name or website for a person lookup')
    for name in ('job-url','company-url','target-role','job-description-file','settings','output-dir','resume-run','export-run','sheet-id','reconcile','release-claim'):
        parser.add_argument('--'+name)
    parser.add_argument('--profile',choices=['auto','fullstack','amazon','accessibility'],default='auto')
    parser.add_argument('--contact-roles',default='hiring_manager,technical_recruiter,engineering_manager')
    parser.add_argument('--max-contacts',type=int,default=None)
    parser.add_argument('--application-status',choices=['unknown','interested','applied'],default='unknown')
    parser.add_argument('--notes',default='')
    for name in ('resume-attached','dry-run','sync-sheet','preview-sheet','setup-sheet','list-pending','confirm'):
        parser.add_argument('--'+name,action='store_true')
    drafts=parser.add_mutually_exclusive_group()
    drafts.add_argument('--draft-email',dest='draft_email',action='store_true')
    drafts.add_argument('--no-draft-email',dest='draft_email',action='store_false')
    parser.set_defaults(draft_email=None)
    parser.add_argument('--as',dest='reconcile_as',choices=['error'])
    return parser


def _request(args,settings=None):
    description=None
    if args.job_description_file:
        try:
            path=Path(args.job_description_file)
            if path.stat().st_size>200_000: raise InputError('JD file too large')
            description=path.read_text()
        except OSError: raise InputError('Cannot read JD file') from None
    if args.input:
        if args.job_url: raise InputError('Provide a positional input or --job-url, not both')
        from .sheets_queue import row_request
        return row_request({'input':args.input,'company':args.company or args.company_url or '',
                            'target_role':args.target_role or '', 'job_description':description or '',
                            'profile':args.profile,'max_contacts':args.max_contacts,
                            'contact_roles':args.contact_roles,'application_status':args.application_status,
                            'resume_attached':args.resume_attached,'draft_email':args.draft_email,
                            'notes':args.notes},settings or load_settings())
    if args.company: raise InputError('--company needs a URL/person positional input')
    request=Request(args.job_url,args.company_url,args.target_role,description,args.profile,3 if args.max_contacts is None else args.max_contacts,
                    tuple(role.strip() for role in args.contact_roles.split(',')),args.application_status,
                    args.resume_attached,bool(args.draft_email),args.notes)
    validate_request(request)
    return request


def parse_request(argv): return _request(_parser().parse_args(argv))


def sheet_exit_code(summary):
    if summary.get('errors',0): return 4
    if summary.get('budget_wait',0): return 3
    if summary.get('changed',0): return 2
    return 0


def main(argv=None):
    args=_parser().parse_args(argv)
    try:
        settings=load_settings(Path(args.settings) if args.settings else None)
        if args.output_dir: settings=replace(settings,output_dir=Path(args.output_dir).resolve())
        recovery=bool(args.list_pending or args.reconcile or args.release_claim)
        special=sum(bool(value) for value in (args.resume_run,args.export_run,args.sync_sheet,args.preview_sheet,args.setup_sheet,args.list_pending,args.reconcile,args.release_claim))
        if special>1: raise InputError('Choose one of resume, export or Sheet sync')
        if special and any((args.input,args.company,args.job_url,args.company_url,args.target_role,args.job_description_file)):
            raise InputError('Do not mix a stored/Sheet operation with URL input')
        if args.confirm and not (args.reconcile or args.release_claim): raise InputError('--confirm requires a recovery action')
        if args.reconcile_as and not args.reconcile: raise InputError('--as requires --reconcile')
        if recovery:
            if args.dry_run: raise InputError('Recovery actions cannot be combined with --dry-run')
            if not args.list_pending and not args.confirm: raise InputError('Recovery changes require --confirm')
            store=Store.open_existing(settings.state_path,settings,read_only=args.list_pending)
            if args.list_pending: print(json.dumps(store.list_pending(),indent=2))
            elif args.reconcile:
                store.reconcile(args.reconcile,confirmed=True)
                print(json.dumps({'id':args.reconcile,'status':'error','usage_refunded':False}))
            else:
                store.release_claim(args.release_claim,confirmed=True)
                print(json.dumps({'id':args.release_claim,'status':'released','requires_new_requeue_token':True}))
            return 0
        if args.dry_run and (args.resume_run or args.export_run): raise InputError('Use dry-run with URL input or Sheet sync')
        if (args.sync_sheet or args.preview_sheet or args.setup_sheet) and args.dry_run:
            print(json.dumps({'mode':'dry_run','network_calls':0,'writes':0,'remaining':Store.preview(settings.state_path,settings),
                              'note':'Queue contents require an explicit Sheets read; no rows fetched in strict dry-run.'},indent=2))
            return 0
        if args.preview_sheet or args.setup_sheet:
            from dotenv import load_dotenv
            from .sheets_queue import GoogleQueue,preview_rows
            load_dotenv(ROOT/'.env',override=False)
            sheet_id=args.sheet_id or os.environ.get('SHEET_ID')
            if not sheet_id: raise InputError('Provide --sheet-id or SHEET_ID')
            sheet=GoogleQueue(sheet_id)
            if args.setup_sheet:
                print(json.dumps(sheet.setup_simple_layout(),indent=2)); return 0
            summary=preview_rows(sheet.read_queue(),settings)
            print(json.dumps(summary,indent=2))
            return 2 if summary['invalid'] else 0
        if not special:
            request=_request(args,settings)
            if request.max_contacts>settings.max_contacts: raise InputError('max_contacts exceeds configured selection cap')
            if args.dry_run:
                from .service import preview
                result=preview(request,settings=settings)
                print(json.dumps(result,indent=2))
                return 2 if result['missing_context'] else 0
        from .export import export_run
        if args.export_run:
            # No provider keys, allocation gate or credentials required for saved output.
            store=Store.open_existing(settings.state_path,settings,read_only=True)
            outcome=outcome_from_dict(store.load_run(args.export_run)['outcome'])
        else:
            if not settings.allocation_confirmed: raise AccountingUnavailable('Set allocation_confirmed only after agreeing shared-account limits')
            from dotenv import load_dotenv
            load_dotenv(ROOT/'.env',override=False)
            if not os.environ.get('APOLLO_API_KEY'): raise InputError('APOLLO_API_KEY is required')
            from .apollo import ApolloClient
            from .drafting import DraftClient
            from .service import run, RunBudget
            apollo=ApolloClient(os.environ['APOLLO_API_KEY'],timeout=settings.timeout_seconds)
            store=Store(settings.state_path,settings)
            budget=RunBudget(settings)
            def process(request):
                drafter=None
                if request.draft_email:
                    if not os.environ.get('ANTHROPIC_API_KEY'): raise InputError('ANTHROPIC_API_KEY is required for drafting')
                    drafter=DraftClient(os.environ['ANTHROPIC_API_KEY'],(ROOT/'claude_cold_email_prompt_v1.md').read_text(),settings.max_tokens,timeout=settings.draft_timeout_seconds)
                return run(request,settings=settings,store=store,fetch=fetch_public_text,apollo=apollo,drafter=drafter,budget=budget)
            if args.sync_sheet:
                from .sheets_queue import GoogleQueue, QueueProcessor
                sheet_id=args.sheet_id or os.environ.get('SHEET_ID')
                if not sheet_id: raise InputError('Provide --sheet-id or SHEET_ID')
                summary=QueueProcessor(GoogleQueue(sheet_id),store,process,settings,sheet_id).sync()
                print(json.dumps(summary,indent=2)); return sheet_exit_code(summary)
            if args.resume_run:
                saved=store.load_run(args.resume_run)
                request=Request(**saved['request'])
            outcome=process(request)
        paths=export_run(outcome,settings.output_dir)
        print(json.dumps({'run_id':outcome.run_id,'status':outcome.status,'contacts':len(outcome.people),'drafts':len(outcome.drafts),
                          'counts':outcome.metadata.get('counts',{}),
                          'files':[str(path) for path in paths]},indent=2))
        return {'done':0,'needs_context':2,'budget_wait':3}.get(outcome.status,4)
    except (InputError,RecoveryError) as error:
        print(str(error)); return 2
    except AccountingUnavailable as error:
        print(str(error)); return 3
    except QueueError as error:
        print(str(error)); return 4
    except (ValueError,OSError) as error:
        print('Configuration or local file error: '+type(error).__name__); return 2
    except Exception as error:
        # No traceback or provider bodies containing secrets/contact data.
        print('Operation failed: '+type(error).__name__); return 4


if __name__=='__main__': raise SystemExit(main())
