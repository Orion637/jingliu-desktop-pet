"""DeepSeek API credentials: Windows user DPAPI, environment, explicit DSH API-key ref.

Account-platform/browser tokens are deliberately never resolved as API keys.
No secret value appears in configuration, logging or process arguments.
"""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import re


def valid_key(value):
    return isinstance(value, str) and re.fullmatch(r'sk-[A-Za-z0-9_-]{12,256}', value) is not None


def _crypt(data, decrypt=False):
    if os.name != 'nt':
        raise OSError('Windows secure storage is required')
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise OSError('Secure credential operation failed')
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(target.data)


def save_key(root, value):
    if not valid_key(value):
        raise ValueError('Invalid API key format')
    path = Path(root)/'secure/deepseek.dpapi'
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _crypt(value.encode('utf-8'))
    temporary = path.with_suffix('.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def read_saved_key(root):
    try:
        data = (Path(root)/'secure/deepseek.dpapi').read_bytes()
        if len(data) > 16384:
            return None
        key = _crypt(data, decrypt=True).decode('utf-8')
        return key if valid_key(key) else None
    except (OSError, ValueError, UnicodeError):
        return None


def clear_key(root):
    (Path(root)/'secure/deepseek.dpapi').unlink(missing_ok=True)
    (Path(root)/'cache/balance.json').unlink(missing_ok=True)


def resolve_key(root, dsh_home):
    saved = read_saved_key(root)
    if saved:
        return saved
    value = os.environ.get('DEEPSEEK_API_KEY')
    if valid_key(value):
        return value
    try:
        import yaml
        path = Path(dsh_home)/'.credentials.yaml'
        if path.stat().st_size > 1024*1024:
            return None
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        value = data.get('refs', {}).get('DEEPSEEK_API_KEY')
        if valid_key(value):
            return value
    except (OSError, ValueError, AttributeError, yaml.YAMLError):
        pass
    return None
