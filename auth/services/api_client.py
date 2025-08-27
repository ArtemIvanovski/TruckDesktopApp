import requests
import json
from typing import Dict, Any, Optional
from ..config.settings import AuthConfig
from ..models.device_info import DeviceInfo
from ..models.auth_response import AuthResponse, HeartbeatResponse, LogoutResponse
from ..exceptions.auth_exceptions import (
    NetworkException, InvalidTokenException, 
    TokenExpiredException, TokenOccupiedException
)


class ApiClient:
    def __init__(self, config: AuthConfig):
        self.config = config
        self.session = requests.Session()
        self.session.timeout = config.connection_timeout
        if not config.verify_ssl:
            self.session.verify = False
    
    def verify_token(self, code: str, device_info: DeviceInfo) -> AuthResponse:
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
    
    def send_heartbeat(self, code: str) -> HeartbeatResponse:
        url = f"{self.config.base_url}/api/tokens/heartbeat/"
        data = {"code": code}
        
        try:
            response = self.session.post(url, json=data)
            
            if response.status_code == 200:
                return HeartbeatResponse.from_dict(response.json())
            elif response.status_code == 404:
                raise InvalidTokenException("Invalid token or not occupied")
            else:
                raise NetworkException(f"Server error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise NetworkException(f"Network error: {str(e)}")
    
    def logout(self, code: str) -> LogoutResponse:
        url = f"{self.config.base_url}/api/tokens/logout/"
        data = {"code": code}
        
        try:
            response = self.session.post(url, json=data)
            
            if response.status_code == 200:
                return LogoutResponse.from_dict(response.json())
            elif response.status_code == 404:
                raise InvalidTokenException("Invalid token")
            else:
                raise NetworkException(f"Server error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise NetworkException(f"Network error: {str(e)}")
    
    def close(self):
        self.session.close()
