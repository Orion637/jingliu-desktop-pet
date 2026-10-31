"""Authoring utility. Runtime reads JSON, never generated image frames."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets/jingliu"


def write(name, data):
    (ASSETS / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build():
    bones = [
        ("root", None, [440, 1470]),
        ("torso", "root", [440, 840]),
        ("neck", "torso", [430, 650]),
        ("head", "neck", [430, 611]),
        ("ponytail_root", "head", [581, 71]),
        ("ponytail_mid", "ponytail_root", [735, 471]),
        ("ponytail_tip", "ponytail_mid", [790, 841]),
        ("arm_left", "torso", [340, 690]),
        ("arm_right", "torso", [530, 688]),
        ("sleeve_root", "arm_right", [590, 811]),
        ("sleeve_mid", "sleeve_root", [655, 1010]),
        ("sleeve_tip", "sleeve_mid", [755, 1190]),
        ("skirt_root", "torso", [440, 1060]),
        ("skirt_tip", "skirt_root", [600, 1220]),
        ("leg_left", "torso", [356, 1090]),
        ("leg_right", "torso", [466, 1097]),
        ("tassel", "torso", [480, 935]),
        ("weapon", "arm_left", [164, 943]),
    ]
    layers = []

    def layer(id, file, bone, rect, z, **kwargs):
        layers.append(dict(id=id, file=file, bone=bone, rect=rect, z=z, **kwargs))

    layer("ponytail", "parts/ponytail.png", "ponytail_root", [469, 15, 549, 1102], 10,
          mesh={"rows": 14, "columns": 2, "chain": [[71, "ponytail_root"], [471, "ponytail_mid"], [906, "ponytail_tip"]]})
    layer("skirt", "parts/skirt_back.png", "skirt_root", [199, 1042, 777, 296], 20,
          mesh={"rows": 7, "columns": 2, "chain": [[1060, "skirt_root"], [1260, "skirt_tip"]]})
    layer("leg_left", "parts/leg_viewer_left.png", "leg_left", [257, 1058, 193, 397], 25)
    layer("leg_right", "parts/leg_viewer_right.png", "leg_right", [392, 1077, 174, 446], 26)
    layer("sleeve", "parts/sleeve_tail_viewer_right.png", "sleeve_root", [555, 805, 300, 490], 30,
          anchor_source=[350,350], anchor_world=[590,811],
          mesh={"rows": 16, "columns": 2, "chain": [[811, "sleeve_root"], [1010, "sleeve_mid"], [1250, "sleeve_tip"]]})
    layer("neck", None, "neck", [397, 606, 77, 68], 39, procedural_shape="neck",
          mesh={"rows": 6, "columns": 2, "chain": [[612, "head"], [650, "neck"]]})
    layer("torso", "parts/torso.png", "torso", [142, 615, 588, 545], 40)
    layer("sword_slender", "weapons/sword_slender_chibi.png", "weapon", [150, 540, 90, 480], 49,
          rest_rotation=-135, rest_pivot=[164,943], grip_source=[512,1190], grip_world=[164,943], texture_scale=.34,
          compact_handle=dict(start=1080,compression=.55,taper=.72),weapon="slender")
    layer("sword_ice", "weapons/sword_ice_chibi.png", "weapon", [109, 535, 185, 500], 49,
          rest_rotation=-135, rest_pivot=[164,943], grip_source=[512,1210], grip_world=[164,943], texture_scale=.34,
          compact_handle=dict(start=1100,compression=.55,taper=.72),weapon="ice")
    layer("arm_left", "parts/arm_viewer_left.png", "arm_left", [114, 674, 239, 304], 45)
    layer("grip_fingers", "parts/arm_viewer_left.png", "arm_left", [114,674,239,304], 50,
          mask_source=[[[305,1045],[335,1020],[376,1025],[397,1050],[378,1076],[378,1108],[346,1129],[307,1120],[295,1090]],
                       [[395,981],[442,994],[440,1056],[414,1092],[385,1111],[375,1082],[387,1047]]])
    layer("arm_right", "parts/arm_viewer_right.png", "arm_right", [337, 684, 285, 203], 55)
    layer("tassel", "parts/tassel.png", "tassel", [466, 900, 172, 134], 60)
    layer("head", "parts/head.png", "head", [72, 58, 702, 646], 65)

    write("rig.json", {
        "schema_version": 1, "canvas": [1024, 1536],
        "viewport": [-340, -180, 1640, 1840],
        "coordinates": "viewer-left/right, master-image coordinates, degrees clockwise",
        "notes": ["原 PNG 保留；按 alpha 包围盒在运行时取图。", "袖带由右臂带动；裙摆保持紫色。", "18 bones; 4 weighted meshes; procedural neck and eyelids."],
        "bones": [dict(id=id, parent=parent, pivot=pivot) for id, parent, pivot in bones],
        "layers": layers,
    })

    clips = {}

    def clip(id, label, duration, tracks, loop=False, weapon_visible=True, weapon=None):
        # Follow-through curves have different phases down each chain.
        for bone, amplitude, phase in [
            ("ponytail_root", 1.5, 0), ("ponytail_mid", 2.3, -.7), ("ponytail_tip", 3.4, -1.3),
            ("sleeve_mid", 2.8, -.5), ("sleeve_tip", 4.2, -1.1), ("skirt_tip", 1.3, -.8),
            ("tassel", 3.0, -.4),
        ]:
            key = bone+".rotation"
            if key not in tracks:
                keys = []
                for i in range(9):
                    t = duration*i/8
                    envelope = 1 if loop else math.sin(math.pi*i/8)
                    keys.append([round(t, 4), round(amplitude*math.sin(2*math.pi*i/8+phase)*envelope, 4)])
                tracks[key] = keys
        clips[id] = dict(label=label, duration=duration, loop=loop, tracks=tracks, weapon_visible=weapon_visible)
        if weapon:
            clips[id]["weapon"] = weapon

    clip("idle", "待机 · 呼吸浮动", 4, {
        "root.y": [[0, 0], [1, -9], [2, 0], [3, 6], [4, 0]],
        "head.rotation": [[0, 0], [1, -1.4], [2, 0], [3, 1.4], [4, 0]],
        "torso.sy": [[0, 1], [1, 1.006], [2, 1], [3, .996], [4, 1]],
        "arm_left.rotation": [[0, 0], [2, 1.6], [4, 0]],
        "arm_right.rotation": [[0, 0], [2, -1.4], [4, 0]],
    }, True)
    clip("look", "环顾 · 左右探看", 3.6, {
        "head.rotation": [[0, 0], [.8, -5], [1.5, -5], [2.3, 5], [3, 5], [3.6, 0]],
        "head.x": [[0, 0], [1, -12], [2.6, 12], [3.6, 0]],
        "torso.rotation": [[0, 0], [1, -1.5], [2.6, 1.5], [3.6, 0]],
    }, True)
    clip("tap", "点击 · 歪头回应", 1.3, {
        "head.rotation": [[0, 0], [.25, -9], [.65, 4], [1, -2], [1.3, 0]],
        "root.y": [[0, 0], [.2, -18], [.45, 5], [.8, -3], [1.3, 0]],
        "arm_right.rotation": [[0, 0], [.35, 7], [.8, -3], [1.3, 0]],
    })
    clip("headpat", "摸头 · 轻轻摇晃", 2.4, {
        "head.rotation": [[0, 0], [.45, 7], [.95, -5], [1.45, 5], [1.9, -3], [2.4, 0]],
        "torso.rotation": [[0, 0], [.7, 2], [1.4, -2], [2.4, 0]],
        "head.y": [[0, 0], [.4, 8], [1, 4], [1.6, 8], [2.4, 0]],
    })
    clip("wave", "招手 · 挥挥小手", 2.8, {
        "arm_left.rotation": [[0, 0], [.6, 60], [1, 45], [1.4, 62], [1.8, 45], [2.2, 60], [2.8, 0]],
        "head.rotation": [[0, 0], [.8, 4], [2, 4], [2.8, 0]],
        "torso.rotation": [[0, 0], [1.3, 2], [2.8, 0]],
    }, weapon_visible=False)
    clip("nod", "点头 · 收到啦", 1.9, {
        "head.rotation": [[0, 0], [.3, 6], [.6, -2], [.95, 6], [1.3, -2], [1.9, 0]],
        "head.y": [[0, 0], [.3, 12], [.6, -3], [.95, 12], [1.3, -3], [1.9, 0]],
    })
    clip("shake", "摇头 · 不可以哦", 1.9, {
        "head.rotation": [[0, 0], [.3, -6], [.65, 6], [1, -6], [1.35, 4], [1.9, 0]],
        "head.x": [[0, 0], [.3, -8], [.65, 8], [1, -8], [1.35, 6], [1.9, 0]],
    })
    clip("hop", "小跳 · 轻盈落地", 1.6, {
        "root.y": [[0, 0], [.22, 18], [.65, -95], [1.05, 12], [1.3, -8], [1.6, 0]],
        "torso.sy": [[0, 1], [.22, .98], [.6, 1.015], [1.05, .985], [1.6, 1]],
        "leg_left.rotation": [[0, 0], [.6, 7], [1, -3], [1.6, 0]],
        "leg_right.rotation": [[0, 0], [.6, -7], [1, 3], [1.6, 0]],
        "arm_left.rotation": [[0, 0], [.6, 9], [1.6, 0]],
    })
    clip("drag", "拖拽 · 晃晃手脚", 1.2, {
        "root.rotation": [[0, -2], [.3, 2], [.6, -2], [.9, 2], [1.2, -2]],
        "head.rotation": [[0, 2], [.3, -2], [.6, 2], [.9, -2], [1.2, 2]],
        "leg_left.rotation": [[0, -6], [.3, 8], [.6, -6], [.9, 8], [1.2, -6]],
        "leg_right.rotation": [[0, 8], [.3, -6], [.6, 8], [.9, -6], [1.2, 8]],
        "arm_left.rotation": [[0, 6], [.3, -4], [.6, 6], [.9, -4], [1.2, 6]],
        "arm_right.rotation": [[0, -3], [.6, 5], [1.2, -3]],
    }, True, weapon_visible=False)
    clip("rest", "休息 · 歪头放松", 5, {
        "head.rotation": [[0, 9], [2.5, 11], [5, 9]],
        "torso.rotation": [[0, 2], [2.5, 3], [5, 2]],
        "root.y": [[0, 0], [2.5, 8], [5, 0]],
    }, True, weapon_visible=False)
    clip("slender", "细剑 · 举剑致意", 3.2, {
        "arm_left.rotation": [[0, 0], [.5, -5], [1.3, 38], [2, 38], [2.7, 10], [3.2, 0]],
        "weapon.rotation": [[0, 0], [.6, 0], [1.3, 35], [2, 35], [3.2, 0]],
        "head.rotation": [[0, 0], [1.2, -4], [2, -4], [3.2, 0]],
        "torso.rotation": [[0, 0], [1.2, 2], [2.2, 2], [3.2, 0]],
    }, weapon="slender")
    clip("ice", "冰剑 · 唤出月霜", 3.6, {
        "arm_left.rotation": [[0, 0], [.6, 6], [1.5, 24], [2.3, 24], [3.6, 0]],
        "weapon.rotation": [[0, 0], [1.5, 33], [2.3, 33], [3.6, 0]],
        "head.rotation": [[0, 0], [1.3, -5], [2.3, -5], [3.6, 0]],
        "root.y": [[0, 0], [1.4, -20], [2.3, -20], [3.6, 0]],
        "arm_right.rotation": [[0, 0], [1.4, 5], [2.3, 5], [3.6, 0]],
    }, weapon="ice")
    clip("blink", "眨眼 · 轻轻闭眼", .8, {
        "head.blink": [[0, 0], [.15, 0], [.28, 1], [.36, 1], [.55, 0], [.8, 0]],
    })
    clip("moon_arc", "月弧 · 挽剑收势", 2.6, {
        "arm_left.rotation": [[0,0],[.35,-8],[.85,28],[1.25,36],[1.65,14],[2.1,8],[2.6,0]],
        "weapon.rotation": [[0,0],[.35,-12],[.9,58],[1.3,70],[1.7,-15],[2.15,8],[2.6,0]],
        "torso.rotation": [[0,0],[.4,-2],[1.05,3],[1.65,-1],[2.6,0]],
        "head.rotation": [[0,0],[.4,3],[1,-5],[1.7,2],[2.6,0]],
        "root.y": [[0,0],[.4,5],[1,-20],[1.8,-4],[2.6,0]],
        "arm_right.rotation": [[0,0],[.65,5],[1.2,-5],[1.8,3],[2.6,0]],
        "sleeve_mid.rotation": [[0,0],[.8,2],[1.3,6],[1.8,-4],[2.6,0]],
        "sleeve_tip.rotation": [[0,0],[.9,3],[1.5,9],[2.1,-5],[2.6,0]],
    })
    clips['slender']['effect'] = 'salute'
    clips['ice']['effect'] = 'summon'
    clips['moon_arc']['effect'] = 'moon_arc'
    write("animations.json", {"schema_version": 1, "transition_seconds": .24, "clips": clips})
    qa = ROOT / "qa"
    qa.mkdir(exist_ok=True)
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in ASSETS.rglob("*.png")}
    if not (qa / "source_hashes.json").exists():
        (qa / "source_hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    print(f"Authored {len(bones)} bones, {len(layers)} layers and {len(clips)} clips")


if __name__ == "__main__":
    build()
