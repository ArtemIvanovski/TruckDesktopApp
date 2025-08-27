#!/usr/bin/env python3
import sys
import os
from PyQt5 import QtWidgets, QtGui
from GUI.access_code_dialog import AccessCodeDialog
from GUI.main_window import MainWindow
from auth.auth_module import auth_module


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


def show_auth_dialog():
    guard = AccessCodeDialog()
    return guard.exec_() == QtWidgets.QDialog.Accepted


if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    _load_qt_fonts()
    
    # auth_module.initialize()
    #
    # # Всегда показываем диалог аутентификации
    # if not show_auth_dialog():
    #     sys.exit(0)
    
    win = MainWindow()
    
    # def on_auth_required():
    #     if not show_auth_dialog():
    #         qt_app.quit()
    #
    # def on_connection_lost():
    #     win.setEnabled(False)
    #
    # def on_connection_restored():
    #     win.setEnabled(True)
    #
    # auth_module.authentication_required.connect(on_auth_required)
    # auth_module.connection_lost.connect(on_connection_lost)
    # auth_module.connection_restored.connect(on_connection_restored)
    
    screen = qt_app.primaryScreen()
    if screen:
        screen_geometry = screen.availableGeometry()
        win.resize(screen_geometry.width(), screen_geometry.height())
        win.move(screen_geometry.x(), screen_geometry.y())
    win.show()
    
    try:
        sys.exit(qt_app.exec_())
    finally:
        auth_module.cleanup()
