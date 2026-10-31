import json
from pathlib import Path
import random
import unittest


class RandomClickTests(unittest.TestCase):
    def test_clicks_offer_many_visible_actions_without_loops_or_immediate_repeats(self):
        from core.interaction import random_action
        clips = json.loads((Path(__file__).resolve().parents[1]/'assets/jingliu/animations.json').read_text(encoding='utf-8'))['clips']
        rng = random.Random(17)
        previous = None
        seen = set()
        for _ in range(200):
            selected = random_action(clips,last=previous,current='idle',rng=rng)
            self.assertIn(selected,clips)
            self.assertNotIn(selected,('idle','drag','blink'))
            self.assertNotEqual(selected,previous)
            self.assertFalse(clips[selected].get('loop',False))
            seen.add(selected)
            previous = selected
        self.assertGreaterEqual(len(seen),8)

    def test_current_action_is_not_restarted_by_next_click(self):
        from core.interaction import random_action
        clips = {'idle':dict(loop=True),'wave':dict(loop=False),'nod':dict(loop=False)}
        self.assertEqual(random_action(clips,last='wave',current='wave',rng=random.Random(1)),'nod')
        self.assertEqual(random_action({'idle':dict(loop=True)},rng=random.Random(1)),'idle')


if __name__ == '__main__':
    unittest.main()
