from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import models
from app.database.db import get_db
from app.schemas import common_schemas
from app.services import auth_service

router = APIRouter(tags=["Authentication"])


@router.post(
    "/signup", 
    response_model=common_schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
def signup(payload: common_schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user with hashed password."""
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )
    
    hashed_pwd = auth_service.get_password_hash(payload.password)
    user = models.User(
        email=payload.email,
        hashed_password=hashed_pwd,
        full_name=payload.full_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login", 
    response_model=common_schemas.Token,
    summary="Login to receive a JWT access token"
)
def login(
    payload: common_schemas.UserLogin, 
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token."""
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth_service.verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me", 
    response_model=common_schemas.UserResponse,
    summary="Get current user profile"
)
def get_me(current_user: models.User = Depends(auth_service.get_current_user)):
    """Return the authenticated user profile."""
    return current_user
