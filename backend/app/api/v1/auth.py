from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.db import get_db
from app.core.ratelimit import login_limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Agency, User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserCreate, UserOut

router = APIRouter(tags=["auth"])


def _token(user: User) -> TokenOut:
    return TokenOut(access_token=create_access_token(str(user.id), str(user.agency_id), user.role))


async def _authenticate(request: Request, db: AsyncSession, email: str, password: str) -> User:
    # Keyed by client IP + email. Behind a proxy, run uvicorn with --proxy-headers so the real IP is used.
    key = f"{request.client.host if request.client else 'unknown'}|{email.lower()}"
    wait = login_limiter.retry_after(key)
    if wait:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"Too many failed attempts. Try again in {max(1, wait // 60)} min.",
                            headers={"Retry-After": str(wait)})
    user = (await db.execute(select(User).where(User.email == email.lower()))).scalar_one_or_none()
    if not user or not user.is_active or not verify_password(password, user.hashed_password):
        login_limiter.fail(key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    login_limiter.reset(key)
    return user


@router.post("/auth/register", response_model=TokenOut, status_code=201)
async def register(data: RegisterIn, db: AsyncSession = Depends(get_db)):
    """Self-serve signup: creates a new agency (tenant) and its owner."""
    if (await db.execute(select(User).where(User.email == data.email.lower()))).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    agency = Agency(name=data.agency_name, country=data.country.upper(), default_currency=data.currency.upper())
    db.add(agency)
    await db.flush()
    user = User(agency_id=agency.id, email=data.email.lower(), full_name=data.full_name,
                hashed_password=hash_password(data.password), role="owner")
    db.add(user)
    await db.commit()
    return _token(user)


@router.post("/auth/login", response_model=TokenOut)
async def login(request: Request, data: LoginIn, db: AsyncSession = Depends(get_db)):
    return _token(await _authenticate(request, db, data.email, data.password))


@router.post("/auth/token", response_model=TokenOut, include_in_schema=True)
async def token_form(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Form-based login used by the Swagger 'Authorize' button."""
    return _token(await _authenticate(request, db, form.username, form.password))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.get("/users", response_model=list[UserOut])
async def list_users(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await db.execute(select(User).where(User.agency_id == user.agency_id).order_by(User.created_at))
    return rows.scalars().all()


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(data: UserCreate, owner: User = Depends(require_roles("owner", "manager")),
                      db: AsyncSession = Depends(get_db)):
    if data.role == "owner":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot create another owner")
    if (await db.execute(select(User).where(User.email == data.email.lower()))).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(agency_id=owner.agency_id, email=data.email.lower(), full_name=data.full_name,
                hashed_password=hash_password(data.password), role=data.role)
    db.add(user)
    await db.commit()
    return user
