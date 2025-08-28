import sys
import traceback
import functools
from typing import Any, Callable, Optional, Type, Dict, List
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QWidget

from core.exceptions import (
    ApplicationError, ErrorSeverity, ErrorCategory, ErrorHandler,
    RecoveryStrategy, get_error_handler, safe_execute, error_context
)
from GUI.error_management import ErrorDialogManager, ErrorDialogType
from core.logging import get_logger, LoggingMixin


class GlobalErrorHandler(QObject, LoggingMixin):
    error_handled = pyqtSignal(ApplicationError)
    recovery_executed = pyqtSignal(str, bool)
    application_degraded = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.error_handler = get_error_handler()
        self.dialog_manager = None
        self.degraded_features = set()
        self.error_counts = {}
        self.last_error_time = {}
        self.max_errors_per_minute = 10
        
        self._setup_connections()
        self._setup_degradation_strategies()
        
    def initialize_ui(self, main_window: QWidget):
        self.dialog_manager = ErrorDialogManager(main_window)
        
    def _setup_connections(self):
        self.error_handler.error_occurred.connect(self._handle_application_error)
        self.error_handler.recovery_attempted.connect(self._on_recovery_attempted)
        
    def _setup_degradation_strategies(self):
        self.degradation_strategies = {
            ErrorCategory.GRAPHICS: self._degrade_graphics,
            ErrorCategory.UI: self._degrade_ui,
            ErrorCategory.NETWORK: self._degrade_network,
            ErrorCategory.FILE_IO: self._degrade_file_io,
            ErrorCategory.CALCULATION: self._degrade_calculation
        }
        
    def _handle_application_error(self, error: ApplicationError):
        self.log_error(f"Handling application error: {error.message}", error)
        
        if self._should_suppress_error(error):
            self.log_info(f"Suppressing repeated error: {error.message}")
            return
            
        self._record_error(error)
        
        if error.severity == ErrorSeverity.CRITICAL:
            self._handle_critical_error(error)
        elif self._should_degrade_functionality(error):
            self._apply_degradation(error)
        else:
            self._show_error_dialog(error)
            
        self.error_handled.emit(error)
        
    def _should_suppress_error(self, error: ApplicationError) -> bool:
        error_key = f"{type(error).__name__}:{error.message}"
        current_time = QTimer()
        
        if error_key in self.error_counts:
            if self.error_counts[error_key] > self.max_errors_per_minute:
                return True
        return False
        
    def _record_error(self, error: ApplicationError):
        error_key = f"{type(error).__name__}:{error.message}"
        if error_key not in self.error_counts:
            self.error_counts[error_key] = 0
        self.error_counts[error_key] += 1
        
        QTimer.singleShot(60000, lambda: self._reset_error_count(error_key))
        
    def _reset_error_count(self, error_key: str):
        if error_key in self.error_counts:
            self.error_counts[error_key] = max(0, self.error_counts[error_key] - 1)
            
    def _handle_critical_error(self, error: ApplicationError):
        self.log_critical(f"Critical error detected: {error.message}", error)
        
        if self.dialog_manager:
            self.dialog_manager.show_error(error, ErrorDialogType.DETAILED)
        
        if not error.recoverable:
            self._initiate_safe_shutdown()
        else:
            self._attempt_critical_recovery(error)
            
    def _attempt_critical_recovery(self, error: ApplicationError):
        recovery_strategies = self.error_handler.recovery_strategies.get(error.category, [])
        fallback_strategies = self.error_handler.fallback_strategies
        
        all_strategies = recovery_strategies + fallback_strategies
        
        if all_strategies and self.dialog_manager:
            self.dialog_manager.show_error(error, ErrorDialogType.RECOVERY, all_strategies)
        else:
            self._apply_degradation(error)
            
    def _should_degrade_functionality(self, error: ApplicationError) -> bool:
        error_key = f"{error.category.value}:{type(error).__name__}"
        return self.error_counts.get(error_key, 0) >= 3
        
    def _apply_degradation(self, error: ApplicationError):
        if error.category in self.degradation_strategies:
            strategy = self.degradation_strategies[error.category]
            feature_name = strategy()
            
            if feature_name:
                self.degraded_features.add(feature_name)
                self.application_degraded.emit(feature_name)
                self.log_warning(f"Feature degraded: {feature_name}")
                
                if self.dialog_manager:
                    degradation_error = ApplicationError(
                        message=f"Feature '{feature_name}' has been disabled due to repeated errors",
                        category=ErrorCategory.SYSTEM,
                        severity=ErrorSeverity.MEDIUM,
                        user_message=f"Some features have been temporarily disabled to ensure stability"
                    )
                    self.dialog_manager.show_error(degradation_error, ErrorDialogType.NOTIFICATION)
                    
    def _degrade_graphics(self) -> str:
        try:
            app = QApplication.instance()
            if app:
                for widget in app.topLevelWidgets():
                    if hasattr(widget, 'viewer') and hasattr(widget.viewer, 'app3d'):
                        graphics_manager = getattr(widget.viewer.app3d, 'graphics_manager', None)
                        if graphics_manager:
                            graphics_manager.set_low_quality_mode()
            return "3D Graphics Quality"
        except Exception:
            return ""
            
    def _degrade_ui(self) -> str:
        try:
            app = QApplication.instance()
            if app:
                app.setStyleSheet("* { animation: none; }")
            return "UI Animations"
        except Exception:
            return ""
            
    def _degrade_network(self) -> str:
        try:
            from auth.auth_module import auth_module
            auth_module.disable_heartbeat()
            return "Network Features"
        except Exception:
            return ""
            
    def _degrade_file_io(self) -> str:
        return "Auto-save"
        
    def _degrade_calculation(self) -> str:
        return "Advanced Calculations"
        
    def _show_error_dialog(self, error: ApplicationError):
        if self.dialog_manager:
            if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self.dialog_manager.show_error(error, ErrorDialogType.DETAILED)
            else:
                self.dialog_manager.show_error(error, ErrorDialogType.NOTIFICATION)
                
    def _on_recovery_attempted(self, strategy_name: str, success: bool):
        self.recovery_executed.emit(strategy_name, success)
        if success:
            self.log_info(f"Recovery strategy '{strategy_name}' succeeded")
        else:
            self.log_warning(f"Recovery strategy '{strategy_name}' failed")
            
    def _initiate_safe_shutdown(self):
        self.log_critical("Initiating safe application shutdown")
        
        try:
            from auth.auth_module import auth_module
            auth_module.cleanup()
        except Exception:
            pass
            
        try:
            self._save_emergency_state()
        except Exception:
            pass
            
        app = QApplication.instance()
        if app:
            app.quit()
            
    def _save_emergency_state(self):
        import json
        import os
        from datetime import datetime
        
        emergency_data = {
            "timestamp": datetime.now().isoformat(),
            "degraded_features": list(self.degraded_features),
            "error_counts": dict(self.error_counts)
        }
        
        try:
            os.makedirs("logs", exist_ok=True)
            with open("logs/emergency_state.json", "w") as f:
                json.dump(emergency_data, f, indent=2)
        except Exception:
            pass
            
    def is_feature_degraded(self, feature_name: str) -> bool:
        return feature_name in self.degraded_features
        
    def restore_feature(self, feature_name: str):
        if feature_name in self.degraded_features:
            self.degraded_features.remove(feature_name)
            self.log_info(f"Feature restored: {feature_name}")


