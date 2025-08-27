from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class AuthResponse:
    success: bool
    session_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthResponse':
        return cls(
            success=data.get('success', False),
            session_id=data.get('session_id'),
            message=data.get('message'),
            error=data.get('error')
        )


@dataclass
class HeartbeatResponse:
    success: bool
    error: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HeartbeatResponse':
        return cls(
            success=data.get('success', False),
            error=data.get('error')
        )


@dataclass
class LogoutResponse:
    success: bool
    error: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogoutResponse':
        return cls(
            success=data.get('success', False),
            error=data.get('error')
        )
