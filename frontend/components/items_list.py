import flet as ft
from models import Item
from components.item_tile import build_item_tile


class ItemsList(ft.Column):
    """Список предметов с поддержкой пустого состояния."""

    def __init__(self, on_edit, on_delete):
        super().__init__(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self.on_edit = on_edit
        self.on_delete = on_delete

    def set_items(self, items: list[Item]):
        self.controls.clear()
        if not items:
            self.controls.append(
                ft.Text("Пока нет ни одного предмета", italic=True)
            )
        else:
            for item in items:
                self.controls.append(
                    build_item_tile(item, self.on_edit, self.on_delete)
                )
        self.update()