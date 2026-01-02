"""
Blockchain routes for CodeProof

Provides endpoints for blocks and mempool (unconfirmed transactions).
Inspired by mempool.space API design.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Block, Submission, User, Problem, Verdict
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================
# SCHEMAS
# ============================================

class TransactionOut(BaseModel):
    """Transaction (submission) in a block"""
    id: int
    user_id: int
    username: str
    problem_id: int
    problem_title: str
    points_earned: float
    execution_time: int
    tx_hash: Optional[str]
    submitted_at: str  # ISO format
    confirmed_at: Optional[str]  # ISO format

    class Config:
        from_attributes = True


class BlockOut(BaseModel):
    """Block summary (for list)"""
    id: int
    block_height: int
    block_hash: str
    timestamp: str  # ISO format
    tx_count: int
    total_points: float
    miner_username: Optional[str]
    is_empty: bool
    btc_block_height: Optional[int]

    class Config:
        from_attributes = True


class BlockDetail(BaseModel):
    """Block detail with all transactions"""
    id: int
    block_height: int
    block_hash: str
    prev_block_hash: str
    timestamp: str  # ISO format
    tx_count: int
    total_points: float
    block_size: int
    miner_id: Optional[int]
    miner_username: Optional[str]
    is_empty: bool

    # Bitcoin anchor
    btc_block_height: Optional[int]
    btc_block_hash: Optional[str]
    btc_timestamp: Optional[str]
    btc_tx_count: Optional[int]
    btc_fees: Optional[int]
    btc_size: Optional[int]
    btc_weight: Optional[int]
    btc_miner: Optional[str]
    btc_difficulty: Optional[float]

    # Transactions
    transactions: List[TransactionOut]

    class Config:
        from_attributes = True


class MempoolOut(BaseModel):
    """Mempool (unconfirmed transactions)"""
    pending_count: int  # Submissions being judged
    unconfirmed_count: int  # AC submissions waiting for next block
    pending_submissions: List[TransactionOut]
    unconfirmed_submissions: List[TransactionOut]


# ============================================
# ENDPOINTS
# ============================================

@router.get("", response_model=List[BlockOut])
async def list_blocks(
    limit: int = Query(default=30, ge=1, le=100, description="Number of blocks to return"),
    offset: int = Query(default=0, ge=0, description="Number of blocks to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    List recent blocks

    Returns blocks in reverse chronological order (newest first).

    **Query Parameters:**
    - **limit** (int): Number of blocks to return (1-100, default 30)
    - **offset** (int): Number of blocks to skip (for pagination)

    **Returns:**
    - List of BlockOut with summary information

    **Example:**
    ```
    GET /api/blocks?limit=10&offset=0
    ```

    **Response:**
    ```json
    [
        {
            "id": 5,
            "block_height": 4,
            "block_hash": "0000abc...",
            "timestamp": "2024-01-01T12:00:00Z",
            "tx_count": 15,
            "total_points": 125.5,
            "miner_username": "satoshi",
            "is_empty": false,
            "btc_block_height": 870004
        },
        ...
    ]
    ```
    """

    try:
        # Query blocks ordered by height DESC
        query = (
            select(Block)
            .order_by(Block.block_height.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        blocks = result.scalars().all()

        # Convert to Pydantic models with ISO timestamps
        blocks_out = []
        for block in blocks:
            blocks_out.append(BlockOut(
                id=block.id,
                block_height=block.block_height,
                block_hash=block.block_hash,
                timestamp=block.timestamp.isoformat(),
                tx_count=block.tx_count,
                total_points=block.total_points,
                miner_username=block.miner_username,
                is_empty=block.is_empty,
                btc_block_height=block.btc_block_height
            ))

        logger.info(f"Listed {len(blocks)} blocks (limit={limit}, offset={offset})")

        return blocks_out

    except Exception as e:
        logger.exception(f"Error listing blocks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list blocks"
        )


@router.get("/id/{block_id}", response_model=BlockDetail)
async def get_block(
    block_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get block details with all transactions

    **Path Parameters:**
    - **block_id** (int): Block ID (or use block_height with /blocks/height/:height)

    **Returns:**
    - BlockDetail with full block information including all transactions

    **Example:**
    ```
    GET /api/blocks/id/5
    ```

    **Response:**
    ```json
    {
        "id": 5,
        "block_height": 4,
        "block_hash": "0000abc...",
        "prev_block_hash": "0000def...",
        "timestamp": "2024-01-01T12:00:00Z",
        "tx_count": 15,
        "total_points": 125.5,
        "block_size": 42,
        "miner_username": "satoshi",
        "is_empty": false,
        "btc_block_height": 870004,
        "btc_block_hash": "00000000...",
        "btc_miner": "Foundry USA",
        "transactions": [
            {
                "id": 123,
                "username": "alice",
                "problem_title": "Two Sum",
                "points_earned": 10.0,
                "tx_hash": "abc123...",
                ...
            },
            ...
        ]
    }
    ```

    **Errors:**
    - 404: Block not found
    """

    try:
        # Fetch block
        query = select(Block).where(Block.id == block_id)
        result = await db.execute(query)
        block = result.scalar_one_or_none()

        if not block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Block not found"
            )

        # Fetch transactions (submissions in this block)
        tx_query = (
            select(Submission, User, Problem)
            .join(User, Submission.user_id == User.id)
            .join(Problem, Submission.problem_id == Problem.id)
            .where(Submission.block_id == block.id)
            .order_by(Submission.submitted_at.asc())
        )

        tx_result = await db.execute(tx_query)
        transactions_raw = tx_result.all()

        # Build transaction list
        transactions = []
        for submission, user, problem in transactions_raw:
            transactions.append(TransactionOut(
                id=submission.id,
                user_id=user.id,
                username=user.username,
                problem_id=problem.id,
                problem_title=problem.title_en,
                points_earned=submission.points_earned,
                execution_time=submission.execution_time or 0,
                tx_hash=submission.tx_hash,
                submitted_at=submission.submitted_at.isoformat(),
                confirmed_at=submission.confirmed_at.isoformat() if submission.confirmed_at else None
            ))

        # Build BlockDetail response
        block_detail = BlockDetail(
            id=block.id,
            block_height=block.block_height,
            block_hash=block.block_hash,
            prev_block_hash=block.prev_block_hash,
            timestamp=block.timestamp.isoformat(),
            tx_count=block.tx_count,
            total_points=block.total_points,
            block_size=block.block_size,
            miner_id=block.miner_id,
            miner_username=block.miner_username,
            is_empty=block.is_empty,
            btc_block_height=block.btc_block_height,
            btc_block_hash=block.btc_block_hash,
            btc_timestamp=block.btc_timestamp.isoformat() if block.btc_timestamp else None,
            btc_tx_count=block.btc_tx_count,
            btc_fees=block.btc_fees,
            btc_size=block.btc_size,
            btc_weight=block.btc_weight,
            btc_miner=block.btc_miner,
            btc_difficulty=block.btc_difficulty,
            transactions=transactions
        )

        logger.info(f"Fetched block #{block.block_height} with {len(transactions)} transactions")

        return block_detail

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching block {block_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch block"
        )


@router.get("/height/{block_height}", response_model=BlockDetail)
async def get_block_by_height(
    block_height: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get block by height (alternative to ID)

    **Path Parameters:**
    - **block_height** (int): Block height (e.g., 0 for genesis, 1 for first block, etc.)

    **Returns:**
    - BlockDetail with full block information

    **Example:**
    ```
    GET /api/blocks/height/4
    ```

    **Errors:**
    - 404: Block not found
    """

    try:
        # Fetch block by height
        query = select(Block).where(Block.block_height == block_height)
        result = await db.execute(query)
        block = result.scalar_one_or_none()

        if not block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Block at height {block_height} not found"
            )

        # Reuse get_block logic
        return await get_block(block.id, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching block at height {block_height}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch block"
        )


@router.get("/mempool", response_model=MempoolOut)
async def get_mempool(
    db: AsyncSession = Depends(get_db)
):
    """
    Get mempool (unconfirmed transactions)

    Returns submissions that are:
    - **Pending**: Currently being judged (verdict = PENDING)
    - **Unconfirmed**: Accepted but not yet in a block (verdict = AC, block_id = NULL)

    **Returns:**
    - MempoolOut with counts and lists of pending/unconfirmed submissions

    **Example:**
    ```
    GET /api/blocks/mempool
    ```

    **Response:**
    ```json
    {
        "pending_count": 5,
        "unconfirmed_count": 12,
        "pending_submissions": [...],
        "unconfirmed_submissions": [...]
    }
    ```

    **Note:**
    This is similar to Bitcoin's mempool, showing transactions waiting to be confirmed.
    """

    try:
        # Query pending submissions (being judged)
        pending_query = (
            select(Submission, User, Problem)
            .join(User, Submission.user_id == User.id)
            .join(Problem, Submission.problem_id == Problem.id)
            .where(Submission.verdict == Verdict.PENDING)
            .order_by(Submission.submitted_at.desc())
            .limit(50)  # Limit for performance
        )

        pending_result = await db.execute(pending_query)
        pending_raw = pending_result.all()

        # Query unconfirmed AC submissions (waiting for block)
        unconfirmed_query = (
            select(Submission, User, Problem)
            .join(User, Submission.user_id == User.id)
            .join(Problem, Submission.problem_id == Problem.id)
            .where(
                and_(
                    Submission.verdict == Verdict.AC,
                    Submission.block_id == None
                )
            )
            .order_by(Submission.submitted_at.asc())
            .limit(100)  # Limit for performance
        )

        unconfirmed_result = await db.execute(unconfirmed_query)
        unconfirmed_raw = unconfirmed_result.all()

        # Build transaction lists
        pending_submissions = []
        for submission, user, problem in pending_raw:
            pending_submissions.append(TransactionOut(
                id=submission.id,
                user_id=user.id,
                username=user.username,
                problem_id=problem.id,
                problem_title=problem.title_en,
                points_earned=submission.points_earned,
                execution_time=submission.execution_time or 0,
                tx_hash=submission.tx_hash,
                submitted_at=submission.submitted_at.isoformat(),
                confirmed_at=None
            ))

        unconfirmed_submissions = []
        for submission, user, problem in unconfirmed_raw:
            unconfirmed_submissions.append(TransactionOut(
                id=submission.id,
                user_id=user.id,
                username=user.username,
                problem_id=problem.id,
                problem_title=problem.title_en,
                points_earned=submission.points_earned,
                execution_time=submission.execution_time or 0,
                tx_hash=submission.tx_hash,
                submitted_at=submission.submitted_at.isoformat(),
                confirmed_at=None
            ))

        logger.info(f"Mempool: {len(pending_submissions)} pending, {len(unconfirmed_submissions)} unconfirmed")

        return MempoolOut(
            pending_count=len(pending_submissions),
            unconfirmed_count=len(unconfirmed_submissions),
            pending_submissions=pending_submissions,
            unconfirmed_submissions=unconfirmed_submissions
        )

    except Exception as e:
        logger.exception(f"Error fetching mempool: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch mempool"
        )
