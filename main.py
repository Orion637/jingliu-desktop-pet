"""Jingliu desktop pet and isolated read-only source-worker entry point."""
import argparse
import logging
import hashlib
import sys
import tempfile
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Open rig/action inspector")
    parser.add_argument("--smoke-test", action="store_true", help="Launch real windows and exit after a short runtime check")
    parser.add_argument('--source-worker',choices=('rog','dsh','balance','g3m'),help=argparse.SUPPRESS)
    parser.add_argument('--state-root',help=argparse.SUPPRESS)
    parser.add_argument('--result-file',help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.source_worker:
        from sources.worker import cli
        return cli(args.source_worker,args.state_root,args.result_file)
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication,QMessageBox
    from core.runtime import configure_logging,select_state_root
    from ui.app import AppManager
    from ui.instance import InstanceChannel
    root = Path(__file__).resolve().parent
    install_root = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else root
    state_root = select_state_root(install_root)
    smoke_directory = tempfile.TemporaryDirectory(prefix='jingliu-smoke-') if args.smoke_test else None
    if smoke_directory:
        state_root = Path(smoke_directory.name)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("JingliuPet")
    app.setOrganizationName("LocalJingliu")
    try:
        configure_logging(state_root)
        channel = None
        if not args.smoke_test:
            install_id = hashlib.sha256(str(install_root).casefold().encode()).hexdigest()[:16]
            channel = InstanceChannel('jingliu-pet-'+install_id)
            if not channel.claim_or_notify('preview' if args.preview else 'pet'):
                return 0
            app.aboutToQuit.connect(channel.close)
        manager = AppManager(root, state_root, enable_sources=not args.smoke_test)
        if channel:
            channel.command_received.connect(lambda command: manager.show_inspector() if command == 'preview' else manager.show_pet())
        if args.preview:
            manager.show_inspector()
        else:
            manager.show_pet()
        if args.smoke_test:
            manager.show_pet()
            manager.show_inspector()
            QTimer.singleShot(300, lambda: manager.session.play("wave"))
            QTimer.singleShot(750, lambda: manager.session.play("ice"))
            QTimer.singleShot(1200, lambda: manager.session.set_paused(True))
            QTimer.singleShot(1400, lambda: manager.session.set_paused(False))
            QTimer.singleShot(2000, manager.quit)
        logging.info("Started rig/action viewer; preview=%s", args.preview)
        result = app.exec()
        logging.info("Clean exit")
        logging.shutdown()
        if smoke_directory:
            smoke_directory.cleanup()
        return result
    except Exception:
        logging.exception("Startup failure")
        QMessageBox.critical(None, "镜流启动失败", "请查看项目 logs/jingliu.log。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
