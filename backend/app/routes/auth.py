"""
Authentication routes
Handles user registration, login, logout, and profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserLogin, Token, UserOut, MessageResponse, UserUpdate, PasswordChange
from app.auth import (
    authenticate_user,
    register_user,
    create_access_token,
    get_current_user,
    verify_password,
    hash_password
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user

    **Request body:**
    - username: Unique username (3-50 chars, alphanumeric + underscore)
    - password: Password (min 8 chars)
    - email: Optional email address

    **Returns:**
    - User object with public information

    **Errors:**
    - 400: Username or email already registered
    """
    user = await register_user(
        db=db,
        username=user_data.username,
        password=user_data.password,
        email=user_data.email
    )
    return user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login and receive JWT access token

    **Request body:**
    - username: Username
    - password: Password

    **Returns:**
    - access_token: JWT token for authentication
    - token_type: "bearer"

    **Errors:**
    - 401: Invalid credentials

    **Usage:**
    Store the token and include it in subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    user = await authenticate_user(
        db=db,
        username=credentials.username,
        password=credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user_id as subject (must be string for JWT)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout", response_model=MessageResponse)
async def logout():
    """
    Logout (client-side only)

    Since we're using stateless JWT tokens, logout is handled client-side
    by removing the token from localStorage.

    In a production system, you might want to:
    - Implement token blacklisting
    - Use refresh tokens with shorter-lived access tokens
    - Store session info in Redis

    **Returns:**
    - Success message

    **Note:**
    Client should remove the token from localStorage after calling this endpoint
    """
    return {"message": "Successfully logged out. Remove token from client."}


@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's information

    **Requires authentication** (Bearer token in Authorization header)

    **Returns:**
    - User object with current user's public information

    **Errors:**
    - 401: Not authenticated or invalid token
    """
    return current_user


@router.put("/me", response_model=UserOut)
async def update_current_user_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile

    **Requires authentication** (Bearer token in Authorization header)

    **Request Body:**
    ```json
    {
        "email": "newemail@example.com",
        "npub": "npub1...",
        "github_url": "https://github.com/username",
        "country": "Cuba",
        "organization": "University"
    }
    ```

    All fields are optional. Only provided fields will be updated.

    **Returns:**
    - Updated user object

    **Errors:**
    - 401: Not authenticated or invalid token
    - 400: Invalid data (e.g., malformed email)
    """
    from email_validator import validate_email, EmailNotValidError

    try:
        # Update only provided fields
        if profile_data.email is not None:
            # Validate email format if provided
            if profile_data.email.strip() != "":
                try:
                    validate_email(profile_data.email)
                    current_user.email = profile_data.email
                except EmailNotValidError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid email format"
                    )
            else:
                current_user.email = None

        if profile_data.npub is not None:
            current_user.npub = profile_data.npub if profile_data.npub.strip() != "" else None

        if profile_data.github_url is not None:
            current_user.github_url = profile_data.github_url if profile_data.github_url.strip() != "" else None

        if profile_data.country is not None:
            current_user.country = profile_data.country if profile_data.country.strip() != "" else None

        if profile_data.organization is not None:
            current_user.organization = profile_data.organization if profile_data.organization.strip() != "" else None

        await db.commit()
        await db.refresh(current_user)

        logger.info(f"User {current_user.username} updated their profile")

        return current_user

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating user profile: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user's password

    **Requires authentication** (Bearer token in Authorization header)

    **Request Body:**
    ```json
    {
        "current_password": "oldpassword123",
        "new_password": "newpassword456"
    }
    ```

    **Returns:**
    - Success message

    **Errors:**
    - 401: Not authenticated or invalid token
    - 400: Current password is incorrect
    - 400: New password too short (minimum 8 characters)
    """
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Hash and update new password
        current_user.password_hash = hash_password(password_data.new_password)
        await db.commit()

        logger.info(f"User {current_user.username} changed their password")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error changing password: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/check", response_model=MessageResponse)
async def check_auth(
    current_user: User = Depends(get_current_user)
):
    """
    Check if current token is valid

    **Requires authentication**

    **Returns:**
    - Success message with username

    **Errors:**
    - 401: Token is invalid or expired
    """
    return {"message": f"Authenticated as {current_user.username}"}
