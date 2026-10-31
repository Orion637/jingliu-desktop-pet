import unittest


class BlinkTests(unittest.TestCase):
    def test_blink_closes_then_reopens_and_stays_bounded(self):
        from core.face import automatic_blink
        values = [automatic_blink(i/100) for i in range(1000)]
        self.assertTrue(all(0 <= v <= 1 for v in values))
        self.assertEqual(automatic_blink(0), 0)
        self.assertEqual(automatic_blink(3.3), 1)
        self.assertEqual(automatic_blink(3.7), 0)
        self.assertTrue(any(v > .95 for v in values))

    def test_closed_eyes_cover_old_white_highlights(self):
        from pathlib import Path
        from PySide6.QtGui import QImage, QPainter
        from ui.face import Eyelids
        path = Path(__file__).resolve().parents[1] / 'assets/jingliu/parts/head.png'
        original = QImage(str(path))
        result = original.copy()
        p = QPainter(result)
        Eyelids(original).draw(p, 1)
        p.end()
        white = sum(1 for y in range(664, 716) for x in range(572, 625)
                    if min(result.pixelColor(x,y).red(), result.pixelColor(x,y).green(), result.pixelColor(x,y).blue()) > 235)
        self.assertEqual(white, 0)

    def test_partial_blink_does_not_copy_fringe_into_skin(self):
        from pathlib import Path
        from PySide6.QtGui import QImage, QPainter
        from ui.face import Eyelids
        path = Path(__file__).resolve().parents[1] / 'assets/jingliu/parts/head.png'
        original = QImage(str(path))
        result = original.copy()
        p = QPainter(result)
        Eyelids(original).draw(p, .5)
        p.end()
        ghosts = 0
        for y in range(620, 760):
            for x in range(220, 750):
                before, after = original.pixelColor(x,y), result.pixelColor(x,y)
                if before.red() > before.blue()+8 and after.blue() > after.red()+25 and after.blue() > after.green()+8 and after.red() < 230:
                    ghosts += 1
        self.assertEqual(ghosts, 0)


if __name__ == '__main__':
    unittest.main()
