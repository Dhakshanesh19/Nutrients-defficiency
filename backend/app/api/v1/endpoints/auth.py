from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import ValidationError

from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.deficiency import User
from app.schemas.auth import Token, RefreshTokenInput, TokenPayload
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user in the database.
    """
    # Verify if email is already taken
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system."
        )

    # Save new user to the database
    db_user = User(
        email=user_in.email,
        name=user_in.name,
        password_hash=security.get_password_hash(user_in.password),
        age=user_in.age,
        gender=user_in.gender,
        height=user_in.height,
        weight=user_in.weight,
        bmi=user_in.bmi,
        activity_level=user_in.activity_level
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, retrieve a JWT access token and refresh token.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = security.create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(
        subject=user.id
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshTokenInput, db: Session = Depends(get_db)):
    """
    Validate refresh token and issue new access & refresh tokens.
    """
    try:
        payload = jwt.decode(
            data.refresh_token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = security.create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(
        subject=user.id
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserOut)
def read_user_me(current_user: User = Depends(get_current_user)):
    """
    Get current logged-in user profile details.
    """
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Logout the current user (stateless: client deletes tokens).
    """
    return {"detail": "Successfully logged out"}
