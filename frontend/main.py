import flet as ft

from api import ItemsApi
from config import API_BASE_URL
from views.items_view import ItemsView


def main(page: ft.Page):
    page.title = "Pillars — предметы"
    page.padding = 20

    api = ItemsApi(API_BASE_URL)
    view = ItemsView(page, api)

    page.add(view.build())
    view.load_items()


if __name__ == "__main__":
    ft.run(main)