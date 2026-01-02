"""
RQ Worker for judging submissions

This script starts an RQ worker that listens to queues
and executes judging jobs in the background.
"""

from rq import Worker, Queue, Connection
from redis import Redis
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_worker():
    """
    Start RQ worker to process judge jobs

    The worker listens to multiple queues in priority order:
    1. high   - High priority jobs (rejudge, contests)
    2. default - Normal user submissions
    3. low    - Low priority jobs (bulk rejudge)
    """

    try:
        # Import queue config
        from app.queue.config import redis_conn, high_queue, default_queue, low_queue

        # Create worker
        worker = Worker(
            [high_queue, default_queue, low_queue],  # Priority order
            connection=redis_conn,
            name=f"judge-worker-{os.getpid()}"
        )

        logger.info("=" * 60)
        logger.info("🔨 CodeProof Judge Worker Starting")
        logger.info("=" * 60)
        logger.info(f"Worker name: {worker.name}")
        logger.info(f"Listening to queues: high, default, low")
        logger.info(f"Process ID: {os.getpid()}")
        logger.info("=" * 60)

        # Start working
        worker.work(
            with_scheduler=False,
            logging_level='INFO'
        )

    except KeyboardInterrupt:
        logger.info("👋 Worker stopped by user")
        sys.exit(0)

    except Exception as e:
        logger.exception(f"❌ Worker crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    """
    Run worker from command line:
    python -m app.queue.worker
    """
    run_worker()
