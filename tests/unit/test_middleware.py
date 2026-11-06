"""Tests for observability middleware components."""


class TestCorrelationIdMiddleware:
    """Tests for CorrelationIdMiddleware class."""

    def test_middleware_class_exists(self) -> None:
        from app.middleware.correlation import CorrelationIdMiddleware

        assert CorrelationIdMiddleware is not None

    def test_middleware_is_asgi_middleware(self) -> None:
        from app.middleware.correlation import CorrelationIdMiddleware

        assert callable(CorrelationIdMiddleware)
        assert hasattr(CorrelationIdMiddleware, "__init__")


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware class."""

    def test_middleware_class_exists(self) -> None:
        from app.middleware.logging import RequestLoggingMiddleware

        assert RequestLoggingMiddleware is not None

    def test_middleware_is_asgi_middleware(self) -> None:
        from app.middleware.logging import RequestLoggingMiddleware

        assert callable(RequestLoggingMiddleware)
        assert hasattr(RequestLoggingMiddleware, "__init__")


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware class."""

    def test_middleware_class_exists(self) -> None:
        from app.middleware.security import SecurityHeadersMiddleware

        assert SecurityHeadersMiddleware is not None

    def test_middleware_is_asgi_middleware(self) -> None:
        from app.middleware.security import SecurityHeadersMiddleware

        assert callable(SecurityHeadersMiddleware)
        assert hasattr(SecurityHeadersMiddleware, "__init__")
