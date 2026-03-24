import pytest
import asyncio
from utils.logger import setup_logging, get_logger, track_performance

def test_setup_logging_no_crashes():
    """Ensure structlog configuration initializes correctly without errors."""
    setup_logging()
    logger = get_logger("test_logger")
    assert logger is not None

def test_track_performance_sync():
    """Ensure the performance tracking decorator works on standard sync functions."""
    @track_performance
    def sync_dummy():
        return "sync_ok"
        
    result = sync_dummy()
    assert result == "sync_ok"

@pytest.mark.asyncio
async def test_track_performance_async():
    """Ensure the performance tracking decorator correctly wraps asynchronous coroutines."""
    @track_performance
    async def async_dummy():
        await asyncio.sleep(0.01)
        return "async_ok"
        
    result = await async_dummy()
    assert result == "async_ok"

def test_track_performance_sync_exception():
    """Ensure exceptions are re-raised correctly in tracked sync functions."""
    @track_performance
    def failing_sync():
        raise ValueError("Boom")
        
    with pytest.raises(ValueError, match="Boom"):
        failing_sync()
