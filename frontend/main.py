import flet as ft

from api import PillarsApi
from config import API_BASE_URL
from views.items_view import PillarsView


def main(page: ft.Page):
    page.title = "Pillars — опоры"
    page.padding = 24          # было 8
    page.spacing = 12          # было 4

    api = PillarsApi(API_BASE_URL)
    view = PillarsView(page, api)

    page.add(view.build())
    page.run_task(view.load_pillars)


if __name__ == "__main__":
    ft.run(main)