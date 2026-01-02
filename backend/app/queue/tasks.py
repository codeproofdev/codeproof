"""
Background tasks for judging submissions
Executed by RQ workers
"""

from app.database import SessionLocal
from app.models import Submission, Problem, TestCase, User, Verdict, UserProblemSolve
from app.judge.isolate_executor import IsolateExecutor, Verdict as ExecutorVerdict
from app.judge.language_config import Language
from app.utils.scoring import calculate_dynamic_points
from app.config import settings
from sqlalchemy import select
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def judge_submission(submission_id: int):
    """
    Judge a submission (called by RQ worker)

    This is the main judging function that:
    1. Loads submission from database
    2. Executes code against test cases
    3. Determines verdict
    4. Calculates points (dynamic scoring)
    5. Updates database (submission, problem, user stats)

    Args:
        submission_id: ID of submission to judge
    """

    db = SessionLocal()

    try:
        logger.info(f"⚖️  Judging submission {submission_id}")

        # 1. Load submission
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"Submission {submission_id} not found")
            return

        # Prevent double judging
        if submission.verdict != Verdict.PENDING:
            logger.warning(f"Submission {submission_id} already judged: {submission.verdict.value}")
            return

        # 2. Load problem and test cases
        problem = db.query(Problem).filter(Problem.id == submission.problem_id).first()
        if not problem:
            logger.error(f"Problem {submission.problem_id} not found")
            submission.verdict = Verdict.IE  # Internal Error
            db.commit()
            return

        # Load test cases ordered by case_number
        test_cases = db.query(TestCase).filter(
            TestCase.problem_id == problem.id
        ).order_by(TestCase.case_number).all()

        if not test_cases:
            logger.error(f"Problem {problem.id} has no test cases")
            submission.verdict = Verdict.IE
            db.commit()
            return

        logger.info(f"Problem: {problem.title_en} ({len(test_cases)} test cases)")

        # 3. Create secure executor with isolate sandbox
        # Use submission_id as box_id to allow parallel judging
        executor = IsolateExecutor(
            time_limit=problem.time_limit,
            memory_limit=problem.memory_limit,
            box_id=submission_id % 100,  # Use 100 boxes (0-99) in rotation
            language=Language(submission.language)  # IMPORTANT: Use submission's language!
        )

        # 4. Run test cases
        test_results = []
        max_time = 0
        max_memory = 0
        all_passed = True
        final_verdict = None

        for test_case in test_cases:
            logger.debug(f"Running test case {test_case.case_number}/{len(test_cases)}")

            # Load test input and expected output
            if problem.file_based:
                # For file-based problems, read from filesystem
                problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path
                input_path = problem_dir / test_case.input_file
                output_path = problem_dir / test_case.output_file

                try:
                    test_input = input_path.read_text(encoding='utf-8')
                    expected_output = output_path.read_text(encoding='utf-8')
                except Exception as e:
                    logger.error(f"Failed to read test case files: {e}")
                    submission.verdict = Verdict.IE
                    db.commit()
                    return
            else:
                # For legacy DB-based problems, input_file/output_file contain the content
                test_input = test_case.input_file
                expected_output = test_case.output_file

            # Execute code
            result = executor.execute(
                source_code=submission.source_code,
                test_input=test_input,
                expected_output=expected_output
            )

            # Record result (with extended metrics from IsolateExecutor)
            test_results.append({
                "case_number": test_case.case_number,
                "verdict": result.verdict.value,
                "time_ms": result.time_ms,
                "wall_time_ms": result.wall_time_ms,  # NEW: Wall time tracking
                "memory_kb": result.memory_kb,
                "exitcode": result.exitcode,  # NEW: Exit code
                "points": test_case.points if result.verdict == ExecutorVerdict.AC else 0.0
            })

            # Track max time and memory
            max_time = max(max_time, result.time_ms)
            max_memory = max(max_memory, result.memory_kb)

            # Stop on first failure (can be configured per problem)
            if result.verdict != ExecutorVerdict.AC:
                all_passed = False
                final_verdict = result.verdict.value

                # Log detailed failure reason
                if result.verdict == ExecutorVerdict.TLE:
                    logger.info(f"Test case {test_case.case_number} failed: TLE ({result.time_ms}ms > {problem.time_limit * 1000}ms)")
                elif result.verdict == ExecutorVerdict.MLE:
                    logger.info(f"Test case {test_case.case_number} failed: MLE ({result.memory_kb}KB > {problem.memory_limit * 1024}KB)")
                elif result.verdict == ExecutorVerdict.OLE:
                    logger.info(f"Test case {test_case.case_number} failed: OLE (output too large)")
                elif result.verdict == ExecutorVerdict.RE:
                    logger.info(f"Test case {test_case.case_number} failed: RE (exitcode={result.exitcode})")
                elif result.verdict == ExecutorVerdict.WA:
                    logger.info(f"Test case {test_case.case_number} failed: WA (wrong answer)")
                else:
                    logger.info(f"Test case {test_case.case_number} failed: {result.verdict.value}")

                break  # Stop testing

        # 5. Determine final verdict
        if all_passed:
            final_verdict = "AC"
            logger.info(f"All {len(test_cases)} test cases passed!")

        # 6. Calculate points (only for AC) - RETROACTIVE SYSTEM
        points_earned = 0.0

        if final_verdict == "AC":
            # Check if this is the user's first AC for this problem
            previous_solve = db.query(UserProblemSolve).filter(
                UserProblemSolve.user_id == submission.user_id,
                UserProblemSolve.problem_id == problem.id
            ).first()

            if not previous_solve:
                # First AC for this user on this problem

                # 1. Increment solved_count FIRST (before recalculating points)
                problem.solved_count += 1

                # 2. Recalculate current_points of the problem (DECAY)
                problem.current_points = calculate_dynamic_points(
                    problem.solved_count,
                    base_points=problem.initial_points
                )

                logger.info(f"First AC for user {submission.user_id} on problem {problem.id}")
                logger.info(f"Problem solved_count: {problem.solved_count}")
                logger.info(f"Problem new value: {problem.current_points:.2f} points (decayed)")

                # 3. Record solve in UserProblemSolve table
                new_solve = UserProblemSolve(
                    user_id=submission.user_id,
                    problem_id=problem.id,
                    first_submission_id=submission.id,
                    solved_at=datetime.utcnow(),
                    solve_position=problem.solved_count  # Their position
                )
                db.add(new_solve)

                # 4. Update user stats
                user = db.query(User).filter(User.id == submission.user_id).first()
                if user:
                    user.problems_solved += 1

                    # 5. Invalidate score cache (will be recalculated later)
                    user.score_updated_at = None

                    logger.info(f"User {user.username} problems_solved: {user.problems_solved}")
                    logger.info(f"User score cache invalidated (will recalc)")

                # For display purposes, show current problem value
                points_earned = problem.current_points

            else:
                logger.info(f"User already solved this problem (solve #{previous_solve.id})")

        # 7. Update submission
        submission.verdict = getattr(Verdict, final_verdict)
        submission.execution_time = max_time
        submission.memory_used = max_memory
        submission.points_earned = points_earned
        submission.test_results = {"cases": test_results}
        submission.judged_at = datetime.utcnow()

        db.commit()

        logger.info(f"✅ Submission {submission_id}: {final_verdict} ({points_earned:.2f} pts, {max_time}ms)")

    except Exception as e:
        logger.exception(f"❌ Error judging submission {submission_id}: {e}")

        # Mark as Internal Error
        try:
            submission.verdict = Verdict.IE
            submission.test_results = {"error": str(e)}
            submission.judged_at = datetime.utcnow()
            db.commit()
        except:
            pass

    finally:
        db.close()


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
    from datetime import timedelta
    from app.utils.scoring import calculate_user_score

    db = SessionLocal()

    try:
        # Check if there were any AC submissions in last 5 minutes
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)

        recent_ac_count = db.query(Submission).filter(
            Submission.verdict == Verdict.AC,
            Submission.judged_at >= five_minutes_ago
        ).count()

        if recent_ac_count == 0:
            logger.info("No AC submissions in last 5 minutes, skipping score recalculation")
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


# For testing locally
if __name__ == "__main__":
    """
    Test judging a submission locally
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.queue.tasks <submission_id>")
        sys.exit(1)

    submission_id = int(sys.argv[1])
    print(f"Testing judge_submission({submission_id})")
    print("=" * 60)

    judge_submission(submission_id)

    print("=" * 60)
    print("Done!")
