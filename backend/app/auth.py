"""
Authentication and Authorization
JWT tokens, password hashing, role-based access control (RBAC)
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt

from app.config import settings
from app.database import get_db
from app.models import User, UserRole

# HTTP Bearer token scheme
security = HTTPBearer()


# ============================================
# PASSWORD HASHING
# ============================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# ============================================
# JWT TOKEN MANAGEMENT
# ============================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary with user data to encode (should include 'sub' with user_id)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Attempting to decode token (first 20 chars): {token[:20]}...")
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        logger.info(f"Token decoded successfully")
        return payload
    except JWTError as e:
        logger.error(f"JWT decode error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# ============================================
# AUTHENTICATION DEPENDENCIES
# ============================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    This is a FastAPI dependency that:
    1. Extracts the Bearer token from Authorization header
    2. Decodes and validates the JWT
    3. Fetches the user from database
    4. Returns the User object

    Usage:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.username}

    Args:
        credentials: HTTP Bearer credentials from request header
        db: Database session

    Returns:
        User object from database

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Decoding token...")

    # Decode token
    payload = decode_access_token(credentials.credentials)
    logger.info(f"Token decoded successfully: {payload}")

    # Extract user_id from token (sub is string in JWT)
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        logger.error("No 'sub' in token payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    try:
        user_id = int(user_id_str)
        logger.info(f"Fetching user_id: {user_id}")
    except ValueError:
        logger.error(f"Invalid user_id format: {user_id_str}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    logger.info(f"User query result: {user}")

    if user is None:
        logger.error(f"User not found for id: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    logger.info(f"User found: {user.username}")

    # Update last_login timestamp (don't commit here to avoid session issues)
    # The commit will happen at the end of the request if there are changes
    user.last_login = datetime.utcnow()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (placeholder for future account deactivation feature)

    Usage:
        @app.get("/me")
        async def read_users_me(current_user: User = Depends(get_current_active_user)):
            return current_user
    """
    # Future: Add account deactivation check here
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, or None if not
    Used for public endpoints that want to customize behavior based on auth state

    Usage:
        @app.get("/public-but-better-when-logged-in")
        async def endpoint(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"message": f"Welcome back {user.username}"}
            else:
                return {"message": "Welcome guest"}
    """
    if not credentials:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None

        user_id = int(user_id_str)
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        return user

    except (HTTPException, ValueError):
        # Invalid token, but we don't error - just return None
        return None


# ============================================
# ROLE-BASED ACCESS CONTROL (RBAC)
# ============================================

class RoleChecker:
    """
    Dependency class for role-based access control

    Usage:
        # Single role
        require_admin = RoleChecker([UserRole.ADMIN])

        @app.post("/admin/action")
        async def admin_action(current_user: User = Depends(require_admin)):
            return {"message": "Admin action performed"}

        # Multiple roles
        require_staff = RoleChecker([UserRole.ADMIN, UserRole.PROBLEMSETTER])

        @app.post("/problems")
        async def create_problem(current_user: User = Depends(require_staff)):
            return {"message": "Problem created"}
    """

    def __init__(self, allowed_roles: list[UserRole]):
        """
        Initialize role checker

        Args:
            allowed_roles: List of roles that are allowed access
        """
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        Check if current user has required role

        Args:
            current_user: Current authenticated user

        Returns:
            User object if authorized

        Raises:
            HTTPException 403: If user doesn't have required role
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return current_user


# Pre-configured role checkers for common use cases
require_admin = RoleChecker([UserRole.ADMIN])
require_problemsetter = RoleChecker([UserRole.ADMIN, UserRole.PROBLEMSETTER])
require_authenticated = Depends(get_current_user)  # Any authenticated user


# ============================================
# AUTHENTICATION HELPERS
# ============================================

async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str
) -> Optional[User]:
    """
    Authenticate a user by username and password

    Args:
        db: Database session
        username: Username
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    # Fetch user by username
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user:
        return None

    # Verify password
    if not verify_password(password, user.password_hash):
        return None

    return user


async def register_user(
    db: AsyncSession,
    username: str,
    password: str,
    email: Optional[str] = None
) -> User:
    """
    Register a new user

    Args:
        db: Database session
        username: Desired username
        password: Plain text password
        email: Optional email address

    Returns:
        Created User object

    Raises:
        HTTPException 400: If username already exists
    """
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == username)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists (if provided)
    if email:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        existing_email = result.scalar_one_or_none()

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Create new user
    new_user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
        role=UserRole.USER  # Default role
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
