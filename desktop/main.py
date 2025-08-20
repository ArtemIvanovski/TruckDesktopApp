#!/usr/bin/env python3
import sys
import os
from PyQt5 import QtWidgets, QtGui
from qt_widgets import MainWindow


def _load_qt_fonts():
    try:
        base_dir = os.path.dirname(__file__)
        font_candidates = [
            os.path.join(base_dir, 'fonts', 'NotoSans_Condensed-Regular.ttf'),
            os.path.join(base_dir, 'fonts', 'NotoSans-Regular.ttf'),
            os.path.join(base_dir, 'fonts', 'arial.ttf'),
        ]
        for path in font_candidates:
            if os.path.exists(path):
                QtGui.QFontDatabase.addApplicationFont(path)
    except Exception:
        pass


if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    _load_qt_fonts()
    win = MainWindow()
    screen = qt_app.primaryScreen()
    if screen:
        screen_geometry = screen.availableGeometry()
        win.resize(screen_geometry.width(), screen_geometry.height())
        win.move(screen_geometry.x(), screen_geometry.y())
    win.show()
    sys.exit(qt_app.exec_())
