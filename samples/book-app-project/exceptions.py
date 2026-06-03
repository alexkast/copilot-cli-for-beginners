class BookAppError(Exception):
    """Base exception for all book app domain errors."""


class ValidationError(BookAppError):
    """Raised when user input fails validation (empty fields, bad year, out-of-range choice)."""


class BookNotFoundError(BookAppError):
    """Raised when a requested book does not exist in the collection."""


class StorageError(BookAppError):
    """Raised when the data file cannot be read or written."""
