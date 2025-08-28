import os
import shutil
from PyQt5 import QtWidgets, QtGui, QtCore

from core.i18n import tr, TranslatableMixin
from utils.settings_manager import SettingsManager


class CustomizationWidget(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_manager = SettingsManager()
        self.logo_folder = "company_logos"
        self.truck_app = None
        self.setup_ui()
        self.load_current_settings()
        self.retranslate_ui()

    def setup_ui(self):
        self.setMinimumSize(500, 400)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.title_btn = QtWidgets.QPushButton()
        self.title_btn.setCheckable(False)
        self.title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.title_btn)

        main_group = QtWidgets.QGroupBox()
        main_layout = QtWidgets.QVBoxLayout(main_group)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        self.logo_label = QtWidgets.QLabel()
        main_layout.addWidget(self.logo_label)

        file_row = QtWidgets.QHBoxLayout()
        self.logo_path_edit = QtWidgets.QLineEdit()
        self.logo_path_edit.setReadOnly(True)
        self.logo_path_edit.setStyleSheet(self.get_line_edit_style())
        self.logo_path_edit.setMinimumHeight(32)
        self.browse_btn = QtWidgets.QPushButton()
        self.browse_btn.setStyleSheet(self.get_button_style())
        self.browse_btn.setMinimumHeight(32)
        self.browse_btn.setMinimumWidth(100)
        self.browse_btn.clicked.connect(self.browse_logo_file)
        file_row.addWidget(self.logo_path_edit, 1)
        file_row.addWidget(self.browse_btn)
        main_layout.addLayout(file_row)

        self.logo_info = QtWidgets.QLabel()
        self.logo_info.setStyleSheet("color: #666; font-size: 11px; margin: 4px 0;")
        main_layout.addWidget(self.logo_info)

        self.logo_preview = QtWidgets.QLabel()
        self.logo_preview.setFixedSize(150, 150)
        self.logo_preview.setAlignment(QtCore.Qt.AlignCenter)
        self.logo_preview.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #6c757d;
                font-size: 12px;
            }
        """)
        preview_container = QtWidgets.QHBoxLayout()
        preview_container.addStretch()
        preview_container.addWidget(self.logo_preview)
        preview_container.addStretch()
        main_layout.addLayout(preview_container)

        controls_layout = QtWidgets.QHBoxLayout()

        size_group = QtWidgets.QGroupBox()
        size_layout = QtWidgets.QVBoxLayout(size_group)
        size_layout.setContentsMargins(12, 12, 12, 12)
        self.size_label = QtWidgets.QLabel()
        self.size_spin = QtWidgets.QSpinBox()
        self.size_spin.setRange(25, 200)
        self.size_spin.setSingleStep(5)
        self.size_spin.setValue(100)
        self.size_spin.setSuffix("%")
        self.size_spin.setMinimumHeight(32)
        self.size_spin.setStyleSheet(self.get_spinbox_style())
        size_layout.addWidget(self.size_label)
        size_layout.addWidget(self.size_spin)

        rotation_group = QtWidgets.QGroupBox()
        rotation_layout = QtWidgets.QVBoxLayout(rotation_group)
        rotation_layout.setContentsMargins(12, 12, 12, 12)
        self.rotation_label = QtWidgets.QLabel()
        self.rotation_spin = QtWidgets.QSpinBox()
        self.rotation_spin.setRange(0, 359)
        self.rotation_spin.setSingleStep(15)
        self.rotation_spin.setValue(0)
        self.rotation_spin.setSuffix("°")
        self.rotation_spin.setMinimumHeight(32)
        self.rotation_spin.setStyleSheet(self.get_spinbox_style())
        rotation_layout.addWidget(self.rotation_label)
        rotation_layout.addWidget(self.rotation_spin)

        controls_layout.addWidget(size_group)
        controls_layout.addWidget(rotation_group)
        main_layout.addLayout(controls_layout)

        layout.addWidget(main_group)
        self.create_buttons(layout)

    def create_buttons(self, layout):
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 16, 0, 0)
        button_layout.addStretch()

        self.remove_logo_btn = QtWidgets.QPushButton()
        self.remove_logo_btn.setStyleSheet(self.get_remove_button_style())
        self.remove_logo_btn.setMinimumWidth(120)
        self.remove_logo_btn.setMinimumHeight(36)
        self.remove_logo_btn.clicked.connect(self.remove_logo)

        self.apply_btn = QtWidgets.QPushButton()
        self.apply_btn.setStyleSheet(self.get_apply_button_style())
        self.apply_btn.setMinimumWidth(120)
        self.apply_btn.setMinimumHeight(36)
        self.apply_btn.clicked.connect(self.apply_settings)

        self.test_logo_btn = QtWidgets.QPushButton()
        self.test_logo_btn.setStyleSheet(self.get_button_style())
        self.test_logo_btn.setMinimumWidth(120)
        self.test_logo_btn.setMinimumHeight(36)
        self.test_logo_btn.clicked.connect(self.create_test_logo)

        button_layout.addWidget(self.test_logo_btn)
        button_layout.addSpacing(12)
        button_layout.addWidget(self.remove_logo_btn)
        button_layout.addSpacing(12)
        button_layout.addWidget(self.apply_btn)
        layout.addLayout(button_layout)

    def browse_logo_file(self):
        file_dialog = QtWidgets.QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            tr("Выберите файл логотипа"),
            "",
            "Изображения (*.png *.jpg *.jpeg *.svg *.bmp);;Все файлы (*.*)"
        )
        
        if file_path:
            if self.validate_logo_file(file_path):
                processed_path = self.process_logo_file(file_path)
                if processed_path:
                    self.logo_path_edit.setText(processed_path)
                    self.update_logo_preview(processed_path)
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    tr("Ошибка"),
                    tr("Пожалуйста, выберите корректный файл изображения.")
                )

    def validate_logo_file(self, file_path):
        allowed_extensions = ('.png', '.jpg', '.jpeg', '.svg', '.bmp')
        if not file_path.lower().endswith(allowed_extensions):
            return False
        
        if not os.path.exists(file_path):
            return False
            
        if os.path.getsize(file_path) > 20 * 1024 * 1024:
            return False
            
        return True

    def process_logo_file(self, source_path):
        try:
            os.makedirs(self.logo_folder, exist_ok=True)

            ext = os.path.splitext(source_path)[1].lower()

            if ext == '.svg':
                base_name = os.path.splitext(os.path.basename(source_path))[0]
                temp_png = os.path.join(self.logo_folder, f"{base_name}_tmp.png")
                converted = False
                # Try QtSvg first
                try:
                    from PyQt5.QtSvg import QSvgRenderer
                    from PyQt5.QtGui import QImage, QPainter
                    image = QImage(512, 512, QImage.Format_ARGB32)
                    image.fill(0)
                    painter = QPainter(image)
                    renderer = QSvgRenderer(source_path)
                    if renderer.isValid():
                        renderer.render(painter)
                        painter.end()
                        image.save(temp_png, 'PNG')
                        source_path = temp_png
                        converted = True
                except Exception:
                    pass
                # Fallback to CairoSVG
                if not converted:
                    try:
                        import cairosvg
                        cairosvg.svg2png(url=source_path, write_to=temp_png, output_width=512, output_height=512)
                        source_path = temp_png
                        converted = True
                    except Exception as e:
                        QtWidgets.QMessageBox.critical(
                            self,
                            tr("Ошибка"),
                            tr("Не удалось обработать файл: {error}").format(error=str(e))
                        )
                        return None

            from PIL import Image
            with Image.open(source_path) as img:
                if img.mode not in ('RGBA', 'LA'):
                    img = img.convert('RGBA')

                w, h = img.size
                if max(w, h) != 512:
                    img = img.resize((512, 512), Image.LANCZOS)
                    QtWidgets.QMessageBox.information(
                        self,
                        tr("Изображение обработано"),
                        tr("Изображение было изменено до размера 512x512 пикселей для оптимальной производительности.")
                    )

                base_name = os.path.splitext(os.path.basename(source_path))[0]
                dest_path = os.path.join(self.logo_folder, f"{base_name}_logo.png")
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(self.logo_folder, f"{base_name}_logo_{counter}.png")
                    counter += 1
                img.save(dest_path, 'PNG', optimize=True)
                return os.path.abspath(dest_path)

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                tr("Ошибка"),
                tr("Не удалось обработать файл: {error}").format(error=str(e))
            )
            return None

    def update_logo_preview(self, file_path):
        if file_path and os.path.exists(file_path):
            try:
                pixmap = QtGui.QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        140, 140, 
                        QtCore.Qt.KeepAspectRatio, 
                        QtCore.Qt.SmoothTransformation
                    )
                    self.logo_preview.setPixmap(scaled_pixmap)
                    
                    size = pixmap.size()
                    file_size = os.path.getsize(file_path) / 1024
                    if file_size < 1024:
                        size_text = f"{file_size:.1f} КБ"
                    else:
                        size_text = f"{file_size/1024:.1f} МБ"
                    
                    self.logo_info.setText(
                        tr("Размер: {width}x{height} пикселей, {size}").format(
                            width=size.width(), height=size.height(), size=size_text
                        )
                    )
                else:
                    self.logo_preview.setText(tr("Превью недоступно"))
                    self.logo_info.setText("")
            except Exception:
                self.logo_preview.setText(tr("Ошибка загрузки превью"))
                self.logo_info.setText("")
        else:
            self.logo_preview.clear()
            self.logo_preview.setText(tr("Логотип не выбран"))
            self.logo_info.setText(tr("Рекомендуемый размер: 512x512 пикселей"))

    def remove_logo(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            tr('Удаление логотипа'),
            tr('Вы уверены, что хотите удалить текущий логотип компании?'),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            current_path = self.logo_path_edit.text()
            if current_path and os.path.exists(current_path):
                try:
                    os.remove(current_path)
                except Exception:
                    pass
            
            self.logo_path_edit.clear()
            self.logo_preview.clear()
            self.logo_preview.setText(tr("Логотип не выбран"))
            self.logo_info.setText(tr("Рекомендуемый размер: 512x512 пикселей"))
            
            if self.truck_app:
                self.truck_app.remove_company_logo()
            
            self.apply_settings()

    def load_current_settings(self):
        settings = self.settings_manager.get_section('customization')
        
        logo_path = settings.get('logo_path', '')
        self.logo_path_edit.setText(logo_path)
        self.update_logo_preview(logo_path)
        
        self.size_spin.setValue(settings.get('logo_size', 100))
        self.rotation_spin.setValue(settings.get('logo_rotation', 0))

    def apply_settings(self):
        settings = {
            'logo_path': self.logo_path_edit.text(),
            'logo_size': self.size_spin.value(),
            'logo_rotation': self.rotation_spin.value()
        }
        
        self.settings_manager.update_section('customization', settings)
        
        if self.truck_app:
            self.truck_app.update_company_logo()
        
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle(tr("Настройки"))
        msg.setText(tr("Настройки кастомизации применены успешно!"))
        msg.exec_()



    def retranslate_ui(self):
        self.title_btn.setText(f"🎨 {tr('Кастомизация компании')}")
        self.logo_label.setText(f"{tr('Логотип компании')}:")
        self.browse_btn.setText(tr("Обзор..."))
        self.size_label.setText(f"{tr('Размер')}:")
        self.rotation_label.setText(f"{tr('Поворот')}:")
        self.test_logo_btn.setText(tr("Тестовый логотип"))
        self.remove_logo_btn.setText(tr("Удалить логотип"))
        self.apply_btn.setText(tr("Применить"))
        
        if not self.logo_path_edit.text():
            self.logo_preview.setText(tr("Логотип не выбран"))
            self.logo_info.setText(tr("Рекомендуемый размер: 512x512 пикселей"))

    def set_truck_app(self, truck_app):
        self.truck_app = truck_app
    
    def create_test_logo(self):
        try:
            from PIL import Image, ImageDraw, ImageFont
            import tempfile
            
            os.makedirs(self.logo_folder, exist_ok=True)
            
            img = Image.new('RGBA', (512, 512), (70, 130, 180, 255))
            draw = ImageDraw.Draw(img)
            
            draw.ellipse([50, 50, 462, 462], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=10)
            
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            text = "LOGO"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = (512 - text_width) // 2
            text_y = (512 - text_height) // 2
            
            draw.text((text_x, text_y), text, fill=(0, 0, 0, 255), font=font)
            
            test_logo_path = os.path.join(self.logo_folder, "test_logo.png")
            img.save(test_logo_path, 'PNG')
            test_logo_path = os.path.abspath(test_logo_path)
            
            self.logo_path_edit.setText(test_logo_path)
            self.update_logo_preview(test_logo_path)
            
            QtWidgets.QMessageBox.information(
                self,
                tr("Тестовый логотип"),
                tr("Создан тестовый логотип. Нажмите 'Применить' для его отображения.")
            )
            
        except ImportError:
            QtWidgets.QMessageBox.warning(
                self,
                tr("Ошибка"),
                tr("Для создания тестового логотипа требуется библиотека Pillow.")
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                tr("Ошибка"),
                tr("Не удалось создать тестовый логотип: {error}").format(error=str(e))
            )

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

    def get_line_edit_style(self):
        return """
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
        """

    def get_button_style(self):
        return """
            QPushButton {
                font-size: 11px;
                color: #2c3e50;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
        """

    def get_spinbox_style(self):
        return """
            QDoubleSpinBox, QSpinBox {
                padding: 6px 8px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-size: 11px;
                min-width: 100px;
                min-height: 28px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus {
                border: 2px solid #3498db;
            }
        """

    def get_reset_button_style(self):
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

    def get_remove_button_style(self):
        return """
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
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """

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
