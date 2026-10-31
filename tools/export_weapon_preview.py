"""Focused deterministic preview of the real swap renderer and sleeve motion."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor,QImage,QPainter
from PySide6.QtWidgets import QApplication
from core.animation import sample_clip
from core.face import automatic_blink
from core.weapon import WeaponSwap,action_effect
from tools.export_preview import pillow,caption
from ui.renderer import Renderer


def main():
    app=QApplication.instance() or QApplication([])
    r=Renderer(ROOT/'assets/jingliu/rig.json')
    clips=json.loads((ROOT/'assets/jingliu/animations.json').read_text(encoding='utf-8'))['clips']
    output=ROOT/'preview'
    r.frame({},(800,944),background='#edf2fa').save(str(output/'镜流_握剑与飘带修正.png'))
    swap=WeaponSwap('slender')
    frames=[]
    import imageio_ffmpeg
    command=[imageio_ffmpeg.get_ffmpeg_exe(),'-y','-f','rawvideo','-pix_fmt','rgba','-s','1000x680','-r','24','-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart',str(output/'镜流_冰霜换剑与月弧.mp4')]
    with (ROOT/'qa/weapon_video.log').open('w',encoding='utf-8') as log:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=log)
        try:
            for i in range(120):
                t=i/24
                if i==12:
                    swap.request('ice',t)
                if i==72:
                    swap.request('slender',t)
                action='idle' if t<.5 else 'ice' if t<3 else 'slender'
                elapsed=t if t<.5 else t-.5 if t<3 else t-3
                pose=sample_clip(clips[action],elapsed)
                pose.setdefault('head',{})['blink']=automatic_blink(t)
                state=swap.sample(t)
                pose['_weapon_weights']=state['weights']
                pose['_weapon_reveal']=state['reveal']
                pose['_fx']=action_effect(clips[action],elapsed)
                if state['active']:
                    pose['_fx']['swap']=state['phase']
                moon=sample_clip(clips['moon_arc'],min(t,clips['moon_arc']['duration']))
                moon['_fx']=action_effect(clips['moon_arc'],t)
                moon.setdefault('head',{})['blink']=automatic_blink(t)
                canvas=QImage(1000,680,QImage.Format.Format_RGBA8888)
                canvas.fill(QColor('#dce6f2'))
                p=QPainter(canvas)
                for index,(current,weapon,title) in enumerate(((pose,swap.target,'冰霜换剑 · 柄到剑尖凝成'),(moon,'ice','月弧挽剑 · 袖带跟随'))):
                    box=QRectF(index*500+3,3,494,674)
                    p.fillRect(box,QColor('#edf2fa'))
                    caption(p,box,title)
                    r.draw_fitted(p,box.adjusted(0,36,0,0),current,weapon)
                p.end()
                process.stdin.write(bytes(canvas.bits()))
                if i%2==0:
                    small=canvas.scaled(740,503)
                    frames.append(pillow(small).convert('RGB').quantize(colors=224))
                if i==40:
                    canvas.save(str(output/'镜流_换剑动作总览.png'))
        finally:
            process.stdin.close()
        if process.wait()!=0:
            raise RuntimeError('Weapon preview encoder failed')
    frames[0].save(output/'镜流_冰霜换剑与月弧.gif',save_all=True,append_images=frames[1:],duration=83,loop=0,optimize=False,disposal=2)
    r.viewport=[-90,785,420,330]
    detail=QImage(1000,440,QImage.Format.Format_ARGB32_Premultiplied)
    detail.fill(QColor('#edf2fa'))
    p=QPainter(detail)
    for index,weapon in enumerate(('slender','ice')):
        box=QRectF(index*500,0,500,440)
        caption(p,box,'细剑握持' if index==0 else '冰剑握持')
        r.draw_fitted(p,box.adjusted(0,30,0,0),{},weapon)
    p.end()
    detail.save(str(output/'镜流_两把武器握持细节.png'))
    print('Exported grip detail, 60-frame GIF and 5-second MP4',flush=True)


if __name__=='__main__':
    main()
