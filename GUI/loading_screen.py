from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from core.error_management import ErrorReportingMixin, safe_method, handle_exceptions
from core.exceptions import ErrorCategory, ErrorSeverity
from core.i18n import tr, TranslatableMixin
import math


class LoadingScreen(QtWidgets.QSplashScreen, TranslatableMixin):
    progress_changed = pyqtSignal(int, str)
    
    def __init__(self):
        super().__init__()
        self.progress = 0
        self.status_text = tr("Initializing...")
        self.rotation_angle = 0
        self._setup_ui()
        self._setup_animations()
        
    def _setup_ui(self):
        self.setFixedSize(400, 300)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        
    def _setup_animations(self):
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self._update_rotation)
        self.rotation_timer.start(50)
        
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
    def _update_rotation(self):
        self.rotation_angle = (self.rotation_angle + 6) % 360
        self.update()
        
    def set_progress(self, value, status=""):
        self.progress = max(0, min(100, value))
        if status:
            self.status_text = status
        self.update()
        QtWidgets.QApplication.processEvents()
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        self._draw_background(painter)
        self._draw_logo(painter)
        self._draw_spinner(painter)
        self._draw_progress_bar(painter)
        self._draw_status_text(painter)
        
    def _draw_background(self, painter):
        gradient = QtGui.QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QtGui.QColor(45, 62, 80))
        gradient.setColorAt(1, QtGui.QColor(52, 73, 94))
        
        painter.fillRect(self.rect(), gradient)
        
        painter.setPen(QtGui.QPen(QtGui.QColor(127, 140, 141), 2))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
        
    def _draw_logo(self, painter):
        painter.setPen(QtGui.QPen(QtGui.QColor(236, 240, 241)))
        font = QtGui.QFont("Arial", 24, QtGui.QFont.Bold)
        painter.setFont(font)
        
        title_rect = QtCore.QRect(0, 50, self.width(), 40)
        painter.drawText(title_rect, QtCore.Qt.AlignCenter, "GTSTREAM")
        
        painter.setPen(QtGui.QPen(QtGui.QColor(189, 195, 199)))
        font = QtGui.QFont("Arial", 10)
        painter.setFont(font)
        
        subtitle_rect = QtCore.QRect(0, 90, self.width(), 20)
        painter.drawText(subtitle_rect, QtCore.Qt.AlignCenter, tr("Professional Cargo Management"))
        
    def _draw_spinner(self, painter):
        center_x = self.width() // 2
        center_y = 150
        radius = 20
        
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation_angle)
        
        for i in range(8):
            angle = i * 45
            painter.save()
            painter.rotate(angle)
            
            alpha = 255 - (i * 25)
            color = QtGui.QColor(52, 152, 219, alpha)
            pen = QtGui.QPen(color, 3)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            painter.setPen(pen)
            
            painter.drawLine(radius - 8, 0, radius, 0)
            painter.restore()
            
        painter.restore()
        
    def _draw_progress_bar(self, painter):
        bar_rect = QtCore.QRect(50, 200, self.width() - 100, 8)
        
        painter.setPen(QtGui.QPen(QtGui.QColor(127, 140, 141)))
        painter.setBrush(QtGui.QColor(44, 62, 80))
        painter.drawRoundedRect(bar_rect, 4, 4)
        
        if self.progress > 0:
            progress_width = int((bar_rect.width() * self.progress) / 100)
            progress_rect = QtCore.QRect(bar_rect.x(), bar_rect.y(), progress_width, bar_rect.height())
            
            gradient = QtGui.QLinearGradient(progress_rect.topLeft(), progress_rect.topRight())
            gradient.setColorAt(0, QtGui.QColor(46, 204, 113))
            gradient.setColorAt(1, QtGui.QColor(39, 174, 96))
            
            painter.setBrush(gradient)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRoundedRect(progress_rect, 4, 4)
            
    def _draw_status_text(self, painter):
        painter.setPen(QtGui.QPen(QtGui.QColor(189, 195, 199)))
        font = QtGui.QFont("Arial", 9)
        painter.setFont(font)
        
        status_rect = QtCore.QRect(0, 220, self.width(), 20)
        painter.drawText(status_rect, QtCore.Qt.AlignCenter, self.status_text)
        
        if self.progress > 0:
            progress_rect = QtCore.QRect(0, 240, self.width(), 20)
            painter.drawText(progress_rect, QtCore.Qt.AlignCenter, f"{self.progress}%")
            
    def fade_out(self, callback=None):
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        if callback:
            self.fade_animation.finished.connect(callback)
        self.fade_animation.start()
        
    def closeEvent(self, event):
        self.rotation_timer.stop()
        super().closeEvent(event)


