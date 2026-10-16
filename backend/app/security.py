from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt  # ← PyJWT

from app.config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token() -> str:
    """Создаёт JWT-токен с заданным сроком жизни."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {"sub": "user", "exp": expire}
    return jwt.encode(
        payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )


async def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    """Проверяет JWT-токен. Бросает 401, если невалиден или истёк."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],  # ← список!
        )
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return sub
    except jwt.PyJWTError:  # ← исключение PyJWT
        raise credentials_exception


def verify_password(password: str) -> bool:
    """Проверяет пароль (сравнение с эталоном из настроек)."""
    return password == settings.auth_password