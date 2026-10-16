import flet as ft

from api import PillarsApi
from auth import auth_state, login


class LoginView:
    def __init__(self, page: ft.Page, api: PillarsApi, on_success):
        self.page = page
        self.api = api
        self.on_success = on_success

    def build(self) -> ft.Control:
        email_field = ft.TextField(
            label="Email", autofocus=True, width=300
        )
        password_field = ft.TextField(
            label="Пароль", password=True, can_reveal_password=True, width=300
        )
        error_text = ft.Text("", color=ft.Colors.RED_400, size=12)

        async def do_login(e=None):
            email = (email_field.value or "").strip()
            pwd = (password_field.value or "").strip()
            if not email or not pwd:
                error_text.value = "Введите email и пароль"
                self.page.update()
                return
            try:
                token = await login(self.api.base_url, email, pwd)
                auth_state.set_token(token)
                await self.api.reset_client()
                self.on_success()
            except ValueError as err:
                error_text.value = str(err)
                self.page.update()
            except Exception as err:
                error_text.value = f"Ошибка: {err}"
                self.page.update()

        password_field.on_submit = lambda e: self.page.run_task(do_login)
        login_btn = ft.FilledButton(
            content="Войти", icon=ft.Icons.LOGIN,
            on_click=lambda e: self.page.run_task(do_login),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Pillars", size=32, weight=ft.FontWeight.BOLD),
                    ft.Text("Вход в систему", size=14, color=ft.Colors.GREY_600),
                    ft.Container(height=20),
                    email_field,
                    password_field,
                    error_text,
                    ft.Container(height=8),
                    login_btn,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )