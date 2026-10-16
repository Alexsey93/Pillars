import flet as ft

from api import PillarsApi, ApiError
from config import REGIONS
from models import Registry

FIELD_WIDTH = 360
HINT_STYLE = ft.TextStyle(size=13, color=ft.Colors.GREY_600)
DIALOG_PADDING = ft.Padding(left=16, top=20, right=16, bottom=8)


def _text_field(label: str, value) -> ft.TextField:
    return ft.TextField(
        hint_text=label,
        hint_style=HINT_STYLE,
        value=value or "",
        width=FIELD_WIDTH,
    )


def _build_fields(registry: Registry | None):
    region_dd = ft.Dropdown(
        hint_text="Регион *",
        hint_style=HINT_STYLE,
        options=[ft.dropdown.Option(r) for r in REGIONS],
        value=registry.region if registry else None,
        width=FIELD_WIDTH,
    )
    raion_field = _text_field("Район", registry.raion if registry else None)
    city_field = _text_field("Населённый пункт", registry.city if registry else None)
    street_field = _text_field("Улица *", registry.street if registry else None)

    return {
        "region_dd": region_dd,
        "raion_field": raion_field,
        "city_field": city_field,
        "street_field": street_field,
    }


def _build_payload(fields: dict) -> dict:
    region = fields["region_dd"].value
    if not region:
        raise ValueError("Регион обязателен")

    street = (fields["street_field"].value or "").strip()
    if not street:
        raise ValueError("Улица обязательна")

    payload = {"region": region, "street": street}

    raion = (fields["raion_field"].value or "").strip()
    if raion:
        payload["raion"] = raion

    city = (fields["city_field"].value or "").strip()
    if city:
        payload["city"] = city

    return payload


def _build_form(fields: dict) -> ft.Column:
    return ft.Column(
        controls=[
            fields["region_dd"],
            fields["raion_field"],
            fields["city_field"],
            fields["street_field"],
        ],
        scroll=ft.ScrollMode.AUTO,
        tight=True,
        spacing=12,
        width=FIELD_WIDTH,
        height=350,
    )


async def _save_new(page, api: PillarsApi, fields, on_success, show_error, show_info):
    try:
        payload = _build_payload(fields)
    except ValueError as err:
        show_error(str(err))
        return

    try:
        await api.create_registry(payload)
        page.pop_dialog()
        show_info("Реестр создан")
        on_success()
    except ApiError as err:
        show_error(f"Ошибка: {err}")
    except Exception as err:
        show_error(f"Сеть недоступна: {err}")


async def _save_edit(
    page, api: PillarsApi, registry: Registry, fields, on_success, show_error, show_info
):
    try:
        payload = _build_payload(fields)
    except ValueError as err:
        show_error(str(err))
        return

    try:
        await api.update_registry(registry.id, payload)
        page.pop_dialog()
        show_info("Реестр обновлён")
        on_success()
    except ApiError as err:
        show_error(f"Ошибка: {err}")
    except Exception as err:
        show_error(f"Сеть недоступна: {err}")


def open_registry_add_dialog(page, api: PillarsApi, on_success, show_error, show_info):
    fields = _build_fields(None)

    def save(e=None):
        page.run_task(
            _save_new, page, api, fields, on_success, show_error, show_info
        )

    dialog = ft.AlertDialog(
        title=ft.Text("Новый реестр", size=16),
        content=ft.Container(
            content=_build_form(fields),
            padding=DIALOG_PADDING,
        ),
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: page.pop_dialog()),
            ft.FilledButton("Создать", on_click=save),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)


def open_registry_edit_dialog(
    page, api: PillarsApi, registry: Registry, on_success, show_error, show_info
):
    fields = _build_fields(registry)

    def save(e=None):
        page.run_task(
            _save_edit, page, api, registry, fields, on_success, show_error, show_info
        )

    dialog = ft.AlertDialog(
        title=ft.Text(f"Реестр #{registry.id}", size=16),
        content=ft.Container(
            content=_build_form(fields),
            padding=DIALOG_PADDING,
        ),
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: page.pop_dialog()),
            ft.FilledButton("Сохранить", on_click=save),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)