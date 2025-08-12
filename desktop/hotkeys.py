# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets


class HotkeyController(QtCore.QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self._install_shortcuts()

    def _install_shortcuts(self):
        self.sc_fullscreen = QtWidgets.QShortcut(QtCore.Qt.Key_F12, self.window)
        self.sc_fullscreen.activated.connect(self.toggle_fullscreen)
        self.sc_escape = QtWidgets.QShortcut(QtCore.Qt.Key_Escape, self.window)
        self.sc_escape.activated.connect(self.exit_fullscreen)

    def toggle_fullscreen(self):
        if self.window.isFullScreen():
            self.window.showNormal()
        else:
            self.window.showFullScreen()

    def exit_fullscreen(self):
        if self.window.isFullScreen():
            self.window.showNormal()


