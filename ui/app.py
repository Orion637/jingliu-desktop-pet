"""Interactive rig inspector and transparent standalone desktop pet."""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QCursor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget,
    QMenu, QPushButton, QSlider, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from core.animation import Animator
from core.face import automatic_blink
from core.settings import Settings
from core.weapon import WeaponSwap, action_effect
from core.monitor_state import derive_state
from core.window_geometry import recover_geometry
from core.interaction import random_action
from core.fullscreen import foreground_fullscreen,pet_visibility
from ui.renderer import Renderer
from ui.sources import SourceSupervisor
from ui.source_panel import SourcePanel, STATE_LABELS, hardware_text


class Session(QObject):
    changed = Signal()

    def __init__(self, root):
        super().__init__()
        self.renderer = Renderer(root / "assets/jingliu/rig.json")
        data = json.loads((root / "assets/jingliu/animations.json").read_text(encoding="utf-8"))
        self.clips = data["clips"]
        self.animator = Animator(self.clips, transition=data["transition_seconds"])
        self.clock = 0.
        self.last_time = time.perf_counter()
        self.paused, self.bones = False, False
        self._weapon = "slender"
        self.swap = WeaponSwap('slender')
        self.look_target = 0.
        self.look_offset = 0.
        self.follow_cursor = True
        self.last_interaction = None
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

    @property
    def weapon(self):
        return self._weapon

    @weapon.setter
    def weapon(self, value):
        self.set_weapon(value)

    def set_weapon(self, value, animate=True):
        if value not in ('slender','ice','none'):
            raise ValueError('Unknown weapon')
        if not animate:
            self._weapon, self.swap = value, WeaponSwap(value)
            return
        if self.swap.request(value, self.clock):
            self._weapon = value
            # Menus and selector both stage the same held-sword gesture.
            self.animator.play('ice' if value == 'ice' else 'slender' if value == 'slender' else 'idle', self.clock)
            self.changed.emit()

    def tick(self):
        now = time.perf_counter()
        dt, self.last_time = now-self.last_time, now
        if not self.paused:
            self.clock += dt
            self.look_offset += (self.look_target-self.look_offset)*min(1., dt*5)
        self.changed.emit()

    def play(self, name):
        self.animator.play(name, self.clock)
        if self.clips[name].get("weapon"):
            self.weapon = self.clips[name]["weapon"]
        self.changed.emit()

    def interact(self):
        name = random_action(self.clips,last=self.last_interaction,current=self.animator.name)
        self.last_interaction = name
        self.play(name)
        return name

    def current(self):
        pose = self.animator.sample(self.clock)
        face = pose.setdefault("head", {})
        face["blink"] = max(face.get("blink", 0), automatic_blink(self.clock))
        if self.follow_cursor:
            channel = pose.setdefault("head", {})
            channel["rotation"] = channel.get("rotation", 0)+self.look_offset*1.8
            channel["x"] = channel.get("x", 0)+self.look_offset*5
        clip = self.clips[self.animator.name]
        pose['_fx'] = action_effect(clip, self.clock-self.animator.started)
        transition = self.swap.sample(self.clock)
        if transition['active']:
            pose['_fx']['swap'] = transition['phase']
        pose['_weapon_weights'] = transition['weights'] if clip.get('weapon_visible', True) else {}
        pose['_weapon_reveal'] = transition['reveal']
        weapon = self.weapon if clip.get("weapon_visible", True) else "none"
        return pose, weapon

    def set_paused(self, paused):
        self.paused = paused
        self.last_time = time.perf_counter()
        self.changed.emit()


class Stage(QWidget):
    def __init__(self, session, desktop=False):
        super().__init__()
        self.session, self.desktop = session, desktop
        self.setMouseTracking(True)
        self.setMinimumSize(280, 360)
        self.session.changed.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.desktop:
            painter.fillRect(self.rect(), QColor("#edf3fc"))
            painter.setPen(QColor("#c8d7e9"))
            for x in range(0, self.width(), 28):
                for y in range(0, self.height(), 28):
                    painter.drawPoint(x, y)
        pose, weapon = self.session.current()
        self.session.renderer.draw_fitted(painter, QRectF(self.rect()), pose, weapon, self.session.bones)
        if self.desktop:
            self.manager.draw_badge(painter,self.rect())
        painter.end()

    def mouseMoveEvent(self, event):
        self.session.look_target = max(-1., min(1., (event.position().x()/max(1, self.width())-.5)*2))

    def leaveEvent(self, event):
        self.session.look_target = 0.

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.session.interact()


