from datetime import UTC, datetime


class AegisError(Exception):
    """Base exception for all framework errors."""

    def __init__(
        self, message: str, request_id: str | None = None, is_retryable: bool = False
    ) -> None:
        super().__init__(message)
        self.message = message
        self.request_id = request_id
        self.timestamp = datetime.now(UTC)
        self.is_retryable = is_retryable

    def __str__(self) -> str:
        req_part = f" [req_id={self.request_id}]" if self.request_id else ""
        return f"{self.__class__.__name__}: {self.message}{req_part}"


# Protocol Errors
class ProtocolError(AegisError):
    pass


class InvalidMessageError(ProtocolError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)


class UnsupportedCapabilityError(ProtocolError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)


class VersionMismatchError(ProtocolError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)


# Execution Errors
class ExecutionError(AegisError):
    pass


class ToolNotFoundError(ExecutionError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)


class ToolTimeoutError(ExecutionError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=True)


class ToolRetryExhaustedError(ExecutionError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)


class ResourceNotFoundError(ExecutionError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)


# Security Errors
class SecurityError(AegisError):
    """Base for auth/authz failures. Never leaks internals."""

    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)


class AuthenticationError(SecurityError):
    pass


class AuthorizationError(SecurityError):
    pass


class PolicyViolationError(SecurityError):
    pass


# Validation Errors
class ValidationError(AegisError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)


class SchemaValidationError(ValidationError):
    pass


# Transport Errors
class TransportError(AegisError):
    pass


class ConnectionError(TransportError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=True)


class SerializationError(TransportError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)


# Configuration Errors
class ConfigurationError(AegisError):
    def __init__(self, message: str, request_id: str | None = None) -> None:
        super().__init__(message, request_id, is_retryable=False)
