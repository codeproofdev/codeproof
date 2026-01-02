"""
Editorial and Reference Files routes
Handles editorial and reference file upload/download for problems
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import logging
import yaml

from app.database import get_db
from app.models import Problem, User, UserProblemSolve
from app.auth import get_current_user, get_optional_user
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# EDITORIAL ENDPOINTS
# ============================================================================

@router.get("/{problem_id}/editorial")
async def get_editorial(
    problem_id: int,
    lang: str = Query("en", regex="^(en|es)$"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get problem editorial (if available and user has permission)
    """
    # Get problem
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    if not problem.has_editorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This problem has no editorial"
        )

    # Check visibility permissions
    can_view, reason = await check_editorial_visibility(problem, current_user, db)
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Editorial not available yet",
                "reason": problem.editorial_visibility,
                "hint": get_visibility_hint(problem.editorial_visibility)
            }
        )

    # Read editorial file
    problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path
    editorial_path = problem_dir / "editorials" / f"{lang}.md"

    # Fallback to English if requested language doesn't exist
    if not editorial_path.exists() and lang != "en":
        editorial_path = problem_dir / "editorials" / "en.md"

    if not editorial_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Editorial file not found"
        )

    # Read file content
    try:
        with open(editorial_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading editorial file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reading editorial file"
        )

    return {
        "problem_id": problem_id,
        "language": lang,
        "content": content,
        "visibility": problem.editorial_visibility
    }


