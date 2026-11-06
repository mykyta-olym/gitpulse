"""ASGI middleware, one module each, in the order main.py stacks them:
security headers, rate limit, correlation id, locale, request logging,
performance timing and the error boundary (with the error pages it renders).
Metrics, tracing and structured logging stay in `app.observability`."""
