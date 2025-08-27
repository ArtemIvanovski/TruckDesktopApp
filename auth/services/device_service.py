from ..models.device_info import DeviceInfo
from ..exceptions.auth_exceptions import DeviceInfoException


class DeviceService:
    _instance = None
    _device_info = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_device_info(self) -> DeviceInfo:
        if self._device_info is None:
            try:
                self._device_info = DeviceInfo.generate()
            except Exception as e:
                raise DeviceInfoException(f"Failed to generate device info: {str(e)}")
        return self._device_info
    
    def refresh_device_info(self) -> DeviceInfo:
        try:
            self._device_info = DeviceInfo.generate()
            return self._device_info
        except Exception as e:
            raise DeviceInfoException(f"Failed to refresh device info: {str(e)}")
