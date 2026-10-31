import json
from pathlib import Path
import tempfile
import unittest
import zstandard

NOW = 1793318400  # 2026-10-30 00:00 UTC / 08:00 Shanghai


def event(kind, seq, data, at=NOW):
    return dict(type=kind, seq=seq, time=int(at*1000), data=data)


def reply(seq, identifier, at=NOW):
    usage = dict(inputTokens=10, outputTokens=5, cacheReadTokens=20, cacheWriteTokens=0, totalTokens=35)
    return event('assistant/message', seq, dict(turn=1, step=1, message=dict(id=identifier, role='assistant',
        content=[dict(type='text', text='PRIVATE TASK CONTENT')]), usage=usage,
        stream=[dict(chunk=dict(type='usage', usage=usage))]), at)


class DshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home = self.root/'dsh'
        (self.home/'sessions').mkdir(parents=True)
        self.path = self.home/'sessions/a.v4.jsonl'
        self.rows = [dict(type='session', version=4, id='session-a'),
                     event('turn/start', 0, dict(turn=1)), reply(1, 'reply-a')]

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        self.path.write_text(''.join(json.dumps(r)+'\n' for r in self.rows), encoding='utf-8')

    def monitor(self):
        from sources.dsh import DshMonitor
        return DshMonitor(self.home, self.root/'cache')

    def test_canonical_usage_only_and_dedup_survives_restart_and_compressed_copy(self):
        self.write()
        monitor = self.monitor()
        first = monitor.snapshot(True, NOW+10)
        self.assertEqual(first['session_tokens']['total'], 35)
        self.assertEqual(first['day_tokens']['total'], 35)
        compressed = self.path.with_suffix('.jsonl.zstd')
        compressed.write_bytes(zstandard.ZstdCompressor().compress(self.path.read_bytes()))
        again = self.monitor().snapshot(True, NOW+15)
        self.assertEqual(again['day_tokens']['total'], 35)
        self.assertNotIn('PRIVATE TASK CONTENT', json.dumps(again))
        for database in (self.root/'cache').rglob('*.sqlite3'):
            self.assertNotIn(b'PRIVATE TASK CONTENT', database.read_bytes())

    def test_partial_append_is_retried_and_turn_end_controls_progress(self):
        self.write()
        self.monitor().snapshot(True, NOW+1)
        row = json.dumps(event('turn/end', 2, dict(turn=1, reason=dict(kind='completed')), NOW+2))
        with self.path.open('a', encoding='utf-8') as f:
            f.write(row[:20])
        self.assertEqual(self.monitor().snapshot(True, NOW+3)['activity'], 'working')
        with self.path.open('a', encoding='utf-8') as f:
            f.write(row[20:]+'\n')
        final = self.monitor().snapshot(True, NOW+4)
        self.assertEqual(final['activity'], 'completed')
        self.assertIsNone(final['progress_percent'])
        self.assertEqual(final['session_tokens']['total'], 35)

    def test_shanghai_day_boundary_and_same_message_id_count_once(self):
        self.rows = [self.rows[0], reply(0,'before', NOW-8*3600-1),
                     reply(1,'after', NOW-8*3600), reply(2,'after', NOW)]
        self.write()
        actual = self.monitor().snapshot(False, NOW+10)
        self.assertEqual(actual['day_tokens']['total'], 35)
        self.assertEqual(actual['session_tokens']['total'], 70)
        self.assertFalse(actual['running'])
        self.assertEqual(actual['activity'], 'idle')

    def test_rotation_and_seed_only_session_do_not_hide_actual_work(self):
        self.write()
        self.monitor().snapshot(True, NOW+1)
        self.rows.append(reply(2,'reply-b', NOW+2))
        self.write()
        (self.home/'sessions/seed.jsonl').write_text(json.dumps(dict(type='session',version=4,id='seed'))+'\n'+
            json.dumps(event('session/end-seed', 0, {}, NOW+100))+'\n')
        actual = self.monitor().snapshot(True, NOW+110)
        self.assertEqual(actual['session_tokens']['total'], 70)
        self.assertEqual(actual['activity'], 'working')

    def test_process_matching_requires_full_path_or_verified_ancestor(self):
        from sources.dsh import matches_process
        expected = str(self.root/'DeepSeek Harness.exe')
        self.assertTrue(matches_process(expected, expected))
        self.assertFalse(matches_process(str(self.root/'node.exe'), expected))
        self.assertFalse(matches_process(str(self.root/'Uninstall DeepSeek Harness.exe'), expected))

    def test_corrupt_compressed_file_and_nonobject_header_do_not_disable_valid_log(self):
        self.write()
        (self.home/'sessions/corrupt.jsonl.zstd').write_bytes(b'not a zstandard frame')
        (self.home/'sessions/header.jsonl').write_text('[]\n')
        actual = self.monitor().snapshot(True,NOW+10)
        self.assertEqual(actual['session_tokens']['total'],35)
        self.assertEqual(actual['status'],'ok')
        self.assertGreaterEqual(actual['unreadable_files'],1)

    def test_changing_dsh_home_does_not_mix_accounts_or_usage(self):
        from sources.dsh import DshMonitor
        self.write()
        self.monitor().snapshot(True,NOW+10)
        other = self.root/'other-home'
        (other/'sessions').mkdir(parents=True)
        actual = DshMonitor(other,self.root/'cache').snapshot(False,NOW+10)
        self.assertEqual(actual['day_tokens']['total'],0)
        self.assertEqual(actual['session_tokens']['total'],0)

    def test_log_coverage_limit_is_reported_instead_of_silent_complete_total(self):
        self.write()
        for i in range(4096):
            (self.home/'sessions'/f'seed-{i}.jsonl').write_text(json.dumps(dict(type='session',version=4,id=f'seed-{i}'))+'\n')
        actual = self.monitor().snapshot(False,NOW+10)
        self.assertTrue(actual['coverage_limited'])


if __name__ == '__main__':
    unittest.main()
