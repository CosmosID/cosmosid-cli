"""Exceptions."""


class CosmosidException(Exception):
    """Default CosmosidException. Base class for another Exceptions."""

    def __init__(self, *args, **kwargs):
        """
        You may pass dict to Exception so error handler can render
        representation error description.
        """
        self.exception_data = kwargs

    @staticmethod
    def generic_exception(dict_, status_code):
        """
        Build an exception from incoming dict.

        :dict_ - dict which contains name and message of exception
        :status_code - status code
        """
        exception = CosmosidException()
        exception.name = dict_.get('error_code', '')
        exception.message = dict_.get('message', '')
        exception.status_code = status_code
        exception.additional_data = dict_
        return exception


class MethodNotSupported(CosmosidException):
    pass


class PermissionDenied(CosmosidException):
    pass


class StatusException(CosmosidException):
    name = "NoStatus"
    status_code = 406
    message = "Wrong status of dataset."


class AuthenticationFailed(CosmosidException):
    name = "NoAuth"
    status_code = 403
    message = "Authentication Failed. Wrong API Key."


class NotEnoughCredits(CosmosidException):
    name = "NoCredits"
    status_code = 402
    message = "Insufficient credits for upload."


class ServerError(CosmosidException):
    pass


class ValidationError(ValueError):
    pass


class ValidationWarning(Warning):
    pass


class UploadException(Exception):
    pass


class ConnectionException(CosmosidException):
    pass


class NotFound(CosmosidException):
    name = "NoAuth"
    status_code = 404
    message = "Object with given ID not found."


class NotFoundException(CosmosidException):
    pass


class FileExistsException(CosmosidException):
    pass
