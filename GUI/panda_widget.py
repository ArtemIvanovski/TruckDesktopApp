import json
import logging
import os
import sys

from PyQt5 import QtWidgets, QtCore
from GUI.box_info_widget import BoxInfoWidget
from core.i18n import tr, TranslatableMixin


print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:

    from GUI.truck_loading_app import TruckLoadingApp
    print("TruckLoadingApp imported successfully")
except ImportError as e:
    print(f"Import error: {e}")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AxleResultsOverlay(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, parent=None, units_manager=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setStyleSheet("QLabel { color: #000; font-size: 12px; }")
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(2)
        self.lbl_n1 = QtWidgets.QLabel()
        self.lbl_n2 = QtWidgets.QLabel()
        self.lbl_n3 = QtWidgets.QLabel()
        self.lbl_mg = QtWidgets.QLabel()
        for lbl in (self.lbl_n1, self.lbl_n2, self.lbl_n3, self.lbl_mg):
            lay.addWidget(lbl)
        self.results = None
        self.units_manager = units_manager
        try:
            if self.units_manager:
                self.units_manager.units_changed.connect(self.retranslate_ui)
        except Exception:
            pass
        self.hide()

    def set_results(self, results: dict):
        self.results = results or {}
        self._render()

    def _render(self):
        if not self.results:
            self.hide()
            return
        n1_t = self.results.get('N1')
        n2_t = self.results.get('N2')
        n3_t = self.results.get('N3')
        mg_t = self.results.get('Mg')
        by1_t = self.results.get('N1_max_kz')
        ru1_t = self.results.get('N1_max')
        by2_t = self.results.get('N2_max_kz')
        ru2_t = self.results.get('N2_max')
        by3_t = self.results.get('NPP_max_kz')
        ru3_t = self.results.get('NPP_max')

        if self.units_manager:
            symbol = self.units_manager.get_weight_symbol()
            def to_unit(val_tons: float) -> float:
                kg = (val_tons or 0) * 1000.0
                return self.units_manager.from_internal_weight(kg)
            n1 = to_unit(n1_t)
            n2 = to_unit(n2_t)
            n3 = to_unit(n3_t)
            mg = to_unit(mg_t)
            by1 = to_unit(by1_t)
            ru1 = to_unit(ru1_t)
            by2 = to_unit(by2_t)
            ru2 = to_unit(ru2_t)
            by3 = to_unit(by3_t)
            ru3 = to_unit(ru3_t)
            unit_str = symbol
        else:
            n1, n2, n3, mg = n1_t, n2_t, n3_t, mg_t
            by1, ru1, by2, ru2, by3, ru3 = by1_t, ru1_t, by2_t, ru2_t, by3_t, ru3_t
            unit_str = tr('т.')
        n1_ex = self.results.get('N1_exceeded')
        n2_ex = self.results.get('N2_exceeded')
        n3_ex = self.results.get('N3_exceeded')
        map_ex = self.results.get('Map_exceeded')
        color1 = "#d34e4e" if n1_ex else "#2c3e50"
        color2 = "#d34e4e" if n2_ex else "#2c3e50"
        color3 = "#d34e4e" if n3_ex else "#2c3e50"
        colorm = "#d34e4e" if map_ex else "#2c3e50"
        self.lbl_n1.setText(f"{tr('Нагрузка на ось 1')}: {n1} {unit_str} (BY {by1}, RU {ru1})")
        self.lbl_n1.setStyleSheet(f"color: {color1}; font-size: 12px;")
        self.lbl_n2.setText(f"{tr('Нагрузка на ось 2')}: {n2} {unit_str} (BY {by2}, RU {ru2})")
        self.lbl_n2.setStyleSheet(f"color: {color2}; font-size: 12px;")
        self.lbl_n3.setText(f"{tr('Нагрузка на три оси п/прицепа')}: {n3} {unit_str} (BY {by3}, RU {ru3})")
        self.lbl_n3.setStyleSheet(f"color: {color3}; font-size: 12px;")
        self.lbl_mg.setText(f"{tr('Масса груза')}: {mg} {unit_str}")
        self.lbl_mg.setStyleSheet(f"color: {colorm}; font-size: 12px;")
        self.adjustSize()
        self.show()

    def position_below_box_info(self, panda_widget):
        try:
            parent = self.parentWidget()
            if parent and panda_widget:
                top_left = panda_widget.mapTo(parent, QtCore.QPoint(0, 0))
                x = top_left.x() + panda_widget.width() - self.width() - 10
                y = top_left.y() + 10 + 4 + 120
                self.move(x, y)
                self.raise_()
        except Exception:
            pass

    def retranslate_ui(self):
        if self.results:
            self._render()


class PandaWidget(QtWidgets.QWidget):
    ready = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_NativeWindow)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        self.setAutoFillBackground(False)
        self.setAcceptDrops(True)
        self.setMinimumSize(800, 500)
        self.app3d = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._step)
        self.timer.start(16)
        
        # Делаем инфо-виджет дочерним к окну, чтобы перекрывать native-окно Panda3D
        # Передаем общий UnitsManager из главного окна, если есть
        shared_units = None
        try:
            mw = self.window()
            if hasattr(mw, 'units_manager'):
                shared_units = mw.units_manager
        except Exception:
            pass
        self.box_info_widget = BoxInfoWidget(self.window(), shared_units)
        self.axle_overlay = AxleResultsOverlay(self.window(), shared_units)
        
        QtCore.QTimer.singleShot(100, self._init_panda)

    def _init_panda(self):
        try:
            handle = int(self.winId())
            dpr = 1.0
            wh = self.window().windowHandle()
            if wh:
                dpr = float(wh.devicePixelRatio())
            w = int(max(1, round(self.width() * dpr)))
            h = int(max(1, round(self.height() * dpr)))
            logging.info(f"[Qt] Creating Panda3D with parent HWND={handle}, size=({w}x{h}), dpr={dpr}")
            self.app3d = TruckLoadingApp(
                window_type='none',
                embed_parent_window=handle,
                embed_size=(w, h),
                enable_direct_gui=False,
            )
            self.app3d.set_panda_widget(self)
            self.ready.emit()
        except Exception as e:
            logging.error(f"[Qt] Failed to init Panda3D: {e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            try:
                json.loads(event.mimeData().text())
                event.acceptProposedAction()
            except:
                event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        try:
            box_data = json.loads(event.mimeData().text())
            print(f"[Drop] Received box data for {box_data.get('label', 'Unknown')} with size: {box_data.get('width')}x{box_data.get('height')}x{box_data.get('depth')} (color will be determined by size)")
            
            if self.app3d:
                drop_pos = event.pos()
                screen_x = drop_pos.x() / self.width()
                screen_y = 1.0 - (drop_pos.y() / self.height())

                world_pos = self.screen_to_world(screen_x, screen_y)
                # Создаем новую коробку для 3D сцены (с quantity=1 для отдельного экземпляра)
                single_box_data = box_data.copy()
                single_box_data['quantity'] = 1  # Перетаскиваем только одну коробку
                
                try:
                    box_node = self.app3d.create_3d_box_from_data(single_box_data, world_pos)
                    
                    if box_node:
                        # Устанавливаем правильный action для успешного drag&drop
                        event.setDropAction(QtCore.Qt.MoveAction)
                        event.accept()
                        print(f"[Drop] Successfully placed box: {box_data.get('label', 'Unknown')}")
                        logging.info(f"Successfully dropped box: {box_data.get('label', 'Unknown')}")
                    else:
                        print(f"[Drop] Failed to place box: {box_data.get('label', 'Unknown')} - create_3d_box_from_data returned None")
                        event.ignore()
                except Exception as e:
                    print(f"[Drop] Exception creating 3D box: {e}")
                    event.ignore()
            else:
                event.ignore()
        except Exception as e:
            logging.error(f"Error handling drop: {e}")
            print(f"[Drop] Error: {e}")
            event.ignore()

    def screen_to_world(self, screen_x, screen_y):
        if not self.app3d:
            return (0, 0, 0)

        # Размещаем коробки перед грузовиком в зоне размещения
        truck_depth = getattr(self.app3d, 'truck_depth', 245)
        truck_front_y = truck_depth / 2  # Передняя граница грузовика
        placement_zone_start = truck_front_y + 150  # Начало зоны размещения
        placement_zone_depth = 400  # Глубина зоны размещения
        
        # Преобразуем экранные координаты в мировые
        world_x = (screen_x - 0.5) * 1200  # Расширяем диапазон X
        world_y = placement_zone_start + screen_y * placement_zone_depth  # Размещаем в зоне перед грузовиком
        world_z = 135  # Уровень земли
        
        print(f"[ScreenToWorld] Screen({screen_x:.3f}, {screen_y:.3f}) -> World({world_x:.1f}, {world_y:.1f}, {world_z:.1f})")
        return (world_x, world_y, world_z)

    def _step(self):
        try:
            if self.app3d:
                self.app3d.taskMgr.step()
        except Exception as e:
            logging.error(f"[Qt] taskMgr.step error: {e}")

    def resizeEvent(self, event):
        if self.app3d and hasattr(self.app3d, 'resize_window'):
            dpr = 1.0
            wh = self.window().windowHandle()
            if wh:
                dpr = float(wh.devicePixelRatio())
            w = int(max(1, round(self.width() * dpr)))
            h = int(max(1, round(self.height() * dpr)))
            logging.info(f"[Qt] resizeEvent -> logical={self.width()}x{self.height()} physical={w}x{h} dpr={dpr}")
            self.app3d.resize_window(w, h)
        
        self.box_info_widget.position_at_corner(self)
        self.axle_overlay.position_below_box_info(self)
        super().resizeEvent(event)
    
    def show_box_info(self, box_data):
        logging.debug(f"[PandaWidget] show_box_info called for box: {box_data.get('label', 'Unknown')}")
        self.box_info_widget.show_box_info(box_data)
        self.box_info_widget.position_at_corner(self)
        self.axle_overlay.position_below_box_info(self)

    def update_axle_results_overlay(self, visible: bool, results: dict):
        if not visible:
            self.axle_overlay.hide()
            return
        self.axle_overlay.set_results(results)
        self.axle_overlay.position_below_box_info(self)