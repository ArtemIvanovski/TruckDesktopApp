from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer, QPropertyAnimation, QEasingCurve, QRect
from typing import Optional, List, Callable
from enum import Enum
import json
from datetime import datetime

from core.exceptions import ApplicationError, ErrorSeverity, ErrorCategory, RecoveryStrategy
from core.i18n import tr


class ErrorDialogType(Enum):
    SIMPLE = "simple"
    DETAILED = "detailed"
    RECOVERY = "recovery"
    NOTIFICATION = "notification"


class ErrorActionButton(QtWidgets.QPushButton):
    def __init__(self, text: str, action: Callable[[], bool], parent=None):
        super().__init__(text, parent)
        self.action = action
        self.clicked.connect(self._execute_action)
        
    def _execute_action(self):
        try:
            success = self.action()
            if success:
                self.setText(tr("Success"))
                self.setEnabled(False)
                QTimer.singleShot(2000, self.parent().accept)
            else:
                self.setText(tr("Failed"))
                QTimer.singleShot(1000, lambda: self.setText(tr("Retry")))
        except Exception:
            self.setText(tr("Error"))
            QTimer.singleShot(1000, lambda: self.setText(tr("Retry")))


class DetailedErrorDialog(QtWidgets.QDialog):
    def __init__(self, error: ApplicationError, parent=None):
        super().__init__(parent)
        self.error = error
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle(tr("Error Details"))
        self.setFixedSize(650, 500)
        self.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header_layout = QtWidgets.QHBoxLayout()
        
        icon_label = QtWidgets.QLabel()
        icon = self._get_severity_icon()
        icon_label.setPixmap(icon.pixmap(64, 64))
        header_layout.addWidget(icon_label)
        
        header_info = QtWidgets.QVBoxLayout()
        
        title_label = QtWidgets.QLabel(self._get_title())
        title_label.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {self._get_severity_color()};")
        header_info.addWidget(title_label)
        
        category_label = QtWidgets.QLabel(f"{tr('Category')}: {self.error.category.value.title()}")
        category_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        header_info.addWidget(category_label)
        
        severity_label = QtWidgets.QLabel(f"{tr('Severity')}: {self.error.severity.value.title()}")
        severity_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        header_info.addWidget(severity_label)
        
        header_layout.addLayout(header_info)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        message_group = QtWidgets.QGroupBox(tr("User Message"))
        message_layout = QtWidgets.QVBoxLayout(message_group)
        
        user_message = self.error.user_message or self.error.message
        message_text = QtWidgets.QTextEdit()
        message_text.setPlainText(user_message)
        message_text.setReadOnly(True)
        message_text.setMaximumHeight(80)
        message_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        message_layout.addWidget(message_text)
        layout.addWidget(message_group)
        
        if self.error.context:
            context_group = QtWidgets.QGroupBox(tr("Technical Details"))
            context_layout = QtWidgets.QVBoxLayout(context_group)
            
            context_text = QtWidgets.QTextEdit()
            context_json = json.dumps(self.error.context, indent=2, ensure_ascii=False)
            context_text.setPlainText(context_json)
            context_text.setReadOnly(True)
            context_text.setMaximumHeight(150)
            context_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: monospace;
                    font-size: 9px;
                }
            """)
            context_layout.addWidget(context_text)
            layout.addWidget(context_group)
            
        buttons_layout = QtWidgets.QHBoxLayout()
        
        self.copy_button = QtWidgets.QPushButton(tr("Copy Details"))
        self.copy_button.clicked.connect(self._copy_details)
        self.copy_button.setStyleSheet(self._get_button_style("#6c757d", "#5a6268"))
        
        self.report_button = QtWidgets.QPushButton(tr("Report Issue"))
        self.report_button.clicked.connect(self._report_issue)
        self.report_button.setStyleSheet(self._get_button_style("#17a2b8", "#138496"))
        
        self.ok_button = QtWidgets.QPushButton(tr("OK"))
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        self.ok_button.setStyleSheet(self._get_button_style("#007bff", "#0056b3"))
        
        buttons_layout.addWidget(self.copy_button)
        buttons_layout.addWidget(self.report_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ok_button)
        layout.addLayout(buttons_layout)
        
    def _get_severity_icon(self):
        if self.error.severity == ErrorSeverity.CRITICAL:
            return self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxCritical)
        elif self.error.severity == ErrorSeverity.HIGH:
            return self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
        else:
            return self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation)
            
    def _get_severity_color(self):
        if self.error.severity == ErrorSeverity.CRITICAL:
            return "#dc3545"
        elif self.error.severity == ErrorSeverity.HIGH:
            return "#ffc107"
        else:
            return "#17a2b8"
            
    def _get_title(self):
        if self.error.severity == ErrorSeverity.CRITICAL:
            return tr("Critical Error")
        elif self.error.severity == ErrorSeverity.HIGH:
            return tr("Warning")
        else:
            return tr("Information")
            
    def _get_button_style(self, bg_color: str, hover_color: str):
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """
        
    def _copy_details(self):
        details = {
            "error_type": type(self.error).__name__,
            "message": self.error.message,
            "category": self.error.category.value,
            "severity": self.error.severity.value,
            "timestamp": datetime.now().isoformat(),
            "context": self.error.context
        }
        
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(json.dumps(details, indent=2, ensure_ascii=False))
        
        self.copy_button.setText(tr("Copied!"))
        QTimer.singleShot(2000, lambda: self.copy_button.setText(tr("Copy Details")))
        
    def _report_issue(self):
        from core.logging import get_logger
        logger = get_logger()
        logger.error(f"User reported issue: {self.error.message}", self.error)
        
        self.report_button.setText(tr("Reported"))
        self.report_button.setEnabled(False)


