"""
Admin routes
Handles admin-specific operations like statistics and problem management
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import User, Problem, Submission, Block, ProblemStatus, Verdict
from app.auth import require_admin

router = APIRouter()


@router.get("/statistics")
async def get_statistics(
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get platform statistics (admin only)

    Returns:
    - Total users
    - Total problems
    - Total submissions
    - Total blocks
    - Pending problems count
    """

    # Count users
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar()

    # Count problems
    result = await db.execute(select(func.count(Problem.id)))
    total_problems = result.scalar()

    # Count approved problems
    result = await db.execute(
        select(func.count(Problem.id)).where(Problem.status == ProblemStatus.APPROVED)
    )
    approved_problems = result.scalar()

    # Count pending problems
    result = await db.execute(
        select(func.count(Problem.id)).where(Problem.status == ProblemStatus.PENDING)
    )
    pending_problems = result.scalar()

    # Count submissions
    result = await db.execute(select(func.count(Submission.id)))
    total_submissions = result.scalar()

    # Count AC submissions
    result = await db.execute(
        select(func.count(Submission.id)).where(Submission.verdict == Verdict.AC)
    )
    ac_submissions = result.scalar()

    # Count blocks
    result = await db.execute(select(func.count(Block.id)))
    total_blocks = result.scalar()

    return {
        "total_users": total_users,
        "total_problems": total_problems,
        "approved_problems": approved_problems,
        "pending_problems": pending_problems,
        "total_submissions": total_submissions,
        "ac_submissions": ac_submissions,
        "total_blocks": total_blocks,
        "accuracy": round((ac_submissions / total_submissions * 100) if total_submissions > 0 else 0, 2)
    }


@router.get("/problems/pending")
async def get_pending_problems(
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pending problems (admin only)

    Returns list of problems with status=PENDING
    """

    result = await db.execute(
        select(Problem)
        .where(Problem.status == ProblemStatus.PENDING)
        .order_by(Problem.created_at.desc())
    )
    problems = result.scalars().all()

    return problems
