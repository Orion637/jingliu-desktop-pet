"""Hardware badges, DSH activity and secure configuration, without log content."""
from datetime import datetime,timedelta,timezone
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox,QDialog,QFormLayout,QFrame,QGroupBox,QHBoxLayout,
    QLabel,QLineEdit,QMessageBox,QProgressBar,QPushButton,QScrollArea,QVBoxLayout,QWidget)

from sources.config import SourceConfig
from sources.credentials import clear_key,save_key

STATE_LABELS = dict(idle='独立待机',working='DSH 正在工作',low_battery='设备电量低',error='数据源暂时异常')
CODES = dict(receiver_missing='未检测到接收器',headset_offline='耳机离线或未返回电量',
    protocol_unverified='已识别设备，电量协议尚未验证',key_required='请配置 DeepSeek API Key',
    balance_request_failed='余额查询失败，60 秒后重试',source_failed='读取失败，下次自动重试',
    timeout='读取超时，已结束本次读取',start_failed='后台读取未能启动',invalid_output='读取结果无效',
    sessions_missing='未找到 DSH 会话目录',disabled='监控已关闭',
    battery_no_response='接收器已连接 · 鼠标暂未响应')


def hardware_text(snapshot):
    percent = snapshot.get('percent')
    if snapshot.get('status') == 'ok' and type(percent) is int:
        return str(percent)+'%'+(' · 充电中' if snapshot.get('charging') else '')
    return 'N/A'


