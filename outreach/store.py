"""Durable local ledger. A reservation is consumed before any provider call."""
from contextlib import contextmanager, closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import os
import sqlite3
import uuid
import re
import hashlib


class BudgetExceeded(RuntimeError): pass
class AccountingUnavailable(RuntimeError): pass
class AttemptUncertain(RuntimeError): pass
class RecoveryError(ValueError): pass
class CachedResult(RuntimeError):
    def __init__(self, payload): self.payload = payload


class Store:
    def __init__(self, path, settings, now=None, *, read_only=False):
        self.path, self.settings = Path(path), settings
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.read_only = read_only
        if read_only:
            if not self.path.is_file(): raise AccountingUnavailable('Accounting database does not exist')
            with self._db() as db: db.execute('SELECT id FROM attempts LIMIT 1')
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            descriptor = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
            os.close(descriptor)
            os.chmod(self.path, 0o600)
            with self._db() as db:
                db.executescript('''
                CREATE TABLE IF NOT EXISTS attempts (
                  id TEXT PRIMARY KEY, kind TEXT NOT NULL, operation_key TEXT NOT NULL,
                  day TEXT NOT NULL, units INTEGER NOT NULL, status TEXT NOT NULL,
                  payload_json TEXT, created_at TEXT NOT NULL);
                CREATE UNIQUE INDEX IF NOT EXISTS pending_operation ON attempts(kind,operation_key)
                  WHERE status IN ('pending','uncertain');
                CREATE TABLE IF NOT EXISTS cache (kind TEXT, cache_key TEXT, payload_json TEXT,
                  expires_at TEXT, PRIMARY KEY(kind,cache_key));
                CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY,payload_json TEXT,updated_at TEXT);
                CREATE TABLE IF NOT EXISTS claims (id TEXT PRIMARY KEY,payload_json TEXT,status TEXT);
                CREATE TABLE IF NOT EXISTS recovery_audit (id INTEGER PRIMARY KEY, object_type TEXT,
                  object_id TEXT, previous_status TEXT, new_status TEXT, created_at TEXT);
                CREATE TABLE IF NOT EXISTS email_identities (email_hash TEXT, apollo_id TEXT,
                  PRIMARY KEY(email_hash,apollo_id));
                CREATE TABLE IF NOT EXISTS company_contacts (company_domain TEXT, apollo_id TEXT,
                  payload_json TEXT, source_run_id TEXT, expires_at TEXT,
                  PRIMARY KEY(company_domain,apollo_id));
                ''')
        except (OSError, sqlite3.Error):
            raise AccountingUnavailable('Cannot initialize local accounting') from None

    @contextmanager
    def _db(self):
        db = None
        try:
            db = sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro', uri=True, timeout=5) if self.read_only else sqlite3.connect(self.path, timeout=5)
            db.row_factory = sqlite3.Row
            with db: yield db
        except sqlite3.Error:
            raise AccountingUnavailable('Cannot read/write local accounting') from None
        finally:
            if db is not None: db.close()

    @classmethod
    def open_existing(cls, path, settings, *, read_only=False):
        if not Path(path).is_file(): raise AccountingUnavailable('Accounting database does not exist')
        return cls(path,settings,read_only=read_only)

    def _audit(self, db, object_type, identifier, before, after):
        db.execute('INSERT INTO recovery_audit(object_type,object_id,previous_status,new_status,created_at) VALUES(?,?,?,?,?)',
                   (object_type,identifier,before,after,self.now().isoformat()))

    def list_pending(self):
        with self._db() as db:
            attempts=[dict(row) for row in db.execute("SELECT id,kind,day,status,created_at FROM attempts WHERE status IN ('pending','uncertain') ORDER BY created_at,id")]
            claims=[{'id':row['id'],'kind':'claim','status':row['status'],
                     'created_at':json.loads(row['payload_json']).get('created_at','unknown')}
                    for row in db.execute("SELECT id,status,payload_json FROM claims WHERE status='processing' ORDER BY id")]
        return {'attempts':attempts,'claims':claims}

    def reconcile(self, identifier, *, confirmed=False):
        if not confirmed: raise RecoveryError('Reconciliation requires --confirm after reviewing provider usage')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT status FROM attempts WHERE id=?',(identifier,)).fetchone()
            if not row: raise RecoveryError('Unknown attempt ID')
            if row['status'] not in ('pending','uncertain'): raise RecoveryError('Attempt is already terminal')
            self._audit(db,'attempt',identifier,row['status'],'error')
            db.execute("UPDATE attempts SET status='error' WHERE id=?",(identifier,))
        # Units are deliberately unchanged; no cache entry is invented.

    def release_claim(self, identifier, *, confirmed=False):
        if not confirmed: raise RecoveryError('Claim release requires --confirm and a new requeue_token')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT status,payload_json FROM claims WHERE id=?',(identifier,)).fetchone()
            if not row: raise RecoveryError('Unknown claim ID')
            if row['status'] != 'processing': raise RecoveryError('Claim is not processing')
            payload=json.loads(row['payload_json'])
            base=payload.get('base_claim',identifier)
            prefix,separator,suffix=identifier.rpartition(':')
            if 'base_claim' not in payload and separator and re.fullmatch('[a-f0-9]{64}',suffix):
                if db.execute('SELECT 1 FROM claims WHERE id=?',(prefix,)).fetchone(): base=prefix
            for related in db.execute("SELECT id,payload_json FROM claims WHERE status='processing'").fetchall():
                child=related['id'][len(base)+1:] if related['id'].startswith(base+':') else ''
                if related['id']==base or related['id']==identifier or json.loads(related['payload_json']).get('base_claim')==base or re.fullmatch('[a-f0-9]{64}',child):
                    self._audit(db,'claim',related['id'],'processing','released')
                    db.execute("UPDATE claims SET status='released' WHERE id=?",(related['id'],))

    def audit_entries(self):
        with self._db() as db: return [dict(row) for row in db.execute('SELECT * FROM recovery_audit ORDER BY id')]

    def observe_email(self,email,apollo_id):
        hashed=hashlib.sha256(email.strip().casefold().encode()).hexdigest()
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            duplicate=db.execute('SELECT 1 FROM email_identities WHERE email_hash=? AND apollo_id<>? LIMIT 1',(hashed,apollo_id)).fetchone() is not None
            db.execute('INSERT OR IGNORE INTO email_identities VALUES(?,?)',(hashed,apollo_id))
        return duplicate

    def email_identities(self):
        with self._db() as db: return [dict(row) for row in db.execute('SELECT email_hash,apollo_id FROM email_identities')]

    def _day(self): return self.now().astimezone(ZoneInfo(self.settings.timezone)).date().isoformat()

    def _limit(self, kind):
        if kind not in ('search', 'enrich', 'draft'): raise ValueError('Unknown operation kind')
        return getattr(self.settings, kind+'_daily_limit')

    def reserve(self, kind, key, units=1):
        if type(units) is not int or units < 1: raise ValueError('Positive units required')
        limit = self._limit(kind)
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            pending = db.execute("SELECT id FROM attempts WHERE kind=? AND operation_key=? AND status IN ('pending','uncertain')", (kind,key)).fetchone()
            if pending: raise AttemptUncertain('Previous provider attempt requires manual reconciliation')
            cached = db.execute('SELECT payload_json FROM cache WHERE kind=? AND cache_key=? AND expires_at>?', (kind,key,self.now().isoformat())).fetchone()
            if cached: raise CachedResult(json.loads(cached[0]))
            used = db.execute('SELECT COALESCE(SUM(units),0) FROM attempts WHERE kind=? AND day=?', (kind,self._day())).fetchone()[0]
            if used + units > limit: raise BudgetExceeded(f'{kind} daily limit exhausted')
            identifier = uuid.uuid4().hex
            db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?)', (identifier,kind,key,self._day(),units,'pending',None,self.now().isoformat()))
        return identifier

    def finish(self, attempt_id, status, payload):
        if status not in ('done','error','uncertain'): raise ValueError('Invalid attempt status')
        encoded = json.dumps(payload)
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT kind,operation_key,status FROM attempts WHERE id=?', (attempt_id,)).fetchone()
            if not row or row['status'] != 'pending': raise AccountingUnavailable('Attempt is not pending')
            db.execute('UPDATE attempts SET status=?,payload_json=? WHERE id=?', (status,encoded,attempt_id))
            if status == 'done':
                expires = (self.now()+timedelta(days=self.settings.cache_ttl_days)).isoformat()
                db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?,?)', (row['kind'],row['operation_key'],encoded,expires))

    def remaining(self, kind):
        with self._db() as db:
            used = db.execute('SELECT COALESCE(SUM(units),0) FROM attempts WHERE kind=? AND day=?',(kind,self._day())).fetchone()[0]
        return max(0, self._limit(kind)-used)

    def cached(self, kind, key):
        with self._db() as db:
            row = db.execute('SELECT payload_json FROM cache WHERE kind=? AND cache_key=? AND expires_at>?',(kind,key,self.now().isoformat())).fetchone()
        return json.loads(row[0]) if row else None

    def cache_record(self, kind, key):
        """Include expired records so callers can request review instead of silently paying."""
        with self._db() as db:
            row = db.execute('SELECT payload_json,expires_at FROM cache WHERE kind=? AND cache_key=?',
                             (kind,key)).fetchone()
        return {'payload':json.loads(row[0]), 'expires_at':row[1]} if row else None

    def save_cached(self, kind, key, payload, *, expires_at=None):
        deadline = (self.now()+timedelta(days=self.settings.cache_ttl_days)).isoformat()
        if expires_at is not None: deadline = min(deadline, expires_at)
        with self._db() as db:
            db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?,?)',
                       (kind,key,json.dumps(payload),deadline))

    def remember_contact(self, person, source_run_id, enrichment_key):
        if not person.get('email') or person.get('employer_match') != 'confirmed': return
        with self._db() as db:
            entry = db.execute("SELECT expires_at FROM cache WHERE kind='enrich' AND cache_key=? AND expires_at>?",
                               (enrichment_key,self.now().isoformat())).fetchone()
            if entry is None: return
            db.execute('''INSERT INTO company_contacts VALUES(?,?,?,?,?)
                ON CONFLICT(company_domain,apollo_id) DO UPDATE SET
                  payload_json=excluded.payload_json, source_run_id=excluded.source_run_id,
                  expires_at=excluded.expires_at
                WHERE excluded.expires_at > company_contacts.expires_at''',
                (person['company_domain'],person['apollo_id'],json.dumps(person),source_run_id,entry[0]))

    def saved_contacts(self, company_domain, *, include_expired=False):
        with self._db() as db:
            rows = db.execute('SELECT payload_json,source_run_id,expires_at FROM company_contacts WHERE company_domain=? ORDER BY apollo_id',
                              (company_domain,)).fetchall()
        return [{'person':json.loads(row[0]), 'source_run_id':row[1], 'expires_at':row[2]} for row in rows
                if include_expired or row[2] > self.now().isoformat()]

    def alias_cache(self,kind,source_key,target_key):
        """Reuse an already completed lookup without adding a submission or extending TTL."""
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT payload_json,expires_at FROM cache WHERE kind=? AND cache_key=? AND expires_at>?',
                           (kind,source_key,self.now().isoformat())).fetchone()
            if row: db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?,?)',(kind,target_key,row['payload_json'],row['expires_at']))

    def save_run(self, run_id, payload):
        with self._db() as db:
            db.execute('INSERT OR REPLACE INTO runs VALUES(?,?,?)',(run_id,json.dumps(payload),self.now().isoformat()))

    def load_run(self, run_id):
        with self._db() as db: row = db.execute('SELECT payload_json FROM runs WHERE id=?',(run_id,)).fetchone()
        if not row: raise AccountingUnavailable('Unknown run ID')
        return json.loads(row[0])

    def saved_runs(self):
        with self._db() as db:
            rows = db.execute('SELECT payload_json FROM runs ORDER BY updated_at DESC').fetchall()
        return [json.loads(row[0]) for row in rows]

    def claim(self, identifier, payload):
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT status,payload_json FROM claims WHERE id=?',(identifier,)).fetchone()
            if row:
                old=json.loads(row['payload_json'])
                if row['status']=='processing' or not payload.get('token') or old.get('token')==payload['token']: return False
                self._audit(db,'claim',identifier,row['status'],'processing')
            payload={**payload,'created_at':self.now().isoformat()}
            db.execute('INSERT OR REPLACE INTO claims VALUES(?,?,?)',(identifier,json.dumps(payload),'processing'))
        return True

    def finish_claim(self, identifier, payload, *, status='done'):
        if status not in ('done','error'): raise RecoveryError('Invalid terminal claim status')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT status,payload_json FROM claims WHERE id=?',(identifier,)).fetchone()
            if not row or row['status']!='processing': raise AccountingUnavailable('Claim is not processing')
            owner=json.loads(row['payload_json'])
            if any(owner.get(key)!=payload.get(key) for key in ('token','input_hash')):
                raise AccountingUnavailable('Claim belongs to a newer input version; stale completion refused')
            if status=='error': self._audit(db,'claim',identifier,row['status'],status)
            db.execute('UPDATE claims SET payload_json=?,status=? WHERE id=?',(json.dumps(payload),status,identifier))

    def get_claim(self, identifier):
        with self._db() as db: row = db.execute('SELECT payload_json,status FROM claims WHERE id=?',(identifier,)).fetchone()
        return (row['status'], json.loads(row['payload_json'])) if row else None

    @staticmethod
    def preview(path, settings):
        limits = {kind:getattr(settings,kind+'_daily_limit') for kind in ('search','enrich','draft')}
        if not Path(path).exists(): return limits
        try:
            with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True)) as db:
                day = datetime.now(timezone.utc).astimezone(ZoneInfo(settings.timezone)).date().isoformat()
                for kind in limits:
                    count = db.execute('SELECT COALESCE(SUM(units),0) FROM attempts WHERE kind=? AND day=?',(kind,day)).fetchone()[0]
                    limits[kind] = max(0,limits[kind]-count)
        except (OSError, sqlite3.Error): raise AccountingUnavailable('Cannot preview existing accounting') from None
        return limits
