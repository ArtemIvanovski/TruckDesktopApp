from PyQt5 import QtWidgets, QtCore
from core.i18n import tr, TranslatableMixin
from GUI.trucks.truck_item_widget import TruckItemWidget


class TruckListWidget(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, get_truck_manager, parent=None):
        super().__init__(parent)
        self._get_manager = get_truck_manager
        self.truck_manager = None
        self._attached = False
        self._setup_ui()
        QtCore.QTimer.singleShot(0, self._try_attach)

    def _setup_ui(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        self.header_label = QtWidgets.QLabel()
        self.header_label.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                padding: 6px;
                background-color: #f1c40f;
                border-radius: 3px;
            }
            """
        )
        lay.addWidget(self.header_label)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.container = QtWidgets.QWidget()
        self.container_lay = QtWidgets.QVBoxLayout(self.container)
        self.container_lay.setContentsMargins(0, 0, 0, 0)
        self.container_lay.setSpacing(4)
        self.container_lay.addStretch()

        self.scroll.setWidget(self.container)
        lay.addWidget(self.scroll)

        btns = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton()
        self.btn_add.setStyleSheet(
            """
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: white;
                background-color: #27ae60;
                border: none;
                border-radius: 4px;
                padding: 8px;
                min-height: 24px;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:pressed { background-color: #229954; }
            """
        )
        self.btn_add.clicked.connect(self._on_add)

        self.btn_remove = QtWidgets.QPushButton()
        self.btn_remove.setStyleSheet(
            """
            QPushButton {
                font-size: 10px;
                color: white;
                background-color: #e74c3c;
                border: none;
                border-radius: 3px;
                padding: 6px;
            }
            QPushButton:hover { background-color: #c0392b; }
            """
        )
        self.btn_remove.clicked.connect(self._on_remove)

        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_remove)
        btns.addStretch(1)
        lay.addLayout(btns)

        self.retranslate_ui()

    def _try_attach(self):
        mgr = None
        try:
            mgr = self._get_manager()
        except Exception:
            mgr = None
        if mgr and not self._attached:
            self.truck_manager = mgr
            try:
                self.truck_manager.add_on_changed(self._rebuild)
            except Exception:
                pass
            self._attached = True
            self._rebuild()
        elif not mgr:
            QtCore.QTimer.singleShot(200, self._try_attach)

    def _clear_items(self):
        while self.container_lay.count() > 1:
            item = self.container_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _rebuild(self):
        if not self.truck_manager:
            return
        self._clear_items()
        items = self.truck_manager.get_items()
        for idx, t in enumerate(items):
            w = TruckItemWidget(self.truck_manager, t, idx, self.container)
            self.container_lay.insertWidget(self.container_lay.count() - 1, w)
        self._update_header()

    def _update_header(self):
        if not self.truck_manager:
            self.header_label.setText(f"{tr('Грузовики')} (0)")
            return
        total = len(self.truck_manager.get_items())
        self.header_label.setText(f"{tr('Грузовики')} ({total})")

    def _on_add(self):
        if self.truck_manager:
            self.truck_manager.add_truck()

    def _on_remove(self):
        if self.truck_manager:
            self.truck_manager.remove_current_truck()

    def retranslate_ui(self):
        self.btn_add.setText(tr('Добавить'))
        self.btn_remove.setText(tr('Удалить'))
        self._update_header()

