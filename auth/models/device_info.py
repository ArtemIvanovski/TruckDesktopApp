import platform
import socket
import uuid
import hashlib
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DeviceInfo:
    device_id: str
    device_name: str
    os_info: str
    hardware_info: str
    ip_address: str
    
    @classmethod
    def generate(cls) -> 'DeviceInfo':
        hostname = socket.gethostname()
        
        system_info = {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
        
        unique_string = f"{hostname}-{system_info['machine']}-{system_info['processor']}"
        device_id = hashlib.sha256(unique_string.encode()).hexdigest()[:32]
        
        os_info = f"{system_info['system']} {system_info['release']}"
        
        try:
            ip_address = socket.gethostbyname(hostname)
        except socket.gaierror:
            ip_address = "127.0.0.1"
        
        return cls(
            device_id=device_id,
            device_name=hostname,
            os_info=os_info,
            hardware_info=str(system_info),
            ip_address=ip_address
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'os_info': self.os_info,
            'hardware_info': self.hardware_info
        }
