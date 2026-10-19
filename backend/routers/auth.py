import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import db_models
from backend.auth import create_access_token, hash_password, require_current_user, verify_password
from backend.database import get_db
from backend.schemas import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    clean_username = request.username.strip()
    existing_user = (
        db.query(db_models.User)
        .filter(db_models.User.username == clean_username)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered. Please choose another username.",
        )

    hashed_pw = hash_password(request.password)
    user = db_models.User(
        username=clean_username,
        hashed_password=hashed_pw,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    clean_username = request.username.strip()
    user = (
        db.query(db_models.User)
        .filter(db_models.User.username == clean_username)
        .first()
    )
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: db_models.User = Depends(require_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)

