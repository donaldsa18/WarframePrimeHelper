from gui import App
import time
import threading
import pytest

from pytestqt import qt_compat
from pytestqt.qt_compat import qt_api

def test_window(qtbot):
    app = App()
    app.create_window()
    app.init_threads()
    qtbot.addWidget(app.window)
    assert app.window.isVisible()
    assert app.window.windowTitle() == "Warframe Prime Helper"


if __name__ == "__main__":
    test_window()
