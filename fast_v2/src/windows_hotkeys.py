"""Action shortcuts delivered by Windows, independently of keyboard's hook state."""
import ctypes
from ctypes import wintypes
import itertools

from PyQt6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QThread


MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
_MODIFIERS = {'alt': 1, 'ctrl': 2, 'control': 2, 'shift': 4,
              'windows': 8, 'win': 8, 'meta': 8, 'cmd': 8}
_KEYS = {
    'backspace': 8, 'tab': 9, 'enter': 13, 'return': 13, 'pause': 19,
    'caps lock': 20, 'capslock': 20, 'esc': 27, 'escape': 27, 'space': 32,
    'page up': 33, 'pageup': 33, 'pgup': 33,
    'page down': 34, 'pagedown': 34, 'pgdown': 34, 'pgdn': 34,
    'end': 35, 'home': 36, 'left': 37, 'up': 38, 'right': 39, 'down': 40,
    'print screen': 44, 'print': 44, 'insert': 45, 'ins': 45,
    'delete': 46, 'del': 46, 'num lock': 144, 'numlock': 144,
    'scroll lock': 145, 'scrolllock': 145,
    'semicolon': 186, ';': 186, 'equal': 187, '=': 187, 'plus': 187,
    'comma': 188, ',': 188, 'minus': 189, '-': 189,
    'period': 190, '.': 190, 'slash': 191, '/': 191,
    'grave': 192, '`': 192, 'left bracket': 219, '[': 219,
    'backslash': 220, '\\': 220, 'right bracket': 221, ']': 221,
    'apostrophe': 222, "'": 222,
}
_KEYS.update({chr(key).lower(): key for key in range(ord('A'), ord('Z') + 1)})
_KEYS.update({str(key): ord(str(key)) for key in range(10)})
_KEYS.update({f'f{key}': 111 + key for key in range(1, 25)})
# Shift is recorded separately by KeyRecorder; resolve its printed symbols too.
_KEYS.update({symbol: ord(key) for symbol, key in zip('!@#$%^&*()', '1234567890')})
_KEYS.update({':': 186, '_': 189, '<': 188, '>': 190, '?': 191,
              '~': 192, '{': 219, '|': 220, '}': 221, '"': 222})
_IDS = itertools.cycle(range(0x4000, 0xC000))
_ACTIVE_IDS = set()


def parse_hotkey(value):
    """Resolve one modifier chord; reject sequences and unsupported keys early."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Phím tắt không được để trống')
    value = value.strip().lower()
    # QKeySequence records the + key as e.g. "ctrl+shift++".
    if value == '+':
        value = 'plus'
    elif value.endswith('++'):
        value = value[:-1] + 'plus'
    parts = [part.strip() for part in value.split('+')]
    modifiers = 0
    for part in parts[:-1]:
        flag = _MODIFIERS.get(part)
        if flag is None or modifiers & flag:
            raise ValueError(f'Phím tắt không hợp lệ: {value!r}; dùng một tổ hợp phím')
        modifiers |= flag
    key = _KEYS.get(parts[-1])
    if key is None:
        raise ValueError(f'Phím không được hỗ trợ: {parts[-1]!r}; dùng một tổ hợp phím')
    return modifiers | MOD_NOREPEAT, key


class WindowsHotkeys(QAbstractNativeEventFilter):
    """Register on Qt's main thread; removers are safe to call repeatedly."""

    def __init__(self, user32=None):
        super().__init__()
        self._user32 = user32
        self._callbacks = {}
        self._chords = {}
        self._app = None

    def _main_app(self):
        app = QCoreApplication.instance()
        if app is None or QThread.currentThread() != app.thread():
            raise RuntimeError('Phím tắt Windows cần Qt application và luồng chính Qt')
        return app

    def add_hotkey(self, value, callback):
        app = self._main_app()
        chord = parse_hotkey(value)
        if not callable(callback):
            raise TypeError('callback phải là hàm')
        if chord in self._chords:
            raise ValueError(f'Phím tắt đã đăng ký: {value}')
        if self._user32 is None:
            self._user32 = ctypes.WinDLL('user32', use_last_error=True)
            self._user32.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int,
                                                   wintypes.UINT, wintypes.UINT)
            self._user32.RegisterHotKey.restype = wintypes.BOOL
            self._user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
            self._user32.UnregisterHotKey.restype = wintypes.BOOL
        if len(_ACTIVE_IDS) == 0x8000:
            raise RuntimeError('Đã hết mã đăng ký phím tắt Windows')
        identifier = next(_IDS)
        while identifier in _ACTIVE_IDS:
            identifier = next(_IDS)
        if not self._user32.RegisterHotKey(None, identifier, *chord):
            error = ctypes.get_last_error()
            raise OSError(error, f'Windows không đăng ký được {value!r}; '
                          'tổ hợp có thể đang bị ứng dụng khác chiếm')
        _ACTIVE_IDS.add(identifier)
        self._callbacks[identifier] = callback
        self._chords[chord] = identifier
        if self._app is None:
            self._app = app
            app.installNativeEventFilter(self)

        removed = False

        def remove():
            nonlocal removed
            if removed:
                return
            self._main_app()
            if not self._user32.UnregisterHotKey(None, identifier):
                raise OSError(ctypes.get_last_error(),
                              f'Windows không gỡ được phím tắt {value!r}')
            del self._callbacks[identifier]
            del self._chords[chord]
            _ACTIVE_IDS.discard(identifier)
            removed = True
            if not self._callbacks:
                self._app.removeNativeEventFilter(self)
                self._app = None

        return remove

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) in (b'windows_generic_MSG', b'windows_dispatcher_MSG'):
            msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
            callback = self._callbacks.get(int(msg.wParam))
            if msg.message == WM_HOTKEY and callback is not None:
                callback()
                return True, 0
        return False, 0


_default_registry = None


def add_hotkey(value, callback):
    global _default_registry
    if _default_registry is None:
        _default_registry = WindowsHotkeys()
    return _default_registry.add_hotkey(value, callback)
