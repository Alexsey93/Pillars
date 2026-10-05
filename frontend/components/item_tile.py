import flet as ft
from models import Item


def build_item_tile(
    item: Item,
    on_edit,
    on_delete,
) -> ft.ListTile:
    return ft.ListTile(
        leading=ft.Icon(ft.Icons.INVENTORY_2),
        title=ft.Text(item.name),
        subtitle=ft.Text(f"ID: {item.id}"),
        on_click=lambda e: on_edit(item),
        trailing=ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=ft.Colors.RED_400,
            tooltip="Удалить",
            on_click=lambda e: on_delete(item),
        ),
    )