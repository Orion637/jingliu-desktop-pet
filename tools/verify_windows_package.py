"""Relocate and execute the frozen GUI/worker bundle without leaking credentials."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import zipfile

import psutil

ROOT = Path(__file__).resolve().parents[1]


def verify():
    report = {}
    archive = ROOT/'镜流桌宠_v1.1_Windows.zip'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert not any(set(Path(name).parts)&{'secure','config','logs','cache','workers','diagnostics'} for name in z.namelist())
        report['archive_integrity_and_private_state_exclusion'] = 'pass'
    with tempfile.TemporaryDirectory(prefix='relocated-镜流-',dir=ROOT/'qa') as directory:
        stage = Path(directory)/'不同目录'
        shutil.copytree(ROOT/'release/JingliuPet',stage,
            ignore=shutil.ignore_patterns('logs','config','cache','secure','workers','diagnostics'))
        executable = stage/'JingliuPet.exe'
        result = subprocess.run([str(executable),'--smoke-test'],cwd=stage,timeout=20)
        assert result.returncode == 0,result.returncode
        report['relocated_native_smoke'] = 'pass'
        state = Path(directory)/'worker-state'
        results = {}
        for kind in ('rog','dsh','balance','g3m'):
            destination = state/'workers'/(kind+'.json')
            child = subprocess.run([str(executable),'--source-worker',kind,'--state-root',str(state),
                                    '--result-file',str(destination)],cwd=stage,timeout=16)
            assert child.returncode == 0,(kind,child.returncode)
            data = json.loads(destination.read_text(encoding='utf-8'))
            assert data['status'] in ('ok','unavailable'),(kind,data.get('code'))
            results[kind] = dict(status=data['status'],code=data.get('code'))
            if kind in ('rog','g3m'):
                results[kind]['percent']=data.get('percent')
        report['frozen_workers'] = results
        children = [subprocess.Popen([str(executable),'--preview'],cwd=stage) for _ in range(5)]
        owned = []
        try:
            deadline=time.monotonic()+20
            live=children
            while time.monotonic()<deadline:
                time.sleep(.2)
                live=[child for child in children if child.poll() is None]
                if len(live)==1: break
            assert len(live)==1,len(live)
            assert all(child.poll() in (0,None) for child in children)
            report['five_concurrent_launches_one_owner'] = 'pass'
        finally:
            # This check's isolated process tree only; normal Qt shutdown is tested separately.
            for process in psutil.process_iter(['exe']):
                try:
                    if process.info['exe'] and Path(process.info['exe']).resolve() == executable.resolve():
                        owned.append(process)
                except (OSError,psutil.Error):
                    pass
            for process in owned:
                try: process.terminate()
                except psutil.Error: pass
            psutil.wait_procs(owned,timeout=8)
            for child in children:
                child.wait(timeout=5)
    (ROOT/'qa/package-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    verify()
