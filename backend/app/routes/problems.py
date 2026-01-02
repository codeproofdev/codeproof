"""
Problems routes
Handles problem CRUD operations, approval workflow, and test cases
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from pathlib import Path
import tempfile
import shutil
import logging
from datetime import datetime

from app.database import get_db
from app.models import Problem, TestCase, User, ProblemStatus, UserRole, Category, Subcategory, UserProblemSolve

logger = logging.getLogger(__name__)
from app.schemas import (
    ProblemCreate,
    ProblemUpdate,
    ProblemOut,
    ProblemDetail,
    ProblemListItem,
    MessageResponse,
    ProblemPackageInfo
)
from app.auth import (
    get_current_user,
    get_optional_user,
    require_admin,
    require_problemsetter
)
from app.problem_data.manager import ProblemDataManager
from app.problem_data.schema import ProblemYAML
from app.config import settings

router = APIRouter()


@router.get("", response_model=List[ProblemListItem])
async def list_problems(
    tier: Optional[str] = Query(None, description="Filter by tier (tier1, tier2, tier3)"),
    status: Optional[str] = Query(None, description="Filter by status (only for admin/problemsetter)"),
    limit: int = Query(50, ge=1, le=100, description="Number of problems to return"),
    offset: int = Query(0, ge=0, description="Number of problems to skip"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all approved problems (public endpoint)

    **Query Parameters:**
    - tier: Filter by problem tier (tier1, tier2, tier3)
    - status: Filter by status - only works for admin/problemsetter (pending, approved, rejected)
    - limit: Number of results (1-100, default 50)
    - offset: Pagination offset (default 0)

    **Returns:**
    - List of problems with basic information

    **Note:**
    - Regular users only see approved problems
    - Admins/problemsetters can filter by status to see pending/rejected problems
    """
    # Build query with eager loading of categories and subcategories
    from sqlalchemy.orm import selectinload
    query = select(Problem).options(
        selectinload(Problem.categories),
        selectinload(Problem.subcategories)
    )

    # Apply filters
    filters = []

    # Status filter logic:
    # - Admins: see all problems (or filter by status if provided)
    # - Problemsetters: see approved problems + their own problems (any status)
    # - Regular users: only see approved problems
    if status:
        # Explicit status filter (only for admin/problemsetter)
        if current_user and current_user.role in [UserRole.ADMIN, UserRole.PROBLEMSETTER]:
            filters.append(Problem.status == status)
        else:
            # Regular users only see approved problems
            filters.append(Problem.status == ProblemStatus.APPROVED)
    else:
        # No status filter specified
        if current_user and current_user.role == UserRole.ADMIN:
            # Admins see all problems
            pass  # No status filter
        elif current_user and current_user.role == UserRole.PROBLEMSETTER:
            # Problemsetters see: approved problems OR their own problems (any status)
            filters.append(
                or_(
                    Problem.status == ProblemStatus.APPROVED,
                    Problem.created_by == current_user.id
                )
            )
        else:
            # Regular users only see approved problems
            filters.append(Problem.status == ProblemStatus.APPROVED)

    # Tier filter
    if tier:
        filters.append(Problem.tier == tier)

    # Apply all filters
    if filters:
        query = query.where(and_(*filters))

    # Order by current_points descending (harder problems first)
    query = query.order_by(Problem.current_points.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    problems = result.scalars().all()

    return problems


@router.get("/{problem_id}", response_model=ProblemDetail)
async def get_problem(
    problem_id: int,
    current_user: Optional[User] = Depends(get_optional_user),  # Optional - public endpoint
    db: AsyncSession = Depends(get_db)
):
    """
    Get problem details by ID

    **Path Parameters:**
    - problem_id: Problem ID

    **Returns:**
    - Problem with full details including sample test cases

    **Errors:**
    - 404: Problem not found
    - 403: Problem not approved (unless admin/problemsetter)

    **Note:**
    - Sample test cases (is_sample=true) are included
    - Hidden test cases are never exposed via API
    - Regular users can only view approved problems
    """
    # Fetch problem with eager loading for categories and subcategories
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Problem)
        .options(selectinload(Problem.categories))
        .options(selectinload(Problem.subcategories))
        .where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem #{problem_id} not found"
        )

    # Check if user can access this problem
    if problem.status != ProblemStatus.APPROVED:
        # Only admin/problemsetter can view non-approved problems
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.PROBLEMSETTER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This problem is not approved yet"
            )

    # Fetch test cases
    # - Admins and problem creators: see ALL test cases (sample + hidden)
    # - Other users: only see sample test cases
    if current_user and (current_user.role == UserRole.ADMIN or problem.created_by == current_user.id):
        # Show all test cases for creator/admin
        result = await db.execute(
            select(TestCase)
            .where(TestCase.problem_id == problem_id)
            .order_by(TestCase.case_number)
        )
        all_test_cases = result.scalars().all()
    else:
        # Show only sample test cases for regular users
        result = await db.execute(
            select(TestCase)
            .where(
                and_(
                    TestCase.problem_id == problem_id,
                    TestCase.is_sample == True
                )
            )
            .order_by(TestCase.case_number)
        )
        all_test_cases = result.scalars().all()

    # For file-based problems, load test case content from filesystem
    test_cases_with_content = []
    if problem.file_based and problem.data_path:
        from app.config import settings
        problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path

        logger.info(f"Loading test cases for problem {problem_id}, total test cases: {len(all_test_cases)}")

        for tc in all_test_cases:
            try:
                input_path = problem_dir / tc.input_file
                output_path = problem_dir / tc.output_file

                logger.info(f"Reading test case {tc.case_number}: {tc.input_file} (sample={tc.is_sample})")

                # Read actual file content
                input_content = input_path.read_text(encoding='utf-8') if input_path.exists() else tc.input_file
                output_content = output_path.read_text(encoding='utf-8') if output_path.exists() else tc.output_file

                # Create a TestCaseOut object with content
                from app.schemas import TestCaseOut
                tc_with_content = TestCaseOut(
                    id=tc.id,
                    problem_id=tc.problem_id,
                    case_number=tc.case_number,
                    input_file=input_content,  # Content, not path
                    output_file=output_content,  # Content, not path
                    is_sample=tc.is_sample,
                    points=tc.points,
                    time_limit_override=tc.time_limit_override,
                    memory_limit_override=tc.memory_limit_override
                )
                test_cases_with_content.append(tc_with_content)
                logger.info(f"✅ Loaded test case {tc.case_number}")
            except Exception as e:
                logger.error(f"❌ Failed to read test case {tc.id} content: {e}")
                # Fallback to original object
                test_cases_with_content.append(tc)
    else:
        # Legacy: content is already in database
        test_cases_with_content = all_test_cases

    logger.info(f"Returning {len(test_cases_with_content)} test cases for problem {problem_id}")

    # For file-based problems, load description content from filesystem
    description_en = problem.description_en
    description_es = problem.description_es

    if problem.file_based and problem.data_path:
        from app.config import settings
        problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path

        # Try to read description files
        if description_en.startswith("See file:"):
            desc_en_file = description_en.replace("See file: ", "").strip()
            desc_en_path = problem_dir / desc_en_file
            if desc_en_path.exists():
                try:
                    description_en = desc_en_path.read_text(encoding='utf-8')
                except Exception as e:
                    logger.warning(f"Failed to read {desc_en_file}: {e}")

        if description_es.startswith("See file:"):
            desc_es_file = description_es.replace("See file: ", "").strip()
            desc_es_path = problem_dir / desc_es_file
            if desc_es_path.exists():
                try:
                    description_es = desc_es_path.read_text(encoding='utf-8')
                except Exception as e:
                    logger.warning(f"Failed to read {desc_es_file}: {e}")

    # Check if editorial exists and get visibility setting
    has_editorial = False
    editorial_visibility = 'always'

    if problem.file_based and problem.data_path:
        # Load problem.yml to check for editorial
        manager = ProblemDataManager(settings.PROBLEM_DATA_ROOT)
        try:
            problem_yml = manager.load_problem_yml(problem.data_path)
            has_editorial = problem_yml.editorial is not None
            editorial_visibility = getattr(problem_yml, 'editorial_visibility', 'always')
        except Exception as e:
            logger.warning(f"Could not load problem.yml for editorial check: {e}")

    # Create response with test cases
    # Note: ProblemDetail expects full Category/Subcategory objects, not just codes
    problem_dict = {
        "id": problem.id,
        "title_en": problem.title_en,
        "title_es": problem.title_es,
        "description_en": description_en,  # Actual markdown content
        "description_es": description_es,  # Actual markdown content
        "tier": problem.tier,
        "time_limit": problem.time_limit,
        "memory_limit": problem.memory_limit,
        "partial": problem.partial,
        "authors": problem.authors,
        "author_note": problem.author_note,
        "status": problem.status,
        "current_points": problem.current_points,
        "solved_count": problem.solved_count,
        "created_by": problem.created_by,
        "created_at": problem.created_at,
        "updated_at": problem.updated_at,
        "tags": problem.tags,
        "test_cases": test_cases_with_content,  # With content loaded
        "categories": problem.categories,  # Full objects for ProblemDetail
        "subcategories": problem.subcategories,  # Full objects for ProblemDetail
        "has_editorial": has_editorial,
        "editorial_visibility": editorial_visibility
    }

    return problem_dict


