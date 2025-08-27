import requests
import threading
from typing import Dict, Optional
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from ..config.settings import AuthConfig


class ConnectionPool:
    _instance: Optional['ConnectionPool'] = None
    _lock = threading.Lock()

    def __new__(cls, config: AuthConfig):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: AuthConfig):
        if self._initialized:
            return

        self.config = config
        self.sessions: Dict[threading.Thread, requests.Session] = {}
        self.lock = threading.Lock()
        self._initialized = True

    def get_session(self) -> requests.Session:
        current_thread = threading.current_thread()

        with self.lock:
            if current_thread not in self.sessions:
                session = self._create_optimized_session()
                self.sessions[current_thread] = session

            return self.sessions[current_thread]

    def _create_optimized_session(self) -> requests.Session:
        session = requests.Session()

        retry_strategy = Retry(
            total=self.config.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            backoff_factor=1
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
            pool_block=False
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.timeout = self.config.connection_timeout
        session.verify = self.config.verify_ssl

        session.headers.update({
            'User-Agent': 'TruckDesktopApp/1.0',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

        return session

    def cleanup_thread(self, thread: threading.Thread):
        with self.lock:
            if thread in self.sessions:
                self.sessions[thread].close()
                del self.sessions[thread]

    def cleanup_all(self):
        with self.lock:
            for session in self.sessions.values():
                try:
                    session.close()
                except Exception:
                    pass
            self.sessions.clear()
