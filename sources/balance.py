"""Official balance endpoint only. Cache successes and failures for 60 seconds."""
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import time
import urllib.request
import urllib.error
import ssl

from sources.config import write_json

ENDPOINT = 'https://api.deepseek.com/user/balance'


def parse_balance(data):
    balances = []
    if not isinstance(data.get('is_available'), bool):
        raise ValueError('Malformed balance')
    for entry in data.get('balance_infos', [])[:8]:
        if entry.get('currency') not in ('CNY', 'USD'):
            continue
        try:
            total = Decimal(entry['total_balance'])
        except (KeyError, InvalidOperation, TypeError):
            raise ValueError('Invalid balance') from None
        if not total.is_finite():
            raise ValueError('Invalid balance')
        balances.append(dict(currency=entry['currency'], total=str(total)))
    if not balances:
        raise ValueError('No balance currency')
    return dict(status='ok', code='ready', balances=balances, available=data['is_available'])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch_official(key):
    request = urllib.request.Request(ENDPOINT, headers={'Authorization': 'Bearer '+key, 'Accept': 'application/json'})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=6) as response:
        body = response.read(65537)
    if len(body) > 65536:
        raise ValueError('Oversized response')
    return json.loads(body)


def get_balance(root, key, now=None, fetch=fetch_official):
    now = time.time() if now is None else now
    if not key:
        return dict(status='unavailable', code='key_required', balances=[])
    key_id = hashlib.sha256(key.encode()).hexdigest()[:16]
    path = Path(root)/'cache/balance.json'
    try:
        cache = json.loads(path.read_text(encoding='utf-8'))
        if cache.get('key_id') == key_id and 0 <= now-cache['checked_at'] < 60:
            return cache['result']
    except (OSError, ValueError, KeyError, TypeError):
        pass
    try:
        result = parse_balance(fetch(key))
    except Exception as error:
        kind = 'invalid_response'
        if isinstance(error,urllib.error.HTTPError):
            kind = 'http_'+str(error.code)
        elif isinstance(error,urllib.error.URLError):
            kind = 'tls_failed' if isinstance(error.reason,ssl.SSLError) else 'network_failed'
        elif isinstance(error,OSError):
            kind = 'network_failed'
        elif isinstance(error,AttributeError):
            kind = 'runtime_attribute_error'
        reason = error.reason if isinstance(error,urllib.error.URLError) else error
        result = dict(status='error', code='balance_request_failed', balances=[],failure_kind=kind,
                      failure_type=type(reason).__name__[:60],
                      failure_errno=getattr(reason,'errno',None),failure_winerror=getattr(reason,'winerror',None))
    result['checked_at'] = now
    try:
        write_json(path, dict(key_id=key_id, checked_at=now, result=result))
    except OSError:
        pass
    return result


def run(config, state_root):
    from sources.credentials import resolve_key
    return get_balance(state_root, resolve_key(state_root, config.dsh_home))
