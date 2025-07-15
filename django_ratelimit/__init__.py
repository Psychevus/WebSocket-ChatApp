# Minimal stub for ratelimit decorator used in tests
# Provides a pass-through decorator to avoid external dependency

def ratelimit(*args, **kwargs):
    def decorator(fn):
        def wrapper(*a, **k):
            return fn(*a, **k)
        return wrapper
    return decorator
