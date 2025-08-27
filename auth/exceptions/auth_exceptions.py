class AuthException(Exception):
    pass


class NetworkException(AuthException):
    pass


class InvalidTokenException(AuthException):
    pass


class TokenExpiredException(AuthException):
    pass


class TokenOccupiedException(AuthException):
    pass


class HeartbeatFailedException(AuthException):
    pass


class DeviceInfoException(AuthException):
    pass


class ConfigurationException(AuthException):
    pass
