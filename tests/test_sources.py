import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class CredentialTests(unittest.TestCase):
    def test_secure_round_trip_never_writes_plaintext(self):
        from sources.credentials import save_key, read_saved_key, clear_key
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key = 'sk-' + 'test-only-not-a-real-key-123456789'
            save_key(root, key)
            self.assertEqual(read_saved_key(root), key)
            for path in root.rglob('*'):
                if path.is_file():
                    self.assertNotIn(key.encode(), path.read_bytes())
            clear_key(root)
            self.assertIsNone(read_saved_key(root))

    def test_dsh_account_token_is_not_used_as_api_key(self):
        from sources.credentials import resolve_key
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / 'dsh'
            home.mkdir()
            (home / '.credentials.yaml').write_text(
                'records:\n  deepseek-account-platform/default:\n    payload:\n      token: private-account-token\nrefs:\n  DEEPSEEK_API_KEY: encrypted-reference\n')
            with patch.dict(os.environ, {}, clear=True):
                self.assertIsNone(resolve_key(root, home))


class BalanceTests(unittest.TestCase):
    def test_network_failure_category_is_useful_without_exposing_error_content(self):
        from sources.balance import get_balance
        from urllib.error import HTTPError
        def denied(key):
            raise HTTPError('https://api.deepseek.com/user/balance',403,'PRIVATE RESPONSE',{},None)
        with tempfile.TemporaryDirectory() as directory:
            result = get_balance(Path(directory),key='sk-test-secret-123456',fetch=denied)
            self.assertEqual(result['failure_kind'],'http_403')
            self.assertNotIn('PRIVATE RESPONSE',json.dumps(result))

    def test_official_response_preserves_currency_and_does_not_accept_nan(self):
        from sources.balance import parse_balance
        response = {'is_available': True, 'balance_infos': [
            {'currency': 'CNY', 'total_balance': '12.34'},
            {'currency': 'USD', 'total_balance': '1.00'}]}
        self.assertEqual(parse_balance(response)['balances'], [
            {'currency': 'CNY', 'total': '12.34'}, {'currency': 'USD', 'total': '1.00'}])
        response['balance_infos'][0]['total_balance'] = 'NaN'
        with self.assertRaises(ValueError):
            parse_balance(response)

    def test_cache_prevents_network_for_sixty_seconds_including_errors(self):
        from sources.balance import get_balance
        calls = []
        def fetch(key):
            calls.append(True)
            raise OSError('sensitive response must not escape')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = get_balance(root, key='sk-test-secret-123456', now=100, fetch=fetch)
            second = get_balance(root, key='sk-test-secret-123456', now=120, fetch=fetch)
            self.assertEqual(len(calls), 1)
            self.assertEqual(first['status'], 'error')
            self.assertNotIn('sensitive', json.dumps(second))
            get_balance(root, key='sk-test-secret-123456', now=161, fetch=fetch)
            self.assertEqual(len(calls), 2)
            self.assertNotIn('sk-test-secret', ''.join(p.read_text() for p in root.glob('*.json')))


if __name__ == '__main__':
    unittest.main()
