import flet as ft

from api import PillarsApi, ApiError
from components.items_list import PillarsList
from dialogs.confirm import open_confirm_dialog
from dialogs.item_form import open_add_dialog, open_edit_dialog


class PillarsView:
    def __init__(self, page: ft.Page, api: PillarsApi):
        self.page = page
        self.api = api
        self.loading = ft.ProgressRing(visible=False)
        self.pillars_list = PillarsList(
            on_edit=self.edit_pillar, on_delete=self.confirm_delete
        )

    def show_error(self, message: str):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED_400)
        self.page.show_dialog(snack)

    def show_info(self, message: str):
        snack = ft.SnackBar(content=ft.Text(message))
        self.page.show_dialog(snack)

    def load_pillars(self, e=None):
        self.loading.visible = True
        self.page.update()
        try:
            pillars = self.api.list_pillars()
            self.pillars_list.set_items(pillars)
        except ApiError as err:
            self.show_error(f"Ошибка загрузки: {err}")
        except Exception as err:
            self.show_error(f"Сеть недоступна: {err}")
        finally:
            self.loading.visible = False
            self.page.update()

    def add_pillar(self, e=None):
        open_add_dialog(
            self.page, self.api,
            on_success=self.load_pillars,
            show_error=self.show_error,
            show_info=self.show_info,
        )

    def edit_pillar(self, pillar):
        open_edit_dialog(
            self.page, self.api, pillar,
            on_success=self.load_pillars,
            show_error=self.show_error,
            show_info=self.show_info,
        )

    def confirm_delete(self, pillar):
        def do_delete():
            try:
                self.api.delete_pillar(pillar.id)
                self.page.pop_dialog()
                self.show_info(f"Удалено: {pillar.region}")
                self.load_pillars()
            except ApiError as err:
                self.show_error(f"Ошибка: {err}")
            except Exception as err:
                self.show_error(f"Сеть недоступна: {err}")

        open_confirm_dialog(
            self.page,
            title="Удалить опору?",
            message=f"Опора #{pillar.id} ({pillar.region}) будет удалена.",
            on_confirm=do_delete,
        )

    def build(self) -> ft.Control:
        button_style = ft.ButtonStyle(
            padding=ft.Padding(left=12, top=0, right=12, bottom=0),
            text_style=ft.TextStyle(size=13),
        )

        add_btn = ft.FilledButton(
            content="Добавить",
            icon=ft.Icons.ADD,
            on_click=self.add_pillar,
            height=32,
            style=button_style,
        )
        refresh_btn = ft.Button(
            content="Обновить",
            icon=ft.Icons.REFRESH,
            on_click=self.load_pillars,
            height=32,
            style=button_style,
        )

        header = ft.Row(
            controls=[
                ft.Text("Опоры", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([refresh_btn, add_btn], spacing=4),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Column(
            controls=[header, self.loading, self.pillars_list],
            spacing=8,
            expand=True,
        )