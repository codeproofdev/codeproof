"""
ProblemDataManager: Manages file-based problem storage
Handles reading, writing, and managing problem packages
"""

import os
import shutil
import yaml
import zipfile
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import date

from .schema import ProblemYAML, TestCases, TestCase
from .validator import ProblemValidator, validate_problem_package
from app.config import settings


class ProblemDataManager:
    """
    Manages file-based problem storage

    Responsibilities:
    - Load/save problem.yml
    - Read test case files
    - Create/extract problem packages (ZIP)
    - Validate problem structure
    """

    def __init__(self, problem_root: Optional[Path] = None):
        """
        Initialize manager

        Args:
            problem_root: Root directory for problems (defaults to PROBLEM_DATA_ROOT)
        """
        self.problem_root = Path(problem_root or settings.PROBLEM_DATA_ROOT)
        self.problem_root.mkdir(parents=True, exist_ok=True)

    def get_problem_path(self, problem_code: str) -> Path:
        """Get absolute path to problem directory"""
        return self.problem_root / problem_code

    def problem_exists(self, problem_code: str) -> bool:
        """Check if problem exists on disk"""
        problem_path = self.get_problem_path(problem_code)
        return problem_path.exists() and (problem_path / 'problem.yml').exists()

    def load_problem_yml(self, problem_code: str) -> ProblemYAML:
        """
        Load and parse problem.yml

        Args:
            problem_code: Problem code (directory name)

        Returns:
            ProblemYAML object

        Raises:
            FileNotFoundError: If problem.yml doesn't exist
            ValueError: If YAML is invalid
        """
        problem_path = self.get_problem_path(problem_code)
        yml_path = problem_path / 'problem.yml'

        if not yml_path.exists():
            raise FileNotFoundError(f"problem.yml not found: {yml_path}")

        with open(yml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return ProblemYAML(**data)

    def save_problem_yml(self, problem_code: str, problem: ProblemYAML):
        """
        Save problem.yml to disk

        Args:
            problem_code: Problem code (directory name)
            problem: ProblemYAML object
        """
        problem_path = self.get_problem_path(problem_code)
        problem_path.mkdir(parents=True, exist_ok=True)

        yml_path = problem_path / 'problem.yml'

        # Convert to dict and save as YAML
        data = problem.model_dump(mode='json')

        with open(yml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def read_test_case(self, problem_code: str, test_path: str) -> str:
        """
        Read test case file content

        Args:
            problem_code: Problem code
            test_path: Relative path to test file

        Returns:
            File content as string
        """
        problem_path = self.get_problem_path(problem_code)
        full_path = problem_path / test_path

        if not full_path.exists():
            raise FileNotFoundError(f"Test file not found: {test_path}")

        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_test_case(self, problem_code: str, test_path: str, content: str):
        """
        Write test case file

        Args:
            problem_code: Problem code
            test_path: Relative path to test file
            content: File content
        """
        problem_path = self.get_problem_path(problem_code)
        full_path = problem_path / test_path

        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def read_description(self, problem_code: str, language: str = 'en') -> str:
        """
        Read problem description

        Args:
            problem_code: Problem code
            language: Language code ('en' or 'es')

        Returns:
            Description markdown content
        """
        problem = self.load_problem_yml(problem_code)
        desc_path = getattr(problem.description, language)

        return self.read_test_case(problem_code, desc_path)

    def read_editorial(self, problem_code: str, language: str = 'en') -> Optional[str]:
        """
        Read problem editorial

        Args:
            problem_code: Problem code
            language: Language code ('en' or 'es')

        Returns:
            Editorial markdown content or None if not available
        """
        problem = self.load_problem_yml(problem_code)

        if not problem.editorial:
            return None

        editorial_path = getattr(problem.editorial, language, None)
        if not editorial_path:
            return None

        try:
            return self.read_test_case(problem_code, editorial_path)
        except FileNotFoundError:
            return None

    def read_reference_file(self, problem_code: str, file_type: str) -> Optional[str]:
        """
        Read reference files (test_generator, official_solution)

        Args:
            problem_code: Problem code
            file_type: Type of file ('test_generator' or 'official_solution')

        Returns:
            File content or None if not available
        """
        # Load raw YAML to handle the reference structure
        problem_path = self.get_problem_path(problem_code)
        yml_path = problem_path / 'problem.yml'

        if not yml_path.exists():
            return None

        with open(yml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Try the new nested structure first (reference.generator/solution)
        if 'reference' in data:
            reference = data['reference']

            # Map file_type to the reference key
            ref_key = None
            if file_type == 'test_generator':
                ref_key = 'generator'
            elif file_type == 'official_solution':
                ref_key = 'solution'

            if ref_key and ref_key in reference:
                # Reference is a list of file entries
                entries = reference[ref_key]
                if isinstance(entries, list) and len(entries) > 0:
                    # Take the first entry
                    file_path = entries[0].get('file')
                    if file_path:
                        try:
                            return self.read_test_case(problem_code, file_path)
                        except FileNotFoundError:
                            return None

        # Try the old simple format as fallback
        if file_type in data:
            file_path = data[file_type]
            if file_path:
                try:
                    return self.read_test_case(problem_code, file_path)
                except FileNotFoundError:
                    return None

        return None

    def create_from_zip(self, zip_path: Path, problem_code: Optional[str] = None) -> str:
        """
        Extract problem from ZIP file

        Args:
            zip_path: Path to ZIP file
            problem_code: Optional problem code (extracted from ZIP if not provided)

        Returns:
            Problem code

        Raises:
            ValueError: If ZIP is invalid or problem already exists
        """
        # Extract to temporary directory first
        temp_dir = self.problem_root / '.temp' / zip_path.stem
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)

            # Find problem.yml (might be in subdirectory)
            yml_files = list(temp_dir.rglob('problem.yml'))

            if not yml_files:
                raise ValueError("No problem.yml found in ZIP")

            if len(yml_files) > 1:
                raise ValueError("Multiple problem.yml files found in ZIP")

            problem_dir = yml_files[0].parent

            # Load and validate
            with open(yml_files[0], 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            problem = ProblemYAML(**data)

            # Use provided code or from YAML
            final_code = problem_code or problem.code

            # Check if already exists
            if self.problem_exists(final_code):
                raise ValueError(f"Problem already exists: {final_code}")

            # Validate
            is_valid, errors, warnings = validate_problem_package(problem_dir)

            if not is_valid:
                raise ValueError(f"Invalid problem package: {', '.join(errors)}")

            # Move to final location
            final_path = self.get_problem_path(final_code)
            if final_path.exists():
                shutil.rmtree(final_path)

            shutil.move(str(problem_dir), str(final_path))

            return final_code

        finally:
            # Cleanup temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir.parent)

    def export_to_zip(self, problem_code: str, output_path: Path):
        """
        Export problem to ZIP file

        Args:
            problem_code: Problem code
            output_path: Output ZIP file path
        """
        problem_path = self.get_problem_path(problem_code)

        if not problem_path.exists():
            raise FileNotFoundError(f"Problem not found: {problem_code}")

        # Create ZIP
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in problem_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(problem_path.parent)
                    zf.write(file_path, arcname)

    def validate_problem(self, problem_code: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate problem package

        Args:
            problem_code: Problem code

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        problem_path = self.get_problem_path(problem_code)
        return validate_problem_package(problem_path)

    def delete_problem(self, problem_code: str):
        """
        Delete problem from disk

        Args:
            problem_code: Problem code
        """
        problem_path = self.get_problem_path(problem_code)

        if problem_path.exists():
            shutil.rmtree(problem_path)

    def list_problems(self) -> List[str]:
        """
        List all problems on disk

        Returns:
            List of problem codes
        """
        if not self.problem_root.exists():
            return []

        problems = []
        for item in self.problem_root.iterdir():
            if item.is_dir() and (item / 'problem.yml').exists():
                problems.append(item.name)

        return sorted(problems)

    def get_problem_size(self, problem_code: str) -> int:
        """
        Calculate total size of problem package in bytes

        Args:
            problem_code: Problem code

        Returns:
            Total size in bytes
        """
        problem_path = self.get_problem_path(problem_code)

        if not problem_path.exists():
            return 0

        total_size = sum(
            f.stat().st_size
            for f in problem_path.rglob('*')
            if f.is_file()
        )

        return total_size

    def update_testcases_from_zip(self, problem_code: str, zip_path: Path):
        """
        Update test cases from a ZIP file

        Args:
            problem_code: Problem code
            zip_path: Path to ZIP file containing test cases

        Raises:
            ValueError: If problem doesn't exist or ZIP is invalid
        """
        problem_path = self.get_problem_path(problem_code)

        if not problem_path.exists():
            raise ValueError(f"Problem not found: {problem_code}")

        # Extract to temporary directory
        temp_dir = self.problem_root / '.temp' / f"{problem_code}_testcases"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)

            # Find tests directory (might be in subdirectory)
            tests_dirs = list(temp_dir.rglob('tests'))

            if not tests_dirs:
                # Check if files are directly in temp_dir
                if any(temp_dir.rglob('*.in')) or any(temp_dir.rglob('*.out')):
                    tests_source = temp_dir
                else:
                    raise ValueError("No tests directory or test files found in ZIP")
            else:
                tests_source = tests_dirs[0]

            # Remove existing tests directory
            tests_dest = problem_path / 'tests'
            if tests_dest.exists():
                shutil.rmtree(tests_dest)

            # Copy new tests
            if tests_source == temp_dir:
                # Files are at root, create tests dir and copy
                tests_dest.mkdir(parents=True, exist_ok=True)
                for item in temp_dir.iterdir():
                    if item.is_file() and (item.suffix in ['.in', '.out']):
                        shutil.copy2(item, tests_dest)
                    elif item.is_dir() and item.name in ['samples', 'hidden', 'pretests']:
                        shutil.copytree(item, tests_dest / item.name)
            else:
                # Copy entire tests directory
                shutil.copytree(tests_source, tests_dest)

            # Update problem.yml timestamps
            problem = self.load_problem_yml(problem_code)
            problem.updated_at = date.today()
            self.save_problem_yml(problem_code, problem)

        finally:
            # Cleanup temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
