from gui import App


def test_window(qtbot):
    app = App()
    app.create_window()
    app.init_threads()
    #qtbot.addWidget(app.window)

    assert app.window.isVisible()
    assert app.window.windowTitle() == "Warframe Prime Helper"


if __name__ == "__main__":
    test_window()
