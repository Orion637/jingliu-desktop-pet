"""Package complete reproducible source/assets with no personal state or binaries."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'镜流桌宠_v1.1_源码.zip'
PREFIX=Path('JingliuPet-source')
SKIP={'__pycache__','.venv','.git','build','release','logs','cache','secure','workers','diagnostics','qa','config'}


def files():
    for name in ('main.py','README.md','requirements.txt','requirements-build.txt','.gitignore','启动桌宠.cmd','启动动作预览.cmd'):
        yield ROOT/name
    for name in ('core','ui','sources','assets','tests','tools','docs'):
        for path in (ROOT/name).rglob('*'):
            relative=path.relative_to(ROOT)
            if path.is_file() and not set(relative.parts)&SKIP and path.suffix!='.pyc':
                if relative.as_posix() not in ('docs/progress.md','docs/integration-ledger.md'):
                    yield path
    for name in ('hid_protocol_notes.md','g3m-protocol-2026-10-30.md','ROGDeltaTray-LICENSE.txt','LGPL-3.0-only.txt','GPL-3.0-only.txt'):
        yield ROOT/'research'/name


def package():
    hashes={}
    with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in sorted(set(files())):
            relative=path.relative_to(ROOT)
            archive.write(path,PREFIX/relative)
            hashes[relative.as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        archive.writestr(str(PREFIX/'SOURCE-MANIFEST.json'),json.dumps(hashes,ensure_ascii=False,indent=2))
        archive.writestr(str(PREFIX/'源码使用说明.txt'),
            '镜流桌宠 v1.1 完整源码\n\n'
            'Windows 安装 Python 3.12，然后在源码目录运行：\n'
            'py -3.12 -m venv .venv\n'
            '.venv\\Scripts\\python.exe -m pip install -r requirements.txt\n'
            '.venv\\Scripts\\python.exe main.py\n\n'
            '动作预览：.venv\\Scripts\\python.exe main.py --preview\n'
            '测试：.venv\\Scripts\\python.exe -m unittest discover -s tests -v\n'
            '重新打包：先安装 requirements-build.txt，再运行 tools/build_windows.py。\n'
            'G3M Pro 需切到 2.4G 并唤醒。全屏隐藏默认开启，可从右键菜单关闭。\n'
            '源码包包含运行素材、构建工具及许可证，不含虚拟环境、程序二进制、个人配置、API Key、日志或会话缓存。\n'
            '详细说明见 README.md 和 docs/integration-guide.md。\n')
    with zipfile.ZipFile(ARCHIVE) as archive:
        assert archive.testzip() is None
        assert str(PREFIX/'core/fullscreen.py').replace('\\','/') in archive.namelist()
        assert str(PREFIX/'sources/g3m.py').replace('\\','/') in archive.namelist()
        assert not any(set(Path(name).parts)&SKIP for name in archive.namelist())
    print(json.dumps(dict(archive=ARCHIVE.name,source_files=len(hashes),bytes=ARCHIVE.stat().st_size)))


if __name__=='__main__':
    package()
