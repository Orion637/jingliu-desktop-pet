"""Portable preferences. Invalid or unwritable configuration is nonfatal."""
from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path


@dataclass
class Settings:
    width: int = 420
    x: int | None = None
    y: int | None = None
    weapon: str = 'slender'
    follow_cursor: bool = True
    hide_in_fullscreen: bool = True

    @classmethod
    def load(cls, path):
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError('Settings root must be an object')
        except FileNotFoundError:
            return cls()
        except (OSError, ValueError) as error:
            logging.warning('Preferences unavailable; using defaults: %s', error)
            return cls()
        result = cls()
        width = data.get('width')
        if type(width) is int and 280 <= width <= 640:
            result.width = width
        for key in ('x', 'y'):
            value = data.get(key)
            if type(value) is int and -100000 <= value <= 100000:
                setattr(result, key, value)
        if data.get('weapon') in ('slender', 'ice', 'none'):
            result.weapon = data['weapon']
        if type(data.get('follow_cursor')) is bool:
            result.follow_cursor = data['follow_cursor']
        if type(data.get('hide_in_fullscreen')) is bool:
            result.hide_in_fullscreen=data['hide_in_fullscreen']
        return result

    def save(self, path):
        path = Path(path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix('.tmp')
            temporary.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(path)
            return True
        except OSError as error:
            logging.warning('Could not save preferences: %s', error)
            return False
