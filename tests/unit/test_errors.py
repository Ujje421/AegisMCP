from aegismcp.kernel.errors import (
    AegisError,
    ConfigurationError,
    ConnectionError,
    InvalidMessageError,
    ResourceNotFoundError,
    SchemaValidationError,
    SecurityError,
    SerializationError,
    ToolNotFoundError,
    ToolRetryExhaustedError,
    ToolTimeoutError,
    UnsupportedCapabilityError,
    VersionMismatchError,
)


def test_error_formatting():
    err = AegisError("Something went wrong", request_id="req-123")
    assert str(err) == "AegisError: Something went wrong [req_id=req-123]"


def test_error_formatting_no_req_id():
    err = AegisError("Something went wrong")
    assert str(err) == "AegisError: Something went wrong"


def test_is_retryable_flag():
    timeout = ToolTimeoutError("timeout")
    assert timeout.is_retryable is True

    invalid = InvalidMessageError("invalid")
    assert invalid.is_retryable is False


def test_protocol_errors():
    err1 = UnsupportedCapabilityError("unsupported", "req1")
    assert err1.is_retryable is False
    assert err1.request_id == "req1"

    err2 = VersionMismatchError("mismatch")
    assert err2.is_retryable is False


def test_execution_errors():
    err1 = ToolNotFoundError("not found")
    assert err1.is_retryable is False

    err2 = ToolRetryExhaustedError("exhausted")
    assert err2.is_retryable is False

    err3 = ResourceNotFoundError("resource missing")
    assert err3.is_retryable is False


def test_transport_and_config_errors():
    err1 = ConnectionError("disconnected")
    assert err1.is_retryable is True

    err2 = SerializationError("bad json")
    assert err2.is_retryable is False

    err3 = ConfigurationError("bad config")
    assert err3.is_retryable is False


def test_validation_errors():
    err = SchemaValidationError("invalid schema")
    assert err.is_retryable is False


def test_security_errors():
    err = SecurityError("access denied")
    assert err.is_retryable is False
