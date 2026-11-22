import flet as ft
from models import Pillar
from components.item_tile import build_pillar_tile


class PillarsList(ft.Column):
    def __init__(self, on_edit, on_delete):
        super().__init__(
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            expand=True,  # Занимает всё доступное пространство для работы скролла
        )
        self.on_edit = on_edit
        self.on_delete = on_delete

    def set_items(self, pillars: list[Pillar]):
        self.controls.clear()
        if not pillars:
            self.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Пока нет ни одной опоры",
                        italic=True,
                        size=13,
                        color=ft.Colors.GREY_600,
                    ),
                    padding=ft.Padding(left=8, top=16, right=8, bottom=16),
                )
            )
        else:
            for p in pillars:
                self.controls.append(
                    build_pillar_tile(p, self.on_edit, self.on_delete)
                )
        self.update()