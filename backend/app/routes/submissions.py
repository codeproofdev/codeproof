"""
Submissions routes
Handles code submission and judging results
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Submission, Problem, User, Verdict, ProblemStatus, UserRole
from app.schemas import SubmissionCreate, SubmissionOut, SubmissionDetail
from app.auth import get_current_user
from app.queue.config import get_queue, SubmissionPriority
from app.queue.tasks import judge_submission

import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
async def submit_code(
    submission_data: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit code for judging

    **Requires authentication** (Bearer token)

    **Rate limiting**: 5 submissions per minute per user

    **Request body**:
    - problem_id: Problem to solve
    - language: Programming language (python only for MVP)
    - source_code: Source code (max 50KB)

    **Returns**:
    - Submission with status PENDING
    - Use GET /api/submissions/{id} to poll for results

    **Errors**:
    - 400: Invalid problem, code too large
    - 404: Problem not found
    - 429: Rate limit exceeded
    """

    # 1. Validate problem exists and is approved
    result = await db.execute(
        select(Problem).where(Problem.id == submission_data.problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Allow submissions to:
    # - APPROVED problems: everyone can submit
    # - PENDING/REJECTED problems: only creator/admin can submit (for testing)
    if problem.status != ProblemStatus.APPROVED:
        if current_user.role != UserRole.ADMIN and problem.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Problem is {problem.status.lower()}. Only approved problems can be solved."
            )
        # Creator/admin testing their own problem
        logger.info(f"🧪 {current_user.username} testing {problem.status} problem: {problem.title_en}")

    # 2. Rate limiting: max 5 submissions per minute
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)

    result = await db.execute(
        select(func.count(Submission.id))
        .where(
            and_(
                Submission.user_id == current_user.id,
                Submission.submitted_at > one_minute_ago
            )
        )
    )
    recent_count = result.scalar()

    if recent_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 5 submissions per minute."
        )

    # 3. Validate code size (max 50KB)
    code_size = len(submission_data.source_code.encode('utf-8'))
    if code_size > 50 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code too large ({code_size} bytes). Maximum 50KB allowed."
        )

    # 4. Validate language
    SUPPORTED_LANGUAGES = ['python', 'cpp', 'rust', 'javascript', 'go']
    if submission_data.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{submission_data.language}' not supported. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
        )

    # 5. Create submission
    new_submission = Submission(
        user_id=current_user.id,
        problem_id=submission_data.problem_id,
        language=submission_data.language,
        source_code=submission_data.source_code,
        verdict=Verdict.PENDING,
        points_earned=0.0
    )

    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)

    logger.info(f"📤 User {current_user.username} submitted code for problem {problem.title_en} (submission #{new_submission.id})")

    # 6. Enqueue for judging
    queue = get_queue(SubmissionPriority.DEFAULT)

    job = queue.enqueue(
        judge_submission,
        new_submission.id,
        job_timeout=300  # 5 minutes max
    )

    logger.info(f"✅ Enqueued submission {new_submission.id} as job {job.id}")

    return new_submission


