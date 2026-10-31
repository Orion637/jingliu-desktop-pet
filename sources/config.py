from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


@dataclass
class SourceConfig:
    dsh_home: str = field(default_factory=lambda: os.environ.get('DSH_HOME') or str(Path.home()/'.dsh'))
    dsh_executable: str = 'E:\\DeepSeek Harness\\DeepSeek Harness.exe'
    enabled: bool = True

    @classmethod
    def load(cls, state_root):
        result = cls()
        try:
            data = json.loads((Path(state_root)/'config/sources.json').read_text(encoding='utf-8'))
            for key in ('dsh_home', 'dsh_executable'):
                value = data.get(key)
                if isinstance(value, str) and len(value) <= 2048 and '\x00' not in value:
                    setattr(result, key, value)
            if type(data.get('enabled')) is bool:
                result.enabled = data['enabled']
        except (OSError, ValueError, AttributeError):
            pass
        return result

    def save(self, state_root):
        write_json(Path(state_root)/'config/sources.json', asdict(self))
