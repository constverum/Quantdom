from quantdom import MainWidget


def test_init(qtbot):
    widget = MainWidget()
    qtbot.addWidget(widget)

    widget.show()

    assert widget.isVisible()
    # contains only the Data tab
    assert widget.count() == 1
