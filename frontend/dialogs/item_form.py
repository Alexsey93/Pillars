import flet as ft
from api import ItemsApi, ApiError
from models import Item


def open_add_dialog(page: ft.Page, api: ItemsApi, on_success, show_error, show_info):
    name_field = ft.TextField(label="Название", autofocus=True)

    def save():
        name = (name_field.value or "").strip()
        if not name:
            show_error("Название не может быть пустым")
            return
        try:
            api.create_item(name)
            page.pop_dialog()
            show_info(f"Добавлено: {name}")
            on_success()
        except ApiError as err:
            show_error(f"Ошибка: {err}")
        except Exception as err:
            show_error(f"Сеть недоступна: {err}")

    name_field.on_submit = lambda e: save()

    dialog = ft.AlertDialog(
        title=ft.Text("Новый предмет"),
        content=ft.Column([name_field], tight=True),
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: page.pop_dialog()),
            ft.FilledButton("Сохранить", on_click=lambda e: save()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)


def open_edit_dialog(page: ft.Page, api: ItemsApi, item: Item, on_success, show_error, show_info):
    name_field = ft.TextField(label="Название", value=item.name, autofocus=True)

    def save():
        name = (name_field.value or "").strip()
        if not name:
            show_error("Название не может быть пустым")
            return
        if name == item.name:
            page.pop_dialog()
            return
        try:
            api.update_item(item.id, name)
            page.pop_dialog()
            show_info(f"Обновлено: {name}")
            on_success()
        except ApiError as err:
            show_error(f"Ошибка: {err}")
        except Exception as err:
            show_error(f"Сеть недоступна: {err}")

    name_field.on_submit = lambda e: save()

    dialog = ft.AlertDialog(
        title=ft.Text(f"Редактировать #{item.id}"),
        content=ft.Column([name_field], tight=True),
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: page.pop_dialog()),
            ft.FilledButton("Сохранить", on_click=lambda e: save()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)