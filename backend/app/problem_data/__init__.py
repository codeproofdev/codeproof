"""
Problem Data Management Package

Provides file-based storage for problems following the DMOJ-inspired structure.
"""

from .manager import ProblemDataManager
from .schema import (
    ProblemYAML,
    BilingualText,
    ProblemLimits,
    LanguageLimits,
    CheckerConfig,
    ScoringConfig,
    TestCase,
    TestCases,
    Batch,
    DockerConfig,
)
from .validator import ProblemValidator, validate_problem_package, ValidationError

__all__ = [
    # Manager
    'ProblemDataManager',

    # Schemas
    'ProblemYAML',
    'BilingualText',
    'ProblemLimits',
    'LanguageLimits',
    'CheckerConfig',
    'ScoringConfig',
    'TestCase',
    'TestCases',
    'Batch',
    'DockerConfig',

    # Validators
    'ProblemValidator',
    'validate_problem_package',
    'ValidationError',
]
