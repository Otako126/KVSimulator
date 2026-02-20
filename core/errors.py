class SimError(Exception):
    code = "INTERNAL_ERROR"

    def __init__(self, message: str, detail=None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class UnknownDeviceError(SimError):
    code = "UNKNOWN_DEVICE"


class OutOfRangeError(SimError):
    code = "OUT_OF_RANGE"


class TypeMismatchError(SimError):
    code = "TYPE_MISMATCH"


class ReadOnlyError(SimError):
    code = "READONLY"


class LockTimeoutError(SimError):
    code = "LOCK_TIMEOUT"


class InvalidRequestError(SimError):
    code = "INVALID_REQUEST"


class TooManyPointsError(SimError):
    code = "TOO_MANY_POINTS"
