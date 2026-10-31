"""Read-only DSH v4 JSONL/Zstandard monitoring, with incremental private aggregates.

No prompts, replies, tool arguments/results or credentials are persisted. Canonical
assistant data.usage counts once; stream usage is never counted a second time.
"""
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import time
import zstandard

SHANGHAI = timezone(timedelta(hours=8))
FIELDS = ('input', 'output', 'cache_read', 'cache_write', 'total')
MAX_LINE = 4*1024*1024


def identity(value):
    return hashlib.sha256(str(value).encode('utf-8')).hexdigest()


def day_at(timestamp):
    return datetime.fromtimestamp(timestamp, SHANGHAI).date().isoformat()


def matches_process(executable, expected):
    return bool(executable and expected and os.path.normcase(os.path.abspath(executable)) ==
                os.path.normcase(os.path.abspath(expected)))


def detect_process(expected):
    import psutil
    started = []
    for process in psutil.process_iter(['exe', 'create_time']):
        try:
            if matches_process(process.info.get('exe'), expected):
                started.append(process.info.get('create_time') or time.time())
        except (psutil.Error, OSError):
            continue
    return bool(started), min(started) if started else None


class DshMonitor:
    def __init__(self, home, cache):
        self.home = Path(home).expanduser().resolve()
        self.cache = Path(cache)/('dsh-'+identity(os.path.normcase(str(self.home)))[:16])

    def connect(self):
        self.cache.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.cache/'dsh.sqlite3', timeout=.3)
        db.execute('PRAGMA max_page_count=32768')  # 128 MiB ceiling at default page size
        db.executescript('''
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY, signature TEXT, size INTEGER, mtime INTEGER,
                offset INTEGER, done INTEGER);
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, seq INTEGER, time REAL, state TEXT);
            CREATE TABLE IF NOT EXISTS usage (
                session TEXT, message TEXT, day TEXT,
                input INTEGER, output INTEGER, cache_read INTEGER, cache_write INTEGER, total INTEGER,
                PRIMARY KEY(session,message));
            CREATE INDEX IF NOT EXISTS usage_day ON usage(day);
        ''')
        return db

    def consume(self, db, session, record):
        kind = record.get('type')
        seq = record.get('seq')
        if type(seq) is not int or seq < 0:
            return
        timestamp = record.get('time', 0)
        if not isinstance(timestamp, (int,float)) or not 1e12 <= timestamp < 1e14:
            return
        timestamp /= 1000
        data = record.get('data')
        if not isinstance(data, dict):
            return
        if kind == 'assistant/message':
            usage, message = data.get('usage'), data.get('message', {})
            if isinstance(usage, dict) and isinstance(message, dict) and message.get('role') == 'assistant':
                names = ('inputTokens','outputTokens','cacheReadTokens','cacheWriteTokens','totalTokens')
                values = [usage.get(key, 0) for key in names]
                if all(type(n) is int and 0 <= n <= 10**12 for n in values) and values[4] == sum(values[:4]):
                    key = identity(message.get('id') or 'seq:'+str(seq))
                    db.execute('INSERT OR IGNORE INTO usage VALUES (?,?,?,?,?,?,?,?)',
                               (session,key,day_at(timestamp),*values))
        meaningful = kind in ('turn/start','turn/end','step/start','step/end','assistant/message',
            'tool/call','tool/result','job/registered','job/settled','approval/asked','approval/decided',
            'llm/retry','llm/retry-started')
        if not meaningful:
            return
        previous = db.execute('SELECT seq,time,state FROM sessions WHERE id=?',(session,)).fetchone()
        if previous and seq <= previous[0]:
            return
        state = json.loads(previous[2]) if previous else dict(active=False, activity='idle', turn=0, step=0,
                                                            tools=[],jobs=[],approvals=[])
        if kind == 'turn/start':
            state.update(active=True,activity='working',turn=data.get('turn',0),step=0,tools=[],approvals=[])
        elif kind == 'turn/end':
            reason = data.get('reason', {})
            state.update(active=False, activity='error' if isinstance(reason,dict) and reason.get('kind') == 'error'
                         else 'completed', tools=[],approvals=[])
        elif kind == 'step/start':
            state.update(step=data.get('step',0),activity='working')
        elif kind == 'tool/call':
            self.update_ids(state,'tools',data.get('callId'),True)
        elif kind == 'tool/result':
            message = data.get('message',{})
            self.update_ids(state,'tools',message.get('toolCallId') if isinstance(message,dict) else None,False)
        elif kind in ('job/registered','job/settled'):
            self.update_ids(state,'jobs',data.get('jobId'),kind == 'job/registered')
        elif kind in ('approval/asked','approval/decided'):
            self.update_ids(state,'approvals',data.get('id') or data.get('callId'),kind == 'approval/asked')
        elif kind in ('llm/retry','llm/retry-started'):
            state['activity'] = 'retrying'
        for key in ('turn','step'):
            if type(state.get(key)) is not int:
                state[key] = 0
        db.execute('INSERT OR REPLACE INTO sessions VALUES (?,?,?,?)',
                   (session,seq,timestamp,json.dumps(state)))

    @staticmethod
    def update_ids(state, field, value, add):
        if value is None:
            return
        values = set(state.get(field,[]))
        key = identity(value)
        if add and len(values) < 2048:
            values.add(key)
        elif not add:
            values.discard(key)
        state[field] = sorted(values)

    def read_file(self, db, path, stat, deadline):
        previous = db.execute('SELECT signature,size,mtime,offset,done FROM files WHERE path=?',(str(path),)).fetchone()
        if previous and previous[1:3] == (stat.st_size,stat.st_mtime_ns) and previous[4]:
            return True
        with ExitStack() as stack:
            raw = stack.enter_context(path.open('rb'))
            signature = str(stat.st_ino)+':'+hashlib.sha256(raw.read(512)).hexdigest()
            raw.seek(0)
            stream = raw
            if path.suffix in ('.zstd','.zst'):
                import zstandard
                reader = stack.enter_context(zstandard.ZstdDecompressor().stream_reader(raw))
                stream = stack.enter_context(io.BufferedReader(reader))
            header_line = stream.readline(MAX_LINE+1)
            if len(header_line) > MAX_LINE or not header_line.endswith(b'\n'):
                return False
            header = json.loads(header_line)
            if not isinstance(header,dict):
                raise ValueError('Invalid session header')
            if header.get('type') != 'session' or header.get('version') != 4 or not isinstance(header.get('id'),str):
                return True
            session = identity(header['id'])
            offset = len(header_line)
            target = previous[3] if (previous and previous[0] == signature and stat.st_size >= previous[1]
                and not (stat.st_size == previous[1] and stat.st_mtime_ns != previous[2])) else offset
            while offset < target:
                part = stream.read(min(1024*1024,target-offset))
                if not part:
                    break
                offset += len(part)
                if time.monotonic() > deadline:
                    return False
            budget = 16*1024*1024
            done = False
            while time.monotonic() < deadline and budget > 0:
                line = stream.readline(MAX_LINE+1)
                if not line:
                    done = True
                    break
                if len(line) > MAX_LINE:
                    # Discard an oversized record without retaining its text in memory/cache.
                    length = len(line)
                    while not line.endswith(b'\n'):
                        line = stream.readline(MAX_LINE+1)
                        length += len(line)
                        if not line or time.monotonic() > deadline:
                            break
                    if not line.endswith(b'\n'):
                        break
                    offset += length
                    budget -= length
                    continue
                if not line.endswith(b'\n'):
                    done = True  # Retry this unfinished record after size/mtime changes.
                    break
                offset += len(line)
                budget -= len(line)
                try:
                    record = json.loads(line)
                    if isinstance(record,dict):
                        self.consume(db,session,record)
                except (ValueError,TypeError,OverflowError):
                    continue
            db.execute('INSERT OR REPLACE INTO files VALUES (?,?,?,?,?,?)',
                       (str(path),signature,stat.st_size,stat.st_mtime_ns,offset,int(done)))
            return done

    def snapshot(self, running=False, now=None, process_started=None):
        now = time.time() if now is None else now
        root = self.home/'sessions'
        result = dict(status='ok',code='ready',running=running,activity='idle',progress_percent=None,
                      session_tokens=dict.fromkeys(FIELDS,0),day_tokens=dict.fromkeys(FIELDS,0),
                      pending_tools=0,pending_jobs=0,pending_approvals=0,turn=0,step=0,indexing=False,
                      unreadable_files=0,coverage_limited=False)
        if not root.is_dir():
            result.update(status='unavailable',code='sessions_missing')
            return result
        db = self.connect()
        try:
            candidates = []
            for path in root.rglob('*'):
                if path.is_file() and (path.name.endswith('.jsonl') or path.name.endswith('.jsonl.zstd') or path.name.endswith('.jsonl.zst')):
                    try:
                        candidates.append((path,path.stat()))
                    except OSError:
                        pass
            candidates.sort(key=lambda item:item[1].st_mtime_ns,reverse=True)
            result['coverage_limited'] = len(candidates)>4096
            deadline = time.monotonic()+2.5
            for path,stat in candidates[:4096]:
                if time.monotonic() >= deadline:
                    result['indexing'] = True
                    break
                try:
                    if not self.read_file(db,path,stat,deadline):
                        result['indexing'] = True
                except (OSError,ValueError,EOFError,zstandard.ZstdError):
                    result['unreadable_files'] += 1
            db.commit()
            latest = db.execute('SELECT id,time,state FROM sessions ORDER BY time DESC LIMIT 1').fetchone()
            if latest:
                session,last_time,encoded = latest
                state = json.loads(encoded)
                result.update(session_id=session[:8],last_activity=last_time,
                              turn=state['turn'],step=state['step'],pending_tools=len(state['tools']),
                              pending_jobs=len(state['jobs']),pending_approvals=len(state['approvals']))
                fresh = process_started is None or last_time >= process_started-5
                if running and fresh:
                    result['activity'] = 'approval' if state['approvals'] else 'tool' if state['tools'] else state['activity']
                row = db.execute('SELECT SUM(input),SUM(output),SUM(cache_read),SUM(cache_write),SUM(total) FROM usage WHERE session=?',(session,)).fetchone()
                result['session_tokens'] = dict(zip(FIELDS,(n or 0 for n in row)))
            row = db.execute('SELECT SUM(input),SUM(output),SUM(cache_read),SUM(cache_write),SUM(total) FROM usage WHERE day=?',(day_at(now),)).fetchone()
            result['day_tokens'] = dict(zip(FIELDS,(n or 0 for n in row)))
            return result
        finally:
            db.close()


def run(config, state_root):
    running,started = detect_process(config.dsh_executable)
    return DshMonitor(config.dsh_home,Path(state_root)/'cache').snapshot(running,process_started=started)
