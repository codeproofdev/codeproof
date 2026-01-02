"""
Block Mining Scheduler for CodeProof

Mines new blocks every 10 minutes with unconfirmed AC submissions.
Inspired by Bitcoin block mining, with Bitcoin anchor data (mock for MVP).
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from app.database import SessionLocal
from app.models import Block, Submission, User, Verdict
from sqlalchemy import select, and_
import logging

logger = logging.getLogger(__name__)


def generate_block_hash(
    prev_hash: str,
    timestamp: datetime,
    tx_count: int,
    nonce: str
) -> str:
    """
    Generate block hash (SHA-256)

    Formula: SHA256(prev_hash + timestamp + tx_count + nonce)

    Args:
        prev_hash: Previous block hash
        timestamp: Block timestamp
        tx_count: Number of transactions
        nonce: Random nonce for uniqueness

    Returns:
        64-character hex string (SHA-256)
    """
    data = f"{prev_hash}{timestamp.isoformat()}{tx_count}{nonce}"
    return hashlib.sha256(data.encode()).hexdigest()


def generate_tx_hash(
    submission_id: int,
    block_height: int,
    timestamp: datetime
) -> str:
    """
    Generate transaction hash for a submission

    Formula: SHA256(submission_id + block_height + timestamp)

    Args:
        submission_id: Submission ID
        block_height: Block height
        timestamp: Block timestamp

    Returns:
        64-character hex string (SHA-256)
    """
    data = f"{submission_id}{block_height}{timestamp.isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()


def get_mock_bitcoin_data(block_height: int) -> dict:
    """
    Generate mock Bitcoin anchor data

    In production, this would fetch real Bitcoin block data from:
    - mempool.space API
    - Bitcoin Core RPC
    - Blockchain.info API

    For MVP, we generate realistic-looking mock data.

    Args:
        block_height: CodeProof block height (used as seed)

    Returns:
        Dict with Bitcoin block data
    """

    # Use CodeProof block height as seed for consistent mock data
    btc_base_height = 870000  # Current-ish Bitcoin height
    btc_block_height = btc_base_height + block_height

    # Generate deterministic mock hash based on height
    btc_hash_seed = f"btc_block_{btc_block_height}"
    btc_block_hash = hashlib.sha256(btc_hash_seed.encode()).hexdigest()

    # Mock miners (famous Bitcoin mining pools)
    miners = [
        "Foundry USA",
        "AntPool",
        "F2Pool",
        "ViaBTC",
        "Binance Pool",
        "Marathon Digital"
    ]
    miner = miners[block_height % len(miners)]

    # Realistic ranges
    tx_count = 2000 + (block_height * 13) % 3000  # 2000-5000 TX
    fees = 50000000 + (block_height * 17) % 100000000  # 0.5-1.5 BTC in satoshis
    size = 1000000 + (block_height * 19) % 3000000  # 1-4 MB
    weight = size * 4  # Weight units
    difficulty = 70000000000000.0 + (block_height * 1000000000.0)  # Increasing difficulty

    # Timestamp: ~10 minutes per block
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    btc_timestamp = base_time + timedelta(minutes=10 * btc_block_height)

    return {
        "btc_block_height": btc_block_height,
        "btc_block_hash": btc_block_hash,
        "btc_timestamp": btc_timestamp,
        "btc_tx_count": tx_count,
        "btc_fees": fees,
        "btc_size": size,
        "btc_weight": weight,
        "btc_miner": miner,
        "btc_difficulty": difficulty
    }


def mine_new_block() -> Optional[Block]:
    """
    Mine a new block with unconfirmed AC submissions

    Algorithm:
    1. Fetch all AC submissions with block_id IS NULL (unconfirmed)
    2. Order by submitted_at ASC
    3. Determine miner: user with first AC in interval
    4. Create new block with all submissions
    5. Generate block_hash and tx_hash for each submission
    6. Anchor to Bitcoin (mock for MVP)
    7. Commit to database

    Returns:
        The newly created Block, or None if no unconfirmed submissions
    """

    db = SessionLocal()

    try:
        logger.info("⛏️  Starting block mining process...")

        # 1. Get unconfirmed AC submissions (ordered by time)
        query = (
            select(Submission)
            .where(
                and_(
                    Submission.verdict == Verdict.AC,
                    Submission.block_id == None
                )
            )
            .order_by(Submission.submitted_at.asc())
        )

        result = db.execute(query)
        unconfirmed_submissions = result.scalars().all()

        if not unconfirmed_submissions:
            logger.info("No unconfirmed AC submissions. Mining empty block.")
            # Don't mine empty blocks for MVP (can enable later)
            return None

        logger.info(f"Found {len(unconfirmed_submissions)} unconfirmed AC submissions")

        # 2. Get previous block to determine new height and prev_hash
        prev_block_query = (
            select(Block)
            .order_by(Block.block_height.desc())
            .limit(1)
        )
        prev_block_result = db.execute(prev_block_query)
        prev_block = prev_block_result.scalar_one_or_none()

        if prev_block:
            new_height = prev_block.block_height + 1
            prev_hash = prev_block.block_hash
        else:
            # Genesis block
            new_height = 0
            prev_hash = "0" * 64  # Genesis prev_hash

        logger.info(f"Mining block #{new_height}")

        # 3. Determine miner (user with first AC)
        first_submission = unconfirmed_submissions[0]
        miner = db.query(User).filter(User.id == first_submission.user_id).first()

        # 4. Calculate block stats
        tx_count = len(unconfirmed_submissions)
        total_points = sum(sub.points_earned for sub in unconfirmed_submissions)
        block_size = sum(len(sub.source_code.encode()) for sub in unconfirmed_submissions) // 1024  # KB

        # 5. Generate block hash
        timestamp = datetime.utcnow()
        nonce = secrets.token_hex(16)  # Random nonce
        block_hash = generate_block_hash(prev_hash, timestamp, tx_count, nonce)

        # 6. Get Bitcoin anchor data (mock)
        btc_data = get_mock_bitcoin_data(new_height)

        # 7. Create new block
        new_block = Block(
            block_height=new_height,
            block_hash=block_hash,
            prev_block_hash=prev_hash,
            timestamp=timestamp,
            tx_count=tx_count,
            total_points=total_points,
            block_size=block_size,
            miner_id=miner.id,
            miner_username=miner.username,
            is_empty=False,
            **btc_data
        )

        db.add(new_block)
        db.flush()  # Get the block ID

        logger.info(f"Created block #{new_height}: hash={block_hash[:16]}..., miner={miner.username}, TX={tx_count}")

        # 8. Update submissions with block_id and tx_hash
        for submission in unconfirmed_submissions:
            submission.block_id = new_block.id
            submission.tx_hash = generate_tx_hash(submission.id, new_height, timestamp)
            submission.confirmed_at = timestamp

        # 9. Update miner's blocks_mined count
        miner.blocks_mined += 1

        # 10. Commit transaction
        db.commit()
        db.refresh(new_block)

        logger.info(f"✅ Block #{new_height} mined successfully!")
        logger.info(f"   Hash: {block_hash}")
        logger.info(f"   Miner: {miner.username}")
        logger.info(f"   Transactions: {tx_count}")
        logger.info(f"   Total Points: {total_points:.2f}")
        logger.info(f"   Bitcoin Anchor: {btc_data['btc_block_height']}")

        return new_block

    except Exception as e:
        logger.exception(f"Error mining block: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def start_block_mining_scheduler():
    """
    Start the block mining scheduler

    Uses APScheduler to run mine_new_block() every 10 minutes.

    In production:
    - Run as separate process/container
    - Use Redis as job store for persistence
    - Add monitoring and alerting
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = BackgroundScheduler()

    # Schedule mining every 10 minutes
    scheduler.add_job(
        func=mine_new_block,
        trigger=IntervalTrigger(minutes=10),
        id='block_miner',
        name='Mine new block every 10 minutes',
        replace_existing=True
    )

    # Mine first block immediately on startup (optional)
    # scheduler.add_job(
    #     func=mine_new_block,
    #     id='mine_initial_block',
    #     name='Mine initial block on startup'
    # )

    scheduler.start()
    logger.info("⛏️  Block mining scheduler started (runs every 10 minutes)")

    return scheduler


# Manual mining for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Manual block mining...")
    block = mine_new_block()
    if block:
        logger.info(f"Mined block: {block}")
    else:
        logger.info("No block mined (no unconfirmed submissions)")
