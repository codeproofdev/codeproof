"""
Pydantic schemas for request/response validation
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.models import UserRole, ProblemTier, ProblemStatus, Verdict


# ============================================
# AUTHENTICATION SCHEMAS
# ============================================

class UserRegister(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    email: Optional[str] = Field(None, max_length=255)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Validate username is alphanumeric with underscores"""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores allowed)')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data"""
    user_id: Optional[int] = None


# ============================================
# USER SCHEMAS
# ============================================

class UserBase(BaseModel):
    """Base user schema"""
    username: str


class UserOut(UserBase):
    """Schema for user output (public info)"""
    id: int
    username: str
    email: Optional[str] = None
    npub: Optional[str] = None
    github_url: Optional[str] = None
    country: Optional[str] = None
    organization: Optional[str] = None
    role: UserRole
    total_score: float
    problems_solved: int
    blocks_mined: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True  # Enable ORM mode (SQLAlchemy models)


class UserProfile(UserOut):
    """Extended user profile with additional stats"""
    pass


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    email: Optional[str] = None
    npub: Optional[str] = None
    github_url: Optional[str] = None
    country: Optional[str] = None
    organization: Optional[str] = None


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


# ============================================
# SETUP SCHEMAS
# ============================================

class SetupStatus(BaseModel):
    """Schema for setup status response"""
    needs_setup: bool
    message: str


class SetupInit(BaseModel):
    """Schema for initial setup (first admin creation)"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Validate username is alphanumeric with underscores"""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores allowed)')
        return v


class UserAdminUpdate(BaseModel):
    """Schema for admin to update users"""
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=8)


class AdminPasswordReset(BaseModel):
    """Schema for admin to reset user password"""
    new_password: str = Field(..., min_length=8, max_length=100)


# ============================================
# PROBLEM SCHEMAS
# ============================================

class TestCaseBase(BaseModel):
    """Base test case schema"""
    case_number: int
    input_file: str
    output_file: str
    is_sample: bool = False
    points: float = 1.0
    time_limit_override: Optional[int] = None
    memory_limit_override: Optional[int] = None


class TestCaseCreate(TestCaseBase):
    """Schema for creating a test case"""
    pass


class TestCaseOut(TestCaseBase):
    """Schema for test case output"""
    id: int
    problem_id: int

    class Config:
        from_attributes = True


# ============================================
# CATEGORY SCHEMAS (defined early for forward refs)
# ============================================

class SubcategoryOut(BaseModel):
    """Schema for subcategory output"""
    id: int
    category_id: int
    code: str
    name_en: str
    name_es: str
    description_en: Optional[str] = None
    description_es: Optional[str] = None
    order: int

    class Config:
        from_attributes = True


class CategoryOut(BaseModel):
    """Schema for category output"""
    id: int
    code: str
    name_en: str
    name_es: str
    description_en: Optional[str] = None
    description_es: Optional[str] = None
    icon: Optional[str] = None
    order: int
    problem_range_start: int
    problem_range_end: int

    class Config:
        from_attributes = True


class CategoryDetail(CategoryOut):
    """Extended category with subcategories"""
    subcategories: list[SubcategoryOut] = []


class ProblemBase(BaseModel):
    """Base problem schema"""
    title_en: str
    title_es: str
    description_en: str
    description_es: str
    tier: ProblemTier = ProblemTier.TIER1
    time_limit: int = 2
    memory_limit: int = 256
    partial: bool = False
    authors: list[str] = []
    author_note: Optional[str] = None
    categories: list[str] = []  # Category codes
    subcategories: list[str] = []  # Subcategory codes


class ProblemCreate(ProblemBase):
    """Schema for creating a problem"""
    test_cases: list[TestCaseCreate] = []
    # Also accept sample_tests and hidden_tests from frontend
    sample_tests: Optional[list[dict]] = None
    hidden_tests: Optional[list[dict]] = None


