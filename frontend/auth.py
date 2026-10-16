import httpx


class AuthState:
    def __init__(self):
        self.token: str | None = None
        self.username: str | None = None
        self.is_superuser: bool = False

    def set_session(self, token: str, username: str, is_superuser: bool):
        self.token = token
        self.username = username
        self.is_superuser = is_superuser

    def clear(self):
        self.token = None
        self.username = None
        self.is_superuser = False

    def is_authenticated(self) -> bool:
        return self.token is not None

    def headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}


auth_state = AuthState()


async def login(base_url: str, username: str, password: str) -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{base_url}/auth/jwt/login",
            data={"username": username, "password": password},
        )
    if r.status_code == 400:
        raise ValueError("Неверное имя пользователя или пароль")
    if not r.is_success:
        raise ValueError(f"Ошибка сервера: HTTP {r.status_code}")
    return r.json()["access_token"]


async def register(
    base_url: str, username: str, password: str, invite_code: str
) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{base_url}/auth/register",
            json={
                "email": username,
                "password": password,
                "invite_code": invite_code,
            },
        )
    if r.status_code == 400:
        try:
            detail = r.json().get("detail", "")
        except Exception:
            detail = ""
        if "invite" in detail.lower() or "инвайт" in detail.lower():
            raise ValueError("Неверный инвайт-код")
        if "REGISTER_USER_ALREADY_EXISTS" in detail:
            raise ValueError("Пользователь с таким именем уже существует")
        raise ValueError(detail or "Ошибка регистрации")
    if r.status_code == 422:
        raise ValueError("Имя пользователя или пароль не соответствуют требованиям")
    if not r.is_success:
        raise ValueError(f"Ошибка сервера: HTTP {r.status_code}")


async def get_me(base_url: str, token: str) -> dict:
    """Получает данные текущего пользователя (email, is_superuser)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{base_url}/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    if not r.is_success:
        raise ValueError(f"Ошибка получения профиля: HTTP {r.status_code}")
    return r.json()


async def logout(base_url: str, token: str) -> None:
    """Сообщает серверу о логауте."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{base_url}/auth/jwt/logout",
                headers={"Authorization": f"Bearer {token}"},
            )
    except Exception:
        pass


async def login_or_register(
    base_url: str, username: str, password: str, invite_code: str
) -> tuple[str, dict]:
    """
    Возвращает (token, user_info).
    Пытается войти. Если пользователя нет — регистрирует с инвайт-кодом.
    """
    try:
        token = await login(base_url, username, password)
        user_info = await get_me(base_url, token)
        return token, user_info
    except ValueError:
        pass

    await register(base_url, username, password, invite_code)
    token = await login(base_url, username, password)
    user_info = await get_me(base_url, token)
    return token, user_info