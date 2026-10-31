"""Continuous eyelid closure, independent of Qt and image playback."""
from core.animation import sample_track


def automatic_blink(seconds):
    t = max(0., seconds) % 5.6
    return sample_track([[0, 0], [3.18, 0], [3.3, 1], [3.36, 1], [3.54, 0], [5.6, 0]], t)
