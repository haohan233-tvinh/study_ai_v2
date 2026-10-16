"""Native shortcut tests use fake WinAPI/Qt app; no hooks or key injection."""
import ctypes
from ctypes import wintypes
import itertools
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import windows_hotkeys as hotkeys


class ParseHotkeysTests(unittest.TestCase):
    def test_existing_config_chords(self):
        for value, modifiers, key in (
            ('ctrl+alt+grave', 3, 192), ('ctrl+enter', 2, 13),
            ('ctrl+alt+r', 3, 82), ('ctrl+q', 2, 81),
            ('ctrl+alt+shift+p', 7, 80), ('ctrl+1', 2, 49),
            ('backspace', 0, 8), ('esc', 0, 27),
        ):
            with self.subTest(value=value):
                self.assertEqual(hotkeys.parse_hotkey(value),
                                 (modifiers | hotkeys.MOD_NOREPEAT, key))

    def test_recorder_and_common_aliases(self):
        for value, modifiers, key in (
            (' control + ALT + Shift + P ', 7, 80),
            ('win+f24', 8, 135), ('meta+home', 8, 36),
            ('ctrl+pgup', 2, 33), ('alt+pgdown', 1, 34),
            ('ctrl+del', 2, 46), ('ctrl+left', 2, 37),
            ('ctrl+shift++', 6, 187), ('+', 0, 187),
            ('ctrl+;', 2, 186), ('ctrl+,', 2, 188),
            ('ctrl+backslash', 2, 220), ('ctrl+[', 2, 219),
            ('ctrl+apostrophe', 2, 222), ('f7', 0, 118), ('f8', 0, 119),
            ('ctrl+shift+?', 6, 191), ('ctrl+shift+~', 6, 192),
            ('ctrl+shift+)', 6, 48), ('ctrl+shift+(', 6, 57),
            ('numlock', 0, 144), ('scrolllock', 0, 145),
        ):
            with self.subTest(value=value):
                self.assertEqual(hotkeys.parse_hotkey(value),
                                 (modifiers | hotkeys.MOD_NOREPEAT, key))

    def test_invalid_or_multistep_shortcuts_are_rejected(self):
        for value in ('', ' ', None, 12, 'ctrl', 'ctrl+', 'ctrl+ctrl+a',
                      'ctrl+control+a', 'ctrl+a, ctrl+b', 'ctrl+a+b',
                      'ctrl+++a', 'mouse_x1', 'f25', 'ctrl+unknown'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                hotkeys.parse_hotkey(value)


class WindowsHotkeysTests(unittest.TestCase):
    def setUp(self):
        self.app = MagicMock()
        self.thread = object()
        self.app.thread.return_value = self.thread
        app_patch = patch.object(hotkeys.QCoreApplication, 'instance', return_value=self.app)
        thread_patch = patch.object(hotkeys.QThread, 'currentThread', return_value=self.thread)
        self.app_mock = app_patch.start()
        self.thread_mock = thread_patch.start()
        self.addCleanup(app_patch.stop)
        self.addCleanup(thread_patch.stop)
        self.api = MagicMock()
        self.api.RegisterHotKey.return_value = True
        self.api.UnregisterHotKey.return_value = True
        self.registry = hotkeys.WindowsHotkeys(self.api)
        self.removers = []
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.api.UnregisterHotKey.return_value = True
        self.app_mock.return_value = self.app
        self.thread_mock.return_value = self.thread
        for remove in self.removers:
            remove()

    def _add(self, value='ctrl+alt+shift+p', callback=None, registry=None):
        callback = callback or MagicMock()
        registry = registry or self.registry
        remove = registry.add_hotkey(value, callback)
        self.removers.append(remove)
        identifier = self.api.RegisterHotKey.call_args.args[1]
        return identifier, callback, remove

    def _event(self, identifier, message=hotkeys.WM_HOTKEY, event_type=b'windows_generic_MSG'):
        msg = wintypes.MSG()
        msg.message, msg.wParam = message, identifier
        return self.registry.nativeEventFilter(event_type, ctypes.addressof(msg))

    def test_native_dispatch_does_not_consult_keyboard_listener_state(self):
        # Direct WM_HOTKEY delivery has no keyboard pressed-state dictionary;
        # held F7/F8 and injected Alt cannot contaminate its chord lookup.
        with patch('keyboard.add_hotkey', side_effect=AssertionError('must not use keyboard')):
            identifier, callback, _ = self._add()
            self.api.RegisterHotKey.assert_called_once_with(None, identifier, 0x4007, 80)
            self.app.installNativeEventFilter.assert_called_once_with(self.registry)
            for event_type in (b'windows_generic_MSG', b'windows_dispatcher_MSG'):
                self.assertEqual(self._event(identifier, event_type=event_type), (True, 0))
            self.assertEqual(callback.call_count, 2)
            self.assertEqual(self._event(identifier + 1), (False, 0))
            self.assertEqual(self._event(identifier, message=0x100), (False, 0))
            self.assertEqual(self.registry.nativeEventFilter(b'other', 0), (False, 0))
            self.assertEqual(callback.call_count, 2)

    def test_remove_is_idempotent_and_rebind_uses_distinct_id(self):
        first, callback, remove = self._add()
        remove()
        remove()
        self.api.UnregisterHotKey.assert_called_once_with(None, first)
        self.app.removeNativeEventFilter.assert_called_once_with(self.registry)
        self.assertEqual(self._event(first), (False, 0))
        callback.assert_not_called()
        second, _, _ = self._add()
        self.assertNotEqual(first, second)
        self.assertEqual(self.app.installNativeEventFilter.call_count, 2)

    def test_keep_filter_until_last_shortcut_removed(self):
        first, _, remove_first = self._add('ctrl+enter')
        second, _, remove_second = self._add('esc')
        self.assertNotEqual(first, second)
        remove_first()
        self.app.removeNativeEventFilter.assert_not_called()
        self.assertEqual(self._event(second), (True, 0))
        remove_second()
        self.app.removeNativeEventFilter.assert_called_once_with(self.registry)

    def test_old_remover_cannot_unregister_a_reused_id(self):
        with patch.object(hotkeys, '_IDS', itertools.repeat(0x5000)):
            identifier, _, old_remove = self._add()
            old_remove()
            self._add()
            old_remove()
            self.assertIn(identifier, self.registry._callbacks)
            self.assertEqual(self.api.UnregisterHotKey.call_count, 1)

    def test_completed_removal_remains_idempotent_after_qt_shutdown(self):
        _, _, remove = self._add()
        remove()
        self.app_mock.return_value = None
        remove()

    def test_ids_are_unique_across_registries(self):
        first, _, _ = self._add('ctrl+enter')
        second, _, _ = self._add('esc', registry=hotkeys.WindowsHotkeys(self.api))
        self.assertNotEqual(first, second)
        self.assertTrue(0x4000 <= first <= 0xBFFF)
        self.assertTrue(0x4000 <= second <= 0xBFFF)

    def test_registration_conflict_is_reported_and_can_retry(self):
        self.api.RegisterHotKey.return_value = False
        with patch.object(ctypes, 'get_last_error', return_value=1409):
            with self.assertRaisesRegex(OSError, '1409.*Windows.*chiếm'):
                self.registry.add_hotkey('ctrl+enter', MagicMock())
        self.assertEqual(self.registry._callbacks, {})
        self.app.installNativeEventFilter.assert_not_called()
        self.api.UnregisterHotKey.assert_not_called()
        self.api.RegisterHotKey.return_value = True
        self._add('ctrl+enter')

    def test_duplicate_alias_does_not_replace_original_callback(self):
        identifier, callback, _ = self._add('ctrl+enter')
        with self.assertRaisesRegex(ValueError, 'đã đăng ký'):
            self.registry.add_hotkey('control+return', MagicMock())
        self.api.RegisterHotKey.assert_called_once()
        self._event(identifier)
        callback.assert_called_once_with()

    def test_unregister_failure_retains_registration_for_retry(self):
        identifier, _, remove = self._add()
        self.api.UnregisterHotKey.return_value = False
        with patch.object(ctypes, 'get_last_error', return_value=5):
            with self.assertRaises(OSError):
                remove()
        self.assertIn(identifier, self.registry._callbacks)
        self.app.removeNativeEventFilter.assert_not_called()
        self.api.UnregisterHotKey.return_value = True
        remove()
        self.assertNotIn(identifier, self.registry._callbacks)

    def test_require_app_and_qt_main_thread(self):
        self.app_mock.return_value = None
        with self.assertRaisesRegex(RuntimeError, 'luồng chính'):
            self.registry.add_hotkey('ctrl+enter', MagicMock())
        self.app_mock.return_value = self.app
        self.thread_mock.return_value = object()
        with self.assertRaisesRegex(RuntimeError, 'luồng chính'):
            self.registry.add_hotkey('ctrl+enter', MagicMock())
        self.api.RegisterHotKey.assert_not_called()


if __name__ == '__main__':
    unittest.main()
