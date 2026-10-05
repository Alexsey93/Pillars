import flet as ft

from api import ItemsApi, ApiError
from components.items_list import ItemsList
from dialogs.confirm import open_confirm_dialog
from dialogs.item_form import open_add_dialog, open_edit_dialog


class ItemsView:
    def __init__(self, page: ft.Page, api: ItemsApi):
        self.page = page
        self.api = api
        self.loading = ft.ProgressRing(visible=False)
        self.items_list = ItemsList(on_edit=self.edit_item, on_delete=self.confirm_delete)

    # ---------- Уведомления ----------

    def show_error(self, message: str):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED_400)
        self.page.show_dialog(snack)

    def show_info(self, message: str):
        snack = ft.SnackBar(content=ft.Text(message))
        self.page.show_dialog(snack)

    # ---------- CRUD ----------

    def load_items(self, e=None):
        self.loading.visible = True
        self.page.update()
        try:
            items = self.api.list_items()
            self.items_list.set_items(items)
        except ApiError as err:
            self.show_error(f"Ошибка загрузки: {err}")
        except Exception as err:
            self.show_error(f"Сеть недоступна: {err}")
        finally:
            self.loading.visible = False
            self.page.update()

    def add_item(self, e=None):
        open_add_dialog(
            self.page, self.api,
            on_success=self.load_items,
            show_error=self.show_error,
            show_info=self.show_info,
        )

    def edit_item(self, item):
        open_edit_dialog(
            self.page, self.api, item,
            on_success=self.load_items,
            show_error=self.show_error,
            show_info=self.show_info,
        )

    def confirm_delete(self, item):
        def do_delete():
            try:
                self.api.delete_item(item.id)
                self.page.pop_dialog()
                self.show_info(f"Удалено: {item.name}")
                self.load_items()
            except ApiError as err:
                self.show_error(f"Ошибка: {err}")
            except Exception as err:
                self.show_error(f"Сеть недоступна: {err}")

        open_confirm_dialog(
            self.page,
            title="Удалить предмет?",
            message=f"«{item.name}» будет удалён безвозвратно.",
            on_confirm=do_delete,
        )

    # ---------- Построение ----------

    def build(self) -> ft.Control:
        add_btn = ft.FilledButton(
            content="Добавить",
            icon=ft.Icons.ADD,
            on_click=self.add_item,
        )
        refresh_btn = ft.Button(
            content="Обновить",
            icon=ft.Icons.REFRESH,
            on_click=self.load_items,
        )
        header = ft.Row(
            [
                ft.Text("Предметы", size=24, weight=ft.FontWeight.BOLD),
                ft.Row([refresh_btn, add_btn], spacing=8),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        return ft.Column(
            [header, self.loading, self.items_list],
            expand=True,
        )