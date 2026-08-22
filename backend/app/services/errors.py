class RegistryConflictError(Exception):
    """Raised when a registry uniqueness constraint is violated."""


class RegistryValidationError(Exception):
    """Raised when a registry relationship or lifecycle rule is invalid."""
