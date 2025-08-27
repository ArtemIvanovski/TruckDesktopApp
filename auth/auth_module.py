import atexit
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

from utils.settings_manager import SettingsManager
from .config.settings import AuthConfig
from .manager.auth_manager import AuthManager


class AuthModule(QObject):
    authentication_required = pyqtSignal()
    authentication_successful = pyqtSignal()
    authentication_failed = pyqtSignal(str)
    connection_lost = pyqtSignal()
    connection_restored = pyqtSignal()
    
    _instance: Optional['AuthModule'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        super().__init__()
        self.settings_manager = SettingsManager()
        self.config = AuthConfig.from_settings(self.settings_manager)
        self.auth_manager: Optional[AuthManager] = None
        self._initialized = True
        
        atexit.register(self.cleanup)
    
    def initialize(self):
        if not self.config.enabled:
            return
        
        if self.auth_manager is None:
            self.auth_manager = AuthManager(self.config)
            self._connect_signals()
    
    def _connect_signals(self):
        if self.auth_manager:
            self.auth_manager.authentication_required.connect(
                self.authentication_required.emit
            )
            self.auth_manager.authentication_successful.connect(
                self.authentication_successful.emit
            )
            self.auth_manager.authentication_failed.connect(
                self.authentication_failed.emit
            )
            self.auth_manager.connection_lost.connect(
                self.connection_lost.emit
            )
            self.auth_manager.connection_restored.connect(
                self.connection_restored.emit
            )
    
    def is_enabled(self) -> bool:
        return self.config.enabled
    
    def enable(self):
        self.config.enabled = True
        self.config.save_to_settings(self.settings_manager)
        self.initialize()
    
    def disable(self):
        self.config.enabled = False
        self.config.save_to_settings(self.settings_manager)
        if self.auth_manager:
            self.auth_manager.cleanup()
            self.auth_manager = None
    
    def authenticate(self, access_code: str) -> bool:
        if not self.is_enabled() or not self.auth_manager:
            return True
        
        return self.auth_manager.authenticate(access_code)
    
    def logout(self):
        if self.auth_manager:
            self.auth_manager.logout()
    
    def is_authenticated(self) -> bool:
        if not self.is_enabled():
            return True
        
        return self.auth_manager.is_authenticated if self.auth_manager else False
    
    def is_connection_active(self) -> bool:
        if not self.is_enabled() or not self.auth_manager:
            return True
        
        return self.auth_manager.is_connection_active()
    
    def require_authentication(self) -> bool:
        if not self.is_enabled():
            return True
        
        if not self.is_authenticated():
            self.authentication_required.emit()
            return False
        
        if not self.is_connection_active():
            return False
        
        return True
    
    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self.config.save_to_settings(self.settings_manager)
        
        if self.auth_manager:
            self.auth_manager.cleanup()
            self.auth_manager = AuthManager(self.config)
            self._connect_signals()
    
    def cleanup(self):
        if self.auth_manager:
            self.auth_manager.cleanup()


auth_module = AuthModule()
