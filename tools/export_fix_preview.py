"""Focused review of the corrected collar/shoulder and continuous blink."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import json
from PySide6.QtWidgets import QApplication
from core.animation import sample_clip
from core.face import automatic_blink
from tools.export_preview import pillow
from ui.renderer import Renderer


app = QApplication.instance() or QApplication([])
renderer = Renderer(ROOT / 'assets/jingliu/rig.json')
clips = json.loads((ROOT / 'assets/jingliu/animations.json').read_text(encoding='utf-8'))['clips']
output = ROOT / 'preview'
renderer.frame({}, (700, 826), background='#edf2fa').save(str(output / '镜流_颈肩修正.png'))
frames = []
for i in range(72):
    t = i/25
    pose = sample_clip(clips['idle'], t)
    pose.setdefault('head', {})['blink'] = automatic_blink(t+2.2)
    image = renderer.frame(pose, (600, 708), background='#edf2fa')
    frames.append(pillow(image).convert('RGB').quantize(colors=224))
frames[0].save(output / '镜流_颈肩修正与眨眼.gif', save_all=True, append_images=frames[1:],
               duration=40, loop=0, optimize=False, disposal=2)
print('Focused preview exported: 72 frames / 25fps')