@router.get("/stats", response_model=dict)
async def get_submission_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's submission statistics

    **Requires authentication** (Bearer token)

    **Returns**:
    - total: Total submissions
    - by_verdict: Count per verdict (AC, WA, TLE, etc)
    - acceptance_rate: AC / Total (percentage)
    """

    # Total submissions
    result = await db.execute(
        select(func.count(Submission.id))
        .where(Submission.user_id == current_user.id)
    )
    total = result.scalar()

    # Count by verdict
    result = await db.execute(
        select(Submission.verdict, func.count(Submission.id))
        .where(Submission.user_id == current_user.id)
        .group_by(Submission.verdict)
    )
    by_verdict = {verdict.value: count for verdict, count in result.all()}

    # Acceptance rate
    ac_count = by_verdict.get('AC', 0)
    acceptance_rate = (ac_count / total * 100) if total > 0 else 0

    return {
        "total": total,
        "by_verdict": by_verdict,
        "acceptance_rate": round(acceptance_rate, 2)
    }


@router.get("/problem/{problem_id}/best", response_model=Optional[SubmissionOut])
async def get_best_submission(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's best submission for a problem

    **Requires authentication** (Bearer token)

    **Path parameters**:
    - problem_id: Problem ID

    **Returns**:
    - Best submission (AC with fastest time, or latest attempt)
    - null if no submissions yet

    **Usage**:
    Used by frontend to show if user already solved the problem
    """

    # First try to find AC submission with best time
    result = await db.execute(
        select(Submission)
        .where(
            and_(
                Submission.user_id == current_user.id,
                Submission.problem_id == problem_id,
                Submission.verdict == Verdict.AC
            )
        )
        .order_by(Submission.execution_time.asc())
        .limit(1)
    )
    best_ac = result.scalar_one_or_none()

    if best_ac:
        return best_ac

    # If no AC, return latest submission
    result = await db.execute(
        select(Submission)
        .where(
            and_(
                Submission.user_id == current_user.id,
                Submission.problem_id == problem_id
            )
        )
        .order_by(Submission.submitted_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    return latest


@router.get("/{submission_id}", response_model=SubmissionDetail)
async def get_submission(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get submission details with source code visibility rules

    **Requires authentication** (Bearer token)

    **Path parameters**:
    - submission_id: Submission ID

    **Returns**:
    - Full submission details including:
      - verdict (PENDING, AC, WA, TLE, RE, CE, IE)
      - execution_time (ms)
      - memory_used (KB)
      - points_earned
      - test_results (detailed per-test results)
      - source_code (hidden based on role and problem status)

    **Errors**:
    - 404: Submission not found

    **Source code visibility rules**:
    - Admin: Can view all source code
    - Problemsetter: Can view source code if problem is approved OR if they created the problem
    - User: Can view source code only if problem is approved

    **Usage**:
    - Poll this endpoint every 1-2 seconds until verdict != PENDING
    - Everyone can see submission metadata, but source_code may be hidden
    """

    # Fetch submission with problem status and creator
    result = await db.execute(
        select(Submission, Problem.status, Problem.created_by).join(
            Problem, Submission.problem_id == Problem.id
        ).where(Submission.id == submission_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    submission, problem_status, problem_creator_id = row

    # Determine if user can view source code
    can_view_source = False

    if current_user.role == UserRole.ADMIN:
        # Admin can view all source code
        can_view_source = True
        logger.info(f"👀 Admin {current_user.username} viewing submission #{submission_id} (full access)")

    elif current_user.role == UserRole.PROBLEMSETTER:
        # Problemsetter can view source code if:
        # - Problem is approved (any submission)
        # - Problem is not approved BUT they created the problem
        if problem_status == ProblemStatus.APPROVED:
            can_view_source = True
            logger.info(f"👀 Problemsetter {current_user.username} viewing submission #{submission_id} (approved problem)")
        elif problem_creator_id == current_user.id:
            can_view_source = True
            logger.info(f"👀 Problemsetter {current_user.username} viewing submission #{submission_id} (their problem, testing)")
        else:
            logger.info(f"🔒 Problemsetter {current_user.username} viewing submission #{submission_id} (source hidden - not their problem)")

    else:  # UserRole.USER
        # User can view source code only if problem is approved
        if problem_status == ProblemStatus.APPROVED:
            can_view_source = True
            logger.info(f"👀 User {current_user.username} viewing submission #{submission_id} (approved problem)")
        else:
            logger.info(f"🔒 User {current_user.username} viewing submission #{submission_id} (source hidden - problem not approved)")

    # Hide source code if user doesn't have permission
    if not can_view_source:
        # Create a copy of submission dict and hide source_code
        submission_dict = {
            "id": submission.id,
            "user_id": submission.user_id,
            "problem_id": submission.problem_id,
            "language": submission.language,
            "source_code": "[Source code hidden - problem not approved]",
            "verdict": submission.verdict,
            "execution_time": submission.execution_time,
            "memory_used": submission.memory_used,
            "points_earned": submission.points_earned,
            "test_results": submission.test_results,
            "submitted_at": submission.submitted_at,
            "judged_at": submission.judged_at,
            "block_id": submission.block_id,
            "tx_hash": submission.tx_hash,
            "confirmed_at": submission.confirmed_at
        }
        return submission_dict

    return submission


@router.get("", response_model=List[SubmissionOut])
async def list_submissions(
    problem_id: Optional[int] = Query(None, description="Filter by problem ID"),
    verdict: Optional[str] = Query(None, description="Filter by verdict (AC, WA, etc)"),
    limit: int = Query(50, ge=1, le=100, description="Number of submissions to return"),
    offset: int = Query(0, ge=0, description="Number of submissions to skip"),
    all: bool = Query(False, description="Get all users' submissions (public judge submissions)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's submissions or all submissions (public judge)

    **Requires authentication** (Bearer token)

    **Query parameters**:
    - problem_id: Filter by specific problem (optional)
    - verdict: Filter by verdict (AC, WA, TLE, etc) (optional)
    - limit: Number of results (1-100, default 50)
    - offset: Pagination offset (default 0)
    - all: Get all users' submissions instead of just current user's (default: false)

    **Returns**:
    - List of submissions (without source code)
    - Ordered by submission time (newest first)

    **Note**:
    - By default, users see only their own submissions
    - With all=true, get all users' submissions (public judge view)
    - Use GET /api/submissions/{id} to get full details including source code
    """

    # Debug: log the value of 'all' parameter
    logger.info(f"🔍 list_submissions called: all={all}, type={type(all)}, user={current_user.username}")

    # Build query with User join to get usernames
    # Everyone can see the list of all submissions (public judge)
    if all:
        # Public judge view - get all submissions from all users with usernames
        logger.info("📋 Fetching ALL submissions from all users")
        query = select(Submission, User.username).join(User, Submission.user_id == User.id)
    else:
        # Default - get only current user's submissions with username
        logger.info(f"📋 Fetching only submissions from user: {current_user.username}")
        query = select(Submission, User.username).join(User, Submission.user_id == User.id).where(Submission.user_id == current_user.id)

    # Apply filters
    if problem_id:
        query = query.where(Submission.problem_id == problem_id)

    if verdict:
        try:
            verdict_enum = getattr(Verdict, verdict.upper())
            query = query.where(Submission.verdict == verdict_enum)
        except AttributeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verdict: {verdict}. Valid values: AC, WA, TLE, MLE, RE, CE, IE, PENDING"
            )

    # Order by newest first
    query = query.order_by(Submission.submitted_at.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    rows = result.all()

    # Build response with username included
    submissions = []
    for submission, username in rows:
        submission_dict = {
            "id": submission.id,
            "user_id": submission.user_id,
            "username": username,
            "problem_id": submission.problem_id,
            "language": submission.language,
            "verdict": submission.verdict,
            "execution_time": submission.execution_time,
            "memory_used": submission.memory_used,
            "points_earned": submission.points_earned,
            "test_results": submission.test_results,
            "submitted_at": submission.submitted_at,
            "judged_at": submission.judged_at,
            "block_id": submission.block_id,
            "tx_hash": submission.tx_hash,
            "confirmed_at": submission.confirmed_at
        }
        submissions.append(submission_dict)

    return submissions
