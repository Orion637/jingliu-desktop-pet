from pathlib import Path
import tempfile
import unittest


class RuntimeTests(unittest.TestCase):
    def test_unwritable_state_uses_fallback_and_logging_failure_is_nonfatal(self):
        from core.runtime import select_state_root,configure_logging
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blocker = root/'blocked'
            blocker.write_text('file')
            self.assertEqual(select_state_root(blocker,root/'fallback'),root/'fallback')
            self.assertFalse(configure_logging(blocker))

    def test_recover_removed_monitor_and_fit_small_high_dpi_work_area(self):
        from core.window_geometry import recover_geometry
        self.assertEqual(recover_geometry(-2200,400,420,472,(0,0,1920,1040)),(0,400,420,472))
        x,y,width,height = recover_geometry(3000,2000,540,606,(-400,0,400,350))
        self.assertGreaterEqual(x,-400)
        self.assertGreaterEqual(y,0)
        self.assertLessEqual(x+width,0)
        self.assertLessEqual(y+height,350)


if __name__ == '__main__':
    unittest.main()
