"""Collection of exceptions."""


class DrifterException(Exception):
    """Base exception all others should extend."""

    pass


class GenericException(DrifterException):
    """Generic exception message."""

    pass


class InvalidArgumentException(DrifterException):
    """Exception to represent an invalid argument."""

    pass


class ProviderException(DrifterException):
    """Exception to represent an error in a provider."""

    pass
