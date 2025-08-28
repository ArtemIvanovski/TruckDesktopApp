from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer
from core.logging import get_logger
from core.i18n import tr


class ErrorDialog(QtWidgets.QDialog):
    def __init__(self, error_type: str, message: str, parent=None):
        super().__init__(parent)
        self.error_type = error_type
        self.message = message
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle(tr("Error"))
        self.setFixedSize(450, 300)
        self.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header_layout = QtWidgets.QHBoxLayout()
        
        icon_label = QtWidgets.QLabel()
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxCritical)
        icon_label.setPixmap(icon.pixmap(48, 48))
        header_layout.addWidget(icon_label)
        
        header_text = QtWidgets.QVBoxLayout()
        title_label = QtWidgets.QLabel(f"{tr('Error')}: {self.error_type}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #c0392b;")
        header_text.addWidget(title_label)
        
        subtitle_label = QtWidgets.QLabel(tr("An error occurred in the application"))
        subtitle_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        header_text.addWidget(subtitle_label)
        
        header_layout.addLayout(header_text)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        message_group = QtWidgets.QGroupBox(tr("Error Details"))
        message_layout = QtWidgets.QVBoxLayout(message_group)
        
        self.message_text = QtWidgets.QTextEdit()
        self.message_text.setPlainText(self.message)
        self.message_text.setReadOnly(True)
        self.message_text.setMaximumHeight(120)
        self.message_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        message_layout.addWidget(self.message_text)
        layout.addWidget(message_group)
        
        buttons_layout = QtWidgets.QHBoxLayout()
        
        self.copy_button = QtWidgets.QPushButton(tr("Copy Error"))
        self.copy_button.clicked.connect(self._copy_error)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        
        self.ok_button = QtWidgets.QPushButton(tr("OK"))
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        
        buttons_layout.addWidget(self.copy_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ok_button)
        layout.addLayout(buttons_layout)
        
    def _copy_error(self):
        clipboard = QtWidgets.QApplication.clipboard()
        error_info = f"Error Type: {self.error_type}\nMessage: {self.message}"
        clipboard.setText(error_info)
        
        self.copy_button.setText(tr("Copied!"))
        QTimer.singleShot(2000, lambda: self.copy_button.setText(tr("Copy Error")))


class ErrorReportDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_errors()
        
    def _setup_ui(self):
        self.setWindowTitle(tr("Error Report"))
        self.setFixedSize(600, 500)
        self.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        title_label = QtWidgets.QLabel(tr("Recent Errors"))
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50;")
        layout.addWidget(title_label)
        
        self.errors_list = QtWidgets.QListWidget()
        self.errors_list.setAlternatingRowColors(True)
        self.errors_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        layout.addWidget(self.errors_list)
        
        buttons_layout = QtWidgets.QHBoxLayout()
        
        self.clear_button = QtWidgets.QPushButton(tr("Clear All"))
        self.clear_button.clicked.connect(self._clear_errors)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        self.close_button = QtWidgets.QPushButton(tr("Close"))
        self.close_button.clicked.connect(self.accept)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)
        layout.addLayout(buttons_layout)
        
    def _load_errors(self):
        logger = get_logger()
        recent_errors = logger.get_recent_errors(100)
        
        for error in reversed(recent_errors):
            timestamp = error.get('timestamp', 'Unknown')
            error_type = error.get('type', 'Unknown')
            message = error.get('message', 'No message')
            
            item_text = f"[{timestamp[:19]}] {error_type}: {message[:100]}..."
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.UserRole, error)
            self.errors_list.addItem(item)
            
    def _clear_errors(self):
        logger = get_logger()
        logger.error_reporter.clear_errors()
        self.errors_list.clear()


class ErrorNotificationWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self._setup_ui()
        
        self.fade_timer = QTimer()
        self.fade_timer.setSingleShot(True)
        self.fade_timer.timeout.connect(self.hide)
        
    def _setup_ui(self):
        self.setFixedSize(350, 80)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.icon_label = QtWidgets.QLabel()
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
        self.icon_label.setPixmap(icon.pixmap(32, 32))
        layout.addWidget(self.icon_label)
        
        text_layout = QtWidgets.QVBoxLayout()
        
        self.title_label = QtWidgets.QLabel()
        self.title_label.setStyleSheet("font-weight: bold; color: #c0392b;")
        text_layout.addWidget(self.title_label)
        
        self.message_label = QtWidgets.QLabel()
        self.message_label.setStyleSheet("color: #2c3e50; font-size: 10px;")
        self.message_label.setWordWrap(True)
        text_layout.addWidget(self.message_label)
        
        layout.addLayout(text_layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(248, 249, 250, 240);
                border: 2px solid #e74c3c;
                border-radius: 8px;
            }
        """)
        
    def show_error(self, error_type: str, message: str, duration: int = 5000):
        self.title_label.setText(f"Error: {error_type}")
        self.message_label.setText(message[:100] + "..." if len(message) > 100 else message)
        
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 20
            self.move(x, y)
        
        self.show()
        self.raise_()
        self.fade_timer.start(duration)
