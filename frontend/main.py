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
    page.padding = 0 # Отступы задаются внутри самих View
    page.spacing = 0

    api = PillarsApi(API_BASE_URL)

    def do_logout():
        token = auth_state.token
        auth_state.clear()
        if token:
            page.run_task(logout, api.base_url, token)
        page.run_task(api.reset_client)
        show_login()

    def show_login():
        view = LoginView(page, api, on_success=show_registries)
        page.views.clear() # Полная замена стека
        page.views.append(ft.View(route="/login", controls=[view.build()], padding=0))
        page.update()

    def show_registries(e=None):
        view = RegistriesView(page=page, api=api, on_open_registry=open_registry, on_logout=do_logout)
        page.views.clear() # Полная замена стека
        page.views.append(ft.View(route="/", controls=[view.build()], padding=0))
        page.update()
        page.run_task(view.load_registries)

    def open_registry(registry: Registry):
        # Защита от двойного клика
        if page.views and page.views[-1].route == f"/registry/{registry.id}":
            return

        view = PillarsView(page=page, api=api, registry=registry, on_back=go_back)
        page.views.append(ft.View(route=f"/registry/{registry.id}", controls=[view.build()], padding=0))
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