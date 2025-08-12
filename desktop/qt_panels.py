from PyQt5 import QtWidgets, QtCore, QtGui


class LeftSidebar(QtWidgets.QWidget):
    toggled = QtCore.pyqtSignal(bool)

    def __init__(self, get_app3d, parent=None):
        super().__init__(parent)
        self.get_app3d = get_app3d
        self.setObjectName("LeftSidebar")
        self._setup_ui()

    def _setup_ui(self):
        self.bar_width = 10  # Уменьшили с 28 до 24
        self.panel_width = 300  # Уменьшили с 320 до 300
        self.setFixedWidth(self.bar_width)  # Initially only bar width

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Vertical bar
        bar = QtWidgets.QWidget(self)
        bar.setFixedWidth(self.bar_width)
        bar_lay = QtWidgets.QVBoxLayout(bar)
        bar_lay.setContentsMargins(0, 0, 0, 0)
        bar_lay.setSpacing(0)
        btn_box = self._make_vertical_button("Бокс")
        btn_box.clicked.connect(self._toggle_box_panel)
        bar_lay.addWidget(btn_box)
        bar_lay.addStretch(1)
        root.addWidget(bar)

        # Panel container to the right of bar
        self.panel_container = QtWidgets.QStackedWidget()
        self.panel_container.setFixedWidth(self.panel_width)
        self.panel_container.hide()
        root.addWidget(self.panel_container)

        # Build Box panel
        self.box_panel = self._build_box_panel()
        self.panel_container.addWidget(self.box_panel)

    def _make_vertical_button(self, text: str) -> QtWidgets.QToolButton:
        btn = QtWidgets.QToolButton(self)
        btn.setText(text)
        btn.setCheckable(True)
        btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        btn.setMinimumHeight(120)
        btn.setStyleSheet("QToolButton{font-weight:600;}")
        btn.setArrowType(QtCore.Qt.RightArrow)
        return btn

    def _toggle_box_panel(self, checked: bool):
        if checked:
            self.panel_container.setCurrentWidget(self.box_panel)
            self.panel_container.show()
            self.setFixedWidth(self.bar_width + self.panel_width)  # Expand width
        else:
            self.panel_container.hide()
            self.setFixedWidth(self.bar_width)  # Collapse to bar width only
        self.toggled.emit(checked)

    def _build_box_panel(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        w.setObjectName("BoxPanel")
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        # Panel title
        title = QtWidgets.QLabel("Настройки прицепа")
        title.setObjectName("PanelTitle")
        title.setStyleSheet("QLabel#PanelTitle { font-weight: bold; font-size: 14px; margin-bottom: 10px; }")
        lay.addWidget(title)

        # Open/Close group
        gb_state = QtWidgets.QGroupBox("Состояние тента")
        v = QtWidgets.QVBoxLayout(gb_state)
        btn_open = QtWidgets.QRadioButton("Открыт")
        btn_close = QtWidgets.QRadioButton("Закрыт")
        btn_open.setChecked(True)
        v.addWidget(btn_open)
        v.addWidget(btn_close)
        btn_open.toggled.connect(lambda on: on and self._set_tent_alpha(0.0))
        btn_close.toggled.connect(lambda on: on and self._set_tent_alpha(0.3))
        lay.addWidget(gb_state)

        # Presets group
        gb_presets = QtWidgets.QGroupBox("Размеры")
        form = QtWidgets.QFormLayout(gb_presets)
        presets = [
            ("Тент 13.6", 1360, 260, 245),
            ("Мега", 1360, 300, 245),
            ("Конт 40ф", 1203, 239, 235),
            ("Конт 20ф", 590, 239, 235),
            ("Рефр", 1340, 239, 235),
            ("Тент 16.5", 1650, 260, 245),
        ]
        grp = QtWidgets.QButtonGroup(gb_presets)
        grp.setExclusive(True)
        for title, W, H, D in presets:
            rb = QtWidgets.QRadioButton(title)
            grp.addButton(rb)
            form.addRow(rb)
            rb.toggled.connect(lambda on, w=W, h=H, d=D: on and self._switch_truck(w, h, d))
        lay.addWidget(gb_presets)

        # Custom size
        gb_custom = QtWidgets.QGroupBox("Свой размер")
        grid = QtWidgets.QGridLayout(gb_custom)
        self.ed_w = QtWidgets.QLineEdit(); self.ed_h = QtWidgets.QLineEdit(); self.ed_d = QtWidgets.QLineEdit()
        for ed in (self.ed_w, self.ed_h, self.ed_d):
            ed.setMaxLength(4)
            ed.setValidator(QtGui.QIntValidator(1, 9999, w))
            ed.setPlaceholderText("см")
        grid.addWidget(QtWidgets.QLabel("Длина"), 0, 0); grid.addWidget(self.ed_w, 0, 1)
        grid.addWidget(QtWidgets.QLabel("Высота"), 1, 0); grid.addWidget(self.ed_h, 1, 1)
        grid.addWidget(QtWidgets.QLabel("Ширина"), 2, 0); grid.addWidget(self.ed_d, 2, 1)
        self.cb_custom = QtWidgets.QCheckBox("Свой размер")
        grid.addWidget(self.cb_custom, 3, 0, 1, 2)
        btn_apply = QtWidgets.QPushButton("Применить")
        grid.addWidget(btn_apply, 4, 0, 1, 2)
        btn_apply.clicked.connect(self._apply_custom)
        lay.addWidget(gb_custom)

        # Reset
        btn_reset = QtWidgets.QPushButton("Сбросить")
        btn_reset.clicked.connect(self._reset_defaults)
        lay.addWidget(btn_reset)

        lay.addStretch(1)
        return w

    def _apply_custom(self):
        if not self.cb_custom.isChecked():
            return
        try:
            w = int(self.ed_w.text())
            h = int(self.ed_h.text())
            d = int(self.ed_d.text())
        except Exception:
            return
        self._switch_truck(w, h, d)

    def _reset_defaults(self):
        # Default: Тент 16.5 открыт
        self._set_tent_alpha(0.0)
        self._switch_truck(1650, 260, 245)

    # helpers
    def _app3d(self):
        try:
            return self.get_app3d()
        except Exception:
            return None

    def _set_tent_alpha(self, a: float):
        app = self._app3d()
        if app:
            app.set_tent_alpha(a)

    def _switch_truck(self, w: int, h: int, d: int):
        app = self._app3d()
        if app:
            app.switch_truck(w, h, d)


