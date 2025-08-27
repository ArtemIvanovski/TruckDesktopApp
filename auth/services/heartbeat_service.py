import threading
import time
from typing import Optional, Callable
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from ..config.settings import AuthConfig
from ..services.api_client import ApiClient
from ..exceptions.auth_exceptions import NetworkException, HeartbeatFailedException


class HeartbeatService(QObject):
    connection_lost = pyqtSignal()
    connection_restored = pyqtSignal()
    
    def __init__(self, config: AuthConfig, api_client: ApiClient):
        super().__init__()
        self.config = config
        self.api_client = api_client
        self.access_code: Optional[str] = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._send_heartbeat)
        self.is_running = False
        self.consecutive_failures = 0
        self.max_failures = 3
        
    def start(self, access_code: str):
        self.access_code = access_code
        self.consecutive_failures = 0
        self.is_running = True
        self.timer.start(self.config.heartbeat_interval * 1000)
        
    def stop(self):
        self.is_running = False
        self.timer.stop()
        
    def _send_heartbeat(self):
        if not self.access_code or not self.is_running:
            return
            
        try:
            response = self.api_client.send_heartbeat(self.access_code)
            if response.success:
                if self.consecutive_failures > 0:
                    self.connection_restored.emit()
                self.consecutive_failures = 0
            else:
                self._handle_failure(response.error or "Unknown error")
                
        except NetworkException as e:
            self._handle_failure(str(e))
        except Exception as e:
            self._handle_failure(f"Unexpected error: {str(e)}")
    
    def _handle_failure(self, error: str):
        self.consecutive_failures += 1
        
        if self.consecutive_failures >= self.max_failures:
            self.connection_lost.emit()
            
    def is_connected(self) -> bool:
        return self.consecutive_failures < self.max_failures