_global_error_handler: Optional[GlobalErrorHandler] = None


def get_global_error_handler() -> GlobalErrorHandler:
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = GlobalErrorHandler()
    return _global_error_handler


def handle_exceptions(
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    user_message: Optional[str] = None,
    recoverable: bool = True,
    show_dialog: bool = True
):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ApplicationError:
                raise
            except Exception as e:
                error = ApplicationError(
                    message=str(e),
                    category=category,
                    severity=severity,
                    user_message=user_message,
                    recoverable=recoverable,
                    context={
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200],
                        "traceback": traceback.format_exc()
                    }
                )
                
                handler = get_global_error_handler()
                if show_dialog:
                    handler._handle_application_error(error)
                else:
                    handler.log_error(f"Exception in {func.__name__}: {str(e)}", e)
                    
                raise error
        return wrapper
    return decorator


def safe_method(
    component: str = "",
    fallback: Any = None,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.LOW,
    suppress_errors: bool = False
):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            operation_name = f"{component}.{func.__name__}" if component else func.__name__
            
            try:
                with error_context(operation_name, component, category, severity, suppress_errors):
                    return func(*args, **kwargs)
            except ApplicationError:
                if fallback is not None:
                    return fallback
                raise
            except Exception as e:
                if fallback is not None:
                    return fallback
                raise
        return wrapper
    return decorator


class ErrorBoundary:
    def __init__(
        self,
        component_name: str,
        fallback_action: Optional[Callable[[], Any]] = None,
        category: ErrorCategory = ErrorCategory.SYSTEM
    ):
        self.component_name = component_name
        self.fallback_action = fallback_action
        self.category = category
        self.handler = get_global_error_handler()
        
    def execute(self, operation: Callable[[], Any]) -> Any:
        try:
            return operation()
        except ApplicationError as e:
            self.handler._handle_application_error(e)
            if self.fallback_action:
                return self.fallback_action()
            raise
        except Exception as e:
            error = ApplicationError(
                message=str(e),
                category=self.category,
                severity=ErrorSeverity.MEDIUM,
                context={
                    "component": self.component_name,
                    "operation": operation.__name__ if hasattr(operation, '__name__') else str(operation),
                    "traceback": traceback.format_exc()
                }
            )
            self.handler._handle_application_error(error)
            if self.fallback_action:
                return self.fallback_action()
            raise error


def setup_global_exception_handler():
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        error = ApplicationError(
            message=str(exc_value),
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            recoverable=False,
            context={
                "exception_type": exc_type.__name__,
                "traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            }
        )
        
        handler = get_global_error_handler()
        handler._handle_application_error(error)
        
    sys.excepthook = handle_exception


class ErrorReportingMixin(LoggingMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_boundary = ErrorBoundary(self.__class__.__name__)
        
    def safe_execute(self, operation: Callable[[], Any], fallback: Any = None) -> Any:
        return safe_execute(
            operation,
            component=self.__class__.__name__,
            operation_name=operation.__name__ if hasattr(operation, '__name__') else "operation",
            fallback=fallback
        )
        
    def with_error_boundary(self, operation: Callable[[], Any]) -> Any:
        return self.error_boundary.execute(operation)
        
    def report_error(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None
    ):
        error = ApplicationError(
            message=message,
            category=category,
            severity=severity,
            context=context or {}
        )
        
        handler = get_global_error_handler()
        handler._handle_application_error(error)
