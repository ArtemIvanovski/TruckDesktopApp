#!/usr/bin/env python3
import sys
import os
from PyQt5 import QtWidgets, QtGui

from GUI.main_window import MainWindow


def _load_qt_fonts():
    try:
        from utils.setting_deploy import get_resource_path
        font_candidates = [
            get_resource_path('assets/fonts/NotoSans_Condensed-Regular.ttf'),
            get_resource_path('assets/fonts/NotoSans-Regular.ttf'),
            get_resource_path('assets/fonts/arial.ttf'),
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
