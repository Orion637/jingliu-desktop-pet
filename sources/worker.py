"""One source request per subprocess; failure output never includes raw exceptions."""
import json
from pathlib import Path

from sources import balance, dsh, g3m, rog
from sources.config import SourceConfig, write_json

SOURCES = dict(rog=rog.run,dsh=dsh.run,g3m=g3m.run,balance=balance.run)


def execute(kind, root):
    try:
        config = SourceConfig.load(root)
        if not config.enabled:
            return dict(status='unavailable',code='disabled')
        result = SOURCES[kind](config,Path(root))
        encoded = json.dumps(result,allow_nan=False)
        if len(encoded.encode('utf-8')) > 60000:
            raise ValueError('Oversized snapshot')
        return result
    except Exception:
        return dict(status='error',code='source_failed')


def cli(kind, state_root, result_file):
    root = Path(state_root).resolve()
    destination = Path(result_file).resolve()
    destination.relative_to((root/'workers').resolve())
    write_json(destination,execute(kind,root))
    return 0
