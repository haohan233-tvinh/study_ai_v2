"""Keep the status indicator out of the taskbar on every monitor."""
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication
from debug_ui import StatusDot


@pytest.mark.parametrize('workarea,scale', [
    (QRect(0, 0, 1920, 1032), 1),
    (QRect(-1920, 0, 1872, 1080), 1),
    (QRect(0, -1080, 1920, 1032), 2),
])
def test_status_dot_stays_in_workarea_including_negative_monitor_coordinates(workarea, scale):
    app = QApplication.instance() or QApplication([])
    screen = SimpleNamespace(availableGeometry=lambda: workarea,
                             geometry=lambda: QRect(0, 0, 1920, 1080),
                             devicePixelRatio=lambda: scale)
    dot = StatusDot()
    try:
        with patch('debug_ui.QApplication.primaryScreen', return_value=screen):
            dot.set_state('ready')
        assert workarea.contains(dot.geometry())
        assert dot.geometry().right() == workarea.right() - 6
        assert dot.geometry().bottom() == workarea.bottom() - 6
        assert app is not None
    finally:
        dot.close()
