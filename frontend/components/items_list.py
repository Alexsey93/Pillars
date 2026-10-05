import flet as ft
from models import Pillar
from components.item_tile import build_pillar_tile


class PillarsList(ft.Column):
    def __init__(self, on_edit, on_delete):
        super().__init__(
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.on_edit = on_edit
        self.on_delete = on_delete

    def set_items(self, pillars: list[Pillar]):
        self.controls.clear()
        if not pillars:
            self.controls.append(
                ft.Text("Пока нет ни одной опоры", italic=True, size=13)
            )
        else:
            for p in pillars:
                self.controls.append(
                    build_pillar_tile(p, self.on_edit, self.on_delete)
                )
        self.update()