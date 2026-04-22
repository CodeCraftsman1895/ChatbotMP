import logging
import time
from functools import wraps

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def time_it(func_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            logging.info(f"OBSERVABILITY: {func_name} took {end - start:.4f} seconds")
            return result
        return wrapper
    return decorator
