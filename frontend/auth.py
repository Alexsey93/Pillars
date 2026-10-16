import httpx


class AuthState:
    """Хранит JWT-токен в памяти приложения."""
    def __init__(self):
        self.token: str | None = None

    def set_token(self, token: str):
        self.token = token

    def clear(self):
        self.token = None

    def is_authenticated(self) -> bool:
        return self.token is not None

    def headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}


auth_state = AuthState()


async def login(base_url: str, email: str, password: str) -> str:
    """Отправляет логин и пароль, получает JWT-токен."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{base_url}/auth/jwt/login",
            data={"username": email, "password": password},
        )
    if r.status_code == 400:
        raise ValueError("Неверный логин или пароль")
    if not r.is_success:
        raise ValueError(f"Ошибка сервера: HTTP {r.status_code}")
    data = r.json()
    return data["access_token"]