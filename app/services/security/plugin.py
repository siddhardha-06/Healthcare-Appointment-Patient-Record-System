from app.services.security.middleware import LoginRateLimiter, SecurityHeaders


def setup(app):
    app.add_middleware(LoginRateLimiter)
    app.add_middleware(SecurityHeaders)
