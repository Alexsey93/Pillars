import flet as ft

from api import PillarsApi, ApiError
from dialogs.confirm import open_confirm_dialog
from dialogs.item_form import open_add_dialog, open_edit_dialog
from models import Pillar, Registry


def _nonzero(v: str | None) -> bool:
    return v is not None and str(v).strip() not in ("", "0")


class PillarsView:
    def __init__(self, page, api, registry: Registry, on_back):
        self.page = page
        self.api = api
        self.registry = registry
        self.on_back = on_back
        self.loading = ft.ProgressRing(visible=False)
        self.pillars = []
        self.is_loading = False
        
        # Список опор (скроллится только он)
        self.list_column = ft.Column(
            spacing=8,
            scroll=ft.ScrollMode.ALWAYS,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        self.url_launcher = ft.UrlLauncher()
        self.page.services.append(self.url_launcher)

    def show_error(self, message: str):
        snack = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED_400)
        self.page.show_dialog(snack)

    def show_info(self, message: str):
        snack = ft.SnackBar(content=ft.Text(message))
        self.page.show_dialog(snack)

    async def load_pillars(self, e=None):
        if self.is_loading:
            return
        self.is_loading = True
        
        self.loading.visible = True
        self.page.update()
        try:
            pillars = await self.api.list_pillars(registry_id=self.registry.id)
            self.pillars = pillars
            self._render(pillars)
        except ApiError as err:
            self.show_error(f"Ошибка загрузки: {err}")
        except Exception as err:
            self.show_error(f"Сеть недоступна: {err}")
        finally:
            self.is_loading = False
            self.loading.visible = False
            self.page.update()

    def _render(self, pillars: list[Pillar]):
        self.list_column.controls.clear()
        
        if not pillars:
            self.list_column.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Пока нет ни одной опоры в этом реестре",
                        italic=True, size=13, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER,
                    ),
                    padding=20,
                )
            )
        else:
            for p in pillars:
                self.list_column.controls.append(self._build_tile(p))
        self.page.update()

    def _build_tile(self, pillar: Pillar) -> ft.Container:
        subtitle_parts = []
        if pillar.material:
            subtitle_parts.append(pillar.material)
        if pillar.height is not None:
            subtitle_parts.append(f"{pillar.height} м")
        if _nonzero(pillar.cnt_fastening):
            subtitle_parts.append(f"подвесов: {pillar.cnt_fastening}")
        if _nonzero(pillar.cnt_o_coup):
            subtitle_parts.append(f"опт. муфт: {pillar.cnt_o_coup}")
        if pillar.latitude is not None and pillar.longitude is not None:
            subtitle_parts.append(f"{pillar.latitude:.5f}, {pillar.longitude:.5f}")

        title = f"Опора #{pillar.id}"
        if pillar.house_number:
            title += f" · д. {pillar.house_number}"

        return ft.Container(
            padding=ft.Padding(left=12, top=8, right=8, bottom=8),
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=ft.BorderRadius.all(6),
            on_click=lambda e: self._edit_pillar(pillar),
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ELECTRIC_BOLT, size=20),
                    ft.Column(
                        controls=[
                            ft.Text(title, size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                " · ".join(subtitle_parts) if subtitle_parts else "—",
                                size=11, color=ft.Colors.GREY_700, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=0, expand=True, tight=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE, icon_size=18, icon_color=ft.Colors.RED_400,
                        tooltip="Удалить", on_click=lambda e: self._confirm_delete(pillar),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _add_pillar(self, e=None):
        open_add_dialog(self.page, self.api, self.registry.id, on_success=lambda: self.page.run_task(self.load_pillars), show_error=self.show_error, show_info=self.show_info)

    def _edit_pillar(self, pillar: Pillar):
        open_edit_dialog(self.page, self.api, pillar, on_success=lambda: self.page.run_task(self.load_pillars), show_error=self.show_error, show_info=self.show_info)

    def _confirm_delete(self, pillar: Pillar):
        def do_delete():
            self.page.run_task(self._do_delete, pillar)
        open_confirm_dialog(self.page, title="Удалить опору?", message=f"Опора #{pillar.id} будет удалена.", on_confirm=do_delete)

    async def _do_delete(self, pillar: Pillar):
        try:
            await self.api.delete_pillar(pillar.id)
            self.page.pop_dialog()
            self.show_info(f"Удалено: опора #{pillar.id}")
            await self.load_pillars()
        except ApiError as err:
            self.show_error(f"Ошибка: {err}")
        except Exception as err:
            self.show_error(f"Сеть недоступна: {err}")

    async def _export_excel(self, e=None):
        if not self.pillars:
            self.show_error("Нет данных для выгрузки")
            return
        try:
            relative_url = await self.api.get_download_link(self.registry.id)
            await self.url_launcher.launch_url(f"{self.api.base_url}{relative_url}")
        except ApiError as err:
            self.show_error(f"Ошибка получения ссылки: {err}")
        except Exception as err:
            self.show_error(f"Ошибка: {err}")

    def build(self) -> ft.Control:
        button_style = ft.ButtonStyle(padding=ft.Padding(left=14, top=0, right=14, bottom=0), text_style=ft.TextStyle(size=13))

        back_btn = ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="К реестрам", on_click=lambda e: self.on_back())

        subtitle_parts = []
        if self.registry.raion: subtitle_parts.append(self.registry.raion)
        if self.registry.city: subtitle_parts.append(self.registry.city)

        # ШАПКА: она статична и не скроллится
        header = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[back_btn, ft.Text(self.registry.street, size=18, weight=ft.FontWeight.BOLD, expand=True)], spacing=4),
                    ft.Text(f"{self.registry.region} · {' · '.join(subtitle_parts)}" if subtitle_parts else self.registry.region, size=12, color=ft.Colors.GREY_700),
                    ft.Row(
                        controls=[
                            ft.Button(content="Обновить", icon=ft.Icons.REFRESH, on_click=lambda e: self.page.run_task(self.load_pillars), height=36, style=button_style),
                            ft.FilledButton(content="Добавить опору", icon=ft.Icons.ADD, on_click=self._add_pillar, height=36, style=button_style),
                            ft.OutlinedButton(content="Экспорт в Excel", icon=ft.Icons.DOWNLOAD, on_click=lambda e: self.page.run_task(self._export_excel), height=36, style=button_style),
                        ],
                        spacing=8, alignment=ft.MainAxisAlignment.CENTER, wrap=True,
                    ),
                ],
                spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=16, top=16, right=16, bottom=16),
        )

        # ОСНОВНОЙ КОНТЕНТ
        return ft.Column(
            controls=[
                header,
                self.loading,
                # Обертка списка. expand=True заставляет список занять ВСЮ оставшуюся высоту и скроллиться
                ft.Container(content=self.list_column, expand=True, padding=ft.Padding(left=16, right=16)),
            ],
            spacing=0,
            expand=True,
        )