
class DrifterException(Exception):
    pass


class GenericException(DrifterException):
    pass


class InvalidArgumentException(DrifterException):
    pass


class ProviderException(DrifterException):
    pass
