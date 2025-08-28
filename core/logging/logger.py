import logging
import logging.handlers
import os
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal

from utils.setting_deploy import get_resource_path


class LogLevel:
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class PerformanceMetrics:
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        
    def start_timer(self, operation_name: str):
        self.start_times[operation_name] = time.perf_counter()
        
    def end_timer(self, operation_name: str) -> float:
        if operation_name not in self.start_times:
            return 0.0
        duration = time.perf_counter() - self.start_times[operation_name]
        del self.start_times[operation_name]
        
        if operation_name not in self.metrics:
            self.metrics[operation_name] = []
        self.metrics[operation_name].append(duration)
        return duration
        
    def get_average(self, operation_name: str) -> float:
        if operation_name not in self.metrics or not self.metrics[operation_name]:
            return 0.0
        return sum(self.metrics[operation_name]) / len(self.metrics[operation_name])
        
    def get_total(self, operation_name: str) -> float:
        if operation_name not in self.metrics:
            return 0.0
        return sum(self.metrics[operation_name])
        
    def clear(self):
        self.metrics.clear()
        self.start_times.clear()


class ErrorReporter:
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.error_log_path = self.log_dir / "errors.json"
        self.errors = []
        self._load_existing_errors()
        
    def _load_existing_errors(self):
        if self.error_log_path.exists():
            try:
                with open(self.error_log_path, 'r', encoding='utf-8') as f:
                    self.errors = json.load(f)
            except Exception:
                self.errors = []
                
    def report_error(self, error_type: str, message: str, traceback_str: str = "", context: Dict[str, Any] = None):
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": message,
            "traceback": traceback_str,
            "context": context or {}
        }
        
        self.errors.append(error_entry)
        self._save_errors()
        
    def _save_errors(self):
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            with open(self.error_log_path, 'w', encoding='utf-8') as f:
                json.dump(self.errors[-1000:], f, indent=2, ensure_ascii=False)
        except Exception:
            pass
            
    def get_recent_errors(self, count: int = 50) -> list:
        return self.errors[-count:]
        
    def clear_errors(self):
        self.errors.clear()
        self._save_errors()


class ApplicationLogger(QObject):
    error_occurred = pyqtSignal(str, str)
    
    _instance: Optional['ApplicationLogger'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        
        self.log_dir = Path(get_resource_path("logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("TruckLoader")
        self.logger.setLevel(LogLevel.DEBUG)
        
        self.performance_metrics = PerformanceMetrics()
        self.error_reporter = ErrorReporter(str(self.log_dir))
        
        self._setup_handlers()
        self._initialized = True
        
    def _setup_handlers(self):
        self.logger.handlers.clear()
        
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "application.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(LogLevel.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "errors.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(LogLevel.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        performance_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "performance.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=2,
            encoding='utf-8'
        )
        performance_handler.setLevel(LogLevel.INFO)
        performance_handler.setFormatter(formatter)
        
        performance_logger = logging.getLogger("TruckLoader.Performance")
        performance_logger.setLevel(LogLevel.INFO)
        performance_logger.addHandler(performance_handler)
        
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)
        
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)
        
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)
        
    def error(self, message: str, exception: Exception = None, **kwargs):
        if exception:
            traceback_str = traceback.format_exc()
            self.error_reporter.report_error(
                type(exception).__name__,
                str(exception),
                traceback_str,
                kwargs
            )
            self.logger.error(f"{message}: {exception}", extra=kwargs)
            self.error_occurred.emit(type(exception).__name__, str(exception))
        else:
            self.logger.error(message, extra=kwargs)
            self.error_occurred.emit("Error", message)
            
    def critical(self, message: str, exception: Exception = None, **kwargs):
        if exception:
            traceback_str = traceback.format_exc()
            self.error_reporter.report_error(
                type(exception).__name__,
                str(exception),
                traceback_str,
                kwargs
            )
            self.logger.critical(f"{message}: {exception}", extra=kwargs)
            self.error_occurred.emit(type(exception).__name__, str(exception))
        else:
            self.logger.critical(message, extra=kwargs)
            self.error_occurred.emit("Critical", message)
            
    def start_performance_timer(self, operation: str):
        self.performance_metrics.start_timer(operation)
        
    def end_performance_timer(self, operation: str) -> float:
        duration = self.performance_metrics.end_timer(operation)
        performance_logger = logging.getLogger("TruckLoader.Performance")
        performance_logger.info(f"{operation}: {duration:.4f}s")
        return duration
        
    def log_performance_summary(self):
        performance_logger = logging.getLogger("TruckLoader.Performance")
        for operation, durations in self.performance_metrics.metrics.items():
            avg = self.performance_metrics.get_average(operation)
            total = self.performance_metrics.get_total(operation)
            count = len(durations)
            performance_logger.info(f"SUMMARY {operation}: avg={avg:.4f}s, total={total:.4f}s, count={count}")
            
    def get_recent_errors(self, count: int = 50) -> list:
        return self.error_reporter.get_recent_errors(count)
        
    def clear_performance_metrics(self):
        self.performance_metrics.clear()


logger = ApplicationLogger()


def get_logger() -> ApplicationLogger:
    return logger


class LoggingMixin:
    @property
    def logger(self) -> ApplicationLogger:
        return get_logger()
        
    def log_debug(self, message: str, **kwargs):
        self.logger.debug(f"[{self.__class__.__name__}] {message}", **kwargs)
        
    def log_info(self, message: str, **kwargs):
        self.logger.info(f"[{self.__class__.__name__}] {message}", **kwargs)
        
    def log_warning(self, message: str, **kwargs):
        self.logger.warning(f"[{self.__class__.__name__}] {message}", **kwargs)
        
    def log_error(self, message: str, exception: Exception = None, **kwargs):
        self.logger.error(f"[{self.__class__.__name__}] {message}", exception, **kwargs)
        
    def log_critical(self, message: str, exception: Exception = None, **kwargs):
        self.logger.critical(f"[{self.__class__.__name__}] {message}", exception, **kwargs)
        
    def start_timer(self, operation: str):
        full_operation = f"{self.__class__.__name__}.{operation}"
        self.logger.start_performance_timer(full_operation)
        
    def end_timer(self, operation: str) -> float:
        full_operation = f"{self.__class__.__name__}.{operation}"
        return self.logger.end_performance_timer(full_operation)