@router.get("/{problem_id}/editorial")
async def get_problem_editorial(
    problem_id: int,
    language: str = Query("en", regex="^(en|es)$", description="Language code (en or es)"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get problem editorial if available

    **Path Parameters:**
    - problem_id: Problem ID

    **Query Parameters:**
    - language: Language code (en or es) - default: en

    **Returns:**
    - Editorial content as markdown string

    **Errors:**
    - 404: Problem not found or editorial not available
    - 403: Problem not approved (unless admin/problemsetter)

    **Note:**
    - Editorial availability depends on problem.yml configuration
    - Returns raw markdown content for rendering on frontend
    """
    # Fetch problem
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check if user can access this problem
    if problem.status != ProblemStatus.APPROVED:
        # Only admin/problemsetter can view non-approved problems
        if not current_user or current_user.role not in [UserRole.ADMIN, UserRole.PROBLEMSETTER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This problem is not approved yet"
            )

    # Check if problem is file-based
    if not problem.file_based or not problem.data_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Editorial not available for this problem"
        )

    # Load editorial using manager
    manager = ProblemDataManager(settings.PROBLEM_DATA_ROOT)

    try:
        editorial_content = manager.read_editorial(problem.data_path, language)

        if editorial_content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Editorial not available in {language}"
            )

        # Return as plain text (markdown content)
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=editorial_content, media_type="text/markdown")

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Editorial file not found"
        )
    except Exception as e:
        logger.error(f"Error reading editorial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load editorial"
        )


@router.get("/{problem_id}/reference/{file_type}")
async def get_problem_reference_file(
    problem_id: int,
    file_type: str,
    current_user: User = Depends(require_problemsetter),
    db: AsyncSession = Depends(get_db)
):
    """
    Get problem reference files (test_generator or official_solution)

    **Requires authentication** (Bearer token)
    **Required role:** Problemsetter or Admin

    **Path Parameters:**
    - problem_id: Problem ID
    - file_type: Type of file (test_generator or official_solution)

    **Returns:**
    - File content as plain text

    **Errors:**
    - 404: Problem not found or file not available
    - 403: Not the problem creator (unless admin)

    **Note:**
    - Reference files are only accessible by problem creator or admin
    - These files are for reference only and not executed on the platform
    """
    # Fetch problem
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check permissions - only creator or admin
    if current_user.role != UserRole.ADMIN and problem.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own problem files"
        )

    # Check if problem is file-based
    if not problem.file_based or not problem.data_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reference files not available for this problem"
        )

    # Load reference file using manager
    manager = ProblemDataManager(settings.PROBLEM_DATA_ROOT)

    try:
        file_content = manager.read_reference_file(problem.data_path, file_type)

        if file_content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{file_type} not available"
            )

        # Return as plain text
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=file_content, media_type="text/plain")

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{file_type} file not found"
        )
    except Exception as e:
        logger.error(f"Error reading {file_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load {file_type}"
        )


@router.post("", response_model=ProblemOut, status_code=status.HTTP_201_CREATED)
async def create_problem(
    problem_data: ProblemCreate,
    current_user: User = Depends(require_problemsetter),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new problem as file-based (requires problemsetter or admin role)

    **Requires authentication** (Bearer token)
    **Required role:** Problemsetter or Admin

    **Request body:**
    - title_en/title_es: Problem titles (bilingual)
    - description_en/description_es: Problem descriptions (markdown)
    - tier: Problem tier (tier1, tier2, tier3) - default tier1
    - time_limit: Time limit in seconds - default 2s
    - memory_limit: Memory limit in MB - default 256MB
    - authors: List of author names - default []
    - author_note: Optional author notes
    - categories/subcategories: Category and subcategory codes
    - sample_tests/hidden_tests: Test cases

    **Returns:**
    - Created file-based problem with PENDING status

    **Errors:**
    - 401: Not authenticated
    - 403: Insufficient permissions (not problemsetter/admin)

    **Note:**
    - All problems are created as file-based (stored on disk)
    - Problems are created with status=PENDING
    - Require admin approval before being visible to users
    """
    # Import required modules
    from app.problem_data.manager import ProblemDataManager
    from app.config import settings
    import yaml
    import re

    # Initialize problem manager
    manager = ProblemDataManager(settings.PROBLEM_DATA_ROOT)

    # First, create the database record to get the problem ID
    new_problem = Problem(
        file_based=True,
        data_path="",  # Will be updated after we know the ID
        title_en=problem_data.title_en,
        title_es=problem_data.title_es,
        description_en=f"See file: descriptions/en.md",
        description_es=f"See file: descriptions/es.md",
        tier=problem_data.tier,
        time_limit=problem_data.time_limit,
        memory_limit=problem_data.memory_limit,
        partial=problem_data.partial,
        authors=problem_data.authors or [],
        author_note=problem_data.author_note,
        status=ProblemStatus.PENDING,
        created_by=current_user.id,
        current_points=10.0,
        initial_points=10.0
    )

    db.add(new_problem)
    await db.flush()  # Get problem ID

    # Simple assignment: number = id (no gap filling)
    problem_slug = re.sub(r'[^a-z0-9]+', '-', problem_data.title_en.lower()).strip('-')
    problem_code = f"{new_problem.id}-{problem_slug}"

    new_problem.data_path = problem_code
    new_problem.number = new_problem.id

    logger.info(f"Created problem #{new_problem.number} (ID: {new_problem.id}) - '{problem_data.title_en}'")

    # Create directory structure
    problem_path = manager.problem_root / problem_code
    problem_path.mkdir(parents=True, exist_ok=True)
    (problem_path / "descriptions").mkdir(exist_ok=True)
    (problem_path / "tests" / "samples").mkdir(parents=True, exist_ok=True)
    (problem_path / "tests" / "hidden").mkdir(parents=True, exist_ok=True)

    # Save descriptions to .md files
    desc_en_path = problem_path / "descriptions" / "en.md"
    desc_es_path = problem_path / "descriptions" / "es.md"
    desc_en_path.write_text(problem_data.description_en, encoding='utf-8')
    desc_es_path.write_text(problem_data.description_es, encoding='utf-8')

    # Save test cases to disk
    sample_count = 0
    hidden_count = 0

    if problem_data.sample_tests:
        for idx, test_data in enumerate(problem_data.sample_tests, 1):
            input_path = problem_path / "tests" / "samples" / f"{idx}.in"
            output_path = problem_path / "tests" / "samples" / f"{idx}.out"
            input_path.write_text(test_data.get('input', ''), encoding='utf-8')
            output_path.write_text(test_data.get('expected_output', ''), encoding='utf-8')
            sample_count += 1

    if problem_data.hidden_tests:
        for idx, test_data in enumerate(problem_data.hidden_tests, 1):
            input_path = problem_path / "tests" / "hidden" / f"{idx}.in"
            output_path = problem_path / "tests" / "hidden" / f"{idx}.out"
            input_path.write_text(test_data.get('input', ''), encoding='utf-8')
            output_path.write_text(test_data.get('expected_output', ''), encoding='utf-8')
            hidden_count += 1

    # Generate problem.yml with complete structure
    from datetime import date

    # Build test_cases section
    test_cases_yml = {
        'pretests': [],
        'samples': [],
        'hidden': []
    }

    # Add sample tests
    if problem_data.sample_tests:
        for idx in range(1, len(problem_data.sample_tests) + 1):
            test_cases_yml['samples'].append({
                'input': f'tests/samples/{idx}.in',
                'output': f'tests/samples/{idx}.out',
                'points': 10.0,
                'description': None,
                'time_limit': None,
                'memory_limit': None
            })

    # Add hidden tests
    if problem_data.hidden_tests:
        for idx in range(1, len(problem_data.hidden_tests) + 1):
            test_cases_yml['hidden'].append({
                'input': f'tests/hidden/{idx}.in',
                'output': f'tests/hidden/{idx}.out',
                'points': 0.0,
                'description': None,
                'time_limit': None,
                'memory_limit': None
            })

    problem_yml = {
        'code': problem_code,
        'number': 0,  # Will be assigned after DB insertion
        'version': 1,
        'created_at': str(date.today()),
        'updated_at': str(date.today()),
        'title': {
            'en': problem_data.title_en,
            'es': problem_data.title_es
        },
        'description': {
            'en': 'descriptions/en.md',
            'es': 'descriptions/es.md'
        },
        'authors': problem_data.authors or [],
        'author_note': problem_data.author_note,
        'tags': [],
        'difficulty': 'medium',  # Default, can be calculated based on tier
        'tier': problem_data.tier.value,
        'categories': problem_data.categories or [],
        'subcategories': problem_data.subcategories or [],
        'limits': {
            'time': float(problem_data.time_limit),
            'memory': problem_data.memory_limit,
            'output': 65536,
            'output_prefix': 4096,
            'source_code': 50
        },
        'language_limits': {},
        'checker': {
            'type': 'standard',
            'executable': None,
            'args': {}
        },
        'scoring': {
            'initial_points': 10.0,
            'partial': problem_data.partial,
            'mode': 'dynamic'
        },
        'test_cases': test_cases_yml,
        'batches': [],
        'docker': None
    }

    # Save problem.yml (number already set correctly from new_problem.id)
    yml_path = problem_path / "problem.yml"
    problem_yml['number'] = new_problem.id
    with open(yml_path, 'w', encoding='utf-8') as f:
        yaml.dump(problem_yml, f, default_flow_style=False, allow_unicode=True)

    # Associate categories using direct inserts into junction table
    from app.models import problem_categories, problem_subcategories
    for cat_code in problem_data.categories:
        result = await db.execute(
            select(Category).where(Category.code == cat_code)
        )
        category = result.scalar_one_or_none()
        if category:
            await db.execute(
                problem_categories.insert().values(
                    problem_id=new_problem.id,
                    category_id=category.id,
                    is_primary=False
                )
            )

    # Associate subcategories
    for subcat_code in problem_data.subcategories:
        result = await db.execute(
            select(Subcategory).where(Subcategory.code == subcat_code)
        )
        subcategory = result.scalar_one_or_none()
        if subcategory:
            await db.execute(
                problem_subcategories.insert().values(
                    problem_id=new_problem.id,
                    subcategory_id=subcategory.id,
                    is_primary=False
                )
            )

    # Add test cases to database
    case_number = 1

    logger.info(f"📝 Adding test cases for problem {new_problem.id}")
    logger.info(f"  Samples: {len(problem_data.sample_tests or [])}")
    logger.info(f"  Hidden: {len(problem_data.hidden_tests or [])}")

    # Add sample test cases
    if problem_data.sample_tests:
        for idx in range(1, len(problem_data.sample_tests) + 1):
            test_case = TestCase(
                problem_id=new_problem.id,
                case_number=case_number,
                batch_number=None,
                input_file=f'tests/samples/{idx}.in',
                output_file=f'tests/samples/{idx}.out',
                is_sample=True,
                points=10.0,
                time_limit_override=None,
                memory_limit_override=None
            )
            db.add(test_case)
            case_number += 1
            logger.info(f"  ✅ Added sample test case {idx}")

    # Add hidden test cases
    if problem_data.hidden_tests:
        for idx in range(1, len(problem_data.hidden_tests) + 1):
            test_case = TestCase(
                problem_id=new_problem.id,
                case_number=case_number,
                batch_number=None,
                input_file=f'tests/hidden/{idx}.in',
                output_file=f'tests/hidden/{idx}.out',
                is_sample=False,
                points=0.0,
                time_limit_override=None,
                memory_limit_override=None
            )
            db.add(test_case)
            case_number += 1
            logger.info(f"  ✅ Added hidden test case {idx}")

    logger.info(f"✅ Total test cases added: {case_number - 1}")

    await db.commit()

    # Reload with eager loading to avoid serialization issues
    result = await db.execute(
        select(Problem).where(Problem.id == new_problem.id)
    )
    problem = result.scalar_one()

    return problem


@router.put("/{problem_id}", response_model=ProblemOut)
async def update_problem(
    problem_id: int,
    problem_data: ProblemUpdate,
    current_user: User = Depends(require_problemsetter),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a problem (requires problemsetter or admin role)

    **Requires authentication** (Bearer token)
    **Required role:** Problemsetter or Admin

    **Path Parameters:**
    - problem_id: Problem ID to update

    **Request body:** (all fields optional)
    - title_en/title_es: Update titles
    - description_en/description_es: Update descriptions
    - time_limit: Update time limit
    - memory_limit: Update memory limit
    - sample_tests/hidden_tests: Update test cases

    **Returns:**
    - Updated problem

    **Errors:**
    - 404: Problem not found
    - 403: Not the problem creator (unless admin)

    **Note:**
    - Problemsetters can only edit their own problems
    - Admins can edit any problem
    - Updating a problem does not change its approval status
    """
    # Fetch problem
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check permissions
    if current_user.role != UserRole.ADMIN and problem.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own problems"
        )

    # Update fields (exclude test cases and categories for now)
    update_data = problem_data.model_dump(exclude_unset=True)
    sample_tests = update_data.pop('sample_tests', None)
    hidden_tests = update_data.pop('hidden_tests', None)
    categories = update_data.pop('categories', None)
    subcategories = update_data.pop('subcategories', None)

    # Update simple fields
    for field, value in update_data.items():
        setattr(problem, field, value)

    # Update categories if provided
    if categories is not None:
        # Delete existing category associations
        from sqlalchemy import delete
        from app.models import problem_categories, Category

        await db.execute(
            delete(problem_categories).where(problem_categories.c.problem_id == problem_id)
        )
        await db.flush()

        # Add new category associations
        for cat_code in categories:
            result = await db.execute(
                select(Category).where(Category.code == cat_code)
            )
            category = result.scalar_one_or_none()
            if category:
                await db.execute(
                    problem_categories.insert().values(
                        problem_id=problem_id,
                        category_id=category.id,
                        is_primary=False
                    )
                )

    # Update subcategories if provided
    if subcategories is not None:
        # Delete existing subcategory associations
        from app.models import problem_subcategories, Subcategory

        await db.execute(
            delete(problem_subcategories).where(problem_subcategories.c.problem_id == problem_id)
        )
        await db.flush()

        # Add new subcategory associations
        for subcat_code in subcategories:
            result = await db.execute(
                select(Subcategory).where(Subcategory.code == subcat_code)
            )
            subcategory = result.scalar_one_or_none()
            if subcategory:
                await db.execute(
                    problem_subcategories.insert().values(
                        problem_id=problem_id,
                        subcategory_id=subcategory.id,
                        is_primary=False
                    )
                )

    # Update file-based problem files (descriptions and problem.yml)
    if problem.file_based and problem.data_path:
        from app.config import settings
        import yaml
        from datetime import date

        problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path

        # Update description files if they were changed
        if 'description_en' in update_data:
            desc_en_path = problem_dir / "descriptions" / "en.md"
            desc_en_path.parent.mkdir(parents=True, exist_ok=True)
            desc_en_path.write_text(update_data['description_en'], encoding='utf-8')
            logger.info(f"Updated description_en file for problem {problem_id}")

        if 'description_es' in update_data:
            desc_es_path = problem_dir / "descriptions" / "es.md"
            desc_es_path.parent.mkdir(parents=True, exist_ok=True)
            desc_es_path.write_text(update_data['description_es'], encoding='utf-8')
            logger.info(f"Updated description_es file for problem {problem_id}")

        # Update problem.yml with all changes
        yml_path = problem_dir / "problem.yml"
        if yml_path.exists():
            with open(yml_path, 'r', encoding='utf-8') as f:
                problem_yml = yaml.safe_load(f)

            # Update titles
            if 'title_en' in update_data or 'title_es' in update_data:
                if 'title_en' in update_data:
                    problem_yml['title']['en'] = update_data['title_en']
                if 'title_es' in update_data:
                    problem_yml['title']['es'] = update_data['title_es']
                logger.info(f"Updated titles in problem.yml for problem {problem_id}")

            # Update limits
            if 'time_limit' in update_data:
                problem_yml['limits']['time'] = float(update_data['time_limit'])
                logger.info(f"Updated time_limit in problem.yml for problem {problem_id}")

            if 'memory_limit' in update_data:
                problem_yml['limits']['memory'] = update_data['memory_limit']
                logger.info(f"Updated memory_limit in problem.yml for problem {problem_id}")

            # Update authors
            if 'authors' in update_data:
                problem_yml['authors'] = update_data['authors']
                logger.info(f"Updated authors in problem.yml for problem {problem_id}")

            if 'author_note' in update_data:
                problem_yml['author_note'] = update_data['author_note']
                logger.info(f"Updated author_note in problem.yml for problem {problem_id}")

            # Update partial scoring
            if 'partial' in update_data:
                problem_yml['scoring']['partial'] = update_data['partial']
                logger.info(f"Updated partial scoring in problem.yml for problem {problem_id}")

            # Update editorial visibility
            if 'editorial_visibility' in update_data:
                problem_yml['editorial_visibility'] = update_data['editorial_visibility']
                logger.info(f"Updated editorial_visibility in problem.yml for problem {problem_id}")

            # Update categories
            if categories is not None:
                problem_yml['categories'] = categories
                logger.info(f"Updated categories in problem.yml for problem {problem_id}")

            # Update subcategories
            if subcategories is not None:
                problem_yml['subcategories'] = subcategories
                logger.info(f"Updated subcategories in problem.yml for problem {problem_id}")

            # Update updated_at timestamp
            problem_yml['updated_at'] = str(date.today())

            # Write updated problem.yml
            with open(yml_path, 'w', encoding='utf-8') as f:
                yaml.dump(problem_yml, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            logger.info(f"Successfully updated problem.yml for problem {problem_id}")

    # Update test cases if provided
    if sample_tests is not None or hidden_tests is not None:
        # Delete existing test cases from database
        from sqlalchemy import delete
        await db.execute(
            delete(TestCase).where(TestCase.problem_id == problem_id)
        )
        await db.flush()  # Ensure deletions are executed before inserts

        # For file-based problems, write to filesystem
        if problem.file_based and problem.data_path:
            from app.config import settings
            from app.problem_data.manager import ProblemDataManager
            import yaml

            manager = ProblemDataManager(settings.PROBLEM_DATA_ROOT)
            problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path

            # Clean test directories
            samples_dir = problem_dir / "tests" / "samples"
            hidden_dir = problem_dir / "tests" / "hidden"

            # Remove old test files
            if samples_dir.exists():
                for f in samples_dir.glob("*"):
                    f.unlink()
            if hidden_dir.exists():
                for f in hidden_dir.glob("*"):
                    f.unlink()

            # Create new test cases
            case_number = 1
            test_cases_yml = {'pretests': [], 'samples': [], 'hidden': []}

            logger.info(f"📝 Updating test cases for problem {problem_id}")
            logger.info(f"  Samples: {len(sample_tests or [])}")
            logger.info(f"  Hidden: {len(hidden_tests or [])}")

            # Write sample tests to filesystem
            if sample_tests:
                for idx, test_data in enumerate(sample_tests, 1):
                    input_path = samples_dir / f"{idx}.in"
                    output_path = samples_dir / f"{idx}.out"

                    input_content = test_data.get('input', '')
                    output_content = test_data.get('expected_output', '')

                    input_path.write_text(input_content, encoding='utf-8')
                    output_path.write_text(output_content, encoding='utf-8')

                    # Add to database
                    test_case = TestCase(
                        problem_id=problem_id,
                        case_number=case_number,
                        input_file=f'tests/samples/{idx}.in',
                        output_file=f'tests/samples/{idx}.out',
                        is_sample=True,
                        points=10.0,
                        time_limit_override=None,
                        memory_limit_override=None
                    )
                    db.add(test_case)
                    case_number += 1

                    # Add to problem.yml
                    test_cases_yml['samples'].append({
                        'input': f'tests/samples/{idx}.in',
                        'output': f'tests/samples/{idx}.out',
                        'points': 10.0,
                        'description': None,
                        'time_limit': None,
                        'memory_limit': None
                    })

                    logger.info(f"  ✅ Updated sample test case {idx}")

            # Write hidden tests to filesystem
            if hidden_tests:
                for idx, test_data in enumerate(hidden_tests, 1):
                    input_path = hidden_dir / f"{idx}.in"
                    output_path = hidden_dir / f"{idx}.out"

                    input_content = test_data.get('input', '')
                    output_content = test_data.get('expected_output', '')

                    input_path.write_text(input_content, encoding='utf-8')
                    output_path.write_text(output_content, encoding='utf-8')

                    # Add to database
                    test_case = TestCase(
                        problem_id=problem_id,
                        case_number=case_number,
                        input_file=f'tests/hidden/{idx}.in',
                        output_file=f'tests/hidden/{idx}.out',
                        is_sample=False,
                        points=0.0,
                        time_limit_override=None,
                        memory_limit_override=None
                    )
                    db.add(test_case)
                    case_number += 1

                    # Add to problem.yml
                    test_cases_yml['hidden'].append({
                        'input': f'tests/hidden/{idx}.in',
                        'output': f'tests/hidden/{idx}.out',
                        'points': 0.0,
                        'description': None,
                        'time_limit': None,
                        'memory_limit': None
                    })

                    logger.info(f"  ✅ Updated hidden test case {idx}")

            # Update problem.yml with new test cases
            yml_path = problem_dir / "problem.yml"
            if yml_path.exists():
                with open(yml_path, 'r', encoding='utf-8') as f:
                    problem_yml = yaml.safe_load(f)

                problem_yml['test_cases'] = test_cases_yml

                with open(yml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(problem_yml, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"✅ Total test cases updated: {case_number - 1}")

        else:
            # Legacy: store content directly in database
            case_number = 1

            if sample_tests:
                for test_data in sample_tests:
                    test_case = TestCase(
                        problem_id=problem_id,
                        case_number=case_number,
                        input_file=test_data.get('input', ''),
                        output_file=test_data.get('expected_output', ''),
                        is_sample=True,
                        points=10.0
                    )
                    db.add(test_case)
                    case_number += 1

            if hidden_tests:
                for test_data in hidden_tests:
                    test_case = TestCase(
                        problem_id=problem_id,
                        case_number=case_number,
                        input_file=test_data.get('input', ''),
                        output_file=test_data.get('expected_output', ''),
                        is_sample=False,
                        points=10.0
                    )
                    db.add(test_case)
                    case_number += 1

    await db.commit()

    # Reload to avoid serialization issues
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    updated_problem = result.scalar_one()

    return updated_problem


@router.put("/{problem_id}/approve", response_model=ProblemOut)
async def approve_problem(
    problem_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a pending problem (admin only)

    **Requires authentication** (Bearer token)
    **Required role:** Admin

    **Path Parameters:**
    - problem_id: Problem ID to approve

    **Returns:**
    - Problem with status=APPROVED

    **Errors:**
    - 404: Problem not found
    - 400: Problem is not pending
    - 403: Not admin

    **Note:**
    - Only PENDING problems can be approved
    - Once approved, the problem becomes visible to all users
    """
    # Fetch problem
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    if problem.status != ProblemStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Problem is already {problem.status.value}"
        )

    # Approve problem
    problem.status = ProblemStatus.APPROVED
    problem.approved_by = current_user.id

    await db.commit()
    await db.refresh(problem)

    return problem


@router.put("/{problem_id}/reject", response_model=ProblemOut)
async def reject_problem(
    problem_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a pending problem (admin only)

    **Requires authentication** (Bearer token)
    **Required role:** Admin

    **Path Parameters:**
    - problem_id: Problem ID to reject

    **Returns:**
    - Problem with status=REJECTED

    **Errors:**
    - 404: Problem not found
    - 400: Problem is not pending
    - 403: Not admin

    **Note:**
    - Only PENDING problems can be rejected
    - Rejected problems are not visible to regular users
    - Problemsetters can view their own rejected problems
    """
    # Fetch problem
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    if problem.status != ProblemStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Problem is already {problem.status.value}"
        )

    # Reject problem
    problem.status = ProblemStatus.REJECTED
    problem.approved_by = current_user.id  # Track who rejected it

    await db.commit()
    await db.refresh(problem)

    return problem


@router.delete("/{problem_id}", response_model=MessageResponse)
async def delete_problem(
    problem_id: int,
    force: bool = Query(False, description="Force delete even if problem has submissions"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a problem (admin only)

    **Requires authentication** (Bearer token)
    **Required role:** Admin

    **Path Parameters:**
    - problem_id: Problem ID to delete

    **Query Parameters:**
    - force: If true, delete problem even if it has submissions (default: false)

    **Returns:**
    - Success message

    **Errors:**
    - 404: Problem not found
    - 400: Problem has submissions (cannot delete without force=true)
    - 403: Not admin

    **Note:**
    - By default, problems with submissions cannot be deleted (force=false)
    - Use force=true to delete problems with submissions (WARNING: deletes all user data)
    - Test cases and submissions are automatically deleted (CASCADE)
    """
    # Fetch problem
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check if problem has submissions
    from app.models import Submission
    result = await db.execute(
        select(Submission).where(Submission.problem_id == problem_id)
    )
    submissions = result.scalars().all()
    submission_count = len(submissions)

    if submission_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete problem with {submission_count} submission(s). Use force=true to delete anyway."
        )

    # If force=true and there are submissions, delete all related data first
    if force and submission_count > 0:
        logger.warning(f"Force deleting problem {problem_id} with {submission_count} submissions and all related data")

        # Step 1: Delete user_problem_solves records (they reference submissions)
        result = await db.execute(
            select(UserProblemSolve).where(UserProblemSolve.problem_id == problem_id)
        )
        user_solves = result.scalars().all()
        solve_count = len(user_solves)

        for user_solve in user_solves:
            await db.delete(user_solve)

        if solve_count > 0:
            logger.warning(f"Deleted {solve_count} user_problem_solve records")

        await db.flush()  # Flush user_problem_solves deletions

        # Step 2: Delete submissions
        for submission in submissions:
            await db.delete(submission)

        await db.flush()  # Flush submission deletions before continuing

    # Delete file-based problem data if it exists
    # Try multiple approaches to find and delete the problem directory
    deleted_dir = False

    # Approach 1: Use data_path if available
    if problem.data_path:
        try:
            problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path
            if problem_dir.exists():
                import shutil
                shutil.rmtree(problem_dir)
                logger.info(f"Deleted problem data directory: {problem_dir}")
                deleted_dir = True
        except Exception as e:
            logger.error(f"Failed to delete problem data directory (data_path): {e}")

    # Approach 2: Try to find directory by problem number (e.g., 41-*, 041-*)
    if not deleted_dir:
        try:
            import glob
            problem_dirs = glob.glob(str(Path(settings.PROBLEM_DATA_ROOT) / f"{problem_id}-*"))
            problem_dirs += glob.glob(str(Path(settings.PROBLEM_DATA_ROOT) / f"{problem_id:03d}-*"))

            for dir_path in problem_dirs:
                if Path(dir_path).is_dir():
                    import shutil
                    shutil.rmtree(dir_path)
                    logger.info(f"Deleted problem data directory (by number): {dir_path}")
                    deleted_dir = True
        except Exception as e:
            logger.error(f"Failed to delete problem data directory (by number): {e}")
            # Continue with database deletion even if file deletion fails

    # Delete problem from database (test cases and submissions will be deleted automatically via CASCADE)
    await db.delete(problem)
    await db.commit()

    # Log the deletion with additional context
    if submission_count > 0:
        logger.warning(
            f"FORCE DELETE: Problem {problem_id} ({problem.title_en}) with {submission_count} submission(s) "
            f"deleted by admin {current_user.username}"
        )
        return {
            "message": f"Problem '{problem.title_en}' (ID: {problem_id}) and {submission_count} submission(s) deleted successfully"
        }
    else:
        logger.info(f"Problem {problem_id} ({problem.title_en}) deleted by admin {current_user.username}")
        return {"message": f"Problem '{problem.title_en}' (ID: {problem_id}) deleted successfully"}


# ============================================
# FILE-BASED PROBLEM MANAGEMENT (PHASE 3)
# ============================================

@router.post("/upload-package", response_model=ProblemOut, status_code=status.HTTP_201_CREATED)
async def upload_problem_package(
    file: UploadFile = File(...),
    current_user: User = Depends(require_problemsetter),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a complete problem package as ZIP file

    **Requires authentication** (Bearer token)
    **Required role:** Problemsetter or Admin

    **Request:**
    - file: ZIP file containing problem.yml, descriptions, and test cases

    **Returns:**
    - Created problem with PENDING status

    **Errors:**
    - 400: Invalid ZIP structure or validation errors
    - 409: Problem code already exists

    **ZIP Structure:**
    ```
    problem-name/
    ├── problem.yml
    ├── descriptions/
    │   ├── en.md
    │   └── es.md
    └── tests/
        ├── samples/
        │   ├── 1.in
        │   └── 1.out
        └── hidden/
            ├── 2.in
            └── 2.out
    ```
    """
    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP archive"
        )

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        tmp_path = Path(tmp_file.name)

        try:
            # Save uploaded file
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()

            # Initialize manager
            manager = ProblemDataManager(settings.PROBLEM_DATA_ROOT)

            # Import problem from ZIP
            try:
                problem_code = manager.create_from_zip(tmp_path)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

            # Validate the imported problem
            is_valid, errors, warnings = manager.validate_problem(problem_code)
            if not is_valid:
                # Clean up on validation failure
                manager.delete_problem(problem_code)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Package validation failed: {', '.join(errors)}"
                )

            # Load problem.yml
            problem_yml = manager.load_problem_yml(problem_code)

            # Check if problem code already exists in database
            result = await db.execute(
                select(Problem).where(Problem.number == problem_yml.number)
            )
            if result.scalar_one_or_none():
                manager.delete_problem(problem_code)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Problem number {problem_yml.number} already exists"
                )

            # Create database record
            new_problem = Problem(
                number=problem_yml.number,
                file_based=True,
                data_path=problem_code,
                title_en=problem_yml.title.en,
                title_es=problem_yml.title.es,
                description_en=f"See file: {problem_yml.description.en}",
                description_es=f"See file: {problem_yml.description.es}",
                authors=problem_yml.authors,
                author_note=problem_yml.author_note,
                tier=problem_yml.tier,
                status=ProblemStatus.PENDING,
                time_limit=int(problem_yml.limits.time),
                memory_limit=problem_yml.limits.memory,
                partial=problem_yml.scoring.partial,
                initial_points=problem_yml.scoring.initial_points,
                current_points=problem_yml.scoring.initial_points,
                tags=problem_yml.tags,
                created_by=current_user.id
            )

            db.add(new_problem)
            await db.flush()

            # Add categories
            for cat_code in problem_yml.categories:
                result = await db.execute(
                    select(Category).where(Category.code == cat_code)
                )
                category = result.scalar_one_or_none()
                if category:
                    new_problem.categories.append(category)

            # Add subcategories
            for subcat_code in problem_yml.subcategories:
                result = await db.execute(
                    select(Subcategory).where(Subcategory.code == subcat_code)
                )
                subcategory = result.scalar_one_or_none()
                if subcategory:
                    new_problem.subcategories.append(subcategory)

            # Add test cases from problem.yml
            case_number = 1

            logger.info(f"📝 Adding test cases for problem {problem_yml.number}")
            logger.info(f"  Samples: {len(problem_yml.test_cases.samples)}")
            logger.info(f"  Hidden: {len(problem_yml.test_cases.hidden)}")

            # Add sample test cases
            for test_case_data in problem_yml.test_cases.samples:
                test_case = TestCase(
                    problem_id=new_problem.id,
                    case_number=case_number,
                    batch_number=None,
                    input_file=test_case_data.input,
                    output_file=test_case_data.output,
                    is_sample=True,
                    points=test_case_data.points,
                    time_limit_override=test_case_data.time_limit,
                    memory_limit_override=test_case_data.memory_limit
                )
                db.add(test_case)
                case_number += 1
                logger.info(f"  ✅ Added sample test case {case_number - 1}")

            # Add hidden test cases
            for test_case_data in problem_yml.test_cases.hidden:
                test_case = TestCase(
                    problem_id=new_problem.id,
                    case_number=case_number,
                    batch_number=None,
                    input_file=test_case_data.input,
                    output_file=test_case_data.output,
                    is_sample=False,
                    points=test_case_data.points,
                    time_limit_override=test_case_data.time_limit,
                    memory_limit_override=test_case_data.memory_limit
                )
                db.add(test_case)
                case_number += 1
                logger.info(f"  ✅ Added hidden test case {case_number - 1}")

            logger.info(f"✅ Total test cases added: {case_number - 1}")

            await db.commit()
            await db.refresh(new_problem)

            return new_problem

        finally:
            # Clean up temporary file
            if tmp_path.exists():
                tmp_path.unlink()


@router.post("/{problem_id}/upload-testcases", response_model=MessageResponse)
async def upload_testcases(
    problem_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_problemsetter),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload test cases for an existing file-based problem

    **Requires authentication** (Bearer token)
    **Required role:** Problemsetter or Admin

    **Path Parameters:**
    - problem_id: Problem ID

    **Request:**
    - file: ZIP file containing test cases only

    **Returns:**
    - Success message

    **Errors:**
    - 404: Problem not found
    - 400: Problem is not file-based or invalid ZIP
    - 403: Not the problem creator (unless admin)

    **ZIP Structure:**
    ```
    tests/
    ├── samples/
    │   ├── 1.in
    │   └── 1.out
    └── hidden/
        ├── 2.in
        └── 2.out
    ```
    """
    # Fetch problem
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check permissions
    if current_user.role != UserRole.ADMIN and problem.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own problems"
        )

    # Check if problem is file-based
    if not problem.file_based or not problem.data_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Problem is not file-based"
        )

    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a ZIP archive"
        )

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        tmp_path = Path(tmp_file.name)

        try:
            # Save uploaded file
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()

            # Initialize manager
            manager = ProblemDataManager(settings.PROBLEM_DATA_ROOT)

            # Update test cases
            try:
                manager.update_testcases_from_zip(problem.data_path, tmp_path)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

            # Validate updated problem
            is_valid, errors, warnings = manager.validate_problem(problem.data_path)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Test case validation failed: {', '.join(errors)}"
                )

            return {"message": "Test cases updated successfully"}

        finally:
            # Clean up temporary file
            if tmp_path.exists():
                tmp_path.unlink()


