import logging
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QPalette
from core.i18n import tr
from core.units import UnitsManager


class BoxInfoWidget(QWidget):
    def __init__(self, parent=None, units_manager: UnitsManager = None):
        super().__init__(parent)
        self.units_manager = units_manager or UnitsManager()
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)
        self._last_box_data = None
        
        self.setup_ui()
        # Обновлять вид при смене единиц
        try:
            self.units_manager.units_changed.connect(self._on_units_changed)
        except Exception:
            pass
        self.hide()
    
    def setup_ui(self):
        self.setFixedWidth(280)
        # Прозрачный для мыши, без рамок, обычный текст
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        font = QFont()
        font.setPointSize(14)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.label_info = QLabel()
        self.label_info.setFont(font)
        self.label_info.setStyleSheet("color: #000;")
        layout.addWidget(self.label_info)

        self.dimensions_info = QLabel()
        self.dimensions_info.setFont(font)
        self.dimensions_info.setStyleSheet("color: #000;")
        layout.addWidget(self.dimensions_info)

        self.weight_info = QLabel()
        self.weight_info.setFont(font)
        self.weight_info.setStyleSheet("color: #000;")
        layout.addWidget(self.weight_info)

        self.markings_info = QLabel()
        self.markings_info.setFont(font)
        self.markings_info.setWordWrap(True)
        self.markings_info.setStyleSheet("color: #000;")
        layout.addWidget(self.markings_info)

        self.additional_info = QLabel()
        self.additional_info.setFont(font)
        self.additional_info.setWordWrap(True)
        self.additional_info.setStyleSheet("color: #000;")
        layout.addWidget(self.additional_info)
    
    def show_box_info(self, box_data):
        logging.debug(f"[BoxInfoWidget] show_box_info called with data: {box_data}")
        if not box_data:
            logging.debug(f"[BoxInfoWidget] No box_data provided, hiding widget")
            self.hide()
            return
        
        try:
            self._last_box_data = box_data
            dist_symbol = self.units_manager.get_distance_symbol()
            weight_symbol = self.units_manager.get_weight_symbol()
            
            width = self.units_manager.from_internal_distance(box_data.get('width', 0))
            height = self.units_manager.from_internal_distance(box_data.get('height', 0))
            depth = self.units_manager.from_internal_distance(box_data.get('depth', 0))
            weight = self.units_manager.from_internal_weight(box_data.get('weight', 0))
            
            self.label_info.setText(f"{box_data.get('label', 'N/A')}")

            self.dimensions_info.setText(f"{width:.2f}×{height:.2f}×{depth:.2f} {dist_symbol}")

            self.weight_info.setText(f"{weight:.2f} {weight_symbol}")
            
            markings = box_data.get('cargo_markings', [])
            if markings:
                marking_names = []
                for marking in markings:
                    if marking in ['fragile', 'this_way_up', 'no_stack', 'keep_dry', 
                                 'center_gravity', 'alcohol', 'no_hooks', 'temperature']:
                        marking_names.append(tr(f'marking_{marking}'))
                
                if marking_names:
                    self.markings_info.setText(f"{', '.join(marking_names)}")
                    self.markings_info.show()
                else:
                    self.markings_info.hide()
            else:
                self.markings_info.hide()

            add_info_text = box_data.get('additional_info', '') or ''
            if isinstance(add_info_text, str) and add_info_text.strip():
                self.additional_info.setText(f"{add_info_text.strip()}")
                self.additional_info.show()
            else:
                self.additional_info.hide()
            
            self.adjustSize()
            self.show()
            # Убираем автоматическое скрытие - пусть показывается пока курсор на коробке
            # self.hide_timer.start(3000)
            
            logging.info(f"[BoxInfoWidget] Successfully displayed info for box: {box_data.get('label', 'Unknown')}")
            
        except Exception as e:
            logging.error(f"[BoxInfoWidget] Error showing box info: {e}")
    
    def position_at_corner(self, panda_widget):
        logging.debug(f"[BoxInfoWidget] position_at_corner called")
        try:
            parent = self.parentWidget()
            if parent and panda_widget:
                top_left = panda_widget.mapTo(parent, QPoint(0, 0))
                x = top_left.x() + panda_widget.width() - self.width() - 10
                y = top_left.y() + 10
                self.move(x, y)
                self.raise_()
                logging.debug(f"[BoxInfoWidget] Positioned at ({x}, {y})")
            else:
                logging.warning(f"[BoxInfoWidget] No valid parent/panda_widget for positioning")
        except Exception as e:
            logging.warning(f"[BoxInfoWidget] position_at_corner error: {e}")

    def _on_units_changed(self):
        try:
            if self.isVisible() and self._last_box_data:
                self.show_box_info(self._last_box_data)
        except Exception:
            pass
