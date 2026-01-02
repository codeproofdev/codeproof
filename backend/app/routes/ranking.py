"""
Ranking/Leaderboard routes for CodeProof

Provides endpoints to retrieve user rankings based on total score.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.database import get_db
from app.models import User
from app.schemas import RankingEntry
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=List[RankingEntry])
async def get_ranking(
    limit: int = Query(default=100, ge=1, le=500, description="Number of entries to return"),
    offset: int = Query(default=0, ge=0, description="Number of entries to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get leaderboard/ranking

    Returns users ordered by total_score in descending order.
    Rank is calculated dynamically based on score.

    **Query Parameters:**
    - **limit** (int): Number of entries to return (1-500, default 100)
    - **offset** (int): Number of entries to skip (for pagination, default 0)

    **Returns:**
    - List of RankingEntry with rank, username, scores, etc.

    **Example:**
    ```
    GET /api/ranking?limit=20&offset=0
    ```

    **Response:**
    ```json
    [
        {
            "rank": 1,
            "user_id": 1,
            "username": "satoshi",
            "total_score": 150.5,
            "problems_solved": 15,
            "blocks_mined": 3
        },
        ...
    ]
    ```

    **Notes:**
    - Rank is calculated dynamically (not stored in DB)
    - Users with same score get same rank
    - Ranks may have gaps (e.g., if 3 users tie for rank 1, next rank is 4)
    """

    try:
        # Query all users ordered by total_score_cached DESC (RETROACTIVE SCORING)
        # Use cached score for performance (updated by background job every 5 min)
        # Fallback to total_score if cache is null

        # Step 1: Get all users with their scores (for rank calculation)
        query = (
            select(User)
            .order_by(
                User.total_score_cached.desc().nullslast(),  # Use cached score (can be null)
                User.total_score.desc(),  # Fallback to legacy score
                User.id.asc()  # Secondary sort by id for stability
            )
        )

        result = await db.execute(query)
        all_users = result.scalars().all()

        # Step 2: Calculate ranks
        # Users with same score get same rank
        ranking = []
        current_rank = 1
        prev_score = None

        for idx, user in enumerate(all_users):
            # Use cached score, fallback to total_score if null
            user_score = user.total_score_cached if user.total_score_cached is not None else user.total_score

            # If score changed, update rank to current position
            if prev_score is not None and user_score < prev_score:
                current_rank = idx + 1

            ranking.append(RankingEntry(
                rank=current_rank,
                user_id=user.id,
                username=user.username,
                total_score=user_score,  # Use dynamic score
                problems_solved=user.problems_solved,
                blocks_mined=user.blocks_mined
            ))

            prev_score = user_score

        # Step 3: Apply pagination
        start = offset
        end = offset + limit
        paginated_ranking = ranking[start:end]

        logger.info(f"Ranking query: total_users={len(all_users)}, offset={offset}, limit={limit}, returned={len(paginated_ranking)}")

        return paginated_ranking

    except Exception as e:
        logger.exception(f"Error fetching ranking: {e}")
        raise


@router.get("/stats")
async def get_ranking_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get ranking statistics

    Returns aggregate statistics about the ranking:
    - Total number of users
    - Total score distributed
    - Total problems solved
    - Total blocks mined

    **Returns:**
    ```json
    {
        "total_users": 150,
        "total_score": 12500.5,
        "total_problems_solved": 450,
        "total_blocks_mined": 120
    }
    ```
    """

    try:
        # Query aggregate stats
        query = select(
            func.count(User.id).label('total_users'),
            func.sum(User.total_score).label('total_score'),
            func.sum(User.problems_solved).label('total_problems_solved'),
            func.sum(User.blocks_mined).label('total_blocks_mined')
        )

        result = await db.execute(query)
        stats = result.one()

        return {
            "total_users": stats.total_users or 0,
            "total_score": float(stats.total_score or 0),
            "total_problems_solved": stats.total_problems_solved or 0,
            "total_blocks_mined": stats.total_blocks_mined or 0
        }

    except Exception as e:
        logger.exception(f"Error fetching ranking stats: {e}")
        raise
