import flet as ft

from api import PillarsApi, ApiError
from auth import auth_state
from dialogs.confirm import open_confirm_dialog
from dialogs.registry_form import open_registry_add_dialog, open_registry_edit_dialog
from models import Registry
from updater import check_for_updates_direct


class RegistriesView:
    def __init__(self, page, api, on_open_registry, on_logout):
        self.page = page
        self.api = api
        self.on_open_registry = on_open_registry
        self.on_logout = on_logout
        self.loading = ft.ProgressRing(visible=False)
        self.is_loading = False
        
        self.list_column = ft.Column(
            spacing=8,
            scroll=ft.ScrollMode.ALWAYS,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def show_error(self, message: str):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED_400)
        self.page.show_dialog(snack)

    def show_info(self, message: str):
        snack = ft.SnackBar(content=ft.Text(message))
        self.page.show_dialog(snack)

    async def load_registries(self, e=None):
        if self.is_loading: return
        self.is_loading = True
        self.loading.visible = True
        self.page.update()
        try:
            registries = await self.api.list_registries()
            self._render(registries)
        except ApiError as err:
            self.show_error(f"Ошибка загрузки: {err}")
        except Exception as err:
            self.show_error(f"Сеть недоступна: {err}")
        finally:
            self.is_loading = False
            self.loading.visible = False
            self.page.update()

    def _render(self, registries: list[Registry]):
        self.list_column.controls.clear()
        if not registries:
            self.list_column.controls.append(
                ft.Container(content=ft.Text("Пока нет ни одного реестра", italic=True, size=13, color=ft.Colors.GREY_600), padding=20)
            )
        else:
            for reg in registries:
                self.list_column.controls.append(self._build_tile(reg))
        self.page.update()

    def _build_tile(self, reg: Registry) -> ft.Container:
        subtitle_parts = []
        if reg.raion: subtitle_parts.append(reg.raion)
        if reg.city: subtitle_parts.append(reg.city)
        subtitle = " · ".join(subtitle_parts) if subtitle_parts else "—"

        return ft.Container(
            padding=ft.Padding(left=12, top=8, right=8, bottom=8),
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=ft.BorderRadius.all(6),
            on_click=lambda e: self.on_open_registry(reg),
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MAP_OUTLINED, size=20),
                    ft.Column(
                        controls=[
                            ft.Text(reg.street, size=14, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"{reg.region} · {subtitle}", size=11, color=ft.Colors.GREY_700, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                        spacing=0, expand=True, tight=True,
                    ),
                    ft.IconButton(icon=ft.Icons.EDIT, icon_size=18, tooltip="Редактировать", on_click=lambda e: self._edit_registry(reg)),
                    ft.IconButton(icon=ft.Icons.CLOSE, icon_size=18, icon_color=ft.Colors.RED_400, tooltip="Удалить", on_click=lambda e: self._confirm_delete(reg)),
                ],
                spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _add_registry(self, e=None):
        open_registry_add_dialog(self.page, self.api, on_success=lambda: self.page.run_task(self.load_registries), show_error=self.show_error, show_info=self.show_info)

    async def _check_updates(self, e=None):
        """Ручная проверка обновлений по нажатию кнопки."""
        try:
            result = await check_for_updates_direct(self.page)
            if result == 'uptodate':
                self.show_info("У вас уже установлена последняя версия.")
            elif result == 'error':
                self.show_info("Не удалось проверить обновления (сеть или релиз недоступен).")
            # 'updated' — диалог уже показан внутри check_for_updates_direct
        except Exception as err:
            self.show_error(f"Ошибка проверки обновлений: {err}")

    def _edit_registry(self, reg: Registry):
        open_registry_edit_dialog(self.page, self.api, reg, on_success=lambda: self.page.run_task(self.load_registries), show_error=self.show_error, show_info=self.show_info)

    def _confirm_delete(self, reg: Registry):
        def do_delete(): self.page.run_task(self._do_delete, reg)
        open_confirm_dialog(self.page, title="Удалить реестр?", message=f"Реестр «{reg.street}» будет удалён.", on_confirm=do_delete)

    async def _do_delete(self, reg: Registry):
        try:
            await self.api.delete_registry(reg.id)
            self.page.pop_dialog()
            self.show_info(f"Удалено: {reg.street}")
            await self.load_registries()
        except ApiError as err:
            self.show_error(f"Ошибка: {err}")
        except Exception as err:
            self.show_error(f"Сеть недоступна: {err}")

    def build(self) -> ft.Control:
        button_style = ft.ButtonStyle(padding=ft.Padding(left=14, top=0, right=14, bottom=0), text_style=ft.TextStyle(size=13))
        title = f"Реестры — {auth_state.username}"
        if auth_state.is_superuser: title += " (админ)"

        # ШАПКА: не скроллится
        header = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        controls=[
                            ft.Button(content="Обновить", icon=ft.Icons.REFRESH, on_click=lambda e: self.page.run_task(self.load_registries), height=36, style=button_style),
                            ft.Button(content="Проверить обновления", icon=ft.Icons.UPDATE, on_click=lambda e: self.page.run_task(self._check_updates), height=36, style=button_style),
                            ft.FilledButton(content="Создать реестр", icon=ft.Icons.ADD, on_click=self._add_registry, height=36, style=button_style),
                            ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Выйти", on_click=lambda e: self.on_logout()),
                        ],
                        spacing=8, alignment=ft.MainAxisAlignment.CENTER, wrap=True,
                    ),
                ],
                spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
        )

        return ft.Column(
            controls=[
                header,
                self.loading,
                ft.Container(content=self.list_column, expand=True, padding=ft.Padding(left=16, right=16)),
            ],
            spacing=0,
            expand=True,
        )