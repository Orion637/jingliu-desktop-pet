"""Read-only foreground/monitor detection. All rectangle coordinates are native pixels."""
import ctypes
from ctypes import wintypes
import os


def covers_monitor(bounds,monitor,tolerance=2):
    return all(abs(a-b)<=tolerance for a,b in zip(bounds,monitor))


def should_hide(*,bounds,monitor,pid,own_pid,class_name,visible,minimized,cloaked,zoomed,style,same_monitor):
    if not visible or minimized or cloaked or pid==own_pid or not same_monitor:
        return False
    if class_name in ('Progman','WorkerW','Shell_TrayWnd','Shell_SecondaryTrayWnd'):
        return False
    if zoomed and style&0x00C00000:
        return False
    return covers_monitor(bounds,monitor)


def pet_visibility(*,requested,enabled,fullscreen):
    return requested and not (enabled and fullscreen)


class WindowsFullscreen:
    def __init__(self):
        self.user=ctypes.WinDLL('user32',use_last_error=True)
        self.dwm=ctypes.WinDLL('dwmapi',use_last_error=True)
        self.user.GetForegroundWindow.restype=wintypes.HWND
        self.user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
        self.user.GetClassNameW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
        self.user.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
        for name in ('IsWindowVisible','IsIconic','IsZoomed'):
            getattr(self.user,name).argtypes=[wintypes.HWND]
        self.user.MonitorFromWindow.argtypes=[wintypes.HWND,wintypes.DWORD]
        self.user.MonitorFromWindow.restype=wintypes.HANDLE
        self.user.GetMonitorInfoW.argtypes=[wintypes.HANDLE,ctypes.c_void_p]
        self.user.GetWindowLongW.argtypes=[wintypes.HWND,ctypes.c_int]
        self.user.GetWindowLongW.restype=wintypes.LONG
        self.dwm.DwmGetWindowAttribute.argtypes=[wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
        self.dwm.DwmGetWindowAttribute.restype=wintypes.LONG

    def active(self,target_hwnd=None):
        foreground=self.user.GetForegroundWindow()
        return self.window_is_fullscreen(foreground,target_hwnd)

    def window_is_fullscreen(self,foreground,target_hwnd=None):
        if not foreground: return False
        monitor=self.user.MonitorFromWindow(foreground,2)
        if not monitor: return False
        class MonitorInfo(ctypes.Structure):
            _fields_=[('size',wintypes.DWORD),('monitor',wintypes.RECT),('work',wintypes.RECT),('flags',wintypes.DWORD)]
        info=MonitorInfo()
        info.size=ctypes.sizeof(info)
        if not self.user.GetMonitorInfoW(monitor,ctypes.byref(info)): return False
        bounds=wintypes.RECT()
        if self.dwm.DwmGetWindowAttribute(foreground,9,ctypes.byref(bounds),ctypes.sizeof(bounds))!=0:
            if not self.user.GetWindowRect(foreground,ctypes.byref(bounds)): return False
        cloaked=wintypes.DWORD()
        self.dwm.DwmGetWindowAttribute(foreground,14,ctypes.byref(cloaked),ctypes.sizeof(cloaked))
        pid=wintypes.DWORD()
        self.user.GetWindowThreadProcessId(foreground,ctypes.byref(pid))
        name=ctypes.create_unicode_buffer(256)
        self.user.GetClassNameW(foreground,name,256)
        rect=lambda r:(r.left,r.top,r.right,r.bottom)
        return should_hide(bounds=rect(bounds),monitor=rect(info.monitor),pid=pid.value,own_pid=os.getpid(),
            class_name=name.value,visible=bool(self.user.IsWindowVisible(foreground)),
            minimized=bool(self.user.IsIconic(foreground)),cloaked=bool(cloaked.value),
            zoomed=bool(self.user.IsZoomed(foreground)),style=self.user.GetWindowLongW(foreground,-16),
            same_monitor=not target_hwnd or self.user.MonitorFromWindow(target_hwnd,2)==monitor)


_backend=None


def foreground_fullscreen(target_hwnd=None):
    global _backend
    if os.name!='nt': return False
    try:
        if _backend is None: _backend=WindowsFullscreen()
        return _backend.active(target_hwnd)
    except (OSError,ValueError):
        return False
