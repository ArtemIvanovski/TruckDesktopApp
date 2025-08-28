from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal

from core.i18n import tr, TranslatableMixin
from core.load_calculation.load_calculator import LoadCalculator
from core.error_management import ErrorReportingMixin, safe_method
from core.exceptions import ErrorCategory, ErrorSeverity


class LoadCalculationWidget(QtWidgets.QWidget, TranslatableMixin, ErrorReportingMixin):
    def __init__(self, units_manager, get_app3d, parent=None):
        super().__init__(parent)
        self.units_manager = units_manager
        self.get_app3d = get_app3d
        self.calculator = LoadCalculator()
        self._truck_manager = None
        self.setup_ui()
        self.retranslate_ui()
        
        self.calculator.settings_changed.connect(self.update_display)
        
        self._attach_to_truck_manager()
        if not self._truck_manager:
            QtCore.QTimer.singleShot(500, self._attach_to_truck_manager)
        self.update_trailer_length_from_truck()
        self.update_display()

    @safe_method(
        component="LoadCalculationWidget",
        category=ErrorCategory.CALCULATION,
        severity=ErrorSeverity.LOW,
        suppress_errors=True
    )
    def update_trailer_length_from_truck(self):
        app = self.get_app3d()
        if app and hasattr(app, 'truck_scene'):
            length_cm = app.truck_scene.truck_width
            self.calculator.set_trailer_length(length_cm)
            if hasattr(self, 'trailer_length_label'):
                self.trailer_length_label.setText(f"{length_cm / 100.0:.1f} м")

    @safe_method(
        component="LoadCalculationWidget",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.MEDIUM,
        suppress_errors=True
    )
    def _attach_to_truck_manager(self):
        app = self.get_app3d()
        if not app or not hasattr(app, 'panda_widget') or not app.panda_widget:
            QtCore.QTimer.singleShot(500, self._attach_to_truck_manager)
            return
        mgr = app.panda_widget.get_truck_manager()
        if not mgr:
            QtCore.QTimer.singleShot(500, self._attach_to_truck_manager)
            return
        if self._truck_manager is not mgr:
            self._truck_manager = mgr
            self._truck_manager.add_on_changed(self._on_truck_changed)
            self._load_from_current_truck()

    @safe_method(
        component="LoadCalculationWidget",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.LOW,
        suppress_errors=True
    )
    def _on_truck_changed(self):
        self._load_from_current_truck()
        self.update_trailer_length_from_truck()
        self.update_display()

    @safe_method(
        component="LoadCalculationWidget",
        category=ErrorCategory.FILE_IO,
        severity=ErrorSeverity.MEDIUM,
        suppress_errors=True
    )
    def _save_to_current_truck(self):
        app = self.get_app3d()
        if not app or not hasattr(app, 'panda_widget'):
            return
        mgr = app.panda_widget.get_truck_manager()
        if not mgr:
            return
        current = mgr.get_current()
        current.load_settings = dict(self.calculator.settings)
        mgr.capture_now()

    @safe_method(
        component="LoadCalculationWidget",
        category=ErrorCategory.FILE_IO,
        severity=ErrorSeverity.MEDIUM,
        suppress_errors=True
    )
    def _load_from_current_truck(self):
        app = self.get_app3d()
        if not app or not hasattr(app, 'panda_widget'):
            return
        mgr = app.panda_widget.get_truck_manager()
        if not mgr:
            return
        current = mgr.get_current()
        
        self.calculator.settings = self.calculator.default_settings.copy()
        
        if getattr(current, 'load_settings', None):
            self.calculator.settings.update(current.load_settings)
        
        self.calculator.settings_changed.emit()
        self._sync_ui_from_settings()

    @safe_method(
        component="LoadCalculationWidget",
        category=ErrorCategory.UI,
        severity=ErrorSeverity.LOW,
        suppress_errors=True
    )
    def _sync_ui_from_settings(self):
        if hasattr(self, 'display_checkbox'):
            old = self.display_checkbox.blockSignals(True)
            self.display_checkbox.setChecked(self.calculator.get_setting('show_on_main_screen'))
            self.display_checkbox.blockSignals(old)

        if hasattr(self, 'tractor_inputs'):
            for key, spin in self.tractor_inputs.items():
                if key in self.calculator.settings:
                    old = spin.blockSignals(True)
                    spin.setValue(float(self.calculator.get_setting(key)))
                    spin.blockSignals(old)

        if hasattr(self, 'trailer_inputs'):
            for key, spin in self.trailer_inputs.items():
                if key in self.calculator.settings:
                    old = spin.blockSignals(True)
                    spin.setValue(float(self.calculator.get_setting(key)))
                    spin.blockSignals(old)

        if hasattr(self, 'cargo_inputs'):
            for key, spin in self.cargo_inputs.items():
                if key in self.calculator.settings:
                    old = spin.blockSignals(True)
                    spin.setValue(float(self.calculator.get_setting(key)))
                    spin.blockSignals(old)

        self.update_trailer_length_from_truck()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

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

        self.display_checkbox_container = QtWidgets.QWidget()
        display_layout = QtWidgets.QHBoxLayout(self.display_checkbox_container)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(6)
        self.display_label = QtWidgets.QLabel()
        self.display_checkbox = QtWidgets.QCheckBox()
        self.display_checkbox.setChecked(self.calculator.get_setting('show_on_main_screen'))
        self.display_checkbox.toggled.connect(self.on_toggle_display)
        display_layout.addWidget(self.display_label)
        display_layout.addWidget(self.display_checkbox)
        display_layout.addStretch(1)
        layout.addWidget(self.display_checkbox_container)

        self.checkbox_btn = QtWidgets.QPushButton()
        self.checkbox_btn.setCheckable(True)
        self.checkbox_btn.setChecked(True)
        self.checkbox_btn.clicked.connect(self.toggle_checkbox)
        self.checkbox_btn.setStyleSheet("""
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
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        layout.addWidget(self.checkbox_btn)

        self.checkbox_widget = QtWidgets.QWidget()
        cb_layout = QtWidgets.QVBoxLayout(self.checkbox_widget)
        cb_layout.setContentsMargins(8, 4, 8, 8)
        cb_layout.setSpacing(6)

        self.season_checkbox = QtWidgets.QCheckBox()
        self.season_checkbox.setChecked(self.calculator.get_setting('season_limit'))
        self.season_checkbox.toggled.connect(lambda checked: self._on_setting_changed('season_limit', checked))
        cb_layout.addWidget(self.season_checkbox)
        layout.addWidget(self.checkbox_widget)

        self.tractor_btn = QtWidgets.QPushButton()
        self.tractor_btn.setCheckable(True)
        self.tractor_btn.setChecked(True)
        self.tractor_btn.clicked.connect(self.toggle_tractor)
        self.tractor_btn.setStyleSheet("""
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
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        layout.addWidget(self.tractor_btn)

        self.tractor_widget = QtWidgets.QWidget()
        tractor_form = QtWidgets.QGridLayout(self.tractor_widget)
        tractor_form.setContentsMargins(8, 4, 8, 8)
        tractor_form.setSpacing(6)

        input_style = """
            QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-size: 10px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #3498db;
            }
        """

        self.tractor_inputs = {}
        self.tractor_labels = {}
        tractor_params = [
            ('Mt', 'Масса тягача, тонн'),
            ('Nt_data', 'Нагрузка на заднюю ось пустого тягача, тонн'),
            ('Lt', 'Расстояние между осями тягача, м'),
            ('L_data', 'Расстояние от точки сцепки до задней оси тягача, м')
        ]

        for i, (key, label_key) in enumerate(tractor_params):
            label = QtWidgets.QLabel(tr(label_key))
            label.setStyleSheet("font-size: 11px; font-weight: 600; color: #2c3e50;")
            self.tractor_labels[key] = (label, label_key)
            tractor_form.addWidget(label, i, 0)

            input_field = QtWidgets.QDoubleSpinBox()
            input_field.setRange(0.1, 999.9)
            input_field.setDecimals(1)
            input_field.setValue(self.calculator.get_setting(key))
            input_field.setStyleSheet(input_style)
            input_field.valueChanged.connect(lambda v, k=key: self._on_setting_changed(k, v))
            self.tractor_inputs[key] = input_field
            tractor_form.addWidget(input_field, i, 1)

        layout.addWidget(self.tractor_widget)

        self.trailer_btn = QtWidgets.QPushButton()
        self.trailer_btn.setCheckable(True)
        self.trailer_btn.setChecked(True)
        self.trailer_btn.clicked.connect(self.toggle_trailer)
        self.trailer_btn.setStyleSheet("""
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
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        layout.addWidget(self.trailer_btn)

        self.trailer_widget = QtWidgets.QWidget()
        trailer_form = QtWidgets.QGridLayout(self.trailer_widget)
        trailer_form.setContentsMargins(8, 4, 8, 8)
        trailer_form.setSpacing(6)

        self.trailer_inputs = {}
        self.trailer_labels = {}
        trailer_params = [
            ('Mp', 'Масса пустого полуприцепа, тонн'),
            ('LC', 'Расстояние от зада полуприцепа до его средней оси, м'),
            ('LB', 'Расстояние от точки сцепки до переда полуприцепа, м'),
            ('Ntp', 'Нагрузка пустого полуприцепа на тягач, тонн')
        ]

        self.trailer_length_title_label = QtWidgets.QLabel(tr("Длина полуприцепа, м") + ":")
        self.trailer_length_title_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #2c3e50;")
        trailer_form.addWidget(self.trailer_length_title_label, 0, 0)

        self.trailer_length_label = QtWidgets.QLabel()
        self.trailer_length_label.setStyleSheet("font-size: 11px; color: #27ae60; font-weight: bold;")
        trailer_form.addWidget(self.trailer_length_label, 0, 1)

        for i, (key, label_key) in enumerate(trailer_params, 1):
            label = QtWidgets.QLabel(tr(label_key))
            label.setStyleSheet("font-size: 11px; font-weight: 600; color: #2c3e50;")
            self.trailer_labels[key] = (label, label_key)
            trailer_form.addWidget(label, i, 0)

            input_field = QtWidgets.QDoubleSpinBox()
            input_field.setRange(0.1, 999.9)
            input_field.setDecimals(1)
            input_field.setValue(self.calculator.get_setting(key))
            input_field.setStyleSheet(input_style)
            input_field.valueChanged.connect(lambda v, k=key: self._on_setting_changed(k, v))
            self.trailer_inputs[key] = input_field
            trailer_form.addWidget(input_field, i, 1)

        layout.addWidget(self.trailer_widget)

        self.cargo_btn = QtWidgets.QPushButton()
        self.cargo_btn.setCheckable(True)
        self.cargo_btn.setChecked(True)
        self.cargo_btn.clicked.connect(self.toggle_cargo)
        self.cargo_btn.setStyleSheet("""
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
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        layout.addWidget(self.cargo_btn)

        self.cargo_widget = QtWidgets.QWidget()
        cargo_form = QtWidgets.QGridLayout(self.cargo_widget)
        cargo_form.setContentsMargins(8, 4, 8, 8)
        cargo_form.setSpacing(6)

        self.cargo_inputs = {}
        self.cargo_labels = {}
        for i in range(1, 5):
            key = f'Mg{i}'
            label_key = f"Борт {i}, вес груза, тонн"
            label = QtWidgets.QLabel(tr(label_key) + ":")
            label.setStyleSheet("font-size: 11px; font-weight: 600; color: #2c3e50;")
            self.cargo_labels[key] = (label, label_key)
            cargo_form.addWidget(label, i-1, 0)

            input_field = QtWidgets.QDoubleSpinBox()
            input_field.setRange(0.0, 999.9)
            input_field.setDecimals(1)
            input_field.setValue(self.calculator.get_setting(key))
            input_field.setStyleSheet(input_style)
            input_field.valueChanged.connect(lambda v, k=key: self._on_setting_changed(k, v))
            self.cargo_inputs[key] = input_field
            cargo_form.addWidget(input_field, i-1, 1)

        layout.addWidget(self.cargo_widget)

        self.results_btn = QtWidgets.QPushButton()
        self.results_btn.hide()
        self.results_widget = QtWidgets.QWidget()
        self.results_widget.hide()
        self.result_labels = {}

        self.calc_button = QtWidgets.QPushButton()
        self.calc_button.hide()

        layout.addStretch(1)

    def toggle_checkbox(self):
        if self.checkbox_btn.isChecked():
            self.checkbox_widget.show()
            self.checkbox_btn.setText(f"⚙️ {tr('Настройки периода')} ▲")
        else:
            self.checkbox_widget.hide()
            self.checkbox_btn.setText(f"⚙️ {tr('Настройки периода')} ▼")

    def toggle_tractor(self):
        if self.tractor_btn.isChecked():
            self.tractor_widget.show()
            self.tractor_btn.setText(f"🚛 {tr('Параметры тягача')} ▲")
        else:
            self.tractor_widget.hide()
            self.tractor_btn.setText(f"🚛 {tr('Параметры тягача')} ▼")

    def toggle_trailer(self):
        if self.trailer_btn.isChecked():
            self.trailer_widget.show()
            self.trailer_btn.setText(f"🚚 {tr('Параметры полуприцепа')} ▲")
        else:
            self.trailer_widget.hide()
            self.trailer_btn.setText(f"🚚 {tr('Параметры полуприцепа')} ▼")

    def toggle_cargo(self):
        if self.cargo_btn.isChecked():
            self.cargo_widget.show()
            self.cargo_btn.setText(f"📦 {tr('Вес груза по бортам')} ▲")
        else:
            self.cargo_widget.hide()
            self.cargo_btn.setText(f"📦 {tr('Вес груза по бортам')} ▼")

    def toggle_results(self):
        if self.results_btn.isChecked():
            self.results_widget.show()
            self.results_btn.setText(f"📊 {tr('Результаты расчетов')} ▲")
        else:
            self.results_widget.hide()
            self.results_btn.setText(f"📊 {tr('Результаты расчетов')} ▼")

    def calculate_and_update(self):
        self.update_trailer_length_from_truck()
        results = self.calculator.calculate_loads()
        if results:
            self.display_results(results)
            self._publish_results_to_main(results)

    def display_results(self, results):
        pass

    def update_display(self):
        self.calculate_and_update()

    def on_toggle_display(self, checked: bool):
        self.calculator.update_setting('show_on_main_screen', checked)
        results = self.calculator.calculate_loads()
        if results:
            self._publish_results_to_main(results)

    def _on_setting_changed(self, key, value):
        self.calculator.update_setting(key, value)
        # Save to current truck when settings change
        self._save_to_current_truck()
        results = self.calculator.calculate_loads()
        if results:
            self.display_results(results)
            self._publish_results_to_main(results)

    @safe_method(
        component="LoadCalculationWidget",
        category=ErrorCategory.UI,
        severity=ErrorSeverity.LOW,
        suppress_errors=True
    )
    def _publish_results_to_main(self, results: dict):
        app = self.get_app3d()
        if not app:
            return
        if hasattr(app, 'panda_widget') and app.panda_widget:
            app.panda_widget.update_axle_results_overlay(
                visible=self.calculator.get_setting('show_on_main_screen'),
                results=results
            )

    def retranslate_ui(self):
        self.title.setText(tr("Расчет нагрузок на оси"))
        if hasattr(self, 'display_label'):
            self.display_label.setText(tr("Отображать на главном экране") + ":")
        
        if hasattr(self, 'season_checkbox'):
            self.season_checkbox.setText(tr("В период паводков (только для Беларуси)"))
        
        self.calc_button.setText(tr("Рассчитать"))
        
        expanded = "▲" if self.checkbox_btn.isChecked() else "▼"
        self.checkbox_btn.setText(f"⚙️ {tr('Настройки периода')} {expanded}")
        
        expanded = "▲" if self.tractor_btn.isChecked() else "▼"
        self.tractor_btn.setText(f"🚛 {tr('Параметры тягача')} {expanded}")
        
        expanded = "▲" if self.trailer_btn.isChecked() else "▼"
        self.trailer_btn.setText(f"🚚 {tr('Параметры полуприцепа')} {expanded}")
        
        expanded = "▲" if self.cargo_btn.isChecked() else "▼"
        self.cargo_btn.setText(f"📦 {tr('Вес груза по бортам')} {expanded}")
        
        expanded = "▲" if self.results_btn.isChecked() else "▼"
        self.results_btn.setText(f"📊 {tr('Результаты расчетов')} {expanded}")
        
        # Update tractor parameter labels
        if hasattr(self, 'tractor_labels'):
            for key, (label, label_key) in self.tractor_labels.items():
                label.setText(tr(label_key))
        
        # Update trailer parameter labels
        if hasattr(self, 'trailer_labels'):
            for key, (label, label_key) in self.trailer_labels.items():
                label.setText(tr(label_key))
        
        # Update trailer length title label
        if hasattr(self, 'trailer_length_title_label'):
            self.trailer_length_title_label.setText(tr("Длина полуприцепа, м") + ":")
        
        # Update cargo parameter labels
        if hasattr(self, 'cargo_labels'):
            for key, (label, label_key) in self.cargo_labels.items():
                label.setText(tr(label_key) + ":")
