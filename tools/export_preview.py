"""Export QA stills, a contact sheet, GIF and MP4 from the live rig renderer."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication

from core.animation import sample_clip
from core.face import automatic_blink
from core.weapon import action_effect
from ui.renderer import Renderer


def pillow(image):
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return Image.frombytes("RGBA", (rgba.width(), rgba.height()), bytes(rgba.bits()), "raw", "RGBA", rgba.bytesPerLine())


def caption(painter, rect, text, subtitle=None):
    painter.setPen(QColor("#23354c"))
    painter.setFont(QFont("Microsoft YaHei UI", 12, QFont.Weight.DemiBold))
    painter.drawText(rect.adjusted(14, 8, -8, -8), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, text)
    if subtitle:
        painter.setFont(QFont("Microsoft YaHei UI", 9))
        painter.setPen(QColor("#64758a"))
        painter.drawText(rect.adjusted(14, 32, -8, -8), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, subtitle)


def draw_card(painter, renderer, clip, t, rect, label=True):
    painter.fillRect(rect, QColor("#f1f5fb"))
    if label:
        caption(painter, rect, clip["label"])
    area = rect.adjusted(0, 36 if label else 0, 0, -3)
    weapon = clip.get("weapon", "slender") if clip.get("weapon_visible", True) else "none"
    pose = sample_clip(clip, t)
    face = pose.setdefault("head", {})
    face["blink"] = max(face.get("blink", 0), automatic_blink(t))
    pose['_fx'] = action_effect(clip, t)
    renderer.draw_fitted(painter, area, pose, weapon)


def export(stills_only=False):
    app = QApplication.instance() or QApplication([])
    renderer = Renderer(ROOT / "assets/jingliu/rig.json")
    clips = json.loads((ROOT / "assets/jingliu/animations.json").read_text(encoding="utf-8"))["clips"]
    output = ROOT / "preview"
    output.mkdir(exist_ok=True)
    renderer.frame({}, (768, 906)).save(str(output / "镜流_绑定静态.png"))
    renderer.frame({}, (768, 906), bones=True, background="#f1f5fb").save(str(output / "镜流_骨骼绑定.png"))

    count = len(clips)
    sheet = QImage(1200, math.ceil(count/4)*440, QImage.Format.Format_ARGB32_Premultiplied)
    sheet.fill(QColor("#dce6f2"))
    painter = QPainter(sheet)
    for index, (name, clip) in enumerate(clips.items()):
        rect = QRectF(index % 4*300+3, index//4*440+3, 294, 434)
        draw_card(painter, renderer, clip, clip["duration"]*.43, rect)
    painter.end()
    sheet.save(str(output / f"镜流_{count}动作总览.png"))

    bounds_issues, bounds_report = [], {}
    vx, vy, vw, vh = renderer.viewport
    for name, clip in clips.items():
        bounds_report[name] = []
        for weapon in ("slender", "ice"):
            selected = clip.get("weapon", weapon) if clip.get("weapon_visible", True) else "none"
            for i in range(61):
                pose = sample_clip(clip, clip["duration"]*i/60)
                bounds = renderer.pose_bounds(pose, selected)
                if bounds[0] < vx or bounds[1] < vy or bounds[2] > vx+vw or bounds[3] > vy+vh:
                    bounds_issues.append(dict(action=name, variant=selected, sample=i, bounds=bounds))
            bounds_report[name].append(selected)
    timings = []
    for i in range(90):
        started = time.perf_counter()
        renderer.frame(sample_clip(clips["idle"], i/30), (400, 472))
        timings.append((time.perf_counter()-started)*1000)
    hashes = json.loads((ROOT / "qa/source_hashes.json").read_text())
    preserved = all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected for path, expected in hashes.items())
    report = dict(bones=len(renderer.rig.bones), layers=len(renderer.layers), actions=len(clips),
                  sampled_poses=count*2*61, viewport=renderer.viewport, bounds_issues=bounds_issues,
                  source_pngs_preserved=preserved, render_mean_ms=round(sum(timings)/len(timings), 2),
                  render_max_ms=round(max(timings), 2), check="Rendered from FK/weighted meshes, not image sequences")
    (ROOT / "qa/rig_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)
    if bounds_issues:
        raise RuntimeError(f"{len(bounds_issues)} out-of-viewport poses; inspect rig before export")
    if not preserved:
        raise RuntimeError("Source artwork changed")
    if stills_only:
        return

    # Four simultaneous clips provide a small inline animated preview.
    gif_frames = []
    for frame in range(80):
        canvas = QImage(560, 730, QImage.Format.Format_ARGB32_Premultiplied)
        canvas.fill(QColor("#dce6f2"))
        painter = QPainter(canvas)
        for index, name in enumerate(("idle", "blink", "wave", "ice")):
            clip = clips[name]
            t = frame/80*clip["duration"]
            draw_card(painter, renderer, clip, t, QRectF(index%2*280+2, index//2*365+2, 276, 361))
        painter.end()
        gif_frames.append(pillow(canvas).convert("RGB").quantize(colors=192))
    gif_frames[0].save(output / "镜流_动画预览.gif", save_all=True, append_images=gif_frames[1:], duration=62, loop=0, optimize=False, disposal=2)
    print("GIF exported", flush=True)

    import imageio_ffmpeg
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
               "-s", "720x850", "-r", "24", "-i", "-", "-an", "-c:v", "libx264",
               "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(output / "镜流_全动作演示.mp4")]
    with (ROOT / "qa/ffmpeg.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=log)
        try:
            for index, (name, clip) in enumerate(clips.items()):
                duration = clip["duration"]
                for frame in range(math.ceil(duration*24)):
                    canvas = QImage(720, 850, QImage.Format.Format_RGBA8888)
                    canvas.fill(QColor("#e7eef8"))
                    painter = QPainter(canvas)
                    caption(painter, QRectF(15, 12, 700, 65), f"{index+1:02d} / {count}   {clip['label']}", "镜流 · 二维骨骼实时驱动 / 高马尾 / 原紫色裙摆")
                    draw_card(painter, renderer, clip, frame/24, QRectF(0, 65, 720, 780), label=False)
                    painter.end()
                    process.stdin.write(bytes(canvas.bits()))
                print(f"Video: {name}", flush=True)
        finally:
            process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError("Video encoder failed; inspect qa/ffmpeg.log")
    print("MP4 exported", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stills-only", action="store_true")
    export(parser.parse_args().stills_only)
