from PyQt5 import QtWidgets, QtGui

from GUI.settings_window.camera_control_widget import CameraControlWidget
from GUI.settings_window.graphics_widget import GraphicsWidget
from GUI.settings_window.grid_widget import GridWidget
from utils.setting_deploy import get_resource_path
from core.i18n import tr, translation_manager, TranslatableMixin


class GeneralWidget(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.title_btn = QtWidgets.QPushButton()
        self.title_btn.setCheckable(False)
        self.title_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                text-align: left;
            }
        """)
        layout.addWidget(self.title_btn)

        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.autosave_cb = QtWidgets.QCheckBox()
        self.autosave_cb.setChecked(True)
        self.autosave_cb.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                font-weight: 500;
                color: #2c3e50;
                spacing: 6px;
                padding: 2px;
            }
        """)
        self.autosave_label = QtWidgets.QLabel()
        form.addRow(self.autosave_label, self.autosave_cb)

        self.backup_cb = QtWidgets.QCheckBox()
        self.backup_cb.setChecked(False)
        self.backup_cb.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                font-weight: 500;
                color: #2c3e50;
                spacing: 6px;
                padding: 2px;
            }
        """)
        self.backup_label = QtWidgets.QLabel()
        form.addRow(self.backup_label, self.backup_cb)

        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.setMinimumWidth(120)
        self.language_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-size: 11px;
            }
        """)
        
        available_languages = translation_manager.get_available_languages()
        for lang_code, lang_name in available_languages.items():
            self.language_combo.addItem(lang_name, lang_code)
        
        current_lang = translation_manager.get_current_language()
        current_index = self.language_combo.findData(current_lang)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        
        self.language_label = QtWidgets.QLabel()
        form.addRow(self.language_label, self.language_combo)

        layout.addWidget(content_widget)
        layout.addStretch()
        
        self.retranslate_ui()

    def on_language_changed(self):
        lang_code = self.language_combo.currentData()
        translation_manager.set_language(lang_code)

    def retranslate_ui(self):
        self.title_btn.setText(f"⚙️ {tr('Общие настройки')}")
        self.autosave_label.setText(f"{tr('Автосохранение')}:")
        self.backup_label.setText(f"{tr('Создавать резервные копии')}:")
        self.language_label.setText(f"{tr('Язык')}:")


