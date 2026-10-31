"""Real Qt/source lifecycle and timed responsiveness check; no input content output."""
import json
from pathlib import Path
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PySide6.QtCore import QTimer,Qt,QPoint
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
import psutil
from ui.app import AppManager


def verify(seconds=90):
    app = QApplication([])
    directory = tempfile.TemporaryDirectory(prefix='jingliu-verify-')
    manager = AppManager(ROOT,Path(directory.name))
    manager.show_pet()
    manager.show_sources()
    observations,errors,samples,gaps = {},[],[],[]
    started = previous = time.monotonic()
    heartbeat = QTimer()
    heartbeat.setInterval(33)
    def tick():
        nonlocal previous
        now = time.monotonic()
        gaps.append(now-previous)
        previous = now
    heartbeat.timeout.connect(tick)
    heartbeat.start()
    sampler = QTimer()
    sampler.setInterval(5000)
    sampler.timeout.connect(lambda:samples.append(psutil.Process().memory_info().rss))
    sampler.start()

    def targeted():
        try:
            assert set(manager.sources.snapshots) == {'rog','g3m','balance','dsh'},manager.sources.snapshots
            observations['actual_statuses'] = {key:dict(status=value.get('status'),code=value.get('code'))
                                               for key,value in manager.sources.snapshots.items()}
            actual = manager.sources.snapshots['dsh']
            fixture = dict(status='ok',running=True,activity='working',progress_percent=None,
                turn=2,step=3,pending_tools=1,pending_jobs=0,pending_approvals=0,
                session_tokens=dict(total=123,input=20,output=3,cache_read=100,cache_write=0),day_tokens=dict(total=123))
            manager.sources.publish('balance',dict(status='unavailable',code='key_required'))
            manager.sources.publish('dsh',fixture)
            assert not manager.source_panel.dsh_box.isHidden()
            assert manager.source_panel.progress.maximum() == 0
            assert manager.monitor_state == 'working'
            manager.sources.publish('rog',dict(status='ok',percent=12,charging=False))
            assert manager.monitor_state == 'low_battery'
            manager.sources.publish('dsh',dict(status='ok',running=False,activity='idle'))
            assert manager.source_panel.dsh_box.isHidden()
            manager.sources.publish('dsh',actual)
            manager.pet.move(-20000,-20000)
            manager.recover_pet()
            assert manager.pet.screen().availableGeometry().contains(manager.pet.frameGeometry())
            manager.source_panel.close()
            assert manager.pet.isVisible()
            assert manager.session.timer.isActive()
            selected = []
            for _ in range(20):
                QTest.mouseClick(manager.pet,Qt.MouseButton.LeftButton,pos=QPoint(manager.pet.width()//2,manager.pet.height()//3))
                selected.append(manager.session.last_interaction)
            assert all(a!=b for a,b in zip(selected,selected[1:]))
            assert len(set(selected))>=4
            assert not set(selected)&{'idle','drag','blink','rest','look'}
            observations['native_click_random_action_count'] = len(set(selected))
            manager.show_sources()
            observations['panel_visibility_progress_state_screen_recovery'] = 'pass'
        except Exception:
            errors.append(traceback.format_exc())
        manager.restart_sources()
    QTimer.singleShot(9500,targeted)

    def finish():
        heartbeat.stop()
        sampler.stop()
        manager.sources.stop()
        observations.update(elapsed_seconds=round(time.monotonic()-started,2),heartbeat_ticks=len(gaps),
            maximum_heartbeat_gap_seconds=round(max(gaps,default=0),3),
            parent_rss_samples_bytes=samples,owned_workers_after_stop=len(manager.sources.jobs),errors=errors)
        if len(samples)>4:
            observations['rss_growth_after_warmup_bytes'] = max(samples[2:])-min(samples[2:])
        (ROOT/'qa/integration-runtime.json').write_text(json.dumps(observations,indent=2),encoding='utf-8')
        manager.quit()
    QTimer.singleShot(int(seconds*1000),finish)
    app.exec()
    directory.cleanup()
    print(json.dumps(observations,ensure_ascii=True))
    return 1 if errors or observations.get('owned_workers_after_stop') else 0


if __name__ == '__main__':
    raise SystemExit(verify(float(sys.argv[1]) if len(sys.argv)>1 else 90))
