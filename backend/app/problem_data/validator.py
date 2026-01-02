"""
Validators for problem packages
Validates structure, files, and data consistency
"""

import os
import yaml
from pathlib import Path
from typing import List, Tuple, Optional
from .schema import ProblemYAML


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class ProblemValidator:
    """Validates problem package structure and content"""

    REQUIRED_FILES = ['problem.yml']
    REQUIRED_DIRS = ['tests']
    MAX_FILE_SIZE_MB = 100  # Max size for individual test files
    MAX_PROBLEM_SIZE_MB = 500  # Max total problem size

    def __init__(self, problem_path: Path):
        """
        Initialize validator

        Args:
            problem_path: Path to problem directory
        """
        self.problem_path = Path(problem_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validations

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Check directory exists
        if not self.problem_path.exists():
            self.errors.append(f"Problem directory does not exist: {self.problem_path}")
            return False, self.errors, self.warnings

        if not self.problem_path.is_dir():
            self.errors.append(f"Path is not a directory: {self.problem_path}")
            return False, self.errors, self.warnings

        # Run validations
        self._validate_structure()
        self._validate_problem_yml()
        self._validate_test_files()
        self._validate_descriptions()
        self._validate_size()

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_structure(self):
        """Validate basic directory structure"""
        # Check required files
        for filename in self.REQUIRED_FILES:
            filepath = self.problem_path / filename
            if not filepath.exists():
                self.errors.append(f"Missing required file: {filename}")

        # Check required directories
        for dirname in self.REQUIRED_DIRS:
            dirpath = self.problem_path / dirname
            if not dirpath.exists():
                self.errors.append(f"Missing required directory: {dirname}")
            elif not dirpath.is_dir():
                self.errors.append(f"'{dirname}' exists but is not a directory")

    def _validate_problem_yml(self) -> Optional[ProblemYAML]:
        """Validate problem.yml file"""
        yml_path = self.problem_path / 'problem.yml'

        if not yml_path.exists():
            return None

        try:
            # Load YAML
            with open(yml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Validate with Pydantic
            problem = ProblemYAML(**data)

            # Additional validations
            self._validate_categories(problem)
            self._validate_test_case_paths(problem)

            return problem

        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML syntax in problem.yml: {e}")
            return None
        except Exception as e:
            self.errors.append(f"Error validating problem.yml: {e}")
            return None

    def _validate_categories(self, problem: ProblemYAML):
        """Validate that categories and subcategories exist in database"""
        # Note: This will be implemented when we have database access
        # For now, just validate the format

        valid_categories = {
            'algorithms', 'bitcoin-protocol', 'cryptography',
            'layer2-3', 'privacy-security'
        }

        for cat in problem.categories:
            if cat not in valid_categories:
                self.warnings.append(
                    f"Unknown category '{cat}'. Valid: {', '.join(valid_categories)}"
                )

    def _validate_test_case_paths(self, problem: ProblemYAML):
        """Validate that all test case files exist"""
        all_test_cases = (
            problem.test_cases.pretests +
            problem.test_cases.samples +
            problem.test_cases.hidden
        )

        for tc in all_test_cases:
            # Check input file
            input_path = self.problem_path / tc.input
            if not input_path.exists():
                self.errors.append(f"Test input file not found: {tc.input}")
            elif not input_path.is_file():
                self.errors.append(f"Test input path is not a file: {tc.input}")

            # Check output file
            output_path = self.problem_path / tc.output
            if not output_path.exists():
                self.errors.append(f"Test output file not found: {tc.output}")
            elif not output_path.is_file():
                self.errors.append(f"Test output path is not a file: {tc.output}")

            # Check file sizes
            if input_path.exists():
                size_mb = input_path.stat().st_size / (1024 * 1024)
                if size_mb > self.MAX_FILE_SIZE_MB:
                    self.errors.append(
                        f"Input file too large ({size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB): {tc.input}"
                    )

            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                if size_mb > self.MAX_FILE_SIZE_MB:
                    self.errors.append(
                        f"Output file too large ({size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB): {tc.output}"
                    )

    def _validate_descriptions(self):
        """Validate description files exist"""
        yml_path = self.problem_path / 'problem.yml'

        if not yml_path.exists():
            return

        try:
            with open(yml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            desc = data.get('description', {})

            # Check English description
            if 'en' in desc:
                desc_path = self.problem_path / desc['en']
                if not desc_path.exists():
                    self.errors.append(f"English description file not found: {desc['en']}")
                elif desc_path.stat().st_size == 0:
                    self.warnings.append(f"English description file is empty: {desc['en']}")

            # Check Spanish description
            if 'es' in desc:
                desc_path = self.problem_path / desc['es']
                if not desc_path.exists():
                    self.errors.append(f"Spanish description file not found: {desc['es']}")
                elif desc_path.stat().st_size == 0:
                    self.warnings.append(f"Spanish description file is empty: {desc['es']}")

        except Exception as e:
            self.errors.append(f"Error checking description files: {e}")

    def _validate_size(self):
        """Validate total problem size"""
        try:
            total_size = sum(
                f.stat().st_size
                for f in self.problem_path.rglob('*')
                if f.is_file()
            )

            size_mb = total_size / (1024 * 1024)

            if size_mb > self.MAX_PROBLEM_SIZE_MB:
                self.errors.append(
                    f"Problem package too large: {size_mb:.1f}MB (max: {self.MAX_PROBLEM_SIZE_MB}MB)"
                )
            elif size_mb > self.MAX_PROBLEM_SIZE_MB * 0.8:
                self.warnings.append(
                    f"Problem package is quite large: {size_mb:.1f}MB "
                    f"(close to limit of {self.MAX_PROBLEM_SIZE_MB}MB)"
                )

        except Exception as e:
            self.warnings.append(f"Could not calculate problem size: {e}")


def validate_problem_package(problem_path: Path) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate a problem package

    Args:
        problem_path: Path to problem directory

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = ProblemValidator(problem_path)
    return validator.validate()
