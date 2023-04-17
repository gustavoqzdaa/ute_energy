"""Ute Energy exceptions."""


class UteEnergyError(Exception):
    """Base class for UteEnergy errors."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class ApiError(UteEnergyError):
    """Raised when UTE API request ended in error."""


class InvalidRequestDataError(UteEnergyError):
    """Raised when request data is invalid."""


class UteApiAccessDenied(Exception):
    """Exception raised for wrong credentials.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)


class UteEnergyException(Exception):
    """Exception raised for errors in the ute api.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)
