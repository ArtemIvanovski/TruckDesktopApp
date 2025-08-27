from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthConfig:
    enabled: bool = True
    base_url: str = "http://localhost:8000"
    heartbeat_interval: int = 15
    connection_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    verify_ssl: bool = True
    
    @classmethod
    def from_settings(cls, settings_manager) -> 'AuthConfig':
        auth_settings = settings_manager.get_section('auth')
        return cls(
            enabled=auth_settings.get('enabled', cls.enabled),
            base_url=auth_settings.get('base_url', cls.base_url),
            heartbeat_interval=auth_settings.get('heartbeat_interval', cls.heartbeat_interval),
            connection_timeout=auth_settings.get('connection_timeout', cls.connection_timeout),
            max_retries=auth_settings.get('max_retries', cls.max_retries),
            retry_delay=auth_settings.get('retry_delay', cls.retry_delay),
            verify_ssl=auth_settings.get('verify_ssl', cls.verify_ssl)
        )
    
    def save_to_settings(self, settings_manager):
        settings_manager.update_section('auth', {
            'enabled': self.enabled,
            'base_url': self.base_url,
            'heartbeat_interval': self.heartbeat_interval,
            'connection_timeout': self.connection_timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'verify_ssl': self.verify_ssl
        })


auth_config = AuthConfig()
