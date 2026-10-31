"""Exercise native foreign-process fullscreen windows and the real pet lifecycle."""
import json
from pathlib import Path
import sys
import tempfile
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PySide6.QtCore import QProcess,QTimer
from PySide6.QtWidgets import QApplication,QLabel,QVBoxLayout,QWidget


def child():
    app=QApplication([])
    window=QWidget()
    window.setWindowTitle('镜流全屏检测验证')
    window.resize(700,450)
    layout=QVBoxLayout(window)
    layout.addWidget(QLabel('镜流全屏隐藏功能验证 / 测试窗口将自动关闭'))
    window.show()
    def phase(name):
        if name=='fullscreen': window.showFullScreen()
        elif name=='maximized': window.showMaximized()
        elif name=='normal': window.showNormal()
        window.raise_()
        window.activateWindow()
        print(json.dumps(dict(phase=name,hwnd=int(window.winId()))),flush=True)
    for delay,name in ((300,'fullscreen'),(2300,'normal'),(3800,'maximized'),(5300,'fullscreen')):
        QTimer.singleShot(delay,lambda n=name:phase(n))
    QTimer.singleShot(7400,app.quit)
    return app.exec()


def verify():
    from core.fullscreen import WindowsFullscreen
    from ui.app import AppManager
    app=QApplication([])
    with tempfile.TemporaryDirectory(prefix='jingliu-fullscreen-') as directory:
        manager=AppManager(ROOT,Path(directory),enable_sources=False)
        manager.show_pet()
        backend=WindowsFullscreen()
        report=dict(phases=[],errors=[])
        process=QProcess()
        buffer=bytearray()
        def check(message):
            try:
                fullscreen=message['phase']=='fullscreen'
                detected=backend.window_is_fullscreen(message['hwnd'],int(manager.pet.winId()))
                assert detected==fullscreen,(message,detected)
                foreground_before=backend.user.GetForegroundWindow()
                foreground_detected=backend.active(int(manager.pet.winId()))
                if foreground_before==message['hwnd']:
                    assert foreground_detected==fullscreen
                manager.fullscreen_probe=lambda hwnd:backend.window_is_fullscreen(message['hwnd'],hwnd)
                manager.update_fullscreen()
                assert manager.pet.isVisible()!=fullscreen
                assert backend.user.GetForegroundWindow()==foreground_before,'Pet stole foreground focus'
                assert manager.session.timer.isActive()
                if fullscreen:
                    manager.set_fullscreen_hiding(False)
                    assert manager.pet.isVisible()
                    manager.set_fullscreen_hiding(True)
                    assert not manager.pet.isVisible()
                    manager.show_inspector()
                    manager.inspector.close()
                    assert manager.fullscreen_timer.isActive()
                report['phases'].append(dict(phase=message['phase'],detected=detected,pet_hidden=not manager.pet.isVisible(),
                    foreground_was_child=foreground_before==message['hwnd'],foreground_detected=foreground_detected,
                    focus_unchanged_after_pet_visibility=True))
            except Exception:
                report['errors'].append(traceback.format_exc())
        def read():
            buffer.extend(bytes(process.readAllStandardOutput()))
            while b'\n' in buffer:
                line,_,remaining=buffer.partition(b'\n')
                buffer[:]=remaining
                message=json.loads(line)
                QTimer.singleShot(150,lambda m=message:check(m))
        process.readyReadStandardOutput.connect(read)
        def finish(*args):
            manager.fullscreen_probe=lambda hwnd:False
            manager.update_fullscreen()
            report['restored_after_close']=manager.pet.isVisible()
            report['native_foreground_probe_exercised']=isinstance(backend.active(int(manager.pet.winId())),bool)
            manager.quit()
        process.finished.connect(finish)
        process.start(sys.executable,[str(Path(__file__).resolve()),'--child'])
        QTimer.singleShot(15000,finish)
        app.exec()
        if process.state()!=QProcess.ProcessState.NotRunning:
            process.kill()
            process.waitForFinished(1500)
        assert len(report['phases'])==4,report
        assert report['restored_after_close']
        (ROOT/'qa/fullscreen-native.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report))
        return 1 if report['errors'] else 0


if __name__=='__main__':
    raise SystemExit(child() if '--child' in sys.argv else verify())
