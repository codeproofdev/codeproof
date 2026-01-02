"""
User management routes for CodeProof (Admin only)

Provides endpoints for administrators to manage users, roles, and passwords.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import secrets
import string

from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserOut, UserProfile, UserAdminUpdate, MessageResponse, AdminPasswordReset
from app.auth import get_current_user, require_admin, hash_password
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=List[UserOut])
async def list_users(
    limit: int = 100,
    offset: int = 0,
    role: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users (Admin only)

    **Requires: Admin role**

    Returns a paginated list of all users in the system.

    **Query Parameters:**
    - **limit** (int): Number of users to return (default 100, max 500)
    - **offset** (int): Number of users to skip (for pagination)
    - **role** (str): Filter by role (admin, problemsetter, user)

    **Returns:**
    - List of UserOut with public user information

    **Example:**
    ```
    GET /api/users?limit=20&role=problemsetter
    ```

    **Response:**
    ```json
    [
        {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "total_score": 150.5,
            "problems_solved": 15,
            "blocks_mined": 3,
            "created_at": "2024-01-01T00:00:00Z"
        },
        ...
    ]
    ```
    """

    try:
        # Build query
        query = select(User)

        # Filter by role if specified
        if role:
            try:
                role_enum = UserRole[role.upper()]
                query = query.where(User.role == role_enum)
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}. Valid roles: admin, problemsetter, user"
                )

        # Order by created_at DESC
        query = query.order_by(User.created_at.desc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        users = result.scalars().all()

        logger.info(f"Admin {current_user.username} listed {len(users)} users (role={role})")

        return users

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user statistics (Admin only)

    **Requires: Admin role**

    Returns aggregate statistics about users in the system.

    **Returns:**
    ```json
    {
        "total_users": 150,
        "by_role": {
            "admin": 2,
            "problemsetter": 5,
            "user": 143
        },
        "total_score": 12500.5,
        "total_problems_solved": 450
    }
    ```
    """

    try:
        # Total users
        total_query = select(func.count(User.id))
        total_result = await db.execute(total_query)
        total_users = total_result.scalar()

        # Count by role
        by_role = {}
        for role in UserRole:
            role_query = select(func.count(User.id)).where(User.role == role)
            role_result = await db.execute(role_query)
            by_role[role.value.lower()] = role_result.scalar() or 0

        # Aggregate stats
        stats_query = select(
            func.sum(User.total_score).label('total_score'),
            func.sum(User.problems_solved).label('total_problems_solved')
        )
        stats_result = await db.execute(stats_query)
        stats = stats_result.one()

        return {
            "total_users": total_users or 0,
            "by_role": by_role,
            "total_score": float(stats.total_score or 0),
            "total_problems_solved": stats.total_problems_solved or 0
        }

    except Exception as e:
        logger.exception(f"Error fetching user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user statistics"
        )


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user profile

    **Requires: Authentication**

    Users can view their own profile.
    Admins can view any user's profile.

    **Path Parameters:**
    - **user_id** (int): ID of the user to retrieve

    **Returns:**
    - UserProfile with full user information

    **Errors:**
    - 403: User trying to view another user's profile (not admin)
    - 404: User not found
    """

    try:
        # Check permissions: user can view own profile, admin can view any
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own profile"
            )

        # Fetch user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user"
        )


@router.put("/{user_id}/role", response_model=UserOut)
async def change_user_role(
    user_id: int,
    update_data: UserAdminUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user role (Admin only)

    **Requires: Admin role**

    Allows administrators to promote/demote users to different roles.

    **Path Parameters:**
    - **user_id** (int): ID of the user to update

    **Request Body:**
    ```json
    {
        "role": "problemsetter"
    }
    ```

    **Valid roles:**
    - `admin`: Full administrative access
    - `problemsetter`: Can create and manage problems
    - `user`: Normal user (default)

    **Returns:**
    - Updated UserOut

    **Errors:**
    - 400: Invalid role or trying to demote self
    - 404: User not found

    **Security:**
    - Admins cannot demote themselves (prevents lockout)
    - Action is logged for audit trail
    """

    try:
        # Validate role is provided
        if not update_data.role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role field is required"
            )

        # Prevent admin from demoting themselves
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role"
            )

        # Fetch user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Store old role for logging
        old_role = user.role

        # Update role
        user.role = update_data.role
        await db.commit()
        await db.refresh(user)

        logger.info(f"Admin {current_user.username} changed role of user {user.username} from {old_role.value} to {update_data.role.value}")

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error changing role for user {user_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change user role"
        )


@router.put("/{user_id}/reset-password", response_model=MessageResponse)
async def reset_user_password(
    user_id: int,
    password_data: AdminPasswordReset,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset user password (Admin only)

    **Requires: Admin role**

    Sets a new password for the user as specified by the admin.

    **Path Parameters:**
    - **user_id** (int): ID of the user whose password to reset

    **Request Body:**
    ```json
    {
        "new_password": "NewSecurePassword123!"
    }
    ```

    **Returns:**
    ```json
    {
        "message": "Password reset successfully"
    }
    ```

    **Security:**
    - Password must be at least 8 characters
    - Admin should securely communicate the new password to the user
    - User should change password on first login (TODO: implement force change)

    **Errors:**
    - 400: Password too short (minimum 8 characters)
    - 404: User not found
    """

    try:
        # Fetch user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Hash and update password with admin-provided password
        user.password_hash = hash_password(password_data.new_password)
        await db.commit()

        logger.info(f"Admin {current_user.username} reset password for user {user.username}")

        return {
            "message": "Password reset successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error resetting password for user {user_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user (Admin only)

    **Requires: Admin role**

    Permanently deletes a user account.

    **Path Parameters:**
    - **user_id** (int): ID of the user to delete

    **Returns:**
    ```json
    {
        "message": "User deleted successfully"
    }
    ```

    **Security:**
    - Admins cannot delete themselves (prevents lockout)
    - Cascading deletes may affect related data (submissions, problems)
    - This action is irreversible

    **Errors:**
    - 400: Trying to delete self
    - 404: User not found
    """

    try:
        # Prevent admin from deleting themselves
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account"
            )

        # Fetch user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Store username for logging
        username = user.username

        # Delete user
        await db.delete(user)
        await db.commit()

        logger.warning(f"Admin {current_user.username} deleted user {username} (id={user_id})")

        return {
            "message": "User deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting user {user_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
