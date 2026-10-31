import unittest


class FullscreenTests(unittest.TestCase):
    def test_preference_defaults_on_and_round_trips_disabled(self):
        from pathlib import Path
        import tempfile
        from core.settings import Settings
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'settings.json'
            self.assertTrue(Settings.load(path).hide_in_fullscreen)
            settings=Settings(hide_in_fullscreen=False)
            self.assertTrue(settings.save(path))
            self.assertFalse(Settings.load(path).hide_in_fullscreen)

    def test_fullscreen_coverage_and_monitor_location(self):
        from core.fullscreen import covers_monitor
        self.assertTrue(covers_monitor((0,0,1920,1080),(0,0,1920,1080)))
        self.assertTrue(covers_monitor((-1920,-2,2,1082),(-1920,0,0,1080)))
        self.assertFalse(covers_monitor((0,0,1920,1040),(0,0,1920,1080)))
        self.assertFalse(covers_monitor((1920,0,3840,1080),(0,0,1920,1080)))

    def test_desktop_minimized_own_process_and_maximized_caption_are_not_fullscreen(self):
        from core.fullscreen import should_hide
        base = dict(bounds=(0,0,1920,1080),monitor=(0,0,1920,1080),
                    pid=12,own_pid=99,class_name='GameWindow',visible=True,minimized=False,
                    cloaked=False,zoomed=False,style=0,same_monitor=True)
        self.assertTrue(should_hide(**base))
        for update in (dict(class_name='Progman'),dict(class_name='WorkerW'),dict(pid=99),
                       dict(visible=False),dict(minimized=True),dict(cloaked=True),
                       dict(zoomed=True,style=0x00C00000),dict(same_monitor=False)):
            self.assertFalse(should_hide(**(base|update)),update)

    def test_visibility_policy_restores_only_requested_pet_and_respects_preference(self):
        from core.fullscreen import pet_visibility
        self.assertFalse(pet_visibility(requested=True,enabled=True,fullscreen=True))
        self.assertTrue(pet_visibility(requested=True,enabled=True,fullscreen=False))
        self.assertTrue(pet_visibility(requested=True,enabled=False,fullscreen=True))
        self.assertFalse(pet_visibility(requested=False,enabled=True,fullscreen=False))
