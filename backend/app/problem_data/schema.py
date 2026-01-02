"""
Pydantic schemas for problem.yml validation
Based on PROBLEM-STORAGE-SPEC.md
"""

from datetime import date
from typing import Optional, Dict, List, Literal
from pydantic import BaseModel, Field, field_validator


# ============================================
# NESTED SCHEMAS
# ============================================

class BilingualText(BaseModel):
    """Bilingual text (English and Spanish)"""
    en: str
    es: str


class ProblemLimits(BaseModel):
    """Resource limits for problem execution"""
    time: float = Field(default=2.0, gt=0, le=60, description="Time limit in seconds")
    memory: int = Field(default=256, gt=0, le=4096, description="Memory limit in MB")
    output: int = Field(default=65536, gt=0, description="Max output in KB")
    output_prefix: int = Field(default=4096, gt=0, description="First KB for diff")
    source_code: int = Field(default=50, gt=0, le=512, description="Max source code size in KB")


class LanguageLimits(BaseModel):
    """Language-specific overrides"""
    time_multiplier: Optional[float] = Field(None, gt=0, le=10)
    memory_grace_kb: Optional[int] = Field(None, ge=0)
    max_processes: Optional[int] = Field(None, gt=0)


class CheckerConfig(BaseModel):
    """Checker configuration"""
    type: Literal["standard", "token", "float", "custom"] = "standard"
    executable: Optional[str] = None  # For custom checkers
    args: Dict = Field(default_factory=dict)

    @field_validator('executable')
    @classmethod
    def validate_custom_checker(cls, v, info):
        """Validate that custom checkers have executable"""
        if info.data.get('type') == 'custom' and not v:
            raise ValueError("Custom checker requires 'executable' field")
        return v


class ScoringConfig(BaseModel):
    """Scoring configuration"""
    initial_points: float = Field(default=10.0, gt=0)
    partial: bool = Field(default=False)
    mode: Literal["dynamic", "fixed"] = "dynamic"


class TestCase(BaseModel):
    """Individual test case"""
    input: str = Field(..., description="Path to input file (relative to problem dir)")
    output: str = Field(..., description="Path to output file (relative to problem dir)")
    points: float = Field(default=0, ge=0)
    description: Optional[str] = None
    time_limit: Optional[float] = Field(None, gt=0)
    memory_limit: Optional[int] = Field(None, gt=0)


class TestCases(BaseModel):
    """Test cases organized by type"""
    pretests: List[TestCase] = Field(default_factory=list)
    samples: List[TestCase] = Field(default_factory=list)
    hidden: List[TestCase] = Field(default_factory=list)


class Batch(BaseModel):
    """Batch (subtask) configuration"""
    id: int = Field(..., gt=0)
    name: str
    points: float = Field(..., gt=0)
    test_cases: List[int] = Field(default_factory=list, description="Test case indices")
    dependencies: List[int] = Field(default_factory=list, description="Batch IDs that must pass first")


class DockerConfig(BaseModel):
    """Docker configuration for Tier 2/3 problems"""
    image: str = Field(..., description="Docker image name")
    setup_script: Optional[str] = None
    timeout: int = Field(default=300, gt=0, description="Setup timeout in seconds")
    env: Dict[str, str] = Field(default_factory=dict)


# ============================================
# MAIN SCHEMA
# ============================================

class ProblemYAML(BaseModel):
    """
    Complete problem.yml schema
    Represents the on-disk format of a problem
    """
    # Metadata
    code: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9\-]+$')
    number: int = Field(..., ge=0, description="Problem number for ordering")
    version: int = Field(default=1, ge=1)
    created_at: date
    updated_at: date

    # Titles and descriptions
    title: BilingualText
    description: BilingualText = Field(..., description="Paths to description markdown files")

    # Editorial and reference files
    editorial: Optional[BilingualText] = Field(None, description="Paths to editorial markdown files")
    editorial_visibility: str = Field(default="always", description="When to show editorial: always, after_solve, after_attempts")
    test_generator: Optional[str] = Field(None, description="Path to test generator script (reference only)")
    official_solution: Optional[str] = Field(None, description="Path to official solution script (reference only)")

    # Tags
    tags: List[str] = Field(default_factory=list)

    # Authorship
    authors: List[str] = Field(default_factory=list, description="List of problem authors")
    author_note: Optional[str] = Field(None, description="Additional notes about authorship")

    # Classification
    tier: Literal["tier1", "tier2", "tier3"] = "tier1"
    categories: List[str] = Field(default_factory=list, min_length=1, description="Category codes")
    subcategories: List[str] = Field(default_factory=list, description="Subcategory codes")

    # Limits
    limits: ProblemLimits = Field(default_factory=ProblemLimits)
    language_limits: Dict[str, LanguageLimits] = Field(default_factory=dict)

    # Checker
    checker: CheckerConfig = Field(default_factory=CheckerConfig)

    # Scoring
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)

    # Test cases
    test_cases: TestCases = Field(default_factory=TestCases)

    # Batches (optional)
    batches: List[Batch] = Field(default_factory=list)

    # Docker config (for Tier 2/3)
    docker: Optional[DockerConfig] = None

    # Validators
    @field_validator('categories')
    @classmethod
    def validate_categories(cls, v):
        """Ensure at least one category"""
        if not v:
            raise ValueError("At least one category is required")
        return v

    @field_validator('docker')
    @classmethod
    def validate_docker_for_tier(cls, v, info):
        """Validate docker config for tier 2/3"""
        tier = info.data.get('tier')
        if tier in ['tier2', 'tier3'] and not v:
            raise ValueError(f"Docker config is required for {tier} problems")
        return v

    @field_validator('updated_at')
    @classmethod
    def validate_updated_at(cls, v, info):
        """Ensure updated_at >= created_at"""
        created_at = info.data.get('created_at')
        if created_at and v < created_at:
            raise ValueError("updated_at cannot be before created_at")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "code": "0-hello-satoshi",
                "number": 0,
                "version": 1,
                "created_at": "2024-12-25",
                "updated_at": "2024-12-25",
                "title": {
                    "en": "Hello Satoshi",
                    "es": "Hola Satoshi"
                },
                "description": {
                    "en": "descriptions/en.md",
                    "es": "descriptions/es.md"
                },
                "tags": ["bitcoin", "beginner", "string"],
                "tier": "tier1",
                "categories": ["algorithms"],
                "subcategories": ["basics"],
                "limits": {
                    "time": 2.0,
                    "memory": 256
                },
                "checker": {
                    "type": "standard"
                },
                "scoring": {
                    "initial_points": 10.0,
                    "partial": False,
                    "mode": "dynamic"
                },
                "test_cases": {
                    "samples": [
                        {
                            "input": "tests/samples/1.in",
                            "output": "tests/samples/1.out",
                            "points": 10
                        }
                    ]
                }
            }
        }
