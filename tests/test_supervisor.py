import json
from pathlib import Path
import sys
import tempfile
import time
import unittest


class SupervisorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtCore import QCoreApplication
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_hung_worker_is_killed_while_other_source_finishes_and_events_keep_moving(self):
        from ui.sources import SourceSupervisor
        with tempfile.TemporaryDirectory() as directory:
            def command(kind):
                code = 'import time; time.sleep(30)' if kind == 'rog' else 'import json; print(json.dumps(dict(status="ok",percent=77)))'
                return [sys.executable,'-c',code]
            supervisor = SourceSupervisor(Path(directory),command_factory=command)
            ticks = []
            supervisor.updated.connect(lambda kind,result:ticks.append((kind,result)))
            supervisor.launch('rog',timeout_ms=250)
            supervisor.launch('g3m',timeout_ms=1500)
            deadline = time.monotonic()+4
            cycles = 0
            while (supervisor.jobs or len(ticks)<2) and time.monotonic()<deadline:
                self.app.processEvents()
                time.sleep(.005)
                cycles += 1
            self.assertGreater(cycles,10)
            self.assertEqual(supervisor.snapshots['rog']['code'],'timeout')
            self.assertEqual(supervisor.snapshots['g3m']['percent'],77)
            self.assertFalse(supervisor.jobs)
            supervisor.stop()

    def test_exit_cleans_all_owned_children_and_oversized_output_is_bounded(self):
        from ui.sources import SourceSupervisor
        with tempfile.TemporaryDirectory() as directory:
            supervisor = SourceSupervisor(Path(directory),command_factory=lambda kind:
                [sys.executable,'-c','import sys,time; sys.stdout.write("x"*200000); sys.stdout.flush(); time.sleep(30)'])
            supervisor.launch('rog',timeout_ms=2000)
            deadline = time.monotonic()+4
            while supervisor.jobs and time.monotonic()<deadline:
                self.app.processEvents()
                time.sleep(.005)
            self.assertEqual(supervisor.snapshots['rog']['code'],'invalid_output')
            supervisor.launch('dsh',timeout_ms=30000)
            self.app.processEvents()
            owned = [job.process for job in supervisor.jobs.values()]
            supervisor.stop()
            self.assertFalse(supervisor.jobs)
            from PySide6.QtCore import QProcess
            self.assertTrue(all(p.state()==QProcess.ProcessState.NotRunning for p in owned))


class StateTests(unittest.TestCase):
    def test_low_battery_error_working_and_idle_priorities(self):
        from core.monitor_state import derive_state
        self.assertEqual(derive_state({}),'idle')
        self.assertEqual(derive_state(dict(dsh=dict(status='ok',running=True,activity='working'))),'working')
        self.assertEqual(derive_state(dict(rog=dict(status='ok',percent=12,charging=False))),'low_battery')
        self.assertEqual(derive_state(dict(rog=dict(status='ok',percent=12,charging=True))),'idle')
        self.assertEqual(derive_state(dict(rog=dict(status='error'))),'error')
        self.assertEqual(derive_state(dict(rog=dict(status='unavailable',percent=None))),'idle')


if __name__ == '__main__':
    unittest.main()
