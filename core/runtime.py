"""Writable state selection and optional rotating logging."""
import hashlib
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import tempfile


def select_state_root(preferred, fallback=None):
    preferred = Path(preferred)
    suffix = hashlib.sha256(str(preferred.resolve()).casefold().encode()).hexdigest()[:16]
    fallback = Path(fallback) if fallback else Path(os.environ.get('LOCALAPPDATA') or tempfile.gettempdir())/'JingliuPet'/suffix
    for path in (preferred,fallback):
        try:
            path.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryFile(dir=path):
                pass
            return path
        except OSError:
            continue
    return Path(tempfile.mkdtemp(prefix='jingliu-state-'))


def configure_logging(state_root):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    try:
        path = Path(state_root)/'logs/jingliu.log'
        path.parent.mkdir(parents=True,exist_ok=True)
        handler = RotatingFileHandler(path,maxBytes=2*1024*1024,backupCount=2,encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(handler)
        return True
    except OSError:
        logger.addHandler(logging.NullHandler())
        return False
