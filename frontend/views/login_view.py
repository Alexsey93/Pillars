import flet as ft

from api import PillarsApi
from auth import auth_state, login_or_register


class LoginView:
    def __init__(self, page: ft.Page, api: PillarsApi, on_success):
        self.page = page
        self.api = api
        self.on_success = on_success

    def build(self) -> ft.Control:
        username_field = ft.TextField(
            label="Имя пользователя", autofocus=True, width=300
        )
        password_field = ft.TextField(
            label="Пароль", password=True, can_reveal_password=True, width=300
        )
        invite_field = ft.TextField(
            label="Инвайт-код (только для новых)",
            width=300, password=True, can_reveal_password=True,
        )
        error_text = ft.Text("", color=ft.Colors.RED_400, size=12)

        async def do_login(e=None):
            username = (username_field.value or "").strip()
            pwd = (password_field.value or "").strip()
            invite = (invite_field.value or "").strip()

            if not username or not pwd:
                error_text.value = "Введите имя пользователя и пароль"
                self.page.update()
                return
            if len(pwd) < 6:
                error_text.value = "Пароль должен быть не короче 6 символов"
                self.page.update()
                return

            try:
                token, user_info = await login_or_register(
                    self.api.base_url, username, pwd, invite
                )
                auth_state.set_session(
                    token=token,
                    username=user_info["email"],
                    is_superuser=user_info.get("is_superuser", False),
                )
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
                    ft.Text(
                        "Введите имя и пароль. Для нового пользователя — инвайт-код.",
                        size=12, color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER, width=300,
                    ),
                    ft.Container(height=20),
                    username_field,
                    password_field,
                    invite_field,
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