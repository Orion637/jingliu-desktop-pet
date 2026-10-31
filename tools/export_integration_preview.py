"""Export this application's own rendered widgets for layout review."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from ui.app import AppManager

app = QApplication([])
manager = AppManager(ROOT,enable_sources=False)
manager.show_pet()
manager.show_sources()
for name in ('rog','g3m'):
    manager.sources.publish(name,dict(status='unavailable',code='receiver_missing'))
from sources.g3m import run as read_mouse
manager.sources.publish('g3m',read_mouse(None,ROOT))
manager.sources.publish('dsh',dict(status='ok',code='ready',running=False,activity='idle'))
manager.sources.publish('balance',dict(status='unavailable',code='key_required'))
def export():
    manager.pet.grab().save(str(ROOT/'preview/镜流_整合版桌宠.png'))
    manager.source_panel.grab().save(str(ROOT/'preview/镜流_设备状态面板.png'))
    manager.quit()
QTimer.singleShot(500,export)
app.exec()