class PetWindow(Stage):
    def __init__(self, manager):
        super().__init__(manager.session, desktop=True)
        self.manager = manager
        self.setMinimumSize(1,1)
        self.setWindowTitle("镜流桌宠")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.resize(420, 472)
        self.press_global = None
        self.dragging = False
        self.press_position = QPoint()
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right()-self.width()-35, screen.bottom()-self.height()-25)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_global = event.globalPosition().toPoint()
            self.press_position = self.pos()
            self.dragging = False

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.press_global is not None and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint()-self.press_global
            if not self.dragging and delta.manhattanLength() >= QApplication.startDragDistance():
                self.dragging = True
                self.session.play("drag")
            if self.dragging:
                self.move(self.press_position+delta)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self.press_global is None:
            return
        if self.dragging:
            self.session.play("idle")
            self.keep_on_screen()
            self.manager.save_state()
        else:
            if event.position().y() >= self.height()-58:
                self.manager.show_sources()
            else:
                super().mouseReleaseEvent(event)
        self.press_global = None
        self.dragging = False

    def keep_on_screen(self):
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        area = screen.availableGeometry()
        x,y,width,height = recover_geometry(self.x(),self.y(),self.width(),self.height(),
                                           (area.x(),area.y(),area.width(),area.height()))
        self.resize(width,height)
        self.move(x,y)

    def contextMenuEvent(self, event):
        self.manager.menu().exec(event.globalPos())

    def mouseDoubleClickEvent(self, event):
        self.manager.show_inspector()

    def closeEvent(self, event):
        self.manager.quit()