class SettingsWindow(QtWidgets.QDialog, TranslatableMixin):
    def __init__(self, camera, graphics_manager=None, units_manager=None, parent=None):
        super().__init__(parent)
        self.content_stack = None
        self.title_label = None
        self.category_list = None
        self.search_edit = None
        self.categories = None
        self.camera = camera
        self.graphics_manager = graphics_manager
        self.units_manager = units_manager
        self.search_index = {}
        self.setWindowIcon(QtGui.QIcon(get_resource_path("assets/icon/logo.png")))
        self.setModal(True)
        self.resize(680, 580)
        self.setMinimumSize(600, 480)
        self.setup_ui()
        self.build_search_index()
        self.retranslate_ui()

    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        search_layout = QtWidgets.QHBoxLayout()
        search_layout.setContentsMargins(8, 8, 8, 6)

        self.search_label = QtWidgets.QLabel()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.textChanged.connect(self.on_search_changed)
        self.search_edit.setMinimumWidth(300)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #c0c0c0;
                border-radius: 2px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)

        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addStretch()

        main_layout.addLayout(search_layout)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(separator)

        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.category_list = QtWidgets.QListWidget()
        self.category_list.setFixedWidth(160)
        self.category_list.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.category_list.setStyleSheet("""
            QListWidget {
                border-right: 1px solid #c0c0c0;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)

        self.categories = [
            tr("Управление"),
            tr("Графика"),
            tr("Сетка"),
            tr("Единицы"),
            tr("Общие")
        ]

        for category in self.categories:
            self.category_list.addItem(category)

        self.category_list.setCurrentRow(0)
        self.category_list.currentRowChanged.connect(self.on_category_changed)

        content_layout.addWidget(self.category_list)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        content_layout.addWidget(separator)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.title_label = QtWidgets.QLabel("Управление")
        self.title_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            padding: 12px 8px; 
            background-color: #ecf0f1;
            color: #2c3e50;
            border-bottom: 1px solid #bdc3c7;
        """)
        right_layout.addWidget(self.title_label)

        self.content_stack = QtWidgets.QStackedWidget()

        camera_widget = CameraControlWidget(self.camera, self)
        graphics_widget = GraphicsWidget(self.graphics_manager, self)
        grid_widget = GridWidget(self.graphics_manager, self)
        units_widget = UnitsWidget(self.units_manager, self)
        general_widget = GeneralWidget(self)

        self.content_stack.addWidget(camera_widget)
        self.content_stack.addWidget(graphics_widget)
        self.content_stack.addWidget(grid_widget)
        self.content_stack.addWidget(units_widget)
        self.content_stack.addWidget(general_widget)

        right_layout.addWidget(self.content_stack)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(8, 8, 8, 8)
        button_layout.addStretch()

        self.close_btn = QtWidgets.QPushButton()
        self.close_btn.setMinimumWidth(80)
        self.close_btn.setStyleSheet("""
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
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        right_layout.addLayout(button_layout)

        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right_layout)
        content_layout.addWidget(right_widget)

        main_layout.addLayout(content_layout)

    def build_search_index(self):
        self.search_index = {
            'вращение': 'Управление',
            'панорамирование': 'Управление',
            'масштабирование': 'Управление',
            'инерция': 'Управление',
            'затухание': 'Управление',
            'скорость': 'Управление',
            'радиус': 'Управление',
            'угол': 'Управление',
            'инверсия': 'Управление',
            'инвертировать': 'Управление',
            'ограничения': 'Управление',
            'чувствительность': 'Управление',
            'освещение': 'Графика',
            'свет': 'Графика',
            'интенсивность': 'Графика',
            'блики': 'Графика',
            'материалы': 'Графика',
            'цвет': 'Графика',
            'фон': 'Графика',
            'тягач': 'Графика',
            'сетка': 'Сетка',
            'прозрачность': 'Сетка',
            'ячейки': 'Сетка',
            'размер': 'Сетка',
            'отображение': 'Сетка',
            'grid': 'Сетка',
            'единицы': 'Единицы',
            'измерения': 'Единицы',
            'сантиметры': 'Единицы',
            'метры': 'Единицы',
            'футы': 'Единицы',
            'ярды': 'Единицы',
            'килограммы': 'Единицы',
            'фунты': 'Единицы',
            'стоуны': 'Единицы',
            'расстояние': 'Единицы',
            'вес': 'Единицы',
            'автосохранение': 'Общие',
            'резервные': 'Общие',
            'копии': 'Общие',
            'язык': 'Общие',
            'backup': 'Общие'
        }

    def on_search_changed(self, text):
        if not text.strip():
            for i in range(self.category_list.count()):
                self.category_list.item(i).setHidden(False)
            return

        text = text.lower().strip()
        found_categories = set()

        for keyword, category in self.search_index.items():
            if text in keyword:
                found_categories.add(category)

        for i in range(self.category_list.count()):
            item = self.category_list.item(i)
            category_name = item.text()

            if category_name in found_categories or text in category_name.lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def on_category_changed(self, index):
        if 0 <= index < len(self.categories):
            self.title_label.setText(self.categories[index])
            self.content_stack.setCurrentIndex(index)
    
    def retranslate_ui(self):
        self.setWindowTitle(tr("Настройки"))
        self.search_label.setText(f"{tr('Поиск')}:")
        self.search_edit.setPlaceholderText(tr("Введите критерий поиска..."))
        self.close_btn.setText(tr("Закрыть"))
        
        self.categories = [
            tr("Управление"),
            tr("Графика"),
            tr("Сетка"), 
            tr("Единицы"),
            tr("Общие")
        ]
        
        current_index = self.category_list.currentRow()
        self.category_list.clear()
        for category in self.categories:
            self.category_list.addItem(category)
        
        if 0 <= current_index < len(self.categories):
            self.category_list.setCurrentRow(current_index)
            self.title_label.setText(self.categories[current_index])


def get_reset_button_style():
    return """
        QPushButton {
            font-size: 11px;
            color: #2c3e50;
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 8px;
            min-height: 24px;
        }
        QPushButton:hover {
            background-color: #d5dbdb;
        }
        QPushButton:pressed {
            background-color: #bdc3c7;
        }
    """


class UnitsWidget(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, units_manager, parent=None):
        super().__init__(parent)
        self.units_manager = units_manager
        self.setup_ui()
        self.load_current_settings()
        self.retranslate_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Заголовок секции как в sidebar
        self.title_btn = QtWidgets.QPushButton()
        self.title_btn.setCheckable(False)
        self.title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.title_btn)

        # Контент секции
        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        # Комбобокс для расстояний
        self.distance_combo = QtWidgets.QComboBox()
        self.distance_combo.setStyleSheet(self.get_combobox_style())
        if self.units_manager:
            for unit in self.units_manager.DISTANCE_UNITS.keys():
                name = self.units_manager.get_distance_name(unit)
                self.distance_combo.addItem(name, unit)

        # Комбобокс для веса
        self.weight_combo = QtWidgets.QComboBox()
        self.weight_combo.setStyleSheet(self.get_combobox_style())
        if self.units_manager:
            for unit in self.units_manager.WEIGHT_UNITS.keys():
                name = self.units_manager.get_weight_name(unit)
                self.weight_combo.addItem(name, unit)

        self.distance_label = QtWidgets.QLabel()
        self.weight_label = QtWidgets.QLabel()
        form.addRow(self.distance_label, self.distance_combo)
        form.addRow(self.weight_label, self.weight_combo)

        layout.addWidget(content_widget)

        # Кнопки
        self.create_buttons(layout)
        layout.addStretch()

    def create_buttons(self, layout):
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.addStretch()

        self.reset_btn = QtWidgets.QPushButton()
        self.reset_btn.setStyleSheet(get_reset_button_style())
        self.reset_btn.setMinimumWidth(80)
        self.reset_btn.clicked.connect(self.reset_settings)

        self.apply_btn = QtWidgets.QPushButton()
        self.apply_btn.setStyleSheet(self.get_apply_button_style())
        self.apply_btn.setMinimumWidth(80)
        self.apply_btn.clicked.connect(self.apply_settings)

        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.apply_btn)
        layout.addLayout(button_layout)

    def load_current_settings(self):
        if not self.units_manager:
            return
        
        # Устанавливаем текущие единицы измерения
        distance_index = self.distance_combo.findData(self.units_manager.distance_unit)
        if distance_index >= 0:
            self.distance_combo.setCurrentIndex(distance_index)

        weight_index = self.weight_combo.findData(self.units_manager.weight_unit)
        if weight_index >= 0:
            self.weight_combo.setCurrentIndex(weight_index)

    def apply_settings(self):
        if not self.units_manager:
            return
        
        distance_unit = self.distance_combo.currentData()
        weight_unit = self.weight_combo.currentData()
        self.units_manager.set_units(distance_unit, weight_unit)

        # Показываем сообщение об успешном применении
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle(tr("Настройки"))
        msg.setText(tr("Единицы измерения обновлены успешно!"))
        msg.exec_()

    def reset_settings(self):
        reply = QtWidgets.QMessageBox.question(
            self, tr('Сброс настроек'),
            tr('Вы уверены, что хотите сбросить единицы измерения до заводских (см/кг)?'),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            if self.units_manager:
                self.units_manager.set_units('cm', 'kg')
                self.load_current_settings()

                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Information)
                msg.setWindowTitle(tr("Настройки"))
                msg.setText(tr("Единицы измерения сброшены до заводских!"))
                msg.exec_()

    def get_section_title_style(self):
        return """
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                text-align: left;
            }
        """

    def get_combobox_style(self):
        return """
            QComboBox {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-size: 11px;
                min-width: 150px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #bdc3c7;
                border-left-style: solid;
            }
        """

    def retranslate_ui(self):
        self.title_btn.setText(f"📏 {tr('Единицы измерения')}")
        self.distance_label.setText(f"{tr('Расстояние')}:")
        self.weight_label.setText(f"{tr('Вес')}:")
        self.reset_btn.setText(tr("Сбросить"))
        self.apply_btn.setText(tr("Применить"))
        
        # Обновляем тексты в комбобоксах
        if self.units_manager:
            current_distance = self.distance_combo.currentData()
            current_weight = self.weight_combo.currentData()
            
            self.distance_combo.clear()
            for unit in self.units_manager.DISTANCE_UNITS.keys():
                name = self.units_manager.get_distance_name(unit)
                self.distance_combo.addItem(name, unit)
            
            self.weight_combo.clear()
            for unit in self.units_manager.WEIGHT_UNITS.keys():
                name = self.units_manager.get_weight_name(unit)
                self.weight_combo.addItem(name, unit)
            
            # Восстанавливаем выбранные значения
            if current_distance:
                distance_index = self.distance_combo.findData(current_distance)
                if distance_index >= 0:
                    self.distance_combo.setCurrentIndex(distance_index)
            
            if current_weight:
                weight_index = self.weight_combo.findData(current_weight)
                if weight_index >= 0:
                    self.weight_combo.setCurrentIndex(weight_index)

    def get_apply_button_style(self):
        return """
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
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """
