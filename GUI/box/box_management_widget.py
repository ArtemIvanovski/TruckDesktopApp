from PyQt5 import QtWidgets
from PyQt5 import QtWidgets

from GUI.box.box_creation_widget import BoxCreationWidget
from GUI.box.box_list_widget import BoxListWidget
from core.box.box_manager import BoxManager


class BoxManagementWidget(QtWidgets.QWidget):
    def __init__(self, units_manager, parent=None):
        super().__init__(parent)
        self.units_manager = units_manager
        self.box_manager = BoxManager(self)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        creation_widget = BoxCreationWidget(self.units_manager, self)
        creation_widget.box_created.connect(self.box_manager.add_box)
        layout.addWidget(creation_widget)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)

        list_widget = BoxListWidget(self.box_manager, self)
        layout.addWidget(list_widget)

    def get_box_manager(self) -> BoxManager:
        return self.box_manager