class ProblemUpdate(BaseModel):
    """Schema for updating a problem"""
    title_en: Optional[str] = None
    title_es: Optional[str] = None
    description_en: Optional[str] = None
    description_es: Optional[str] = None
    time_limit: Optional[int] = None
    memory_limit: Optional[int] = None
    authors: Optional[list[str]] = None
    author_note: Optional[str] = None
    categories: Optional[list[str]] = None  # Category codes
    subcategories: Optional[list[str]] = None  # Subcategory codes
    editorial_visibility: Optional[str] = None  # always, after_solve, after_deadline
    # Allow updating test cases
    sample_tests: Optional[list[dict]] = None
    hidden_tests: Optional[list[dict]] = None


class ProblemOut(BaseModel):
    """Schema for problem output"""
    id: int
    title_en: str
    title_es: str
    description_en: str
    description_es: str
    tier: ProblemTier
    time_limit: int
    memory_limit: int
    partial: bool
    authors: list[str] = []
    author_note: Optional[str] = None
    status: ProblemStatus
    current_points: float
    solved_count: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    tags: list[str] = []

    class Config:
        from_attributes = True


class ProblemDetail(ProblemOut):
    """Extended problem detail with test cases"""
    test_cases: list[TestCaseOut] = []
    categories: list['CategoryOut'] = []
    subcategories: list['SubcategoryOut'] = []
    has_editorial: bool = False
    editorial_visibility: str = 'always'


class ProblemListItem(BaseModel):
    """Simplified schema for problem list"""
    id: int
    title_en: str
    title_es: str
    tier: ProblemTier
    current_points: float
    solved_count: int

    # Add these fields for problemsetter panel
    status: Optional[ProblemStatus] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

    # Add categories and subcategories for filtering
    categories: list['CategoryOut'] = []
    subcategories: list['SubcategoryOut'] = []

    class Config:
        from_attributes = True


class ProblemPackageInfo(BaseModel):
    """Schema for problem package information"""
    code: str
    problem_id: int
    size_bytes: int
    file_count: int
    has_problem_yml: bool
    has_descriptions: bool
    test_case_count: int
    sample_count: int
    hidden_count: int
    created_at: datetime
    updated_at: datetime


# ============================================
# SUBMISSION SCHEMAS
# ============================================

class SubmissionCreate(BaseModel):
    """Schema for creating a submission"""
    problem_id: int
    language: str = "python"
    source_code: str = Field(..., max_length=50000)  # 50KB limit

    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate supported languages"""
        allowed = ['python', 'cpp', 'rust', 'javascript', 'go']
        if v not in allowed:
            raise ValueError(f'Language must be one of: {allowed}')
        return v


class SubmissionOut(BaseModel):
    """Schema for submission output"""
    id: int
    user_id: int
    username: Optional[str] = None  # Username of the submitter (for public judge view)
    problem_id: int
    language: str
    verdict: Verdict
    execution_time: Optional[int] = None
    memory_used: Optional[int] = None
    points_earned: float
    test_results: Optional[dict] = None
    submitted_at: datetime
    judged_at: Optional[datetime] = None

    # Blockchain fields
    block_id: Optional[int] = None
    tx_hash: Optional[str] = None
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubmissionDetail(SubmissionOut):
    """Extended submission with source code"""
    source_code: str


class SubmissionStatus(BaseModel):
    """Schema for checking submission status"""
    id: int
    verdict: Verdict
    judged_at: Optional[datetime] = None


# ============================================
# BLOCK SCHEMAS
# ============================================

class BlockOut(BaseModel):
    """Schema for block output"""
    id: int
    block_height: int
    block_hash: str
    prev_block_hash: str
    timestamp: datetime
    tx_count: int
    total_points: float
    block_size: int

    # Miner info
    miner_id: Optional[int] = None
    miner_username: Optional[str] = None
    is_empty: bool

    # Bitcoin anchor
    btc_block_height: Optional[int] = None
    btc_block_hash: Optional[str] = None
    btc_timestamp: Optional[datetime] = None
    btc_miner: Optional[str] = None

    class Config:
        from_attributes = True


class BlockDetail(BlockOut):
    """Extended block with transactions"""
    transactions: list[SubmissionOut] = []


# ============================================
# RANKING SCHEMAS
# ============================================

class RankingEntry(BaseModel):
    """Schema for ranking/leaderboard entry"""
    rank: int
    user_id: int
    username: str
    total_score: float
    problems_solved: int
    blocks_mined: int




# ============================================
# GENERIC RESPONSE SCHEMAS
# ============================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
