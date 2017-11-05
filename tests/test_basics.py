from quantdom import MainWidget


def test_init(qtbot):
    widget = MainWidget()
    widget.show()
    qtbot.addWidget(widget)

    assert widget.isVisible()
