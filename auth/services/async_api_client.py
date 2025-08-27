import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Any, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from ..config.settings import AuthConfig
from ..models.device_info import DeviceInfo
from ..models.auth_response import AuthResponse, HeartbeatResponse, LogoutResponse
from ..services.connection_pool import ConnectionPool
from ..exceptions.auth_exceptions import (
    NetworkException, InvalidTokenException,
    TokenExpiredException, TokenOccupiedException
)


class AsyncApiClient(QObject):
    request_completed = pyqtSignal(str, object)
    request_failed = pyqtSignal(str, str)

    def __init__(self, config: AuthConfig):
        super().__init__()
        self.config = config
        self.connection_pool = ConnectionPool(config)
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="auth_api")
        self._request_cache = {}
        self._cache_lock = threading.Lock()
        self._last_heartbeat = 0
        self._heartbeat_interval = 10

    def verify_token_async(self, code: str, device_info: DeviceInfo,
                           callback: Optional[Callable] = None) -> Future:
        return self._submit_request("verify", self._verify_token_sync,
                                    code, device_info, callback=callback)

    def send_heartbeat_async(self, code: str,
                             callback: Optional[Callable] = None) -> Future:
        return self._submit_request("heartbeat", self._send_heartbeat_sync,
                                    code, callback=callback)

    def logout_async(self, code: str,
                     callback: Optional[Callable] = None) -> Future:
        return self._submit_request("logout", self._logout_sync,
                                    code, callback=callback)

    def _submit_request(self, request_type: str, func: Callable,
                        *args, callback: Optional[Callable] = None) -> Future:
        def wrapped_request():
            try:
                result = func(*args)
                self.request_completed.emit(request_type, result)
                if callback:
                    callback(result, None)
                return result
            except Exception as e:
                error_msg = str(e)
                self.request_failed.emit(request_type, error_msg)
                if callback:
                    callback(None, error_msg)
                raise

        return self.executor.submit(wrapped_request)

    def _verify_token_sync(self, code: str, device_info: DeviceInfo) -> AuthResponse:
        url = f"{self.config.base_url}/api/tokens/verify/"
        data = {
            "code": code,
            "device_info": device_info.to_dict(),
            "ip_address": device_info.ip_address,
            "user_agent": f"TruckDesktopApp/{device_info.device_name}"
        }

        try:
            response = self.session.post(url, json=data)

            if response.status_code == 200:
                return AuthResponse.from_dict(response.json())
            elif response.status_code == 404:
                raise InvalidTokenException("Invalid token")
            elif response.status_code == 403:
                raise TokenExpiredException("Token expired")
            elif response.status_code == 409:
                raise TokenOccupiedException("Token is already in use")
            else:
                raise NetworkException(f"Server error: {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise NetworkException(f"Network error: {str(e)}")

    def _send_heartbeat_sync(self, code: str) -> HeartbeatResponse:
        current_time = time.time()

        if current_time - self._last_heartbeat < self._heartbeat_interval:
            return HeartbeatResponse(success=True)

        cache_key = f"heartbeat_{code}_{int(current_time / 30)}"

        with self._cache_lock:
            if cache_key in self._request_cache:
                return self._request_cache[cache_key]

        url = f"{self.config.base_url}/api/tokens/heartbeat/"
        data = {"code": code}

        try:
            session = self.connection_pool.get_session()
            response = session.post(url, json=data)

            if response.status_code == 200:
                result = HeartbeatResponse.from_dict(response.json())
                self._last_heartbeat = current_time

                with self._cache_lock:
                    self._request_cache[cache_key] = result
                    threading.Timer(25.0, lambda: self._clear_cache(cache_key)).start()
                return result
            elif response.status_code == 404:
                raise InvalidTokenException("Invalid token or not occupied")
            else:
                raise NetworkException(f"Server error: {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise NetworkException(f"Network error: {str(e)}")

    def _logout_sync(self, code: str) -> LogoutResponse:
        url = f"{self.config.base_url}/api/tokens/logout/"
        data = {"code": code}

        try:
            session = self.connection_pool.get_session()
            response = session.post(url, json=data)

            if response.status_code == 200:
                return LogoutResponse.from_dict(response.json())
            elif response.status_code == 404:
                raise InvalidTokenException("Invalid token")
            else:
                raise NetworkException(f"Server error: {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise NetworkException(f"Network error: {str(e)}")

    def _clear_cache(self, key: str):
        with self._cache_lock:
            self._request_cache.pop(key, None)

    def close(self):
        self.executor.shutdown(wait=True)
        self.connection_pool.cleanup_all()
