import json
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path


class SettingsTests(unittest.TestCase):
    def test_missing_and_malformed_file_use_defaults(self):
        from core.settings import Settings
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            self.assertEqual(Settings.load(path).width, 420)
            path.write_text('{broken', encoding='utf-8')
            with self.assertLogs(level='WARNING'):
                self.assertEqual(Settings.load(path).weapon, 'slender')

    def test_round_trip_and_bad_values(self):
        from core.settings import Settings
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config/settings.json'
            settings = Settings(width=540, x=-350, y=80, weapon='ice', follow_cursor=False)
            self.assertTrue(settings.save(path))
            self.assertEqual(Settings.load(path), settings)
            path.write_text(json.dumps(dict(width=-1, x=True, y='bad', weapon='bad', follow_cursor='yes')), encoding='utf-8')
            actual = Settings.load(path)
            self.assertEqual(actual, Settings())

    def test_save_failure_does_not_raise(self):
        from core.settings import Settings
        with tempfile.TemporaryDirectory() as directory:
            blocker = Path(directory) / 'file'
            blocker.write_text('not a directory')
            with self.assertLogs(level='WARNING'):
                self.assertFalse(Settings().save(blocker / 'settings.json'))


class InstanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtCore import QCoreApplication
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_second_launch_routes_command_to_first_and_shutdown_releases(self):
        from ui.instance import InstanceChannel
        name = 'jingliu_test_' + uuid.uuid4().hex
        first = InstanceChannel(name)
        received = []
        first.command_received.connect(received.append)
        try:
            self.assertTrue(first.claim_or_notify('pet'))
            code = "from PySide6.QtCore import QCoreApplication; from ui.instance import InstanceChannel; app=QCoreApplication([]); c=InstanceChannel("+repr(name)+"); print(c.claim_or_notify('preview'))"
            child = subprocess.Popen([sys.executable, '-c', code], cwd=Path(__file__).resolve().parents[1], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            deadline = time.monotonic()+5
            while child.poll() is None and time.monotonic() < deadline:
                self.app.processEvents()
            stdout, stderr = child.communicate(timeout=1)
            self.assertEqual(child.returncode, 0, stderr)
            self.assertEqual(stdout.strip(), 'False')
            self.app.processEvents()
            self.assertEqual(received, ['preview'])
            first.close()
            third = InstanceChannel(name)
            try:
                self.assertTrue(third.claim_or_notify('pet'))
            finally:
                third.close()
        finally:
            first.close()

    def test_simultaneous_launches_have_one_owner(self):
        name = 'jingliu_race_'+uuid.uuid4().hex
        with tempfile.TemporaryDirectory() as directory:
            barrier = Path(directory)/'go'
            code = (
                'import time; from pathlib import Path; '
                'from PySide6.QtCore import QCoreApplication,QTimer; '
                'from ui.instance import InstanceChannel; app=QCoreApplication([]); '
                f'c=InstanceChannel({name!r}); gate=Path({str(barrier)!r}); '
                '\nwhile not gate.exists(): time.sleep(.01)\n'
                'owner=c.claim_or_notify("pet"); print(owner,flush=True); '
                'QTimer.singleShot(2000,app.quit); app.exec() if owner else None; c.close()'
            )
            children = [subprocess.Popen([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[1],
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(5)]
            try:
                time.sleep(.6)
                barrier.touch()
                outputs = [child.communicate(timeout=10) for child in children]
                self.assertTrue(all(child.returncode==0 for child in children),outputs)
                self.assertEqual(sum(out[0].strip()=='True' for out in outputs),1,outputs)
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()
                    child.communicate()

    def test_second_launch_waits_for_first_window_initialization(self):
        from ui.instance import InstanceChannel
        name = 'jingliu_slow_'+uuid.uuid4().hex
        first = InstanceChannel(name)
        self.assertTrue(first.claim_or_notify('pet'))
        code = "from PySide6.QtCore import QCoreApplication; from ui.instance import InstanceChannel; app=QCoreApplication([]); c=InstanceChannel("+repr(name)+"); print(c.claim_or_notify('preview'))"
        child = subprocess.Popen([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[1],
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            time.sleep(1.3)  # First owner has not entered its event loop yet.
            deadline=time.monotonic()+5
            while child.poll() is None and time.monotonic()<deadline:
                self.app.processEvents()
                time.sleep(.005)
            out,err=child.communicate(timeout=1)
            self.assertEqual(child.returncode,0,err)
            self.assertEqual(out.strip(),'False')
        finally:
            first.close()
            if child.poll() is None: child.kill()
            child.communicate()


if __name__ == '__main__':
    unittest.main()
