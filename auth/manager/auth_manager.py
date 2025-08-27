from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox, QApplication
from ..config.settings import AuthConfig
from ..services.async_api_client import AsyncApiClient
from ..services.device_service import DeviceService
from ..services.threaded_heartbeat_service import ThreadedHeartbeatService
from ..exceptions.auth_exceptions import (
    NetworkException, InvalidTokenException, 
    TokenExpiredException, TokenOccupiedException,
    AuthException
)


class AuthManager(QObject):
    authentication_required = pyqtSignal()
    authentication_successful = pyqtSignal()
    authentication_failed = pyqtSignal(str)
    connection_lost = pyqtSignal()
    connection_restored = pyqtSignal()
    
    def __init__(self, config: AuthConfig):
        super().__init__()
        self.config = config
        self.api_client = AsyncApiClient(config)
        self.device_service = DeviceService()
        self.heartbeat_service = ThreadedHeartbeatService(config, self.api_client)
        self.current_token: Optional[str] = None
        self.is_authenticated = False
        self.app_blocked = False
        self.auth_in_progress = False
        
        self.heartbeat_service.connection_lost.connect(self._on_connection_lost)
        self.heartbeat_service.connection_restored.connect(self._on_connection_restored)
        
        self.api_client.request_completed.connect(self._on_api_success)
        self.api_client.request_failed.connect(self._on_api_failure)
    
    def authenticate(self, access_code: str) -> bool:
        if self.auth_in_progress:
            return False
        
        self.auth_in_progress = True
        self.current_token = access_code
        
        try:
            device_info = self.device_service.get_device_info()
            
            def on_auth_result(response, error):
                self.auth_in_progress = False
                if error:
                    self._handle_auth_error(error)
                elif response and response.success:
                    self.is_authenticated = True
                    self.heartbeat_service.start(access_code)
                    self.authentication_successful.emit()
                else:
                    self.authentication_failed.emit(response.error if response else "Authentication failed")
            
            self.api_client.verify_token_async(access_code, device_info, callback=on_auth_result)
            return True
            
        except Exception as e:
            self.auth_in_progress = False
            self._handle_auth_error(str(e))
            return False
    
    def _handle_auth_error(self, error: str):
        if "Invalid token" in error:
            self.authentication_failed.emit("Неверный код доступа")
        elif "Token expired" in error:
            self.authentication_failed.emit("Код доступа истек")
        elif "Token is already in use" in error:
            self.authentication_failed.emit("Код уже используется на другом устройстве")
        elif "Network error" in error:
            self.authentication_failed.emit("Проверьте соединение с интернетом")
        else:
            self.authentication_failed.emit(error)
    
    def logout(self):
        if self.current_token:
            try:
                self.heartbeat_service.stop()
                self.api_client.logout_async(self.current_token)
            except Exception:
                pass
            finally:
                self.current_token = None
                self.is_authenticated = False
    
    def _on_connection_lost(self):
        if not self.app_blocked:
            self.app_blocked = True
            self.connection_lost.emit()
            self._show_connection_error()
    
    def _on_connection_restored(self):
        if self.app_blocked:
            self.app_blocked = False
            self.connection_restored.emit()
            self._hide_connection_error()
    
    def _show_connection_error(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Соединение потеряно")
        msg.setText("Проверьте соединение с интернетом")
        msg.setInformativeText("Функционал приложения заблокирован до восстановления соединения")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _hide_connection_error(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Соединение восстановлено")
        msg.setText("Соединение с сервером восстановлено")
        msg.setInformativeText("Функционал приложения разблокирован")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.show()
        QApplication.instance().processEvents()
        msg.close()
    
    def is_connection_active(self) -> bool:
        return self.heartbeat_service.is_connected()
    
    def _on_api_success(self, request_type: str, response):
        pass
    
    def _on_api_failure(self, request_type: str, error: str):
        if request_type == "verify":
            self._handle_auth_error(error)
    
    def cleanup(self):
        self.logout()
        self.heartbeat_service.cleanup()
        self.api_client.close()
