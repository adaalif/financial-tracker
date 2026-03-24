import time
import logging
import asyncio
import structlog
from functools import wraps
from typing import Callable

def setup_logging() -> None:
    """Configures structured JSON logging project-wide."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars, # Support for contextvars like request_id
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False
    )

def get_logger(name: str):
    """Retrieves a bound logger by module name."""
    return structlog.get_logger(name)

# Module-level default logger
logger = get_logger(__name__)

def track_performance(func: Callable) -> Callable:
    """Decorator to measure and log the execution time of a function."""
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Started {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Finished {func.__name__}", duration_s=round(duration, 3))
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed {func.__name__}", error=str(e), duration_s=round(duration, 3))
            raise
            
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Started {func.__name__}")
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Finished {func.__name__}", duration_s=round(duration, 3))
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed {func.__name__}", error=str(e), duration_s=round(duration, 3))
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

def log_token_usage(request_id: str, usage_metadata: dict) -> None:
    """Helper to structure and log LLM token usage."""
    if not usage_metadata:
        logger.warning("No token usage metadata provided", request_id=request_id)
        return
        
    logger.info(
        "Token Usage",
        request_id=request_id,
        input_tokens=usage_metadata.get("input_tokens", 0),
        output_tokens=usage_metadata.get("output_tokens", 0),
        total_tokens=usage_metadata.get("total_tokens", 0)
    )