@router.post("/{problem_id}/upload-editorial")
async def upload_editorial(
    problem_id: int,
    language: str = Query(..., regex="^(en|es)$"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload editorial file (only creator or admin)
    """
    # Get problem
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check permissions (only creator or admin)
    if problem.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # Validate file
    if not file.filename.endswith(('.md', '.txt')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .md or .txt files allowed"
        )

    # Check file size (5MB max)
    content = await file.read()
    if len(content) > 5_000_000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 5MB)"
        )

    # Create editorials directory
    problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path
    editorial_dir = problem_dir / "editorials"
    editorial_dir.mkdir(exist_ok=True)

    # Save file
    file_path = editorial_dir / f"{language}.md"
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error saving editorial file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving editorial file"
        )

    # Update problem.yml
    yml_path = problem_dir / "problem.yml"
    try:
        with open(yml_path, 'r', encoding='utf-8') as f:
            problem_data = yaml.safe_load(f)

        if 'editorial' not in problem_data:
            problem_data['editorial'] = {
                'visibility': problem.editorial_visibility,
                'author': current_user.username,
                'created_at': datetime.utcnow().isoformat()
            }

        problem_data['editorial'][language] = f"editorials/{language}.md"

        with open(yml_path, 'w', encoding='utf-8') as f:
            yaml.dump(problem_data, f, allow_unicode=True)
    except Exception as e:
        logger.error(f"Error updating problem.yml: {e}")
        # Continue even if yml update fails

    # Update database
    problem.has_editorial = True
    await db.commit()

    return {
        "message": f"Editorial ({language}) uploaded successfully",
        "filename": f"{language}.md"
    }


@router.put("/{problem_id}/editorial-visibility")
async def update_editorial_visibility(
    problem_id: int,
    visibility: str = Query(..., regex="^(always|after_solve|after_deadline|manual)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update editorial visibility (only creator or admin)
    """
    # Get problem
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check permissions
    if problem.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # Update visibility
    problem.editorial_visibility = visibility
    await db.commit()

    # Also update problem.yml
    problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path
    yml_path = problem_dir / "problem.yml"
    try:
        with open(yml_path, 'r', encoding='utf-8') as f:
            problem_data = yaml.safe_load(f)

        if 'editorial' not in problem_data:
            problem_data['editorial'] = {}

        problem_data['editorial']['visibility'] = visibility

        with open(yml_path, 'w', encoding='utf-8') as f:
            yaml.dump(problem_data, f, allow_unicode=True)
    except Exception as e:
        logger.error(f"Error updating problem.yml: {e}")

    return {
        "message": "Editorial visibility updated",
        "visibility": visibility
    }


# ============================================================================
# REFERENCE FILES ENDPOINTS
# ============================================================================

@router.post("/{problem_id}/upload-reference-file")
async def upload_reference_file(
    problem_id: int,
    file_type: str = Query(..., regex="^(generator|solution|editorial_md)$"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a reference file (generator, solution, or additional docs)
    Only creator or admin can upload
    """
    # Get problem
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check permissions
    if problem.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # Validate file type
    allowed_extensions = {'.py', '.cpp', '.rs', '.js', '.go', '.md', '.txt'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Check file size (5MB max)
    content = await file.read()
    if len(content) > 5_000_000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 5MB)"
        )

    # Create reference directory
    problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path
    reference_dir = problem_dir / "reference"
    reference_dir.mkdir(exist_ok=True)

    # Sanitize filename
    safe_filename = f"{file_type}_{Path(file.filename).name}"
    file_path = reference_dir / safe_filename

    # Save file
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error saving reference file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving reference file"
        )

    # Update problem.yml
    yml_path = problem_dir / "problem.yml"
    try:
        with open(yml_path, 'r', encoding='utf-8') as f:
            problem_data = yaml.safe_load(f)

        if 'reference' not in problem_data:
            problem_data['reference'] = {}
        if file_type not in problem_data['reference']:
            problem_data['reference'][file_type] = []

        # Detect language
        language = detect_language(file_ext)

        problem_data['reference'][file_type].append({
            'file': f"reference/{safe_filename}",
            'language': language,
            'uploaded_at': datetime.utcnow().isoformat(),
            'uploaded_by': current_user.username
        })

        with open(yml_path, 'w', encoding='utf-8') as f:
            yaml.dump(problem_data, f, allow_unicode=True)
    except Exception as e:
        logger.error(f"Error updating problem.yml: {e}")

    # Update database flag
    problem.has_reference_files = True
    await db.commit()

    return {
        "message": "Reference file uploaded",
        "filename": safe_filename
    }


@router.get("/{problem_id}/reference-files")
async def get_reference_files(
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all reference files for a problem
    Only creator, admin, or problemsetter can view
    """
    # Get problem
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check permissions (creator, admin, or problemsetter)
    if (problem.created_by != current_user.id and
        current_user.role not in ['admin', 'problemsetter']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reference files only visible to problemsetters and admins"
        )

    # Read problem.yml
    problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path
    yml_path = problem_dir / "problem.yml"

    try:
        with open(yml_path, 'r', encoding='utf-8') as f:
            problem_data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error reading problem.yml: {e}")
        return {}

    return problem_data.get('reference', {})


@router.get("/{problem_id}/reference-files/{file_type}/{filename}")
async def download_reference_file(
    problem_id: int,
    file_type: str,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download a specific reference file
    Only creator, admin, or problemsetter can download
    """
    # Get problem
    result = await db.execute(select(Problem).where(Problem.id == problem_id))
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )

    # Check permissions
    if (problem.created_by != current_user.id and
        current_user.role not in ['admin', 'problemsetter']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # Build file path (sanitize to prevent directory traversal)
    problem_dir = Path(settings.PROBLEM_DATA_ROOT) / problem.data_path
    file_path = problem_dir / "reference" / filename

    # Security check: ensure file is within problem directory
    try:
        file_path = file_path.resolve()
        problem_dir = problem_dir.resolve()
        if not str(file_path).startswith(str(problem_dir)):
            raise ValueError("Invalid file path")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Read and return content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # If not text, return as binary
        with open(file_path, 'rb') as f:
            content = f.read()
            content = content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Error reading reference file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reading file"
        )

    return {
        "filename": filename,
        "content": content,
        "language": detect_language(Path(filename).suffix)
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def check_editorial_visibility(
    problem: Problem,
    user: Optional[User],
    db: AsyncSession
) -> tuple[bool, str]:
    """
    Check if user can view editorial
    Returns (can_view, reason)
    """
    if problem.editorial_visibility == "always":
        return True, "always_visible"

    if not user:
        return False, "not_logged_in"

    # Admins and problemsetters always can view
    if user.role in ['admin', 'problemsetter']:
        return True, "privileged_user"

    # Creator can always view
    if problem.created_by == user.id:
        return True, "creator"

    if problem.editorial_visibility == "after_solve":
        # Check if user solved the problem
        result = await db.execute(
            select(UserProblemSolve).where(
                UserProblemSolve.user_id == user.id,
                UserProblemSolve.problem_id == problem.id
            )
        )
        solved = result.scalar_one_or_none()
        if solved:
            return True, "solved"
        return False, "not_solved"

    if problem.editorial_visibility == "after_deadline":
        # TODO: Implement deadline checking when contest system is added
        return True, "no_deadline_set"

    if problem.editorial_visibility == "manual":
        return False, "manual_control"

    return False, "unknown"


def get_visibility_hint(visibility: str) -> str:
    """Get user-friendly hint for editorial visibility"""
    hints = {
        "after_solve": "Solve the problem first to unlock the editorial",
        "after_deadline": "Editorial will be available after the contest ends",
        "manual": "Editorial is not publicly available yet",
        "always": "Editorial is available"
    }
    return hints.get(visibility, "Editorial visibility not configured")


def detect_language(extension: str) -> str:
    """Detect programming language from file extension"""
    mapping = {
        '.py': 'python',
        '.cpp': 'cpp',
        '.c': 'c',
        '.rs': 'rust',
        '.js': 'javascript',
        '.go': 'go',
        '.java': 'java',
        '.md': 'markdown',
        '.txt': 'text'
    }
    return mapping.get(extension.lower(), 'text')
