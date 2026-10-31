"""Reproducible local one-folder Windows build; original artwork is untouched."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import shutil
import ssl
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets/jingliu'
BUILD = ROOT / 'build'
STAGE = BUILD / 'runtime-data/assets/jingliu'


def build():
    STAGE.mkdir(parents=True, exist_ok=True)
    rig = json.loads((ASSETS / 'rig.json').read_text(encoding='utf-8'))
    files = {item['file'] for item in rig['layers'] if item.get('file')}
    files.update(('rig.json', 'animations.json', 'SOURCES.md'))
    hashes = {}
    for name in sorted(files):
        source = (ASSETS / name).resolve()
        source.relative_to(ASSETS.resolve())
        target = STAGE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        hashes[name] = hashlib.sha256(source.read_bytes()).hexdigest()

    # Format/canvas conversion of the existing cutout, no repainting.
    from PIL import Image, ImageOps
    with Image.open(ASSETS / 'parts/head.png') as head:
        head = head.crop(head.getchannel('A').getbbox())
        head = ImageOps.contain(head, (240, 240))
        icon = Image.new('RGBA', (256, 256))
        icon.alpha_composite(head, ((256-head.width)//2, (256-head.height)//2))
        icon.save(BUILD / 'jingliu.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])

    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--windowed',
               '--name', 'JingliuPet', '--distpath', str(ROOT / 'release'),
               '--workpath', str(BUILD / 'pyinstaller'), '--specpath', str(BUILD / 'spec'),
               '--icon', str(BUILD / 'jingliu.ico'), '--add-data', str(STAGE.parent)+':assets',
               '--exclude-module', 'tkinter', '--exclude-module', 'imageio_ffmpeg',
               str(ROOT / 'main.py')]
    # This Python runtime's ssl.SSLContext loads a bundled rejected-CA list.
    # Preserve its trust policy in the frozen stdlib's directory as well.
    ssl_policy = Path(ssl.__file__).parent/'codex-rejected-cas.pem'
    if ssl_policy.is_file():
        command[3:3] = ['--add-data',str(ssl_policy)+':.']
    with (BUILD / 'build.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Build failed: see build/build.log')
    bundle = ROOT / 'release/JingliuPet'
    notices = bundle / 'licenses'
    notices.mkdir(exist_ok=True)
    for package in ('PySide6-Essentials', 'shiboken6', 'Pillow', 'PyInstaller', 'hidapi', 'zstandard', 'psutil', 'PyYAML'):
        distribution = importlib.metadata.distribution(package)
        for relative in distribution.files or []:
            if any(word in str(relative).lower() for word in ('license', 'copying', 'copyright')):
                source = Path(distribution.locate_file(relative))
                if source.is_file():
                    target = notices / package / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    if python_license.exists():
        shutil.copy2(python_license, notices / 'Python-LICENSE.txt')
    shutil.copy2(ASSETS / 'SOURCES.md', bundle / '素材来源.md')
    shutil.copy2(ROOT/'research/ROGDeltaTray-LICENSE.txt',notices/'ROGDeltaTray-MIT.txt')
    g3m_notes=(ROOT/'research/g3m-protocol-2026-10-30.md').read_text(encoding='utf-8')
    g3m_notice=g3m_notes.split('```text')[-1].split('```')[0].strip()+'\n'
    (notices/'G3M-Battery-MIT.txt').write_text(g3m_notice,encoding='utf-8')
    for name in ('LGPL-3.0-only.txt','GPL-3.0-only.txt'):
        shutil.copy2(ROOT/'research'/name,notices/name)
    (notices/'Qt-Notice.txt').write_text(
        'This application uses unmodified Qt/PySide6/shiboken6 6.8.3 shared libraries.\n'
        'Qt/PySide6 are available under LGPLv3/GPL/commercial terms; LGPLv3 text and its GPLv3 terms are included.\n'
        'Shared Qt DLLs and PySide6 modules remain replaceable in _internal.\n'
        'Sources: https://code.qt.io/cgit/pyside/pyside-setup.git/ (tag v6.8.3)\n'
        'Qt sources: https://download.qt.io/archive/qt/6.8/6.8.3/single/\n',encoding='utf-8')
    shutil.copy2(ROOT/'research/hid_protocol_notes.md',bundle/'硬件协议与来源.md')
    shutil.copy2(ROOT/'research/g3m-protocol-2026-10-30.md',bundle/'G3M电量协议与来源.md')
    shutil.copy2(ROOT/'docs/integration-guide.md',bundle/'设备与DSH使用说明.md')
    (bundle / '使用说明.txt').write_text(
        '镜流桌宠 · 完整整合版\n\n'
        '双击 JingliuPet.exe 启动；动作面板用 打开动作预览.cmd。\n'
        '左键互动、按住拖动、右键菜单、托盘常驻。\n'
        '单击人物随机做动作；全屏应用在桌宠所在屏幕运行时自动隐藏，退出全屏后恢复。\n'
        '右键「全屏时自动隐藏」可以关闭或启用此功能，默认启用。\n'
        '重复启动会唤回已有窗口。武器、大小、位置在 config/settings.json 保存。\n'
        '退出用桌宠/托盘右键的「退出镜流」。\n\n'
        '请完整解压并保留 _internal 文件夹，不要只移动 EXE。\n'
        '本地个人使用；人物与同人素材来源见 素材来源.md，软件依赖许可见 licenses。\n'
        '点击桌宠底部角标或右键「设备电量 / DSH 状态」打开监控面板。\n'
        '支持 ROG Delta II 接收器电量、DSH 只读日志与官方余额查询。\n'
        '已支持 Telink 320F:706E 的漫步者 G3M Pro 2.4G 电量读取；鼠标需开机且处于 2.4G 模式。\n'
        '设备未连接、休眠或未响应时显示 N/A。非零充电状态尚不能可靠区分时显示未知。\n'
        'API Key 在数据源设置中输入，使用 Windows 当前用户加密保存。\n'
        '安装目录不可写时自动使用 LocalAppData/JingliuPet。\n'
        '详细说明见 设备与DSH使用说明.md。\n', encoding='utf-8-sig')
    (bundle / '打开动作预览.cmd').write_text(
        '@echo off\r\ncd /d "%~dp0"\r\nstart "" "%~dp0JingliuPet.exe" --preview\r\n', encoding='ascii')
    (BUILD / 'runtime_asset_hashes.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    archive = ROOT / '镜流桌宠_v1.1_Windows.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(bundle.rglob('*')):
            if path.is_file() and not set(path.relative_to(bundle).parts)&{'logs','config','cache','secure','workers','diagnostics'}:
                z.write(path, Path('JingliuPet') / path.relative_to(bundle))
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError('ZIP integrity check failed')
    print(f'Built {bundle / "JingliuPet.exe"}', flush=True)
    print(f'ZIP {archive.stat().st_size:,} bytes; {len(files)} asset/data files', flush=True)


if __name__ == '__main__':
    build()
