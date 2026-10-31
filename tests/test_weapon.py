import unittest


class WeaponSwapTests(unittest.TestCase):
    def test_both_grips_remain_in_hand_through_all_actions(self):
        import json
        from pathlib import Path
        from core.animation import sample_clip
        from core.rig import Rig, apply
        from core.weapon import weapon_rest_point
        root=Path(__file__).resolve().parents[1]/'assets/jingliu'
        rig=Rig.from_file(root/'rig.json')
        clips=json.loads((root/'animations.json').read_text(encoding='utf-8'))['clips']
        swords=[layer for layer in rig.data['layers'] if layer.get('weapon')]
        for clip in clips.values():
            for i in range(9):
                matrices=rig.skin_matrices(sample_clip(clip,clip['duration']*i/8))
                hand=apply(matrices['arm_left'],rig.bones['weapon']['pivot'])
                for sword in swords:
                    grip=apply(matrices['weapon'],weapon_rest_point(sword['grip_source'],sword))
                    self.assertAlmostEqual(grip[0],hand[0],places=7)
                    self.assertAlmostEqual(grip[1],hand[1],places=7)

    def test_sleeve_attachment_follows_right_cuff(self):
        import json
        from pathlib import Path
        from core.animation import sample_clip
        from core.rig import Rig,apply
        root=Path(__file__).resolve().parents[1]/'assets/jingliu'
        rig=Rig.from_file(root/'rig.json')
        anchor=rig.bones['sleeve_root']['pivot']
        clips=json.loads((root/'animations.json').read_text(encoding='utf-8'))['clips']
        for clip in clips.values():
            for i in range(9):
                matrices=rig.skin_matrices(sample_clip(clip,clip['duration']*i/8))
                cuff=apply(matrices['arm_right'],anchor)
                tail=apply(matrices['sleeve_root'],anchor)
                self.assertAlmostEqual(cuff[0],tail[0],places=7)
                self.assertAlmostEqual(cuff[1],tail[1],places=7)

    def test_compact_handle_keeps_grip_fixed(self):
        from core.weapon import weapon_rest_point
        item = dict(grip_source=[512,1190],grip_world=[164,943],texture_scale=.34,rest_rotation=-135,
                    compact_handle=dict(start=1080,compression=.55,taper=.72))
        self.assertEqual(weapon_rest_point([512,1190],item),(164.,943.))
        tip = weapon_rest_point([512,1470],item)
        import math
        self.assertAlmostEqual(math.dist(tip,[164,943]),280*.55*.34)

    def test_dissolve_reform_and_finish(self):
        from core.weapon import WeaponSwap
        swap = WeaponSwap('slender', duration=1)
        swap.request('ice', 0)
        self.assertEqual(swap.sample(0)['weights'], {'slender': 1})
        self.assertLess(swap.sample(.2)['weights']['slender'], 1)
        self.assertNotIn('slender', swap.sample(.5)['weights'])
        self.assertLess(swap.sample(.6)['reveal']['ice'], 1)
        self.assertEqual(swap.sample(1.1)['weights'], {'ice': 1})

    def test_interrupted_swap_preserves_current_visible_state(self):
        from core.weapon import WeaponSwap
        swap = WeaponSwap('slender', duration=1)
        swap.request('ice', 0)
        before = swap.sample(.65)
        swap.request('slender', .65)
        after = swap.sample(.65)
        self.assertEqual(before['weights'], after['weights'])
        self.assertEqual(before['reveal'], after['reveal'])
        self.assertEqual(swap.sample(2)['weights'], {'slender': 1})

    def test_empty_hand(self):
        from core.weapon import WeaponSwap
        swap = WeaponSwap('ice')
        swap.request('none', 0)
        self.assertEqual(swap.sample(2)['weights'], {})


if __name__ == '__main__':
    unittest.main()
