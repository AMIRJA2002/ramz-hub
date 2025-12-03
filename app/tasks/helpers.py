"""Helper functions for Celery tasks"""
import asyncio
import traceback


def run_async(coro):
    """Run async function in Celery task"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        print(f"Error in run_async: {str(e)}")
        traceback.print_exc()
        raise

