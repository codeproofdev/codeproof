"""
SQLAlchemy ORM Models for CodeProof
Based on design from BACKEND-DESIGN.md
"""

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Enum, ARRAY, CheckConstraint,
    Index, UniqueConstraint, Table
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


# ============================================
# ENUMS
# ============================================

class UserRole(str, enum.Enum):
    """User roles"""
    USER = "user"
    PROBLEMSETTER = "problemsetter"
    ADMIN = "admin"


class ProblemStatus(str, enum.Enum):
    """Problem approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProblemTier(str, enum.Enum):
    """Problem execution tier"""
    TIER1 = "tier1"  # Pure code (isolate)
    TIER2 = "tier2"  # Bitcoin Core (docker)
    TIER3 = "tier3"  # Lightning/Cashu (docker-compose)


class Verdict(str, enum.Enum):
    """Submission verdicts"""
    PENDING = "PENDING"
    AC = "AC"  # Accepted
    WA = "WA"  # Wrong Answer
    TLE = "TLE"  # Time Limit Exceeded
    MLE = "MLE"  # Memory Limit Exceeded
    OLE = "OLE"  # Output Limit Exceeded
    RE = "RE"  # Runtime Error
    CE = "CE"  # Compilation Error
    IE = "IE"  # Internal Error


# ============================================
# JUNCTION TABLES
# ============================================

# Tabla de unión: Problemas <-> Categorías (many-to-many)
problem_categories = Table(
    'problem_categories',
    Base.metadata,
    Column('problem_id', Integer, ForeignKey('problems.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True),
    Column('is_primary', Boolean, default=False)
)

# Tabla de unión: Problemas <-> Subcategorías (many-to-many)
problem_subcategories = Table(
    'problem_subcategories',
    Base.metadata,
    Column('problem_id', Integer, ForeignKey('problems.id'), primary_key=True),
    Column('subcategory_id', Integer, ForeignKey('subcategories.id'), primary_key=True),
    Column('is_primary', Boolean, default=False)
)


# ============================================
# MODELS
# ============================================

class Category(Base):
    """Category model (5 main categories)"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name_en = Column(String(100), nullable=False)
    name_es = Column(String(100), nullable=False)
    description_en = Column(Text, nullable=True)
    description_es = Column(Text, nullable=True)
    icon = Column(String(10), nullable=True)
    order = Column(Integer, nullable=False)
    problem_range_start = Column(Integer, nullable=False)
    problem_range_end = Column(Integer, nullable=False)

    # Relationships
    subcategories = relationship("Subcategory", back_populates="category", cascade="all, delete-orphan")
    problems = relationship("Problem", secondary=problem_categories, back_populates="categories")

    def __repr__(self):
        return f"<Category {self.code}>"


class Subcategory(Base):
    """Subcategory model (33 total)"""
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name_en = Column(String(100), nullable=False)
    name_es = Column(String(100), nullable=False)
    description_en = Column(Text, nullable=True)
    description_es = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)

    # Relationships
    category = relationship("Category", back_populates="subcategories")
    problems = relationship("Problem", secondary=problem_subcategories, back_populates="subcategories")

    # Constraints
    __table_args__ = (
        UniqueConstraint('category_id', 'code', name='uq_category_subcategory'),
    )

    def __repr__(self):
        return f"<Subcategory {self.category_id}:{self.code}>"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)

    # Profile fields
    npub = Column(String(255), nullable=True)
    github_url = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    organization = Column(String(255), nullable=True)

    # Stats (denormalized for performance)
    total_score = Column(Float, nullable=False, default=0, index=True)  # DEPRECATED: use total_score_cached
    problems_solved = Column(Integer, nullable=False, default=0)

    # Dynamic scoring cache (NEW - for retroactive system)
    total_score_cached = Column(Float, nullable=True, index=True)  # Cached dynamic score
    score_updated_at = Column(DateTime(timezone=True), nullable=True)  # When cache was updated

    # Mining stats
    blocks_mined = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    problems = relationship("Problem", back_populates="creator", foreign_keys="Problem.created_by")
    submissions = relationship("Submission", back_populates="user")
    mined_blocks = relationship("Block", back_populates="miner", foreign_keys="Block.miner_id")
    solved_problems = relationship("UserProblemSolve", back_populates="user")  # NEW

    # Constraints
    __table_args__ = (
        CheckConstraint("char_length(username) >= 3", name="username_min_length"),
        Index("idx_users_total_score", total_score.desc()),
        Index("idx_users_score_cached", total_score_cached.desc()),  # NEW
    )

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"


