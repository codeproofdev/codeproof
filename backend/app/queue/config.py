"""
Redis Queue configuration
"""

from redis import Redis
from rq import Queue
from enum import IntEnum
import logging

from app.config import settings

logger = logging.getLogger(__name__)


# Redis connection (shared across application)
def get_redis_connection():
    """
    Get Redis connection for RQ

    Uses REDIS_URL from settings (format: redis://host:port/db)

    Returns:
        Redis connection instance
    """
    try:
        # Create connection from URL
        redis_conn = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,  # RQ needs bytes
            health_check_interval=30  # Ping every 30s to keep connection alive
        )

        # Test connection
        redis_conn.ping()
        logger.info(f"✅ Redis connected: {settings.REDIS_URL}")

        return redis_conn

    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise


# Global Redis connection
redis_conn = get_redis_connection()


# Priority levels for submissions
class SubmissionPriority(IntEnum):
    """
    Priority levels for submission judging

    Higher value = higher priority
    """
    CONTEST = 3        # Future: contest submissions (highest priority)
    REJUDGE = 2        # Re-judging after problem update
    DEFAULT = 1        # Normal user submissions
    BATCH_REJUDGE = 0  # Bulk rejudge (lowest priority)


# Queue instances
default_queue = Queue('default', connection=redis_conn, default_timeout=300)
high_queue = Queue('high', connection=redis_conn, default_timeout=300)
low_queue = Queue('low', connection=redis_conn, default_timeout=600)


def get_queue(priority: SubmissionPriority = SubmissionPriority.DEFAULT) -> Queue:
    """
    Get appropriate queue based on priority

    Args:
        priority: Submission priority level

    Returns:
        RQ Queue instance
    """
    if priority >= SubmissionPriority.REJUDGE:
        return high_queue
    elif priority == SubmissionPriority.DEFAULT:
        return default_queue
    else:
        return low_queue


def get_queue_stats() -> dict:
    """
    Get statistics about all queues

    Returns:
        Dictionary with queue stats
    """
    stats = {
        'high': {
            'name': 'high',
            'count': len(high_queue),
            'jobs': high_queue.job_ids
        },
        'default': {
            'name': 'default',
            'count': len(default_queue),
            'jobs': default_queue.job_ids
        },
        'low': {
            'name': 'low',
            'count': len(low_queue),
            'jobs': low_queue.job_ids
        }
    }

    total_jobs = stats['high']['count'] + stats['default']['count'] + stats['low']['count']
    stats['total'] = total_jobs

    return stats


# Test connection on import
if __name__ == "__main__":
    print("Testing Redis connection...")
    try:
        redis_conn.ping()
        print("✅ Redis connection successful")

        # Test queue
        test_queue = get_queue(SubmissionPriority.DEFAULT)
        print(f"✅ Queue created: {test_queue.name}")

        # Get stats
        stats = get_queue_stats()
        print(f"✅ Queue stats: {stats}")

    except Exception as e:
        print(f"❌ Error: {e}")
