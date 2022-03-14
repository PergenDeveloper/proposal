from enum import Enum


class UserErrorCodes(Enum):
    ALREADY_EXISTS = "already_exists"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    INACTIVE = "inactive"
    UNIQUE = "unique"
    INVALID_CREDENTIALS = "invalid_credencials"
    JWT_SIGNATURE_EXPIRED = "signature_expired"
    JWT_DECODE_ERROR = "decode_error"
    JWT_INVALID_TOKEN = "invalid_token"