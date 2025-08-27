from PyQt5 import QtWidgets, QtCore

from core.i18n import tr, TranslatableMixin
from utils.settings_manager import SettingsManager


class TruckManagementWidget(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, units_manager, get_app3d, parent=None):
        super().__init__(parent)
        self.units_manager = units_manager
        self.get_app3d = get_app3d
        self.settings_manager = SettingsManager()
        self.trucks = []  # Список грузовиков (UI-only, not persisted)
        self.current_truck_index = 0
        self.expanded_trucks = set()  # Набор развернутых грузовиков
        self.radio_group = None
        self._setup_ui()
        # Загружаем настройку отображения на главном экране
        self._load_display_setting()
        # Инициализация: гарантируем, что есть хотя бы один грузовик
        self._init_trucks()
        
        # Подключаемся к изменениям единиц измерения
        if self.units_manager:
            self.units_manager.units_changed.connect(self._on_units_changed)
        
        self.retranslate_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Заголовок
        self.title = QtWidgets.QLabel()
        self.title.setStyleSheet("""
            QLabel { 
                font-weight: bold; 
                font-size: 12px; 
                color: #2c3e50;
                padding: 4px;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.title)

        # Чекбокс отображения на главном экране
        self.display_checkbox_container = QtWidgets.QWidget()
        display_layout = QtWidgets.QHBoxLayout(self.display_checkbox_container)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(6)
        
        self.display_label = QtWidgets.QLabel()
        self.display_checkbox = QtWidgets.QCheckBox()
        self.display_checkbox.toggled.connect(self._on_display_toggled)
        
        display_layout.addWidget(self.display_label)
        display_layout.addWidget(self.display_checkbox)
        display_layout.addStretch(1)
        layout.addWidget(self.display_checkbox_container)

        # Контейнер для списка грузовиков
        self.trucks_container = QtWidgets.QWidget()
        self.trucks_layout = QtWidgets.QVBoxLayout(self.trucks_container)
        self.trucks_layout.setContentsMargins(0, 0, 0, 0)
        self.trucks_layout.setSpacing(4)
        
        layout.addWidget(self.trucks_container)

        # Кнопки управления
        buttons_layout = QtWidgets.QHBoxLayout()
        
        self.btn_add = QtWidgets.QPushButton()
        self.btn_add.setStyleSheet("""
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
        """)
        self.btn_add.clicked.connect(self._on_add_truck)
        
        self.btn_remove = QtWidgets.QPushButton()
        self.btn_remove.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: white;
                background-color: #e74c3c;
                border: none;
                border-radius: 4px;
                padding: 8px;
                min-height: 24px;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:pressed { background-color: #a93226; }
        """)
        self.btn_remove.clicked.connect(self._on_remove_truck)
        
        buttons_layout.addWidget(self.btn_add)
        buttons_layout.addWidget(self.btn_remove)
        buttons_layout.addStretch(1)
        layout.addLayout(buttons_layout)

        layout.addStretch(1)

    def _load_settings(self):
        """Больше не сохраняем список грузовиков между сессиями"""
        # Отображение на главном экране загружаем отдельно
        self.trucks = [{'name': tr('Грузовик 1'), 'ready': False, 'boxes': 0, 'weight': 0}]
        self.current_truck_index = 0

    def _load_display_setting(self):
        """Загрузить флаг отображения оверлея из settings.json"""
        try:
            section = self.settings_manager.get_section('truck_management')
            show = bool(section.get('show_on_main_screen', False))
            self.display_checkbox.setChecked(show)
        except Exception:
            self.display_checkbox.setChecked(False)

    def _save_settings(self):
        """Сохраняем только флаг отображения на главном экране"""
        self.settings_manager.update_section('truck_management', {
            'show_on_main_screen': self.display_checkbox.isChecked()
        })

    def _init_trucks(self):
        """Инициализировать отображение грузовиков"""
        # Гарантируем наличие хотя бы одного грузовика по умолчанию
        if not self.trucks:
            self._load_settings()
        self._rebuild_trucks_list()
        # Публикуем в оверлей текущее состояние при инициализации
        self._publish_truck_info_to_main()
        # Синхронизируемся с главным менеджером грузовиков
        self._sync_with_truck_manager()

    def _rebuild_trucks_list(self):
        """Перестроить список грузовиков"""
        # Очищаем существующие виджеты
        for i in reversed(range(self.trucks_layout.count())):
            child = self.trucks_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        # Пересоздаем группу радиокнопок для эксклюзивного выбора
        self.radio_group = QtWidgets.QButtonGroup(self)
        self.radio_group.setExclusive(True)

        # Создаем виджеты для каждого грузовика
        for i, truck in enumerate(self.trucks):
            truck_widget = self._create_truck_widget(truck, i)
            self.trucks_layout.addWidget(truck_widget)

        # Гарантируем, что выбран текущий по индексу
        if self.radio_group:
            btn = self.radio_group.button(self.current_truck_index)
            if btn:
                btn.setChecked(True)

    def _create_truck_widget(self, truck, index):
        """Создать виджет грузовика"""
        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Главная кнопка грузовика (коллапсирующая)
        truck_btn = QtWidgets.QPushButton()
        truck_btn.setCheckable(True)
        truck_btn.setChecked(index in self.expanded_trucks)
        truck_btn.clicked.connect(lambda checked, idx=index: self._toggle_truck_section(idx, checked))
        truck_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                text-align: left;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        
        # Обновляем текст кнопки
        self._update_truck_button_text(truck_btn, truck, index)
        container_layout.addWidget(truck_btn)

        # Раздел с деталями грузовика
        details_widget = QtWidgets.QWidget()
        details_layout = QtWidgets.QVBoxLayout(details_widget)
        details_layout.setContentsMargins(8, 4, 8, 8)
        details_layout.setSpacing(6)

        # Поле для редактирования названия
        name_layout = QtWidgets.QHBoxLayout()
        name_label = QtWidgets.QLabel(tr("Название") + ":")
        name_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #2c3e50;")
        
        name_edit = QtWidgets.QLineEdit(truck.get('name', tr('Грузовик')))
        name_edit.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        name_edit.editingFinished.connect(lambda idx=index: self._on_name_changed(idx, name_edit.text()))
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_edit)
        details_layout.addLayout(name_layout)

        # Радиокнопка для выбора текущего грузовика
        radio_btn = QtWidgets.QRadioButton(tr("Выбрать как текущий"))
        radio_btn.setChecked(index == self.current_truck_index)
        radio_btn.toggled.connect(lambda checked, idx=index: self._on_truck_selected(checked, idx))
        radio_btn.setStyleSheet("""
            QRadioButton {
                font-size: 11px;
                font-weight: 500;
                color: #2c3e50;
                spacing: 6px;
                padding: 2px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
        """)
        if self.radio_group:
            self.radio_group.addButton(radio_btn, index)
        details_layout.addWidget(radio_btn)

        # Чекбокс готовности к загрузке
        ready_checkbox = QtWidgets.QCheckBox(tr("Готов к загрузке"))
        ready_checkbox.setChecked(truck.get('ready', False))
        ready_checkbox.toggled.connect(lambda checked, idx=index: self._on_ready_toggled(checked, idx))
        ready_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #2c3e50;
                spacing: 4px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #27ae60;
                border-color: #229954;
            }
        """)
        details_layout.addWidget(ready_checkbox)

        # Информация о грузовике
        info_layout = QtWidgets.QHBoxLayout()
        info_layout.setSpacing(8)

        boxes_label = QtWidgets.QLabel(f"{tr('Коробки')}: {truck.get('boxes', 0)}")
        boxes_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #34495e;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 4px 6px;
            }
        """)

        weight_symbol = self.units_manager.get_weight_symbol() if self.units_manager else 'кг'
        weight_value = truck.get('weight', 1)
        if self.units_manager:
            weight_display = self.units_manager.from_internal_weight(weight_value)
        else:
            weight_display = weight_value
        weight_label = QtWidgets.QLabel(f"{tr('Общий вес')}: {weight_display:.1f} {weight_symbol}")
        weight_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #34495e;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 4px 6px;
            }
        """)

        info_layout.addWidget(boxes_label)
        info_layout.addWidget(weight_label)
        info_layout.addStretch(1)
        details_layout.addLayout(info_layout)

        # Скрываем детали, если секция не развернута
        if index not in self.expanded_trucks:
            details_widget.hide()

        container_layout.addWidget(details_widget)

        # Сохраняем ссылки на виджеты для обновления
        container.truck_btn = truck_btn
        container.details_widget = details_widget
        container.name_edit = name_edit
        container.radio_btn = radio_btn
        container.ready_checkbox = ready_checkbox
        container.boxes_label = boxes_label
        container.weight_label = weight_label
        container.truck_index = index

        return container

    def _update_truck_button_text(self, button, truck, index):
        """Обновить текст кнопки грузовика"""
        expanded = "▲" if index in self.expanded_trucks else "▼"
        button.setText(f"📋 {truck.get('name', tr('Грузовик'))} {expanded}")

    def _toggle_truck_section(self, index, checked):
        """Переключить раскрытие секции грузовика"""
        if checked:
            self.expanded_trucks.add(index)
        else:
            self.expanded_trucks.discard(index)
        
        # Обновляем отображение
        self._update_truck_widget(index)
        # Обновляем оверлей, если открыт
        self._publish_truck_info_to_main()

    def _update_truck_widget(self, index):
        """Обновить виджет конкретного грузовика"""
        for i in range(self.trucks_layout.count()):
            widget = self.trucks_layout.itemAt(i).widget()
            if hasattr(widget, 'truck_index') and widget.truck_index == index:
                truck = self.trucks[index]
                
                # Обновляем текст кнопки
                self._update_truck_button_text(widget.truck_btn, truck, index)
                
                # Показываем/скрываем детали
                if index in self.expanded_trucks:
                    widget.details_widget.show()
                else:
                    widget.details_widget.hide()
                
                widget.radio_btn.setChecked(index == self.current_truck_index)
                
                widget.ready_checkbox.setChecked(truck.get('ready', False))
                
                widget.name_edit.setText(truck.get('name', tr('Грузовик')))
                
                # Обновляем информацию
                widget.boxes_label.setText(f"{tr('Коробки')}: {truck.get('boxes', 1)}")
                
                weight_symbol = self.units_manager.get_weight_symbol() if self.units_manager else 'кг'
                weight_value = truck.get('weight', 1)
                if self.units_manager:
                    weight_display = self.units_manager.from_internal_weight(weight_value)
                else:
                    weight_display = weight_value
                widget.weight_label.setText(f"{tr('Общий вес')}: {weight_display:.1f} {weight_symbol}")
                break

    def _on_truck_selected(self, checked, index):
        """Обработка выбора грузовика"""
        if checked:
            self.current_truck_index = index
            self._save_settings()
            
            # Обновляем радиокнопки у всех грузовиков
            for i in range(self.trucks_layout.count()):
                widget = self.trucks_layout.itemAt(i).widget()
                if hasattr(widget, 'radio_btn'):
                    widget.radio_btn.setChecked(widget.truck_index == index)
            
            # Синхронизируем с главным менеджером
            truck_manager = self._get_truck_manager()
            if truck_manager:
                truck_manager.select_index(index)
            
            # Публикуем изменения
            self._publish_truck_info_to_main()

    def _on_ready_toggled(self, checked, index):
        """Обработка изменения готовности грузовика"""
        if index < len(self.trucks):
            self.trucks[index]['ready'] = checked
            self._save_settings()
            
            # Синхронизируем с главным менеджером
            truck_manager = self._get_truck_manager()
            if truck_manager and index < len(truck_manager.trucks):
                truck_manager.trucks[index].ready = checked
            
            # Публикуем изменения
            self._publish_truck_info_to_main()

    def _on_name_changed(self, index, new_name):
        """Обработка изменения названия грузовика"""
        if index < len(self.trucks) and new_name.strip():
            self.trucks[index]['name'] = new_name.strip()
            self._save_settings()
            
            # Синхронизируем с главным менеджером
            truck_manager = self._get_truck_manager()
            if truck_manager and index < len(truck_manager.trucks):
                truck_manager.trucks[index].name = new_name.strip()
            
            # Обновляем текст кнопки
            self._update_truck_widget(index)
            # Публикуем изменения
            self._publish_truck_info_to_main()

    def _on_display_toggled(self, checked):
        """Обработка изменения отображения на главном экране"""
        self._save_settings()
        self._publish_truck_info_to_main()

    def _on_units_changed(self):
        """Обработка изменения единиц измерения"""
        self._rebuild_trucks_list()
        self._publish_truck_info_to_main()

    def _on_add_truck(self):
        """Добавить новый грузовик"""
        new_index = len(self.trucks) + 1
        new_truck = {
            'name': f"{tr('Грузовик')} {new_index}",
            'ready': False,
            'boxes': 0,
            'weight': 0
        }
        self.trucks.append(new_truck)
        
        # Синхронизируем с главным менеджером
        truck_manager = self._get_truck_manager()
        if truck_manager:
            truck_manager.add_truck()
            truck_manager.trucks[-1].name = new_truck['name']
        
        self._rebuild_trucks_list()
        # Переходим на добавленный грузовик и публикуем
        self.current_truck_index = len(self.trucks) - 1
        self._publish_truck_info_to_main()

    def _on_remove_truck(self):
        """Удалить текущий грузовик"""
        if len(self.trucks) <= 1:
            # Не удаляем последний грузовик, но можем очистить сцену
            return
        
        # Удаляем выбранный грузовик
        removed_index = self.current_truck_index
        if removed_index < len(self.trucks):
            del self.trucks[removed_index]
            
            # Корректируем индекс текущего грузовика
            if self.current_truck_index >= len(self.trucks):
                self.current_truck_index = len(self.trucks) - 1
            
            # Удаляем из развернутых, если был развернут
            self.expanded_trucks.discard(removed_index)
            
            # Корректируем индексы развернутых грузовиков
            new_expanded = set()
            for idx in self.expanded_trucks:
                if idx > removed_index:
                    new_expanded.add(idx - 1)
                elif idx < removed_index:
                    new_expanded.add(idx)
            self.expanded_trucks = new_expanded
            
            # Синхронизируем с главным менеджером
            truck_manager = self._get_truck_manager()
            if truck_manager:
                truck_manager.remove_current_truck()
            
            # No persistence of list/selection
            self._rebuild_trucks_list()
            
            # TODO: Очистить сцену от объектов удаленного грузовика
            # Публикуем изменения
            self._publish_truck_info_to_main()

    def _get_truck_manager(self):
        """Получить менеджер грузовиков"""
        app = None
        try:
            app = self.get_app3d()
        except Exception:
            pass
        if not app:
            return None
        if hasattr(app, 'panda_widget') and app.panda_widget:
            return app.panda_widget.get_truck_manager()
        return None

    def _sync_with_truck_manager(self):
        """Синхронизировать с главным менеджером грузовиков"""
        truck_manager = self._get_truck_manager()
        if not truck_manager:
            QtCore.QTimer.singleShot(500, self._sync_with_truck_manager)
            return
        
        truck_manager.trucks.clear()
        for i, truck_data in enumerate(self.trucks):
            from core.trucks.truck_model import TruckModel
            truck = TruckModel(i + 1, truck_data['name'], 1650, 260, 245)
            truck.ready = truck_data.get('ready', False)
            truck_manager.trucks.append(truck)
        
        truck_manager.current_index = self.current_truck_index
        truck_manager._notify()

    def retranslate_ui(self):
        """Обновить переводы"""
        self.title.setText(tr("Управление грузовиками"))
        self.display_label.setText(tr("Отображать на главном экране") + ":")
        self.btn_add.setText(tr("Добавить"))
        self.btn_remove.setText(tr("Удалить"))

        # Перестраиваем список для обновления переводов
        self._rebuild_trucks_list()

    def _publish_truck_info_to_main(self):
        """Публикация информации о грузовике на главный экран"""
        try:
            app = self.get_app3d()
            if not app:
                return
            
            if hasattr(app, 'panda_widget') and app.panda_widget:
                truck_info = self._get_current_truck_info()
                app.panda_widget.update_truck_info_overlay(
                    visible=self.display_checkbox.isChecked(),
                    truck_info=truck_info,
                    truck_count=len(self.trucks),
                    current_index=self.current_truck_index
                )
        except Exception:
            pass

    def _get_current_truck_info(self):
        """Получить информацию о текущем грузовике"""
        if self.current_truck_index < len(self.trucks):
            truck = self.trucks[self.current_truck_index]
            
            weight_symbol = self.units_manager.get_weight_symbol() if self.units_manager else 'кг'
            weight_value = truck.get('weight', 1)
            if self.units_manager:
                weight_display = self.units_manager.from_internal_weight(weight_value)
            else:
                weight_display = weight_value
            
            return {
                'name': truck.get('name', tr('Грузовик')),
                'ready': truck.get('ready', False),
                'boxes': truck.get('boxes', 1),
                'weight': weight_display,
                'weight_symbol': weight_symbol
            }
        return None

    def switch_to_next_truck(self):
        """Переключить на следующий грузовик"""
        if self.current_truck_index < len(self.trucks) - 1:
            self.current_truck_index += 1
            self._on_truck_selected(True, self.current_truck_index)
            self._publish_truck_info_to_main()

    def switch_to_previous_truck(self):
        """Переключить на предыдущий грузовик"""
        if self.current_truck_index > 0:
            self.current_truck_index -= 1
            self._on_truck_selected(True, self.current_truck_index)
            self._publish_truck_info_to_main()
