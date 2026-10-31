"""One local process per installation; later launches request a visible window."""
import hashlib
import tempfile
import time
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QLockFile
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class InstanceChannel(QObject):
    command_received = Signal(str)

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.server.newConnection.connect(self.accept)
        self.connections = {}
        lock_name = hashlib.sha256(name.encode()).hexdigest()
        self.lock = QLockFile(str(Path(tempfile.gettempdir())/('jingliu-'+lock_name+'.lock')))
        self.lock.setStaleLockTime(0)
        self.owns_lock = False

    def notify(self, command, timeout):
        socket = QLocalSocket(self)
        try:
            deadline = time.monotonic()+timeout/1000
            socket.connectToServer(self.name)
            if not socket.waitForConnected(timeout):
                return False
            payload = (command+'\n').encode('ascii')
            if socket.write(payload) != len(payload):
                return False
            socket.flush()
            while time.monotonic()<deadline:
                remaining=max(1,int((deadline-time.monotonic())*1000))
                if socket.bytesAvailable() or socket.waitForReadyRead(remaining):
                    return bytes(socket.readAll()).startswith(b'ok\n')
                if socket.state()==QLocalSocket.LocalSocketState.UnconnectedState:
                    return bytes(socket.readAll()).startswith(b'ok\n')
            return False
        finally:
            socket.close()
            socket.deleteLater()

    def claim_or_notify(self, command):
        if command not in ('pet', 'preview'):
            raise ValueError('Invalid window command')
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            if self.lock.tryLock(0):
                self.owns_lock = True
                if self.server.listen(self.name):
                    return True
                self.lock.unlock()
                self.owns_lock = False
                raise RuntimeError('Cannot start local instance channel')
            # Wait for owner initialization as well as pipe creation, with an ACK.
            if self.notify(command,500):
                return False
            time.sleep(.025)
        raise RuntimeError('Running instance did not respond')

    def accept(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            self.connections[socket] = bytearray()
            socket.readyRead.connect(lambda s=socket: self.read(s))
            socket.disconnected.connect(lambda s=socket: self.discard(s))
            self.read(socket)

    def read(self, socket):
        if socket not in self.connections:
            return
        data = self.connections[socket]
        data.extend(bytes(socket.readAll()))
        if len(data) > 64:
            socket.abort()
            return
        if b'\n' in data:
            command = bytes(data).split(b'\n', 1)[0].decode('ascii', errors='ignore')
            self.connections[socket] = bytearray()
            if command in ('pet', 'preview'):
                self.command_received.emit(command)
                socket.write(b'ok\n')
                socket.flush()
            socket.disconnectFromServer()

    def discard(self, socket):
        self.connections.pop(socket, None)
        socket.deleteLater()

    def close(self):
        for socket in list(self.connections):
            socket.abort()
        self.server.close()
        if self.owns_lock:
            self.lock.unlock()
            self.owns_lock = False
