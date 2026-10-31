"""Independent QProcess workers with bounded output, deadlines and shutdown."""
from dataclasses import dataclass, field
import json
from pathlib import Path
import sys
import time
import uuid

from PySide6.QtCore import QObject,QProcess,QTimer,Signal
from sources.config import SourceConfig


@dataclass
class Job:
    process: QProcess
    timer: QTimer
    output: bytearray = field(default_factory=bytearray)
    result_path: Path | None = None
    failure: str | None = None


class SourceSupervisor(QObject):
    updated = Signal(str,dict)
    INTERVALS = dict(rog=15000,dsh=4000,balance=60000,g3m=15000)
    DEADLINES = dict(rog=3500,dsh=8000,balance=8500,g3m=4000)

    def __init__(self,state_root,parent=None,command_factory=None):
        super().__init__(parent)
        self.state_root = Path(state_root)
        self.jobs,self.snapshots,self.pollers = {},{},[]
        self.command_factory = command_factory
        self.closed = False

    def start(self):
        self.closed = False
        if not SourceConfig.load(self.state_root).enabled:
            for kind in self.INTERVALS:
                self.publish(kind,dict(status='unavailable',code='disabled'))
            return
        for i,(kind,interval) in enumerate(self.INTERVALS.items()):
            timer = QTimer(self)
            timer.setInterval(interval)
            timer.timeout.connect(lambda k=kind:self.launch(k))
            timer.start()
            self.pollers.append(timer)
            QTimer.singleShot(80+i*120,lambda k=kind:self.launch(k))

    def refresh(self):
        if SourceConfig.load(self.state_root).enabled:
            for kind in self.INTERVALS:
                self.launch(kind)

    def publish(self,kind,result):
        result = dict(result)
        result['observed_at'] = time.time()
        self.snapshots[kind] = result
        self.updated.emit(kind,result)

    def launch(self,kind,timeout_ms=None):
        if self.closed or kind in self.jobs:
            return
        process,timer = QProcess(self),QTimer(self)
        timer.setSingleShot(True)
        job = Job(process,timer)
        if self.command_factory:
            command = self.command_factory(kind)
        else:
            job.result_path = self.state_root/'workers'/(kind+'-'+uuid.uuid4().hex+'.json')
            job.result_path.parent.mkdir(parents=True,exist_ok=True)
            command = [sys.executable]
            if not getattr(sys,'frozen',False):
                command.append(str(Path(__file__).resolve().parents[1]/'main.py'))
            command += ['--source-worker',kind,'--state-root',str(self.state_root),'--result-file',str(job.result_path)]
        self.jobs[kind] = job
        process.setProgram(command[0])
        process.setArguments(command[1:])
        process.readyReadStandardOutput.connect(lambda:self.read(kind,job))
        process.readyReadStandardError.connect(lambda:process.readAllStandardError())
        process.finished.connect(lambda exit_code,exit_status:self.finish(kind,job,exit_code))
        process.errorOccurred.connect(lambda error:self.process_error(kind,job,error))
        timer.timeout.connect(lambda:self.fail(kind,job,'timeout'))
        timer.start(timeout_ms or self.DEADLINES[kind])
        process.start()

    def read(self,kind,job):
        data = bytes(job.process.readAllStandardOutput())
        if len(job.output)+len(data)>65536:
            self.fail(kind,job,'invalid_output')
        else:
            job.output.extend(data)

    def fail(self,kind,job,code):
        if self.jobs.get(kind) is not job:
            return
        job.failure = code
        job.process.kill()
        if job.process.state() == QProcess.ProcessState.NotRunning:
            self.finish(kind,job,-1)

    def process_error(self,kind,job,error):
        if error == QProcess.ProcessError.FailedToStart:
            job.failure = 'start_failed'
            self.finish(kind,job,-1)

    def finish(self,kind,job,exit_code):
        if self.jobs.get(kind) is not job:
            return
        remaining = bytes(job.process.readAllStandardOutput())
        if len(job.output)+len(remaining)>65536:
            job.failure = 'invalid_output'
        else:
            job.output.extend(remaining)
        job.timer.stop()
        try:
            if job.failure or exit_code != 0:
                raise ValueError('Failed worker')
            payload = bytes(job.output)
            if job.result_path:
                if job.result_path.stat().st_size > 65536:
                    raise ValueError('Oversized result')
                payload = job.result_path.read_bytes()
            result = json.loads(payload)
            if not isinstance(result,dict) or result.get('status') not in ('ok','unavailable','error'):
                raise ValueError('Invalid snapshot')
        except (ValueError,OSError,TypeError):
            result = dict(status='error',code=job.failure or 'invalid_output')
        if job.result_path:
            job.result_path.unlink(missing_ok=True)
        self.jobs.pop(kind,None)
        job.timer.deleteLater()
        job.process.deleteLater()
        if not self.closed:
            self.publish(kind,result)

    def stop(self):
        self.closed = True
        for timer in self.pollers:
            timer.stop()
            timer.deleteLater()
        self.pollers.clear()
        for kind,job in list(self.jobs.items()):
            job.timer.stop()
            job.process.kill()
        # Kill all first, then reap. Four hung drivers do not multiply deadlines.
        for kind,job in list(self.jobs.items()):
            job.process.waitForFinished(1200)
            if kind in self.jobs:
                self.finish(kind,job,-1)
        self.jobs.clear()