class SourceSettings(QDialog):
    def __init__(self,manager,parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle('数据源设置')
        self.resize(570,280)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        config = SourceConfig.load(manager.state_root)
        self.enabled = QCheckBox('启用设备电量和 DSH 监控')
        self.enabled.setChecked(config.enabled)
        layout.addWidget(self.enabled)
        self.home = QLineEdit(config.dsh_home)
        self.executable = QLineEdit(config.dsh_executable)
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText('留空保留现有凭证；输入新的 sk-… 密钥')
        form.addRow('DSH 主目录',self.home)
        form.addRow('DSH 程序完整路径',self.executable)
        form.addRow('DeepSeek API Key',self.key)
        layout.addLayout(form)
        note = QLabel('API Key 使用当前 Windows 用户加密保存。也可读取 DEEPSEEK_API_KEY 环境变量或 DSH 中明确的 API Key。账户登录令牌不会用作 API Key。')
        note.setWordWrap(True)
        layout.addWidget(note)
        row = QHBoxLayout()
        clear = QPushButton('删除本应用保存的 Key')
        clear.clicked.connect(self.clear)
        row.addWidget(clear)
        row.addStretch()
        save = QPushButton('保存')
        save.clicked.connect(self.save)
        row.addWidget(save)
        layout.addLayout(row)

    def clear(self):
        try:
            clear_key(self.manager.state_root)
            self.key.clear()
            self.manager.restart_sources()
        except OSError:
            QMessageBox.warning(self,'无法删除','凭证文件不可写。')

    def save(self):
        try:
            value = self.key.text().strip()
            if value:
                save_key(self.manager.state_root,value)
                self.key.clear()
            SourceConfig(self.home.text().strip(),self.executable.text().strip(),self.enabled.isChecked()).save(self.manager.state_root)
            self.manager.restart_sources()
            self.accept()
        except (OSError,ValueError):
            QMessageBox.warning(self,'设置未保存','请检查路径和 API Key 格式，或 Windows 加密存储是否可用。')


class DeviceCard(QFrame):
    def __init__(self,title,subtitle):
        super().__init__()
        self.setObjectName('deviceCard')
        box=QVBoxLayout(self)
        box.setContentsMargins(18,17,18,17)
        box.setSpacing(9)
        row=QHBoxLayout()
        name=QLabel(title)
        name.setObjectName('cardTitle')
        name.setWordWrap(True)
        row.addWidget(name,1)
        self.connection=QLabel('检测中')
        self.connection.setObjectName('connection')
        row.addWidget(self.connection)
        box.addLayout(row)
        hint=QLabel(subtitle)
        hint.setObjectName('muted')
        box.addWidget(hint)
        self.percent=QLabel('—')
        self.percent.setObjectName('batteryValue')
        box.addWidget(self.percent)
        self.bar=QProgressBar()
        self.bar.setRange(0,100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(7)
        box.addWidget(self.bar)
        self.detail=QLabel('正在连接设备…')
        self.detail.setWordWrap(True)
        self.detail.setMinimumHeight(32)
        self.detail.setObjectName('muted')
        box.addWidget(self.detail)

    def update_snapshot(self,snapshot):
        value=snapshot.get('percent')
        valid=snapshot.get('status')=='ok' and type(value) is int and 0<=value<=100
        accent='#ffba73' if valid and value<=20 else '#7ddcf6' if valid else '#7e8ca9'
        self.percent.setText(str(value)+'%' if valid else 'N/A' if snapshot else '—')
        self.percent.setStyleSheet('color:'+accent+';')
        self.bar.setValue(value if valid else 0)
        self.bar.setStyleSheet('QProgressBar::chunk {background:'+accent+';border-radius:3px;}')
        self.connection.setText('已连接' if valid else '读取异常' if snapshot.get('status')=='error' else '未连接' if snapshot else '检测中')
        self.connection.setStyleSheet('color:'+accent+';background:#1c283e;border-radius:7px;padding:3px 6px;')
        if valid:
            self.detail.setText('正在充电' if snapshot.get('charging') is True else
                               '电池供电' if snapshot.get('charging') is False else '电量已更新 · 充电状态未知')
        else:
            self.detail.setText(CODES.get(snapshot.get('code'),'正在检测接收器…'))


class SourcePanel(QWidget):
    def __init__(self,manager):
        super().__init__()
        self.manager = manager
        self.setWindowTitle('镜流 · 设备与 DSH 状态')
        self.resize(660,590)
        self.setMinimumSize(480,420)
        self.setObjectName('sourcePanel')
        self.setStyleSheet('''
            QWidget {font-family:'Microsoft YaHei UI';font-size:12px;color:#e8edf9;}
            QWidget#sourcePanel, QWidget#panelBody {background:#101624;}
            QDialog {background:#101624;}
            QLineEdit {background:#1c283f;color:#e8edf9;border:1px solid #3a4b6a;border-radius:6px;padding:7px;selection-background-color:#45678c;}
            QScrollArea {border:0;background:transparent;}
            QFrame#deviceCard, QFrame#balanceCard {background:#1a2336;border:1px solid #2d3b55;border-radius:14px;}
            QLabel#cardTitle {font-size:14px;font-weight:600;}
            QLabel#muted {color:#95a6c2;font-size:11px;}
            QLabel#batteryValue {font-size:39px;font-weight:600;padding:2px 0;}
            QLabel#connection {font-size:10px;}
            QProgressBar {border:0;border-radius:3px;background:#2d3950;height:7px;}
            QProgressBar::chunk {background:#89c8f7;border-radius:3px;}
            QGroupBox {background:#1a2336;border:1px solid #2d3b55;border-radius:14px;margin-top:10px;padding:20px 15px 12px;}
            QGroupBox::title {subcontrol-origin:margin;left:16px;padding:0 5px;color:#b6c8e8;}
            QPushButton {background:#222e46;border:1px solid #3a4b6a;border-radius:8px;padding:9px 17px;color:#dce8fa;}
            QPushButton:hover {background:#30405f;border-color:#769bd2;}
            QPushButton#primaryButton {background:#91c8ee;border:1px solid #aad9fa;color:#142238;font-weight:600;}
            QPushButton#primaryButton:hover {background:#b1ddfa;}
            QScrollBar:vertical {background:#151e2f;width:8px;border-radius:4px;}
            QScrollBar::handle:vertical {background:#3d4d68;min-height:24px;border-radius:4px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}
        ''')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        scroll=QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(scroll)
        body=QWidget()
        body.setObjectName('panelBody')
        scroll.setWidget(body)
        layout=QVBoxLayout(body)
        layout.setContentsMargins(24,22,24,20)
        layout.setSpacing(16)
        header=QHBoxLayout()
        heading=QVBoxLayout()
        title=QLabel('镜流 · 设备状态')
        title.setStyleSheet('font-size:23px;font-weight:600;')
        heading.addWidget(title)
        subtitle=QLabel('电量、余额与任务状态')
        subtitle.setObjectName('muted')
        heading.addWidget(subtitle)
        header.addLayout(heading,1)
        self.state = QLabel()
        self.state.setStyleSheet('background:#26324d;color:#b8c9eb;border-radius:9px;padding:7px 10px;font-size:11px;')
        header.addWidget(self.state,0,Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)
        cards=QHBoxLayout()
        cards.setSpacing(14)
        self.device_cards={}
        self.hardware = {}
        for kind,label,caption in (('rog','ROG 棱镜 2','HEADSET / 耳机'),('g3m','漫步者 G3M Pro','MOUSE / 鼠标')):
            card=DeviceCard(label,caption)
            self.device_cards[kind]=card
            self.hardware[kind]=card.percent
            cards.addWidget(card,1)
        layout.addLayout(cards)
        balance_card=QFrame()
        balance_card.setObjectName('balanceCard')
        balance_row=QHBoxLayout(balance_card)
        balance_row.setContentsMargins(18,14,18,14)
        balance_heading=QVBoxLayout()
        balance_title=QLabel('DeepSeek 账户余额')
        balance_title.setObjectName('cardTitle')
        balance_heading.addWidget(balance_title)
        self.balance_hint=QLabel('官方账户 · 每 60 秒更新')
        self.balance_hint.setObjectName('muted')
        self.balance_hint.setWordWrap(True)
        balance_heading.addWidget(self.balance_hint)
        balance_row.addLayout(balance_heading,1)
        self.balance = QLabel('N/A')
        self.balance.setStyleSheet('font-size:22px;font-weight:600;color:#cfbef8;')
        self.balance.setWordWrap(True)
        balance_row.addWidget(self.balance,1,Qt.AlignmentFlag.AlignRight)
        layout.addWidget(balance_card)
        self.offline = QLabel('DSH 未运行 · 镜流保持独立互动')
        self.offline.setStyleSheet('background:#192237;border:1px solid #2b3852;border-radius:9px;padding:12px;color:#a8b9d5;')
        self.offline.setWordWrap(True)
        layout.addWidget(self.offline)
        self.dsh_box = QGroupBox('DSH 只读状态')
        dsh_layout = QVBoxLayout(self.dsh_box)
        self.activity = QLabel()
        self.progress = QProgressBar()
        self.tokens = QLabel()
        self.tokens.setWordWrap(True)
        self.activity.setWordWrap(True)
        dsh_layout.addWidget(self.activity)
        dsh_layout.addWidget(self.progress)
        dsh_layout.addWidget(self.tokens)
        layout.addWidget(self.dsh_box)
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setObjectName('muted')
        layout.addWidget(self.note)
        row = QHBoxLayout()
        self.updated_label=QLabel('正在检测…')
        self.updated_label.setObjectName('muted')
        row.addWidget(self.updated_label,1)
        refresh = QPushButton('刷新状态')
        refresh.clicked.connect(manager.sources.refresh)
        settings = QPushButton('数据源设置')
        settings.setObjectName('primaryButton')
        settings.clicked.connect(lambda:SourceSettings(manager,self).exec())
        row.addWidget(refresh)
        row.addWidget(settings)
        layout.addLayout(row)
        manager.sources.updated.connect(self.update_snapshot)
        self.update_snapshot()

    def update_snapshot(self,*args):
        snapshots = self.manager.sources.snapshots
        self.state.setText(STATE_LABELS[self.manager.monitor_state])
        for kind,card in self.device_cards.items():
            card.update_snapshot(snapshots.get(kind,{}))
        balance = snapshots.get('balance',{})
        self.balance.setText(' / '.join(('¥' if item['currency']=='CNY' else '$')+' '+item['total'] for item in balance.get('balances',[])) or 'N/A')
        self.balance_hint.setText('官方账户 · 每 60 秒更新' if balance.get('status')=='ok' else CODES.get(balance.get('code'),'正在连接官方账户…'))
        observed=max((item.get('observed_at',0) for item in snapshots.values()),default=0)
        self.updated_label.setText('更新于 '+datetime.fromtimestamp(observed,timezone(timedelta(hours=8))).strftime('%H:%M:%S') if observed else '正在检测…')
        dsh = snapshots.get('dsh',{})
        running = bool(dsh.get('running'))
        self.dsh_box.setVisible(running)
        self.offline.setVisible(not running)
        self.offline.setText('DSH 未运行 · 镜流保持独立互动'+('（监控已关闭）' if dsh.get('code') == 'disabled' else ''))
        labels = dict(idle='等待任务',working='处理中',tool='工具执行中',approval='等待操作确认',retrying='正在重试',completed='当前轮次已结束',error='当前轮次出错')
        activity = dsh.get('activity','idle')
        self.activity.setText(f"{labels.get(activity,'等待任务')} · 轮次 {dsh.get('turn',0)} / 步骤 {dsh.get('step',0)}\n"
            f"工具 {dsh.get('pending_tools',0)} · 后台作业 {dsh.get('pending_jobs',0)} · 待确认 {dsh.get('pending_approvals',0)}")
        active = activity in ('working','tool','approval','retrying')
        self.progress.setRange(0,0 if active else 1)
        self.progress.setValue(1 if activity == 'completed' else 0)
        self.progress.setFormat('进度未知' if active else labels.get(activity,'等待任务'))
        current,day = dsh.get('session_tokens',{}),dsh.get('day_tokens',{})
        self.tokens.setText(f"本会话 {current.get('total',0):,} token · 今日 {day.get('total',0):,} token\n"
            f"会话：输入 {current.get('input',0):,} / 输出 {current.get('output',0):,} / 缓存读取 {current.get('cache_read',0):,} / 缓存写入 {current.get('cache_write',0):,}")
        self.note.setText(('正在增量索引历史日志；统计会继续更新。\n' if dsh.get('indexing') else '')+
            ('部分日志无法读取，统计可能不完整。\n' if dsh.get('unreadable_files') else '')+
            ('已达到最新 4,096 份日志的覆盖上限，较早日志未计入。\n' if dsh.get('coverage_limited') else '')+
            ('Token 按北京时间统计，包含缓存用量。\n' if running else '')+
            '设备离线显示 N/A。全屏时可自动隐藏桌宠，退出全屏后恢复。')

    def closeEvent(self,event):
        event.accept()