@router.get("/{problem_id}/export")
async def export_problem(
    problem_id: int,
    current_user: User = Depends(require_problemsetter),
    db: AsyncSession = Depends(get_db)
):
    """
    Export a file-based problem as ZIP archive

    **Requires authentication** (Bearer token)
    **Required role:** Problemsetter or Admin

    **Path Parameters:**
    - problem_id: Problem ID

    **Returns:**
    - ZIP file download

    **Errors:**
    - 404: Problem not found
    - 400: Problem is not file-based
    - 403: Not the problem creator (unless admin)
    """
    # Fetch problem
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check permissions
    if current_user.role != UserRole.ADMIN and problem.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only export your own problems"
        )

    # Check if problem is file-based
    if not problem.file_based or not problem.data_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Problem is not file-based"
        )

    # Initialize manager
    manager = ProblemDataManager(settings.PROBLEM_DATA_ROOT)

    # Create temporary output file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        # Export to ZIP
        manager.export_to_zip(problem.data_path, tmp_path)

        # Return file
        return FileResponse(
            path=tmp_path,
            filename=f"{problem.data_path}.zip",
            media_type="application/zip",
            background=None  # Don't delete immediately - let FastAPI handle it
        )
    except ValueError as e:
        # Clean up on error
        if tmp_path.exists():
            tmp_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{problem_id}/package", response_model=ProblemPackageInfo)