class StartupManager(QtCore.QObject, ErrorReportingMixin):
    progress_update = pyqtSignal(int, str)
    startup_complete = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.loading_screen = None
        self.startup_tasks = [
            ("Loading fonts...", self._load_fonts),
            ("Initializing graphics...", self._init_graphics),
            ("Loading translations...", self._load_translations),
            ("Setting up authentication...", self._setup_auth),
            ("Preparing 3D engine...", self._prepare_3d),
            ("Loading user interface...", self._load_ui),
            ("Loading 3D models...", self._load_models),
            ("Initializing scene...", self._init_scene),
            ("Finalizing setup...", self._finalize),
        ]
        self.main_window = None
        
    def start_loading(self):
        self.loading_screen = LoadingScreen()
        self.loading_screen.show()
        self.progress_update.connect(self.loading_screen.set_progress)
        
        QtCore.QTimer.singleShot(500, self._execute_startup_tasks)
        
    def _execute_startup_tasks(self):
        total_tasks = len(self.startup_tasks)
        self.log_info(f"Starting {total_tasks} startup tasks")
        
        for i, (status, task_func) in enumerate(self.startup_tasks):
            progress = int((i / total_tasks) * 100)
            self.progress_update.emit(progress, tr(status))
            self.log_debug(f"Executing task: {status}")
            
            QtCore.QTimer.singleShot(100, lambda: None)
            QtWidgets.QApplication.processEvents()
            
            try:
                self.start_timer(f"task_{i}")
                task_func()
                duration = self.end_timer(f"task_{i}")
                self.log_debug(f"Task '{status}' completed in {duration:.3f}s")
            except Exception as e:
                self.log_error(f"Task '{status}' failed", e)
                
            QtCore.QTimer.singleShot(200, lambda: None)
            QtWidgets.QApplication.processEvents()
            
        self.progress_update.emit(100, tr("Ready!"))
        QtCore.QTimer.singleShot(1300, self._finish_loading)
        
    def _finish_loading(self):
        if self.loading_screen:
            self.loading_screen.fade_out(self._cleanup_loading)
        else:
            self.startup_complete.emit()
            
    def _cleanup_loading(self):
        if self.loading_screen:
            self.loading_screen.close()
            self.loading_screen = None
        self.startup_complete.emit()
        
    @safe_method(
        component="StartupManager",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.LOW,
        suppress_errors=True
    )
    def _load_fonts(self):
        from utils.setting_deploy import get_resource_path
        import os
        from PyQt5.QtGui import QFontDatabase
        
        font_candidates = [
            get_resource_path('assets/fonts/NotoSans_Condensed-Regular.ttf'),
            get_resource_path('assets/fonts/NotoSans-Regular.ttf'),
            get_resource_path('assets/fonts/arial.ttf'),
        ]
        for path in font_candidates:
            if os.path.exists(path):
                QFontDatabase.addApplicationFont(path)
            
    @safe_method(
        component="StartupManager",
        category=ErrorCategory.GRAPHICS,
        severity=ErrorSeverity.MEDIUM,
        suppress_errors=True
    )
    def _init_graphics(self):
        # GraphicsManager requires an app, defer to TruckLoadingApp initialization
        pass
            
    @safe_method(
        component="StartupManager",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.LOW,
        suppress_errors=True
    )
    def _load_translations(self):
        from core.i18n import setup_translations
        setup_translations()
            
    @safe_method(
        component="StartupManager",
        category=ErrorCategory.AUTH,
        severity=ErrorSeverity.MEDIUM,
        suppress_errors=True
    )
    def _setup_auth(self):
        from auth.auth_module import auth_module
        auth_module.initialize()
            
    @safe_method(
        component="StartupManager",
        category=ErrorCategory.GRAPHICS,
        severity=ErrorSeverity.MEDIUM,
        suppress_errors=True
    )
    def _prepare_3d(self):
        import panda3d
        from direct.showbase.ShowBase import ShowBase
            
    @handle_exceptions(
        category=ErrorCategory.UI,
        severity=ErrorSeverity.CRITICAL,
        user_message="Failed to load the main interface"
    )
    def _load_ui(self):
        from GUI.main_window import MainWindow
        self.main_window = MainWindow()
            
    @safe_method(
        component="StartupManager",
        category=ErrorCategory.GRAPHICS,
        severity=ErrorSeverity.MEDIUM,
        suppress_errors=True
    )
    def _load_models(self):
        if not self.main_window:
            return
        if hasattr(self.main_window, 'viewer') and self.main_window.viewer:
            if hasattr(self.main_window.viewer, 'app3d') and self.main_window.viewer.app3d:
                app3d = self.main_window.viewer.app3d
                if hasattr(app3d, 'ensure_models_loaded'):
                    app3d.ensure_models_loaded()
            
    @safe_method(
        component="StartupManager",
        category=ErrorCategory.GRAPHICS,
        severity=ErrorSeverity.MEDIUM,
        suppress_errors=True
    )
    def _init_scene(self):
        if not self.main_window:
            return
        if hasattr(self.main_window, 'viewer') and self.main_window.viewer:
            if hasattr(self.main_window.viewer, 'app3d') and self.main_window.viewer.app3d:
                app3d = self.main_window.viewer.app3d
                if hasattr(app3d, 'wait_for_scene_ready'):
                    app3d.wait_for_scene_ready()
                QtCore.QTimer.singleShot(500, lambda: None)
            
    def _finalize(self):
        QtCore.QTimer.singleShot(400, lambda: None)
