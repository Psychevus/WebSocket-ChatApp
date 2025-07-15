# Minimal stub mirroring django_ratelimit decorator API

def ratelimit(*args, **kwargs):
    def decorator(fn):
        def wrapper(*a, **k):
            return fn(*a, **k)
        return wrapper
    return decorator