async def get_problem_package_info(
    problem_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a problem package

    **Path Parameters:**
    - problem_id: Problem ID

    **Returns:**
    - Package metadata and statistics

    **Errors:**
    - 404: Problem not found
    - 400: Problem is not file-based
    """
    # Fetch problem
    result = await db.execute(
        select(Problem).where(Problem.id == problem_id)
    )
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check if problem is file-based
    if not problem.file_based or not problem.data_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Problem is not file-based"
        )

    # Initialize manager
    manager = ProblemDataManager(settings.PROBLEM_DATA_ROOT)

    try:
        # Load problem.yml
        problem_yml = manager.load_problem_yml(problem.data_path)

        # Calculate package statistics
        problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path

        # Calculate total size
        total_size = sum(f.stat().st_size for f in problem_dir.rglob('*') if f.is_file())

        # Count files
        file_count = sum(1 for f in problem_dir.rglob('*') if f.is_file())

        # Check for descriptions
        desc_en = problem_dir / problem_yml.description.en
        desc_es = problem_dir / problem_yml.description.es
        has_descriptions = desc_en.exists() and desc_es.exists()

        # Count test cases
        sample_count = len(problem_yml.test_cases.samples)
        hidden_count = len(problem_yml.test_cases.hidden)
        pretest_count = len(problem_yml.test_cases.pretests)
        total_tests = sample_count + hidden_count + pretest_count

        return ProblemPackageInfo(
            code=problem.data_path,
            problem_id=problem.id,
            size_bytes=total_size,
            file_count=file_count,
            has_problem_yml=True,  # If we got here, it exists
            has_descriptions=has_descriptions,
            test_case_count=total_tests,
            sample_count=sample_count,
            hidden_count=hidden_count,
            created_at=problem.created_at,
            updated_at=problem.updated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
