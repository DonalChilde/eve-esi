from typing import TYPE_CHECKING, Optional

from eve_esi_jobs.aiohttp_queue import AiohttpRequest, RaiseForStatus

if TYPE_CHECKING:
    from eve_esi_jobs.callbacks import EsiJobCallback


class BadRequestParameter(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class MissingParameter(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class BadOpId(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class CallbackError(Exception):
    def __init__(
        self, msg: Optional[str], exception: Exception, callback: "EsiJobCallback"
    ) -> None:
        if msg is None:
            message = (
                f"Got an exception during {callback.__class__.__name__}: {exception}"
            )
        else:
            message = msg
        super().__init__(message)
        self.original_exception = exception
        self.callback = callback


class DeserializationError(Exception):
    def __init__(self, msg: Optional[str], exception: Exception) -> None:
        if msg is None:
            message = f"Got an exception during deserialization: {exception}"
        else:
            message = msg
        super().__init__(message)
        self.original_exception = exception


class SerializationError(Exception):
    def __init__(self, msg: Optional[str], exception: Exception) -> None:
        if msg is None:
            message = f"Got an exception during serialization: {exception}"
        else:
            message = msg
        super().__init__(message)
        self.original_exception = exception


class ValidationError(Exception):
    def __init__(self, msg: Optional[str], exception: Exception, obj) -> None:
        """Error raised during job validation."""
        if msg is None:
            message = f"Got an exception during validation: {exception}"
        else:
            message = msg
        super().__init__(message)
        self.original_exception = exception
        self.obj = obj


class EsiSourceException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class EsiLocalSourceException(EsiSourceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class RetrievalError(EsiLocalSourceException):
    def __init__(self, msg, exception: Exception) -> None:
        super().__init__(f"{msg}: {exception}")
        self.original_exception = exception


class EsiRemoteSourceException(EsiSourceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class BadStatusException(EsiRemoteSourceException):
    def __init__(self, msg, exception: RaiseForStatus) -> None:
        if msg is None:
            message = f"Request failed with bad status. {exception.status_exception!r} {exception.request!r}"
        else:
            message = msg
        super().__init__(message)
        self.status_exception = exception


class FailedRetryException(EsiRemoteSourceException):
    def __init__(self, msg, exception: RaiseForStatus) -> None:
        if msg is None:
            message = f"Request exceeded max attempts. {exception.status_exception!r} {exception.request!r}"
        else:
            message = msg
        super().__init__(message)
        self.status_exception = exception


class BadDataException(EsiRemoteSourceException):
    def __init__(self, msg, request: AiohttpRequest, exception: Exception) -> None:
        if msg is None:
            message = "Fix me"
        else:
            message = msg
        super().__init__(message)
        self.request = request
        self.original_exception = exception


class DataUnchangedException(EsiRemoteSourceException):
    def __init__(self, msg, exception: RaiseForStatus) -> None:
        if msg is None:
            message = f"Data unchanged for {exception.request!r}"
        else:
            message = msg
        super().__init__(message)
        self.status_exception = exception
