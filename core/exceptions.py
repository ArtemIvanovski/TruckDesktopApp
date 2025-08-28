from enum import Enum
from typing import Any, Dict, Optional, Callable, Union
import sys
import traceback
from PyQt5.QtCore import QObject, pyqtSignal


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    SYSTEM = "system"
    UI = "ui"
    NETWORK = "network"
    AUTH = "auth"
    FILE_IO = "file_io"
    GRAPHICS = "graphics"
    CALCULATION = "calculation"
    USER_INPUT = "user_input"


class ApplicationError(Exception):
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.recoverable = recoverable
        self.user_message = user_message or message


class SystemError(ApplicationError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.SYSTEM, **kwargs)


class UIError(ApplicationError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.UI, **kwargs)


class NetworkError(ApplicationError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)


class AuthError(ApplicationError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.AUTH, **kwargs)


class FileIOError(ApplicationError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.FILE_IO, **kwargs)


class GraphicsError(ApplicationError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.GRAPHICS, **kwargs)


class CalculationError(ApplicationError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.CALCULATION, **kwargs)


class UserInputError(ApplicationError):
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.USER_INPUT, **kwargs)


class ErrorContext:
    def __init__(self, operation: str = "", component: str = "", additional_data: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.component = component
        self.additional_data = additional_data or {}
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "component": self.component,
            "additional_data": self.additional_data
        }


class RecoveryStrategy:
    def __init__(
        self,
        name: str,
        action: Callable[[], bool],
        description: str = "",
        auto_execute: bool = False
    ):
        self.name = name
        self.action = action
        self.description = description
        self.auto_execute = auto_execute
        
    def execute(self) -> bool:
        try:
            return self.action()
        except Exception:
            return False


class ErrorHandler(QObject):
    error_occurred = pyqtSignal(ApplicationError)
    recovery_attempted = pyqtSignal(str, bool)
    
    def __init__(self):
        super().__init__()
        self.recovery_strategies: Dict[ErrorCategory, list[RecoveryStrategy]] = {}
        self.fallback_strategies: list[RecoveryStrategy] = []
        self._setup_default_strategies()
        
    def _setup_default_strategies(self):
        self.register_recovery_strategy(
            ErrorCategory.GRAPHICS,
            RecoveryStrategy(
                "reset_camera",
                lambda: self._reset_3d_camera(),
                "Reset 3D camera to default position",
                auto_execute=True
            )
        )
        
        self.register_recovery_strategy(
            ErrorCategory.UI,
            RecoveryStrategy(
                "refresh_ui",
                lambda: self._refresh_ui_component(),
                "Refresh UI component",
                auto_execute=True
            )
        )
        
        self.register_recovery_strategy(
            ErrorCategory.FILE_IO,
            RecoveryStrategy(
                "create_backup",
                lambda: self._create_backup_file(),
                "Create backup of current state",
                auto_execute=False
            )
        )
        
        self.add_fallback_strategy(
            RecoveryStrategy(
                "continue_operation",
                lambda: True,
                "Continue with degraded functionality",
                auto_execute=False
            )
        )
        
    def register_recovery_strategy(self, category: ErrorCategory, strategy: RecoveryStrategy):
        if category not in self.recovery_strategies:
            self.recovery_strategies[category] = []
        self.recovery_strategies[category].append(strategy)
        
    def add_fallback_strategy(self, strategy: RecoveryStrategy):
        self.fallback_strategies.append(strategy)
        
    def handle_error(self, error: ApplicationError) -> bool:
        self.error_occurred.emit(error)
        
        if error.severity == ErrorSeverity.CRITICAL:
            return self._handle_critical_error(error)
            
        if not error.recoverable:
            return False
            
        strategies = self.recovery_strategies.get(error.category, [])
        
        for strategy in strategies:
            if strategy.auto_execute:
                success = strategy.execute()
                self.recovery_attempted.emit(strategy.name, success)
                if success:
                    return True
                    
        for strategy in self.fallback_strategies:
            if strategy.auto_execute:
                success = strategy.execute()
                self.recovery_attempted.emit(strategy.name, success)
                if success:
                    return True
                    
        return False
        
    def _handle_critical_error(self, error: ApplicationError) -> bool:
        from core.logging import get_logger
        logger = get_logger()
        logger.critical(f"Critical error occurred: {error.message}", error)
        return False
        
    def _reset_3d_camera(self) -> bool:
        try:
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.topLevelWidgets():
                    if hasattr(widget, 'viewer') and hasattr(widget.viewer, 'app3d'):
                        if hasattr(widget.viewer.app3d, 'arc'):
                            cam = widget.viewer.app3d.arc
                            cam.target.set(0, 0, 0)
                            cam.radius = 3000
                            cam.alpha = 3.14159265 / 2
                            cam.beta = 3.14159265 / 4
                            cam.update()
                            return True
        except Exception:
            pass
        return False
        
    def _refresh_ui_component(self) -> bool:
        try:
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.processEvents()
                return True
        except Exception:
            pass
        return False
        
    def _create_backup_file(self) -> bool:
        try:
            import shutil
            import os
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            config_file = "config/settings.json"
            if os.path.exists(config_file):
                backup_file = f"config/settings_backup_{timestamp}.json"
                shutil.copy2(config_file, backup_file)
                return True
        except Exception:
            pass
        return False


class SafeExecutor:
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        
    def execute(
        self,
        operation: Callable[[], Any],
        context: ErrorContext,
        fallback_value: Any = None,
        error_class: type = ApplicationError
    ) -> Any:
        try:
            return operation()
        except Exception as e:
            app_error = error_class(
                message=str(e),
                context=context.to_dict()
            )
            
            recovered = self.error_handler.handle_error(app_error)
            if not recovered and fallback_value is not None:
                return fallback_value
            raise app_error
            
    def safe_call(
        self,
        func: Callable[[], Any],
        component: str = "",
        operation: str = "",
        fallback: Any = None,
        error_type: type = ApplicationError
    ) -> Any:
        context = ErrorContext(operation=operation, component=component)
        return self.execute(func, context, fallback, error_type)


class ErrorContextManager:
    def __init__(
        self,
        error_handler: ErrorHandler,
        operation: str,
        component: str = "",
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        suppress_errors: bool = False
    ):
        self.error_handler = error_handler
        self.operation = operation
        self.component = component
        self.category = category
        self.severity = severity
        self.suppress_errors = suppress_errors
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            context = ErrorContext(
                operation=self.operation,
                component=self.component,
                additional_data={
                    "exception_type": exc_type.__name__,
                    "traceback": traceback.format_exc()
                }
            )
            
            app_error = ApplicationError(
                message=str(exc_val),
                category=self.category,
                severity=self.severity,
                context=context.to_dict()
            )
            
            self.error_handler.handle_error(app_error)
            
            if self.suppress_errors:
                return True
        return False


_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def safe_execute(
    operation: Callable[[], Any],
    component: str = "",
    operation_name: str = "",
    fallback: Any = None,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
) -> Any:
    handler = get_error_handler()
    executor = SafeExecutor(handler)
    
    context = ErrorContext(
        operation=operation_name,
        component=component
    )
    
    error_class = type(f"{category.value.title()}Error", (ApplicationError,), {
        "__init__": lambda self, message, **kwargs: ApplicationError.__init__(
            self, message, category=category, severity=severity, **kwargs
        )
    })
    
    return executor.execute(operation, context, fallback, error_class)


def error_context(
    operation: str,
    component: str = "",
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    suppress: bool = False
) -> ErrorContextManager:
    handler = get_error_handler()
    return ErrorContextManager(handler, operation, component, category, severity, suppress)
