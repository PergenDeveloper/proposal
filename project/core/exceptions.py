from enum import Enum
from typing import Sequence


class PermissionDenied(Exception):
    def __init__(self, message=None):
        if not message:
            message = "You do not have permission to perform this action"
        super().__init__(message)