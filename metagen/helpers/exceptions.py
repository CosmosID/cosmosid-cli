
class MetagenException(Exception):
    """Default MetagenException. Base class for another Exceptions."""

    def __init__(self, *args, **kwargs):
        """You may pass dict to Exception so error handler can render representation error description."""
        self.exception_data = kwargs

    @staticmethod
    def generic_exception(dict_, status_code):
        """
        Build an exception from incoming dict.

        :dict_ - dict which contains name and message of exception
        :status_code - status code
        """
        exception = MetagenException()
        exception.name = dict_.get('error_code', '')
        exception.message = dict_.get('message', '')
        exception.status_code = status_code
        exception.additional_data = dict_
        return exception


class MethodNotSupported(MetagenException):
    pass


class PermissionDenied(MetagenException):
    pass


class AuthenticationFailed(MetagenException):
    name = "NoAuth"
    status_code = 403
    message = "Authentication Failed. Wrong API Key."


class ServerError(MetagenException):
    pass


class ValidationError(ValueError):
    pass


class ValidationWarning(Warning):
    pass


class UploadException(Exception):
    pass


class ConnectionException(MetagenException):
    pass


class NotFound(MetagenException):
    name = "NoAuth"
    status_code = 404
    message = "Object with given ID not found."


class NotFoundException(MetagenException):
    pass


class FileExistsException(MetagenException):
    pass