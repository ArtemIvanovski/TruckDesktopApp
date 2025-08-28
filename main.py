#!/usr/bin/env python3
import sys
import os
from PyQt5 import QtWidgets, QtCore
from GUI.loading_screen import StartupManager
from GUI.access_code_dialog import AccessCodeDialog
from GUI.main_window import MainWindow
from core.logging import get_logger, LoggingMixin
from core.error_management import (
    get_global_error_handler, setup_global_exception_handler,
    handle_exceptions, ErrorReportingMixin
)
from core.exceptions import ApplicationError, ErrorSeverity, ErrorCategory
from auth.auth_module import auth_module


def show_auth_dialog():
    guard = AccessCodeDialog()
    return guard.exec_() == QtWidgets.QDialog.Accepted


class ApplicationController(QtCore.QObject, ErrorReportingMixin):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.main_window = None
        self.global_error_handler = get_global_error_handler()
        self.startup_manager = StartupManager()
        self.startup_manager.startup_complete.connect(self._on_startup_complete)
        
        self.log_info("Application controller initialized")
        self._setup_error_handling()
        
    def _setup_error_handling(self):
        setup_global_exception_handler()
        self.global_error_handler.error_handled.connect(self._on_error_handled)
        self.global_error_handler.application_degraded.connect(self._on_feature_degraded)
        
    def _on_error_handled(self, error: ApplicationError):
        self.log_info(f"Error handled: {error.category.value} - {error.message}")
        
    def _on_feature_degraded(self, feature_name: str):
        self.log_warning(f"Feature degraded: {feature_name}")
        
    @handle_exceptions(
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.HIGH,
        user_message="Failed to start the application"
    )
    def start(self):
        self.log_info("Starting application")
        self.start_timer("application_startup")
        self.startup_manager.start_loading()
        
    @handle_exceptions(
        category=ErrorCategory.UI,
        severity=ErrorSeverity.CRITICAL,
        user_message="Failed to initialize the main window"
    )
    def _on_startup_complete(self):
        self.log_info("Startup complete, preparing main window")
        
        if hasattr(self.startup_manager, 'main_window') and self.startup_manager.main_window:
            self.main_window = self.startup_manager.main_window
            self.log_info("Using pre-loaded main window")
        else:
            self.log_info("Creating new main window")
            self.main_window = MainWindow()
        
        self.global_error_handler.initialize_ui(self.main_window)
        
        screen = self.app.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            self.main_window.resize(screen_geometry.width(), screen_geometry.height())
            self.main_window.move(screen_geometry.x(), screen_geometry.y())
        
        self._wait_for_scene_ready()
            
    def _wait_for_scene_ready(self):
        self.log_info("Waiting for 3D scene to initialize")
        self._scene_check_timer = QtCore.QTimer()
        self._scene_check_timer.timeout.connect(self._check_scene_ready)
        self._scene_check_timer.start(200)
        self._scene_check_attempts = 0
        self._max_scene_check_attempts = 50
        
    def _check_scene_ready(self):
        self._scene_check_attempts += 1
        
        def check_operation():
            if hasattr(self.main_window, 'viewer') and self.main_window.viewer:
                app3d = getattr(self.main_window.viewer, 'app3d', None)
                if app3d and getattr(app3d, 'scene_initialized', False):
                    self._scene_check_timer.stop()
                    self._show_main_window()
                    return True
                    
            if self._scene_check_attempts >= self._max_scene_check_attempts:
                self.log_warning("Scene initialization timeout, showing window anyway")
                self._scene_check_timer.stop()
                self._show_main_window()
                return True
                
            return False
            
        self.safe_execute(
            check_operation,
            fallback=lambda: (
                self._scene_check_timer.stop() if self._scene_check_attempts >= self._max_scene_check_attempts 
                else None,
                self._show_main_window() if self._scene_check_attempts >= self._max_scene_check_attempts 
                else None
            )[-1]
        )
                
    @handle_exceptions(
        category=ErrorCategory.UI,
        severity=ErrorSeverity.MEDIUM,
        user_message="Failed to display the main window"
    )
    def _show_main_window(self):
        self.main_window.show()
        startup_time = self.end_timer("application_startup")
        self.log_info(f"Application started successfully in {startup_time:.2f}s")


if __name__ == "__main__":
    qt_app = QtWidgets.QApplication(sys.argv)
    qt_app.setApplicationName("GTSTREAM")
    qt_app.setApplicationVersion("1.0.0")
    qt_app.setOrganizationName("GTSTREAM Solutions")
    
    controller = ApplicationController(qt_app)
    controller.start()
    
    try:
        sys.exit(qt_app.exec_())
    finally:
        auth_module.cleanup()