class Problem(Base):
    """Problem model"""
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)

    # Problem number and storage
    number = Column(Integer, nullable=True, unique=True, index=True)
    file_based = Column(Boolean, nullable=False, default=False)
    data_path = Column(String(255), nullable=True)

    # Metadata
    title_en = Column(Text, nullable=False)
    title_es = Column(Text, nullable=False)
    description_en = Column(Text, nullable=False)
    description_es = Column(Text, nullable=False)

    # Authorship
    authors = Column(ARRAY(String), nullable=False, default=[])
    author_note = Column(Text, nullable=True)

    # Classification
    tier = Column(Enum(ProblemTier), nullable=False, default=ProblemTier.TIER1, index=True)
    status = Column(Enum(ProblemStatus), nullable=False, default=ProblemStatus.PENDING, index=True)

    # Limits
    time_limit = Column(Integer, nullable=False, default=2)  # seconds
    memory_limit = Column(Integer, nullable=False, default=256)  # MB

    # Scoring
    initial_points = Column(Float, nullable=False, default=10.0)
    current_points = Column(Float, nullable=False, default=10.0)
    solved_count = Column(Integer, nullable=False, default=0)

    # Partial scoring
    partial = Column(Boolean, nullable=False, default=False)

    # Ownership
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Docker config (for Tier 2/3)
    docker_image = Column(String(255), nullable=True)
    docker_config = Column(JSONB, nullable=True)

    # Categorization
    tags = Column(ARRAY(String), nullable=False, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Editorial and reference files
    has_editorial = Column(Boolean, nullable=False, default=False)
    editorial_visibility = Column(String(20), nullable=False, default="always")  # always, after_solve, after_deadline, manual
    has_reference_files = Column(Boolean, nullable=False, default=False)

    # Relationships
    creator = relationship("User", back_populates="problems", foreign_keys=[created_by])
    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")
    batches = relationship("Batch", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="problem")

    # Categorization relationships
    categories = relationship("Category", secondary=problem_categories, back_populates="problems")
    subcategories = relationship("Subcategory", secondary=problem_subcategories, back_populates="problems")

    def __repr__(self):
        return f"<Problem {self.id}: {self.title_en[:30]}>"

    # Helper methods for categorization
    def get_primary_category(self, db_session):
        """Returns the category marked as primary"""
        from sqlalchemy import select
        stmt = select(Category).join(
            problem_categories
        ).where(
            problem_categories.c.problem_id == self.id,
            problem_categories.c.is_primary == True
        )
        result = db_session.execute(stmt).scalar_one_or_none()
        # If no primary, return the first one
        return result or (self.categories[0] if self.categories else None)

    def get_primary_subcategory(self, db_session):
        """Returns the subcategory marked as primary"""
        from sqlalchemy import select
        stmt = select(Subcategory).join(
            problem_subcategories
        ).where(
            problem_subcategories.c.problem_id == self.id,
            problem_subcategories.c.is_primary == True
        )
        result = db_session.execute(stmt).scalar_one_or_none()
        return result or (self.subcategories[0] if self.subcategories else None)

    def add_category(self, category, is_primary=False):
        """Adds a category to the problem"""
        if category not in self.categories:
            self.categories.append(category)

    def add_subcategory(self, subcategory, is_primary=False):
        """Adds a subcategory to the problem"""
        if subcategory not in self.subcategories:
            self.subcategories.append(subcategory)


class TestCase(Base):
    """Test case model"""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)

    # Order and grouping
    case_number = Column(Integer, nullable=False)
    batch_number = Column(Integer, nullable=True)  # NULL = no batch

    # Test data
    input_file = Column(Text, nullable=False)  # Path or inline data
    output_file = Column(Text, nullable=False)  # Path or inline data

    # Visibility
    is_sample = Column(Boolean, nullable=False, default=False)

    # Scoring
    points = Column(Float, nullable=False, default=1.0)

    # Config
    time_limit_override = Column(Integer, nullable=True)
    memory_limit_override = Column(Integer, nullable=True)

    # Relationships
    problem = relationship("Problem", back_populates="test_cases")

    # Constraints
    __table_args__ = (
        UniqueConstraint("problem_id", "case_number", name="uq_problem_case_number"),
    )

    def __repr__(self):
        return f"<TestCase {self.problem_id}-{self.case_number}>"


