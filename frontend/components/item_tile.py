import flet as ft
from models import Pillar


def _format_title(p: Pillar) -> str:
    parts = [f"#{p.id}", p.region]
    if p.city:
        parts.append(p.city)
    return " · ".join(parts)


def _format_subtitle(p: Pillar) -> str:
    parts = []
    if p.raion:
        parts.append(p.raion)
    if p.address:
        parts.append(p.address)
    if p.owner:
        parts.append(p.owner)
    return " · ".join(parts) if parts else "—"


def build_pillar_tile(pillar: Pillar, on_edit, on_delete) -> ft.Container:
    return ft.Container(
        padding=ft.Padding(left=10, top=6, right=4, bottom=6),
        border=ft.Border.all(1, ft.Colors.GREY_300),
        border_radius=ft.BorderRadius.all(6),
        on_click=lambda e: on_edit(pillar),
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.ELECTRIC_BOLT, size=18),
                ft.Column(
                    controls=[
                        ft.Text(
                            _format_title(pillar),
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            _format_subtitle(pillar),
                            size=11,
                            color=ft.Colors.GREY_700,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    spacing=0,
                    expand=True,
                    tight=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=16,
                    icon_color=ft.Colors.RED_400,
                    tooltip="Удалить",
                    on_click=lambda e: on_delete(pillar),
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )