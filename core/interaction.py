"""Pick visible, finite click reactions while avoiding immediate repetition."""
import random


def random_action(clips,last=None,current=None,rng=None):
    candidates = [name for name,clip in clips.items()
                  if name not in ('idle','drag','blink') and not clip.get('loop',False)]
    if not candidates:
        return 'idle' if 'idle' in clips else next(iter(clips),'idle')
    choices = [name for name in candidates if name not in (last,current)]
    if not choices:
        choices = [name for name in candidates if name != last] or candidates
    return (rng or random).choice(choices)
