"""Deterministic frost-dissolve/reform transition for the two held swords."""
from core.animation import smooth
import math


def weapon_rest_point(source, item):
    gx,gy = item['grip_source']
    x,y = source
    compact = item.get('compact_handle', {})
    start = compact.get('start', 100000)
    compression = compact.get('compression', 1)
    def axial(v):
        return min(v,start)+max(0,v-start)*compression
    taper = 1-(1-compact.get('taper',1))*min(1.,max(0.,(y-start)/180))
    dx = (x-gx)*item['texture_scale']*taper
    dy = (axial(y)-axial(gy))*item['texture_scale']
    angle = math.radians(item.get('rest_rotation',0))
    c,s = math.cos(angle), math.sin(angle)
    wx,wy = item['grip_world']
    return wx+c*dx-s*dy, wy+s*dx+c*dy


class WeaponSwap:
    def __init__(self, weapon='slender', duration=1.15):
        self.target = weapon
        self.duration = duration
        self.started = None
        self.previous = {}
        self.previous_reveal = {}

    def request(self, weapon, now):
        if weapon not in ('slender', 'ice', 'none'):
            raise ValueError('Unknown weapon')
        if weapon == self.target:
            return False
        current = self.sample(now)
        self.previous = current['weights']
        self.previous_reveal = current['reveal']
        self.target, self.started = weapon, now
        return True

    def sample(self, now):
        if self.started is None or now-self.started >= self.duration:
            self.started = None
            weights = {} if self.target == 'none' else {self.target: 1}
            return dict(weights=weights, reveal={k: 1 for k in weights}, phase=1., active=False)
        p = max(0., (now-self.started)/self.duration)
        if p <= .4:
            amount = 1-smooth(p/.4)
            weights = {k: v*amount for k, v in self.previous.items() if v*amount > .00001}
            reveal = {k: self.previous_reveal.get(k, 1) for k in weights}
        else:
            opacity = smooth(min(1., (p-.4)/.2))
            weights = {} if self.target == 'none' else {self.target: opacity}
            reveal = {k: smooth(min(1., (p-.4)/.6)) for k in weights}
        return dict(weights=weights, reveal=reveal, phase=p, active=True)


def action_effect(clip, elapsed):
    duration = clip['duration']
    phase = max(0., min(1., elapsed/duration))
    if clip.get('loop'):
        phase = max(0., elapsed) % duration / duration
    return dict(style=clip.get('effect', ''), phase=phase)
