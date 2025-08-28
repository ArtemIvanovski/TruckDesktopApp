from core.exceptions import ApplicationError, ErrorCategory, ErrorSeverity


class AuthException(ApplicationError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTH,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class NetworkException(AuthException):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            user_message="Network connection error. Please check your internet connection.",
            **kwargs
        )


class InvalidTokenException(AuthException):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            user_message="Authentication failed. Please check your access code.",
            **kwargs
        )


class TokenExpiredException(AuthException):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            user_message="Session expired. Please re-enter your access code.",
            **kwargs
        )


class TokenOccupiedException(AuthException):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            user_message="This access code is already in use on another device.",
            **kwargs
        )


class HeartbeatFailedException(AuthException):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            user_message="Connection to server lost. Working in offline mode.",
            recoverable=True,
            **kwargs
        )


class DeviceInfoException(AuthException):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.LOW,
            user_message="Device information could not be retrieved.",
            **kwargs
        )


class ConfigurationException(AuthException):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            user_message="Configuration error. Please check application settings.",
            **kwargs
        )
