from PyQt5 import QtWidgets, QtCore, QtGui
from auth.auth_module import auth_module


class DigitLineEdit(QtWidgets.QLineEdit):
    def __init__(self):
        super().__init__()
        self.setMaxLength(1)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedSize(52, 64)
        self.setFont(QtGui.QFont("Noto Sans", 22, QtGui.QFont.Bold))
        self.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]")))
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)


class AccessCodeDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.is_authenticating = False
        self._setup_auth_module()
        self._build_ui()
        self._apply_styles()
        QtCore.QTimer.singleShot(0, self._focus_first)

    def _build_ui(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QVBoxLayout())
        container.layout().setContentsMargins(24, 24, 24, 24)
        container.layout().setSpacing(0)
        self.layout().addWidget(container)

        center = QtWidgets.QWidget()
        center.setLayout(QtWidgets.QVBoxLayout())
        center.layout().setAlignment(QtCore.Qt.AlignCenter)
        container.layout().addWidget(center, 1)

        self.card = QtWidgets.QFrame()
        self.card.setObjectName("card")
        self.card.setLayout(QtWidgets.QVBoxLayout())
        self.card.layout().setContentsMargins(32, 32, 32, 28)
        self.card.layout().setSpacing(16)

        title = QtWidgets.QLabel("GTSTREAM")
        title.setObjectName("title")
        title.setAlignment(QtCore.Qt.AlignHCenter)
        subtitle = QtWidgets.QLabel("Введите 6‑значный код доступа")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(QtCore.Qt.AlignHCenter)

        digits_row = QtWidgets.QHBoxLayout()
        digits_row.setSpacing(10)
        digits_row.setAlignment(QtCore.Qt.AlignHCenter)
        self.inputs = [DigitLineEdit() for _ in range(6)]
        for i, le in enumerate(self.inputs):
            le.textChanged.connect(self._on_digit_changed)
            le.installEventFilter(self)
            digits_row.addWidget(le)

        self.action_button = QtWidgets.QPushButton("Войти")
        self.action_button.setObjectName("primaryButton")
        self.action_button.setEnabled(False)
        self.action_button.clicked.connect(self._try_submit)

        self.error_label = QtWidgets.QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setAlignment(QtCore.Qt.AlignHCenter)
        self.error_label.hide()

        self.card.layout().addWidget(title)
        self.card.layout().addWidget(subtitle)
        self.card.layout().addSpacing(6)
        row_widget = QtWidgets.QWidget()
        row_widget.setLayout(digits_row)
        self.card.layout().addWidget(row_widget)
        self.card.layout().addSpacing(8)
        self.card.layout().addWidget(self.action_button)
        self.card.layout().addWidget(self.error_label)

        effect = QtWidgets.QGraphicsDropShadowEffect(self.card)
        effect.setBlurRadius(48)
        effect.setXOffset(0)
        effect.setYOffset(18)
        effect.setColor(QtGui.QColor(0, 0, 0, 60))
        self.card.setGraphicsEffect(effect)

        center.layout().addWidget(self.card)

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QDialog { background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364); }
            #card { background: #ffffff; border-radius: 16px; }
            #title { font-family: 'Noto Sans'; font-size: 26px; font-weight: 800; color: #2c3e50; letter-spacing: 2px; }
            #subtitle { font-size: 14px; color: #6b7b8c; }
            QLineEdit { border: 2px solid #e1e6ef; border-radius: 10px; background: #f8fafc; color: #2c3e50; }
            QLineEdit:focus { border-color: #3498db; background: #ffffff; }
            #primaryButton { background: #3498db; color: white; border: none; border-radius: 10px; padding: 12px 18px; font-size: 16px; font-weight: 600; }
            #primaryButton:disabled { background: #9bbfdd; }
            #primaryButton:hover:!disabled { background: #2d89c6; }
            #error { color: #d34e4e; font-size: 13px; }
            """
        )

    def _focus_first(self):
        self.showFullScreen()
        if self.inputs:
            self.inputs[0].setFocus()

    def _on_digit_changed(self, _):
        for idx, le in enumerate(self.inputs):
            txt = le.text()
            if len(txt) > 0 and idx < len(self.inputs) - 1:
                self.inputs[idx + 1].setFocus()
        self._update_button_state()

    def _update_button_state(self):
        code = "".join([le.text() for le in self.inputs])
        self.action_button.setEnabled(len(code) == 6)

    def eventFilter(self, obj, event):
        if isinstance(obj, DigitLineEdit):
            if event.type() == QtCore.QEvent.KeyPress:
                if event.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Backspace):
                    if obj.text() == "":
                        idx = self.inputs.index(obj)
                        if idx > 0:
                            self.inputs[idx - 1].setFocus()
                            self.inputs[idx - 1].setText("")
                            return True
                if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                    self._try_submit()
                    return True
                if event.key() == QtCore.Qt.Key_Escape:
                    return True
        return super().eventFilter(obj, event)

    def _setup_auth_module(self):
        auth_module.initialize()
        auth_module.authentication_successful.connect(self._on_auth_success)
        auth_module.authentication_failed.connect(self._on_auth_failed)
    
    def _try_submit(self):
        if self.is_authenticating:
            return
            
        code = "".join([le.text() for le in self.inputs])
        if len(code) != 6:
            return
            
        self.is_authenticating = True
        self.action_button.setEnabled(False)
        self.action_button.setText("Проверка...")
        
        if not auth_module.is_enabled():
            if code == "111111":
                self.accept()
                return
            else:
                self._show_error("Неверный код")
                for le in self.inputs:
                    le.setText("")
                if self.inputs:
                    self.inputs[0].setFocus()
                self.is_authenticating = False
                self.action_button.setEnabled(True)
                self.action_button.setText("Войти")
                return
        
        success = auth_module.authenticate(code)
        if not success:
            self.is_authenticating = False
            self.action_button.setEnabled(True)
            self.action_button.setText("Войти")
    
    def _on_auth_success(self):
        self.accept()
    
    def _on_auth_failed(self, error_message: str):
        self._show_error(error_message)
        for le in self.inputs:
            le.setText("")
        if self.inputs:
            self.inputs[0].setFocus()
        self.is_authenticating = False
        self.action_button.setEnabled(True)
        self.action_button.setText("Войти")

    def _show_error(self, message: str = "Неверный код"):
        self.error_label.setText(message)
        self.error_label.show()
        anim = QtCore.QParallelAnimationGroup(self)
        geo = self.card.geometry()
        for i in range(3):
            a1 = QtCore.QPropertyAnimation(self.card, b"pos")
            a1.setDuration(60)
            a1.setStartValue(geo.topLeft() + QtCore.QPoint(0, 0))
            a1.setEndValue(geo.topLeft() + QtCore.QPoint(12, 0))
            a2 = QtCore.QPropertyAnimation(self.card, b"pos")
            a2.setDuration(60)
            a2.setStartValue(geo.topLeft() + QtCore.QPoint(12, 0))
            a2.setEndValue(geo.topLeft() + QtCore.QPoint(-12, 0))
            a3 = QtCore.QPropertyAnimation(self.card, b"pos")
            a3.setDuration(60)
            a3.setStartValue(geo.topLeft() + QtCore.QPoint(-12, 0))
            a3.setEndValue(geo.topLeft() + QtCore.QPoint(0, 0))
            seq = QtCore.QSequentialAnimationGroup(self)
            seq.addAnimation(a1)
            seq.addAnimation(a2)
            seq.addAnimation(a3)
            anim.addAnimation(seq)
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def closeEvent(self, event: QtGui.QCloseEvent):
        QtWidgets.QApplication.instance().quit()
        event.accept()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() in (QtCore.Qt.Key_Alt, QtCore.Qt.Key_Tab):
            event.ignore()
            return
        if event.key() in (QtCore.Qt.Key_Escape,):
            return
        super().keyPressEvent(event)


