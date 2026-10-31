"""Deterministic keyframe evaluation with pose-to-pose crossfades."""
from __future__ import annotations

import copy
import math


def smooth(t):
    return t*t*(3-2*t)


def sample_track(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t <= b:
            return va+(vb-va)*smooth((t-a)/(b-a))
    return keys[-1][1]


def sample_clip(clip, t):
    duration = clip["duration"]
    t = max(0., t) % duration if clip.get("loop") else min(duration, max(0., t))
    pose = {}
    for channel, keys in clip.get("tracks", {}).items():
        bone, parameter = channel.split(".", 1)
        pose.setdefault(bone, {})[parameter] = sample_track(keys, t)
    return pose


def blend(a, b, amount):
    result = {}
    for bone in a.keys() | b.keys():
        left, right = a.get(bone, {}), b.get(bone, {})
        result[bone] = {}
        for parameter in left.keys() | right.keys():
            default = 1. if parameter in ("sx", "sy") else 0.
            va, vb = left.get(parameter, default), right.get(parameter, default)
            result[bone][parameter] = va+(vb-va)*amount
    return result


class Animator:
    def __init__(self, clips, now=0., transition=.22):
        self.clips = clips
        if "idle" not in clips:
            raise ValueError("Missing idle animation")
        for name, clip in clips.items():
            if clip["duration"] <= 0:
                raise ValueError(f"Invalid animation duration: {name}")
            for channel, keys in clip.get("tracks", {}).items():
                if not keys or any(b[0] <= a[0] for a, b in zip(keys, keys[1:])):
                    raise ValueError(f"Keyframe times must increase: {name}/{channel}")
        self.name = "idle"
        self.started = now
        self.transition = transition
        self.from_pose = None

    def play(self, name, now):
        if name not in self.clips:
            raise ValueError(f"Unknown animation: {name}")
        current = self.sample(now)
        self.name, self.started = name, now
        self.from_pose = current

    def sample(self, now):
        clip = self.clips[self.name]
        elapsed = max(0., now-self.started)
        if not clip.get("loop") and elapsed >= clip["duration"]:
            self.from_pose = sample_clip(clip, clip["duration"])
            self.started += clip["duration"]
            self.name = "idle"
            clip = self.clips["idle"]
            elapsed = max(0., now-self.started)
        target = sample_clip(clip, elapsed)
        if self.from_pose is not None and elapsed < self.transition:
            return blend(self.from_pose, target, smooth(elapsed/self.transition))
        self.from_pose = None
        return target
