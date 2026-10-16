import flet as ft

from api import PillarsApi
from auth import auth_state, logout
from config import API_BASE_URL
from models import Registry
from views.login_view import LoginView
from views.pillars_view import PillarsView
from views.registries_view import RegistriesView


def main(page: ft.Page):
    page.title = "Pillars — опоры"
    page.padding = 16
    page.spacing = 12

    api = PillarsApi(API_BASE_URL)

    def do_logout():
        """Логаут: очищает токен и возвращает на экран входа."""
        token = auth_state.token
        auth_state.clear()
        if token:
            page.run_task(logout, api.base_url, token)
        page.run_task(api.reset_client)
        show_login()

    def show_login():
        view = LoginView(page, api, on_success=show_registries)
        page.views.clear()
        page.views.append(
            ft.View(route="/login", controls=[view.build()], padding=0)
        )
        page.update()

    def show_registries(e=None):
        view = RegistriesView(
            page=page, api=api,
            on_open_registry=open_registry,
            on_logout=do_logout,
        )
        page.views.clear()
        page.views.append(
            ft.View(
                route="/",
                controls=[view.build()],
                padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            )
        )
        page.update()
        page.run_task(view.load_registries)

    def open_registry(registry: Registry):
        view = PillarsView(
            page=page, api=api, registry=registry, on_back=go_back,
        )
        page.views.append(
            ft.View(
                route=f"/registry/{registry.id}",
                controls=[view.build()],
                padding=ft.Padding(left=16, top=16, right=16, bottom=16),
            )
        )
        page.update()
        page.run_task(view.load_pillars)

    def go_back(e=None):
        if len(page.views) > 1:
            page.views.pop()
            page.update()

    page.on_view_pop = go_back

    if auth_state.is_authenticated():
        show_registries()
    else:
        show_login()


if __name__ == "__main__":
    ft.run(main)