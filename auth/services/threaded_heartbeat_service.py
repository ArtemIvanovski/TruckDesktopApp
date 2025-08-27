import threading
import time
from typing import Optional
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QMutex, QWaitCondition
from ..config.settings import AuthConfig
from ..services.async_api_client import AsyncApiClient
from ..exceptions.auth_exceptions import NetworkException


class HeartbeatWorker(QObject):
    heartbeat_success = pyqtSignal()
    heartbeat_failed = pyqtSignal(str)
    
    def __init__(self, config: AuthConfig, api_client: AsyncApiClient):
        super().__init__()
        self.config = config
        self.api_client = api_client
        self.access_code: Optional[str] = None
        self.is_running = False
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        
    def start_heartbeat(self, access_code: str):
        self.mutex.lock()
        self.access_code = access_code
        self.is_running = True
        self.condition.wakeAll()
        self.mutex.unlock()
        
    def stop_heartbeat(self):
        self.mutex.lock()
        self.is_running = False
        self.condition.wakeAll()
        self.mutex.unlock()
        
    def run_heartbeat_loop(self):
        while True:
            self.mutex.lock()
            
            if not self.is_running:
                if not self.condition.wait(self.mutex, 1000):
                    self.mutex.unlock()
                    continue
            
            if not self.is_running:
                self.mutex.unlock()
                break
                
            current_code = self.access_code
            interval_ms = self.config.heartbeat_interval * 1000
            self.mutex.unlock()
            
            if current_code:
                self._send_heartbeat(current_code)
            
            self.mutex.lock()
            if self.is_running:
                self.condition.wait(self.mutex, interval_ms)
            self.mutex.unlock()
    
    def _send_heartbeat(self, code: str):
        def on_success(response, error):
            if error:
                self.heartbeat_failed.emit(error)
            else:
                if response and response.success:
                    self.heartbeat_success.emit()
                else:
                    self.heartbeat_failed.emit(response.error if response else "Unknown error")
        
        try:
            self.api_client.send_heartbeat_async(code, callback=on_success)
        except Exception as e:
            self.heartbeat_failed.emit(str(e))


class ThreadedHeartbeatService(QObject):
    connection_lost = pyqtSignal()
    connection_restored = pyqtSignal()
    
    def __init__(self, config: AuthConfig, api_client: AsyncApiClient):
        super().__init__()
        self.config = config
        self.api_client = api_client
        self.worker = HeartbeatWorker(config, api_client)
        self.thread = QThread()
        self.consecutive_failures = 0
        self.max_failures = 3
        self.is_connected_state = True
        
        self.worker.moveToThread(self.thread)
        self.worker.heartbeat_success.connect(self._on_heartbeat_success)
        self.worker.heartbeat_failed.connect(self._on_heartbeat_failed)
        
        self.thread.started.connect(self.worker.run_heartbeat_loop)
        self.thread.start()
        
    def start(self, access_code: str):
        self.consecutive_failures = 0
        self.is_connected_state = True
        self.worker.start_heartbeat(access_code)
        
    def stop(self):
        self.worker.stop_heartbeat()
        
    def _on_heartbeat_success(self):
        if self.consecutive_failures > 0:
            self.consecutive_failures = 0
            if not self.is_connected_state:
                self.is_connected_state = True
                self.connection_restored.emit()
    
    def _on_heartbeat_failed(self, error: str):
        self.consecutive_failures += 1
        
        if self.consecutive_failures >= self.max_failures and self.is_connected_state:
            self.is_connected_state = False
            self.connection_lost.emit()
    
    def is_connected(self) -> bool:
        return self.is_connected_state
    
    def cleanup(self):
        self.stop()
        self.thread.quit()
        self.thread.wait(5000)
        if self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
