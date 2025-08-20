# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets


class HotkeyController(QtCore.QObject):
    # Сигналы для уведомления об нажатии горячих клавиш
    rotate_box = QtCore.pyqtSignal()
    delete_box = QtCore.pyqtSignal()
    
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self._install_shortcuts()

    def _install_shortcuts(self):
        # Полноэкранный режим
        self.sc_fullscreen = QtWidgets.QShortcut(QtCore.Qt.Key_F12, self.window)
        self.sc_fullscreen.activated.connect(self.toggle_fullscreen)
        self.sc_escape = QtWidgets.QShortcut(QtCore.Qt.Key_Escape, self.window)
        self.sc_escape.activated.connect(self.exit_fullscreen)
        
        # Поворот коробки - клавиша R
        self.sc_rotate_r = QtWidgets.QShortcut(QtCore.Qt.Key_R, self.window)
        self.sc_rotate_r.activated.connect(self.rotate_box.emit)
        
        # Поворот коробки - русская К
        self.sc_rotate_k = QtWidgets.QShortcut(QtCore.Qt.Key_K, self.window)  # К
        self.sc_rotate_k.activated.connect(self.rotate_box.emit)
        
        # Удаление коробки - Backspace
        self.sc_delete = QtWidgets.QShortcut(QtCore.Qt.Key_Backspace, self.window)
        self.sc_delete.activated.connect(self.delete_box.emit)
        
        # Удаление коробки - Delete
        self.sc_delete2 = QtWidgets.QShortcut(QtCore.Qt.Key_Delete, self.window)
        self.sc_delete2.activated.connect(self.delete_box.emit)

    def toggle_fullscreen(self):
        if self.window.isFullScreen():
            self.window.showNormal()
        else:
            self.window.showFullScreen()

    def exit_fullscreen(self):
        if self.window.isFullScreen():
            self.window.showNormal()