class Batch(Base):
    """Batch (test case group) model for dependent scoring"""
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    batch_number = Column(Integer, nullable=False)
    points = Column(Float, nullable=False)
    dependencies = Column(ARRAY(Integer), nullable=False, default=[])  # Array of batch_numbers

    # Relationships
    problem = relationship("Problem", back_populates="batches")

    # Constraints
    __table_args__ = (
        UniqueConstraint("problem_id", "batch_number", name="uq_problem_batch_number"),
    )

    def __repr__(self):
        return f"<Batch {self.problem_id}-{self.batch_number}>"


class Submission(Base):
    """Submission model"""
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)

    # Relations
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)

    # Code
    language = Column(String(20), nullable=False, default="python")
    source_code = Column(Text, nullable=False)

    # Results
    verdict = Column(Enum(Verdict), nullable=False, default=Verdict.PENDING, index=True)
    execution_time = Column(Integer, nullable=True)  # milliseconds
    memory_used = Column(Integer, nullable=True)  # KB

    # Scoring
    points_earned = Column(Float, nullable=False, default=0)
    test_results = Column(JSONB, nullable=True)

    # Blockchain
    block_id = Column(Integer, ForeignKey("blocks.id"), nullable=True, index=True)
    tx_hash = Column(String(64), unique=True, nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    judged_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")
    block = relationship("Block", back_populates="transactions")

    # Constraints
    __table_args__ = (
        CheckConstraint("octet_length(source_code) <= 51200", name="source_code_size_limit"),  # 50KB
        Index("idx_submissions_user_problem", user_id, problem_id),
        Index("idx_submissions_user_verdict", user_id, verdict),
        Index("idx_submissions_problem_verdict", problem_id, verdict),
        Index("idx_submissions_submitted_at", submitted_at.desc()),
        # Partial index for unconfirmed AC submissions (hot path for block mining)
        Index("idx_submissions_unconfirmed", submitted_at.asc(),
              postgresql_where=(verdict == 'AC') & (block_id == None)),
    )

    def __repr__(self):
        return f"<Submission {self.id}: {self.verdict.value}>"


class UserProblemSolve(Base):
    """
    Tracking table for user-problem solves (for retroactive scoring)

    This table tracks WHICH problems each user solved and WHEN,
    but NOT how many points they earned (points are calculated dynamically).
    """
    __tablename__ = "user_problem_solves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False, index=True)

    # Metadata of first AC
    first_submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    solved_at = Column(DateTime(timezone=True), nullable=False, index=True)
    solve_position = Column(Integer, nullable=False)  # 1 = first solver, 2 = second, etc.

    # Relationships
    user = relationship("User", back_populates="solved_problems")
    problem = relationship("Problem")
    submission = relationship("Submission")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'problem_id', name='uq_user_problem_solve'),
        Index("idx_user_solves", user_id, solved_at.desc()),
        Index("idx_problem_solves", problem_id, solved_at.asc()),
    )

    def __repr__(self):
        return f"<UserProblemSolve user={self.user_id} problem={self.problem_id} pos={self.solve_position}>"


class Block(Base):
    """Block model (blockchain)"""
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)

    # Block data
    block_height = Column(Integer, unique=True, nullable=False, index=True)
    block_hash = Column(String(64), unique=True, nullable=False)
    prev_block_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Block stats
    tx_count = Column(Integer, nullable=False, default=0)
    total_points = Column(Float, nullable=False, default=0)
    block_size = Column(Integer, nullable=False, default=0)  # KB

    # CodeProof miner (user with first AC in interval)
    miner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    miner_username = Column(String(50), nullable=True)
    is_empty = Column(Boolean, nullable=False, default=False)

    # Bitcoin anchor data
    btc_block_height = Column(Integer, nullable=True)
    btc_block_hash = Column(String(64), nullable=True)
    btc_timestamp = Column(DateTime(timezone=True), nullable=True)
    btc_tx_count = Column(Integer, nullable=True)
    btc_fees = Column(Integer, nullable=True)  # Satoshis
    btc_size = Column(Integer, nullable=True)  # Bytes
    btc_weight = Column(Integer, nullable=True)  # Weight units
    btc_miner = Column(String(255), nullable=True)
    btc_difficulty = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    transactions = relationship("Submission", back_populates="block")
    miner = relationship("User", back_populates="mined_blocks", foreign_keys=[miner_id])

    # Indexes
    __table_args__ = (
        Index("idx_blocks_height", block_height.desc()),
        Index("idx_blocks_timestamp", timestamp.desc()),
    )

    def __repr__(self):
        return f"<Block #{self.block_height}: {self.tx_count} TX>"
