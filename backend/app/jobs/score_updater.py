"""
Score Recalculation Scheduler for CodeProof

Recalculates user scores every 5 minutes ONLY if there were AC submissions.
This implements the retroactive scoring system where problem values decay.
"""

from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import Submission, User, Verdict
from app.utils.scoring import calculate_user_score
import logging

logger = logging.getLogger(__name__)


def recalculate_scores_if_needed():
    """
    Smart background job: Recalculate user scores ONLY if there were AC submissions
    in the last 5 minutes.

    This runs periodically (every 5 minutes) but skips work if no changes happened.

    Strategy:
    1. Check if any AC submissions in last 5 minutes
    2. If yes, recalculate scores for affected users
    3. If no, skip (no work needed)
    """
    db = SessionLocal()

    try:
        # Check if there were any AC submissions in last 5 minutes
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)

        recent_ac_count = db.query(Submission).filter(
            Submission.verdict == Verdict.AC,
            Submission.judged_at >= five_minutes_ago
        ).count()

        if recent_ac_count == 0:
            logger.debug("No AC submissions in last 5 minutes, skipping score recalculation")
            return

        logger.info(f"Found {recent_ac_count} AC submissions in last 5 minutes")
        logger.info("Recalculating user scores...")

        # Get all users with stale cache (score_updated_at is None or > 5 min old)
        stale_users = db.query(User).filter(
            (User.score_updated_at == None) |
            (User.score_updated_at < five_minutes_ago)
        ).all()

        updated_count = 0

        for user in stale_users:
            # Recalculate dynamic score
            new_score = calculate_user_score(user.id, db)

            # Update cache
            user.total_score_cached = new_score
            user.score_updated_at = datetime.utcnow()

            # Also update legacy total_score field for compatibility
            user.total_score = new_score

            updated_count += 1

        db.commit()

        logger.info(f"Updated scores for {updated_count} users")

    except Exception as e:
        logger.exception(f"Error recalculating scores: {e}")
        db.rollback()

    finally:
        db.close()


def start_score_update_scheduler():
    """
    Start the score recalculation scheduler

    Uses APScheduler to run recalculate_scores_if_needed() every 5 minutes.

    In production:
    - Run as separate process/container
    - Monitor performance (recalculation time)
    - Consider using Redis for coordination
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = BackgroundScheduler()

    # Schedule score recalculation every 5 minutes
    scheduler.add_job(
        func=recalculate_scores_if_needed,
        trigger=IntervalTrigger(minutes=5),
        id='score_updater',
        name='Recalculate user scores every 5 minutes (if needed)',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Score recalculation scheduler started (runs every 5 minutes)")

    return scheduler


# Manual recalculation for testing
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    logger.info("Manual score recalculation...")
    recalculate_scores_if_needed()
    logger.info("Done!")