class Inspector(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager, self.session = manager, manager.session
        self.setWindowTitle("镜流 · 骨骼与动作预览")
        self.resize(980, 800)
        self.setMinimumSize(820, 650)
        self.setStyleSheet("""
            QWidget { font-family: 'Microsoft YaHei UI'; font-size: 13px; color: #23354c; }
            Inspector { background: #f7f9fd; }
            QPushButton { background: #e6effb; border: 1px solid #cbd9ec; padding: 9px; border-radius: 6px; }
            QPushButton:hover { background: #d8e8fc; }
            QListWidget { background: white; border: 1px solid #d9e2ee; border-radius: 6px; padding: 5px; }
            QListWidget::item { padding: 8px 5px; }
            QListWidget::item:selected { background: #dceafe; color: #1f487a; border-radius: 4px; }
            QComboBox { background: white; padding: 6px; border: 1px solid #cbd9ec; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        stage = Stage(self.session)
        layout.addWidget(stage, 1)
        side = QVBoxLayout()
        title = QLabel("镜流 / JINGLIU")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        side.addWidget(title)
        meta = QLabel("18 个骨骼 · 4 组柔性网格\n14 个动作 · 冰霜换剑")
        meta.setStyleSheet("color: #64758a; line-height: 1.6;")
        side.addWidget(meta)
        self.actions = QListWidget()
        self.action_names = list(self.session.clips)
        for clip in self.session.clips.values():
            self.actions.addItem(clip["label"])
        self.actions.setCurrentRow(0)
        self.actions.itemClicked.connect(lambda item: self.session.play(self.action_names[self.actions.row(item)]))
        side.addWidget(self.actions, 1)
        side.addWidget(QLabel("武器"))
        self.weapon_box = QComboBox()
        self.weapon_box.addItems(["细剑", "宽刃冰剑", "空手"])
        self.weapon_box.currentIndexChanged.connect(self.choose_weapon)
        side.addWidget(self.weapon_box)
        swap = QPushButton('切换武器 · 冰霜凝刃')
        swap.clicked.connect(lambda: self.session.set_weapon('slender' if self.session.weapon == 'ice' else 'ice'))
        side.addWidget(swap)
        self.bones_box = QCheckBox("显示骨骼与关节")
        self.bones_box.toggled.connect(lambda checked: setattr(self.session, "bones", checked))
        side.addWidget(self.bones_box)
        follow = QCheckBox("鼠标轻微引导视线")
        follow.setChecked(self.session.follow_cursor)
        follow.toggled.connect(lambda checked: setattr(self.session, "follow_cursor", checked))
        side.addWidget(follow)
        row = QHBoxLayout()
        self.pause = QPushButton("暂停")
        self.pause.clicked.connect(lambda: self.session.set_paused(not self.session.paused))
        row.addWidget(self.pause)
        replay = QPushButton("重播所选")
        replay.clicked.connect(lambda: self.session.play(self.action_names[self.actions.currentRow()]))
        row.addWidget(replay)
        side.addLayout(row)
        pet_button = QPushButton("放到桌面")
        pet_button.clicked.connect(self.manager.show_pet)
        side.addWidget(pet_button)
        source_button = QPushButton('设备电量 / DSH 状态')
        source_button.clicked.connect(self.manager.show_sources)
        side.addWidget(source_button)
        self.status = QLabel()
        self.status.setStyleSheet("color: #64758a; font-size: 11px;")
        self.status.setWordWrap(True)
        side.addWidget(self.status)
        side_widget = QWidget()
        side_widget.setFixedWidth(264)
        side_widget.setLayout(side)
        layout.addWidget(side_widget)
        self.session.changed.connect(self.sync)

    def choose_weapon(self, index):
        self.session.weapon = ("slender", "ice", "none")[index]

    def sync(self):
        self.pause.setText("继续" if self.session.paused else "暂停")
        self.weapon_box.blockSignals(True)
        self.weapon_box.setCurrentIndex(("slender", "ice", "none").index(self.session.weapon))
        self.weapon_box.blockSignals(False)
        self.bones_box.blockSignals(True)
        self.bones_box.setChecked(self.session.bones)
        self.bones_box.blockSignals(False)
        self.status.setText("当前："+self.session.clips[self.session.animator.name]["label"]+"\n桌面：左键互动 / 按住拖动 / 右键菜单")

    def closeEvent(self, event):
        if self.manager.pet and self.manager.pet_requested:
            event.accept()
        else:
            self.manager.quit()


class AppManager:
    def __init__(self, root, state_root=None, enable_sources=True):
        self.state_root = Path(state_root or root)
        self.settings_path = (state_root or root) / 'config/settings.json'
        self.settings = Settings.load(self.settings_path)
        self.session = Session(root)
        self.session.set_weapon(self.settings.weapon, animate=False)
        self.session.follow_cursor = self.settings.follow_cursor
        self.pet = None
        self.pet_requested=False
        self.hidden_for_fullscreen=False
        self.fullscreen_probe=foreground_fullscreen
        self.fullscreen_timer=QTimer()
        self.fullscreen_timer.setInterval(500)
        self.fullscreen_timer.timeout.connect(self.update_fullscreen)
        self.fullscreen_timer.start()
        self.inspector = None
        self.tray = None
        self.source_panel = None
        self.monitor_state = 'idle'
        self.sources = SourceSupervisor(self.state_root)
        self.sources.updated.connect(self.source_changed)
        if enable_sources:
            self.sources.start()
        icon = QIcon(QPixmap(str(root / "assets/jingliu/parts/head.png")))
        QApplication.instance().setWindowIcon(icon)
        QApplication.instance().setQuitOnLastWindowClosed(False)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(icon)
            self.tray.setToolTip("镜流桌宠 · 右键切换动作")
            self.tray.setContextMenu(self.menu())
            self.tray.activated.connect(self.tray_activated)
            self.tray.show()
        QApplication.instance().screenRemoved.connect(lambda screen: QTimer.singleShot(0, self.recover_pet))
        QApplication.instance().screenAdded.connect(lambda screen:self.bind_screen(screen))
        for screen in QApplication.screens():
            self.bind_screen(screen)
        QApplication.instance().aboutToQuit.connect(self.save_state)
        QApplication.instance().aboutToQuit.connect(self.sources.stop)
        QApplication.instance().aboutToQuit.connect(self.fullscreen_timer.stop)

    def update_fullscreen(self):
        if self.pet is None or not self.pet_requested: return
        fullscreen=self.fullscreen_probe(int(self.pet.winId())) if self.settings.hide_in_fullscreen else False
        visible=pet_visibility(requested=self.pet_requested,enabled=self.settings.hide_in_fullscreen,fullscreen=fullscreen)
        self.hidden_for_fullscreen=not visible
        if visible and not self.pet.isVisible():
            self.pet.show()
            self.pet.keep_on_screen()
        elif not visible and self.pet.isVisible():
            self.pet.hide()

    def set_fullscreen_hiding(self,enabled):
        self.settings.hide_in_fullscreen=enabled
        self.update_fullscreen()
        self.save_state()

    def bind_screen(self,screen):
        screen.availableGeometryChanged.connect(lambda area:self.recover_pet())
        screen.logicalDotsPerInchChanged.connect(lambda dpi:self.recover_pet())

    def source_changed(self,kind,result):
        self.monitor_state = derive_state(self.sources.snapshots)
        if self.pet:
            self.pet.update()
        if self.tray:
            self.tray.setToolTip('镜流 · '+STATE_LABELS[self.monitor_state])

    def draw_badge(self,painter,rect):
        snapshots = self.sources.snapshots
        text = '耳机 '+hardware_text(snapshots.get('rog',{}))+'    鼠标 '+hardware_text(snapshots.get('g3m',{}))
        badge = QRectF(8,rect.height()-54,min(310,rect.width()-16),46)
        colors = dict(idle='#26354c',working='#235e8a',low_battery='#895c24',error='#79464c')
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(colors[self.monitor_state]))
        painter.drawRoundedRect(badge,9,9)
        painter.setPen(QColor('#f3f7ff'))
        painter.setFont(QFont('Microsoft YaHei UI',9))
        painter.drawText(badge.adjusted(10,3,-8,-20),Qt.AlignmentFlag.AlignVCenter,text)
        painter.setPen(QColor('#ccdbea'))
        painter.drawText(badge.adjusted(10,23,-8,-2),Qt.AlignmentFlag.AlignVCenter,STATE_LABELS[self.monitor_state]+' · 点此查看')

    def show_sources(self):
        if self.source_panel is None:
            self.source_panel = SourcePanel(self)
        self.source_panel.show()
        self.source_panel.raise_()
        self.source_panel.activateWindow()

    def restart_sources(self):
        self.sources.stop()
        self.sources.snapshots.clear()
        self.sources.start()

    def recover_pet(self):
        if self.pet:
            self.pet.keep_on_screen()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_pet()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_inspector()

    def show_pet(self):
        self.pet_requested=True
        if self.pet is None:
            self.pet = PetWindow(self)
            self.pet.resize(self.settings.width, round(self.settings.width*1840/1640))
            if self.settings.x is not None and self.settings.y is not None:
                self.pet.move(self.settings.x, self.settings.y)
        self.update_fullscreen()
        self.pet.keep_on_screen()
        self.save_state()

    def save_state(self):
        self.settings.weapon = self.session.weapon
        self.settings.follow_cursor = self.session.follow_cursor
        if self.pet:
            self.settings.width = self.pet.width()
            self.settings.x, self.settings.y = self.pet.x(), self.pet.y()
        self.settings.save(self.settings_path)

    def show_inspector(self):
        if self.inspector is None:
            self.inspector = Inspector(self)
        self.inspector.show()
        self.inspector.raise_()
        self.inspector.activateWindow()

    def resize_pet(self, width):
        self.show_pet()
        self.pet.resize(width, round(width*1840/1640))
        self.pet.keep_on_screen()
        self.save_state()

    def menu(self):
        menu = QMenu()
        menu.addAction("动作预览与骨骼", self.show_inspector)
        menu.addAction("显示桌宠", self.show_pet)
        menu.addAction('设备电量 / DSH 状态',self.show_sources)
        fullscreen=menu.addAction('全屏时自动隐藏')
        fullscreen.setCheckable(True)
        fullscreen.setChecked(self.settings.hide_in_fullscreen)
        fullscreen.toggled.connect(self.set_fullscreen_hiding)
        menu.aboutToShow.connect(lambda:fullscreen.setChecked(self.settings.hide_in_fullscreen))
        actions = menu.addMenu("切换动作")
        for name, clip in self.session.clips.items():
            actions.addAction(clip["label"], lambda checked=False, n=name: self.session.play(n))
        weapons = menu.addMenu("武器")
        for label, value in [("细剑", "slender"), ("宽刃冰剑", "ice"), ("空手", "none")]:
            weapons.addAction(label, lambda checked=False, w=value: setattr(self.session, "weapon", w))
        sizes = menu.addMenu("大小")
        for label, width in [("小", 320), ("中", 420), ("大", 540)]:
            sizes.addAction(label, lambda checked=False, w=width: self.resize_pet(w))
        pause = menu.addAction("暂停 / 继续")
        pause.triggered.connect(lambda: self.session.set_paused(not self.session.paused))
        menu.addSeparator()
        menu.addAction("退出镜流", self.quit)
        return menu

    def quit(self):
        self.session.timer.stop()
        self.fullscreen_timer.stop()
        self.sources.stop()
        if self.tray:
            self.tray.hide()
        QApplication.instance().quit()
