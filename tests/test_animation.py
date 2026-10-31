import math
import unittest

from core.rig import Rig, apply, identity
from core.animation import Animator, sample_track


class RigTests(unittest.TestCase):
    def make_rig(self):
        return Rig({"bones": [
            {"id": "root", "parent": None, "pivot": [10, 10]},
            {"id": "arm", "parent": "root", "pivot": [20, 10]},
            {"id": "tail", "parent": "arm", "pivot": [20, 20]},
        ]})

    def test_neutral_is_identity(self):
        for matrix in self.make_rig().skin_matrices({}).values():
            for a, b in zip(matrix, identity()):
                self.assertAlmostEqual(a, b)

    def test_child_attachment_follows_ancestor_rotation(self):
        rig = self.make_rig()
        matrices = rig.skin_matrices({"root": {"rotation": 90}})
        x, y = apply(matrices["tail"], (20, 20))
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, 20)

    def test_weighted_point_and_validation(self):
        rig = self.make_rig()
        matrices = rig.skin_matrices({"arm": {"x": 10}})
        self.assertEqual(rig.deform((20, 20), {"root": .25, "arm": .75}, matrices), (27.5, 20.0))
        with self.assertRaises(ValueError):
            rig.deform((20, 20), {"root": .1}, matrices)

    def test_cycle_and_unknown_parent_rejected(self):
        with self.assertRaises(ValueError):
            Rig({"bones": [{"id": "a", "parent": "b", "pivot": [0, 0]}]})
        with self.assertRaises(ValueError):
            Rig({"bones": [
                {"id": "a", "parent": "b", "pivot": [0, 0]},
                {"id": "b", "parent": "a", "pivot": [0, 0]},
            ]})

    def test_mesh_weights_and_triangle_mapping(self):
        from core.rig import chain_weights, affine_triangle
        chain = [[0, "a"], [10, "b"], [20, "c"]]
        self.assertEqual(chain_weights(5, chain), {"a": .5, "b": .5})
        self.assertEqual(chain_weights(-5, chain), {"a": 1.})
        matrix = affine_triangle([(0, 0), (2, 0), (0, 2)], [(5, 3), (5, 7), (1, 3)])
        self.assertEqual(apply(matrix, (1, 1)), (3., 5.))


class AnimationTests(unittest.TestCase):
    def clips(self):
        return {
            "idle": {"duration": 2, "loop": True, "tracks": {"head.rotation": [[0, 0], [1, 10], [2, 0]]}},
            "tap": {"duration": 1, "loop": False, "tracks": {"head.rotation": [[0, 0], [.5, -20], [1, 0]]}},
        }

    def test_track_is_smooth_and_clamps(self):
        track = [[0, 0], [1, 10]]
        self.assertEqual(sample_track(track, -1), 0)
        self.assertEqual(sample_track(track, 2), 10)
        self.assertAlmostEqual(sample_track(track, .5), 5)

    def test_loop_wraps(self):
        player = Animator(self.clips(), now=0)
        self.assertAlmostEqual(player.sample(1)["head"]["rotation"], 10)
        self.assertAlmostEqual(player.sample(3)["head"]["rotation"], 10)

    def test_one_shot_returns_to_idle(self):
        player = Animator(self.clips(), now=0)
        player.play("tap", 0)
        self.assertLess(player.sample(.5)["head"]["rotation"], 0)
        player.sample(1.1)
        self.assertEqual(player.name, "idle")

    def test_interrupt_does_not_snap(self):
        player = Animator(self.clips(), now=0)
        before = player.sample(1)
        player.play("tap", 1)
        after = player.sample(1)
        self.assertEqual(before, after)
        self.assertLess(abs(player.sample(1.01)["head"]["rotation"] - before["head"]["rotation"]), 1)

    def test_invalid_clip_rejected(self):
        player = Animator(self.clips(), now=0)
        with self.assertRaises(ValueError):
            player.play("missing", 0)


if __name__ == "__main__":
    unittest.main()