class RecoveryDialog(QtWidgets.QDialog):
    def __init__(self, error: ApplicationError, recovery_strategies: List[RecoveryStrategy], parent=None):
        super().__init__(parent)
        self.error = error
        self.recovery_strategies = recovery_strategies
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle(tr("Error Recovery"))
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QtWidgets.QLabel(tr("Recovery Options"))
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50;")
        layout.addWidget(title_label)
        
        error_label = QtWidgets.QLabel(f"{tr('Error')}: {self.error.user_message or self.error.message}")
        error_label.setWordWrap(True)
        error_label.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(error_label)
        
        if self.recovery_strategies:
            strategies_group = QtWidgets.QGroupBox(tr("Available Recovery Actions"))
            strategies_layout = QtWidgets.QVBoxLayout(strategies_group)
            
            for strategy in self.recovery_strategies:
                strategy_widget = self._create_strategy_widget(strategy)
                strategies_layout.addWidget(strategy_widget)
                
            layout.addWidget(strategies_group)
        else:
            no_recovery_label = QtWidgets.QLabel(tr("No automatic recovery options available"))
            no_recovery_label.setStyleSheet("color: #dc3545; font-style: italic;")
            layout.addWidget(no_recovery_label)
            
        buttons_layout = QtWidgets.QHBoxLayout()
        
        self.details_button = QtWidgets.QPushButton(tr("Show Details"))
        self.details_button.clicked.connect(self._show_details)
        self.details_button.setStyleSheet(self._get_button_style("#6c757d", "#5a6268"))
        
        self.continue_button = QtWidgets.QPushButton(tr("Continue"))
        self.continue_button.clicked.connect(self.accept)
        self.continue_button.setDefault(True)
        self.continue_button.setStyleSheet(self._get_button_style("#28a745", "#218838"))
        
        buttons_layout.addWidget(self.details_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.continue_button)
        layout.addLayout(buttons_layout)
        
    def _create_strategy_widget(self, strategy: RecoveryStrategy) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        desc_layout = QtWidgets.QVBoxLayout()
        
        name_label = QtWidgets.QLabel(strategy.name.replace("_", " ").title())
        name_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        desc_layout.addWidget(name_label)
        
        if strategy.description:
            desc_label = QtWidgets.QLabel(strategy.description)
            desc_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
            desc_label.setWordWrap(True)
            desc_layout.addWidget(desc_label)
            
        layout.addLayout(desc_layout)
        
        action_button = ErrorActionButton(tr("Execute"), strategy.action, self)
        action_button.setStyleSheet(self._get_button_style("#17a2b8", "#138496"))
        layout.addWidget(action_button)
        
        widget.setStyleSheet("""
            QWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
        """)
        
        return widget
        
    def _get_button_style(self, bg_color: str, hover_color: str):
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """
        
    def _show_details(self):
        details_dialog = DetailedErrorDialog(self.error, self)
        details_dialog.exec_()


class ErrorNotificationToast(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self._setup_ui()
        
        self.fade_timer = QTimer()
        self.fade_timer.setSingleShot(True)
        self.fade_timer.timeout.connect(self._start_fade_out)
        
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.finished.connect(self._on_fade_finished)
        
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def _setup_ui(self):
        self.setFixedSize(400, 100)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        self.icon_label = QtWidgets.QLabel()
        layout.addWidget(self.icon_label)
        
        text_layout = QtWidgets.QVBoxLayout()
        
        self.title_label = QtWidgets.QLabel()
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        text_layout.addWidget(self.title_label)
        
        self.message_label = QtWidgets.QLabel()
        self.message_label.setStyleSheet("font-size: 10px; color: #555;")
        self.message_label.setWordWrap(True)
        text_layout.addWidget(self.message_label)
        
        layout.addLayout(text_layout, 1)
        
        self.close_button = QtWidgets.QPushButton("×")
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self.hide)
        self.close_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 14px;
                font-weight: bold;
                color: #999;
            }
            QPushButton:hover {
                color: #333;
            }
        """)
        layout.addWidget(self.close_button)
        
    def show_notification(self, error: ApplicationError, duration: int = 4000):
        self._configure_for_error(error)
        
        if self.parent():
            self._position_notification()
            
        self.setWindowOpacity(0)
        self.show()
        
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
        
        self.fade_timer.start(duration)
        
    def _configure_for_error(self, error: ApplicationError):
        if error.severity == ErrorSeverity.CRITICAL:
            icon = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxCritical)
            color = "#dc3545"
            title = tr("Critical Error")
        elif error.severity == ErrorSeverity.HIGH:
            icon = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
            color = "#ffc107"
            title = tr("Warning")
        else:
            icon = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation)
            color = "#17a2b8"
            title = tr("Information")
            
        self.icon_label.setPixmap(icon.pixmap(32, 32))
        self.title_label.setText(title)
        self.title_label.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {color};")
        
        message = error.user_message or error.message
        if len(message) > 100:
            message = message[:97] + "..."
        self.message_label.setText(message)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 250);
                border: 2px solid {color};
                border-radius: 8px;
            }}
        """)
        
    def _position_notification(self):
        parent_rect = self.parent().geometry()
        start_x = parent_rect.right()
        end_x = parent_rect.right() - self.width() - 20
        y = parent_rect.top() + 20
        
        start_rect = QRect(start_x, y, self.width(), self.height())
        end_rect = QRect(end_x, y, self.width(), self.height())
        
        self.setGeometry(start_rect)
        
        self.slide_animation.setStartValue(start_rect)
        self.slide_animation.setEndValue(end_rect)
        self.slide_animation.start()
        
    def _start_fade_out(self):
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.start()
        
    def _on_fade_finished(self):
        if self.windowOpacity() == 0:
            self.hide()


class ErrorDialogManager:
    def __init__(self, parent_widget: Optional[QtWidgets.QWidget] = None):
        self.parent_widget = parent_widget
        self.notification_toast = None
        
    def show_error(
        self,
        error: ApplicationError,
        dialog_type: ErrorDialogType = ErrorDialogType.SIMPLE,
        recovery_strategies: Optional[List[RecoveryStrategy]] = None
    ):
        if dialog_type == ErrorDialogType.NOTIFICATION:
            self._show_notification(error)
        elif dialog_type == ErrorDialogType.DETAILED:
            self._show_detailed_dialog(error)
        elif dialog_type == ErrorDialogType.RECOVERY and recovery_strategies:
            self._show_recovery_dialog(error, recovery_strategies)
        else:
            self._show_simple_dialog(error)
            
    def _show_notification(self, error: ApplicationError):
        if not self.notification_toast:
            self.notification_toast = ErrorNotificationToast(self.parent_widget)
        self.notification_toast.show_notification(error)
        
    def _show_simple_dialog(self, error: ApplicationError):
        msg_box = QtWidgets.QMessageBox(self.parent_widget)
        msg_box.setWindowTitle(tr("Error"))
        msg_box.setText(error.user_message or error.message)
        msg_box.setIcon(self._get_message_box_icon(error.severity))
        msg_box.exec_()
        
    def _show_detailed_dialog(self, error: ApplicationError):
        dialog = DetailedErrorDialog(error, self.parent_widget)
        dialog.exec_()
        
    def _show_recovery_dialog(self, error: ApplicationError, recovery_strategies: List[RecoveryStrategy]):
        dialog = RecoveryDialog(error, recovery_strategies, self.parent_widget)
        dialog.exec_()
        
    def _get_message_box_icon(self, severity: ErrorSeverity):
        if severity == ErrorSeverity.CRITICAL:
            return QtWidgets.QMessageBox.Critical
        elif severity == ErrorSeverity.HIGH:
            return QtWidgets.QMessageBox.Warning
        else:
            return QtWidgets.QMessageBox.Information
