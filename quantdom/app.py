"""Application Entry Point."""

import logging
import logging.config
import sys

from PyQt5 import QtGui

from quantdom import __title__ as title
from quantdom import __version__ as version
from quantdom.ui import MainWidget

logger = logging.getLogger(__name__)


class MainWindow(QtGui.QMainWindow):

    size = (800, 500)
    title = '%s %s' % (title, version)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_widget = MainWidget(self)
        self.setCentralWidget(self.main_widget)
        self.setMinimumSize(*self.size)
        self.setWindowTitle(self.title)
        self.resize(*self.size)
        # setGeometry()
        self._move_to_center()

    def _move_to_center(self):
        """Move the application window in the center of the screen."""
        desktop = QtGui.QApplication.desktop()
        x = (desktop.width() - self.width()) / 2
        y = (desktop.height() - self.height()) / 2
        self.move(x, y)


def main(debug=False):
    app = QtGui.QApplication.instance()
    if app is None:
        app = QtGui.QApplication([])
    app.setApplicationName(title)
    app.setApplicationVersion(version)

    window = MainWindow()
    window.show()

    if debug:
        window.main_widget.plot_test_data()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
