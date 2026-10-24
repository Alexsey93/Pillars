import re

import flet as ft
import flet_geolocator as ftg

from api import PillarsApi, ApiError
from config import MATERIALS, CLASS_VOLTAGES, API_BASE_URL
from dialogs.map_picker import open_map_picker
from models import Pillar
from components.photo_capture import PhotoCaptureDialog

FIELD_WIDTH = 360
LABEL_STYLE = ft.TextStyle(size=12, color=ft.Colors.GREY_700)
DIALOG_PADDING = ft.Padding(left=16, top=20, right=16, bottom=8)


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ПОЛЕЙ
# ============================================================

def _number_field(label: str, value, is_int: bool = False) -> ft.Column:
    if value is None:
        text = ""
    elif is_int:
        text = str(int(value))
    else:
        text = str(value)
    return ft.Column(
        controls=[
            ft.Text(label, size=12, color=ft.Colors.GREY_700),
            ft.TextField(
                value=text,
                keyboard_type=ft.KeyboardType.NUMBER,
                width=FIELD_WIDTH,
                height=48,
                content_padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            )
        ],
        spacing=4,
        tight=True,
    )


def _text_field(label: str, value) -> ft.Column:
    return ft.Column(
        controls=[
            ft.Text(label, size=12, color=ft.Colors.GREY_700),
            ft.TextField(
                value=value or "",
                width=FIELD_WIDTH,
                height=48,
                content_padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            )
        ],
        spacing=4,
        tight=True,
    )


def _counter_field(label: str, value: int, tooltip: str | None = None) -> ft.Column:
    field = ft.TextField(
        value=str(int(value)) if value else "0",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=FIELD_WIDTH,
        height=48,
        content_padding=ft.Padding(left=12, top=10, right=12, bottom=10),
    )
    if tooltip:
        field.suffix_icon = ft.Icon(
            ft.Icons.INFO_OUTLINE,
            size=16,
            color=ft.Colors.GREY_500,
            tooltip=tooltip,
        )
    return ft.Column(
        controls=[
            ft.Text(label, size=12, color=ft.Colors.GREY_700),
            field
        ],
        spacing=4,
        tight=True,
    )


def _dropdown_field(label: str, options: list[str], value: str | None) -> ft.Column:
    return ft.Column(
        controls=[
            ft.Text(label, size=12, color=ft.Colors.GREY_700),
            ft.Dropdown(
                options=[ft.dropdown.Option(o) for o in options],
                value=value,
                width=FIELD_WIDTH,
                height=48,
                content_padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            )
        ],
        spacing=4,
        tight=True,
    )


def _section_hint(text: str) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=ft.Colors.GREY_500),
                ft.Text(text, size=11, color=ft.Colors.GREY_600, expand=True),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=ft.Padding(left=0, top=0, right=0, bottom=8),
    )


def _int_value(field: ft.TextField) -> int | None:
    v = (field.value or "").strip()
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        raise ValueError(f"Значение «{v}» не является целым числом")


def _float_value(field: ft.TextField) -> float | None:
    v = (field.value or "").strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        raise ValueError(f"Значение «{v}» не является числом")


# ============================================================
# ГЕОЛОКАЦИЯ И КАРТА
# ============================================================

async def _get_current_location(page, geo, lat_field, lon_field, show_error, show_info):
    try:
        enabled = await geo.is_location_service_enabled()
        if not enabled:
            await geo.open_location_settings()
            show_error("Включите службу геолокации на устройстве")
            return

        permission = await geo.request_permission()
        if permission not in (
            ftg.GeolocatorPermissionStatus.WHILE_IN_USE,
            ftg.GeolocatorPermissionStatus.ALWAYS,
        ):
            show_error("Разрешение на геолокацию не получено")
            return

        pos = await geo.get_current_position()
        lat_field.value = f"{pos.latitude:.6f}"
        lon_field.value = f"{pos.longitude:.6f}"
        page.update()
        show_info(f"Координаты: {pos.latitude:.6f}, {pos.longitude:.6f}")
    except Exception as err:
        show_error(f"Ошибка геолокации: {err}")


async def _open_map_for_pick_async(page, geo, lat_field, lon_field, show_error, show_info):
    cur_lat = None
    cur_lon = None

    try:
        v = (lat_field.value or "").strip()
        if v:
            cur_lat = float(v)
    except ValueError:
        cur_lat = None

    try:
        v = (lon_field.value or "").strip()
        if v:
            cur_lon = float(v)
    except ValueError:
        cur_lon = None

    if cur_lat is None or cur_lon is None:
        try:
            enabled = await geo.is_location_service_enabled()
            if enabled:
                permission = await geo.request_permission()
                if permission in (
                    ftg.GeolocatorPermissionStatus.WHILE_IN_USE,
                    ftg.GeolocatorPermissionStatus.ALWAYS,
                ):
                    pos = await geo.get_current_position()
                    cur_lat = pos.latitude
                    cur_lon = pos.longitude
        except Exception:
            pass

    def on_pick(lat: float, lon: float):
        lat_field.value = f"{lat:.6f}"
        lon_field.value = f"{lon:.6f}"
        page.update()

    open_map_picker(page, cur_lat, cur_lon, on_pick)


# ============================================================
# ПОСТРОЕНИЕ ПОЛЕЙ
# ============================================================

def _build_fields(pillar: Pillar | None, page: ft.Page):
    house_number_col = _text_field("Номер дома", pillar.house_number if pillar else None)
    lat_col = _number_field("Широта", pillar.latitude if pillar else None)
    lon_col = _number_field("Долгота", pillar.longitude if pillar else None)

    house_number_field = house_number_col.controls[1]
    lat_field = lat_col.controls[1]
    lon_field = lon_col.controls[1]

    # --- Блок фото ---
    captured_photo = {"bytes": None}
    
    existing_photo_url = None
    if pillar and pillar.photo_url:
        existing_photo_url = f"{API_BASE_URL}{pillar.photo_url}" if pillar.photo_url.startswith("/") else pillar.photo_url

    photo_preview = ft.Container(
        width=160,
        height=120,
        border=ft.Border.all(1, ft.Colors.GREY_300),
        border_radius=ft.BorderRadius.all(8),
        bgcolor=ft.Colors.GREY_100,
        alignment=ft.Alignment.CENTER,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    def show_placeholder():
        photo_preview.content = ft.Column(
            controls=[
                ft.Icon(ft.Icons.PHOTO_CAMERA_OUTLINED, size=32, color=ft.Colors.GREY_500),
                ft.Text("Нет фото", size=11, color=ft.Colors.GREY_600),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        )
        photo_preview.on_click = None
        photo_preview.tooltip = None

    def show_image(image_bytes=None, url=None):
        if image_bytes:
            photo_preview.content = ft.Image(src=image_bytes, fit=ft.BoxFit.COVER)
        elif url:
            photo_preview.content = ft.Image(src=url, fit=ft.BoxFit.COVER)
        
        photo_preview.on_click = lambda e: view_full_photo()
        photo_preview.tooltip = "Нажмите для просмотра"

    def on_photo_captured(image_bytes: bytes):
        captured_photo["bytes"] = image_bytes
        show_image(image_bytes=image_bytes)
        page.update()

    # ОБНОВЛЕННАЯ ФУНКЦИЯ ПРОСМОТРА ФОТО НА ВЕСЬ ЭКРАН
    def view_full_photo():
        content = photo_preview.content
        if isinstance(content, ft.Image):
            # Кнопка закрытия (крестик) поверх фото
            close_btn = ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_color=ft.Colors.WHITE,
                icon_size=30,
                bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                on_click=lambda e: page.pop_dialog(),
                top=40, 
                right=20,
            )
            
            # Само фото
            full_img = ft.Image(
                src=content.src, 
                fit=ft.BoxFit.CONTAIN,
                expand=True,
            )
            
            # Накладываем кнопку на фото
            photo_stack = ft.Stack(
                controls=[full_img, close_btn],
                expand=True,
            )
            
            # Полноэкранный диалог
            full_screen_dialog = ft.AlertDialog(
                content=ft.Container(
                    content=photo_stack,
                    bgcolor=ft.Colors.BLACK,
                    expand=True,
                    padding=0,
                ),
                inset_padding=0,
                shape=ft.RoundedRectangleBorder(radius=0),
                actions_padding=0,
                actions=[],
            )
            
            page.show_dialog(full_screen_dialog)

    if existing_photo_url:
        show_image(url=existing_photo_url)
    else:
        show_placeholder()

    camera_dialog = PhotoCaptureDialog(page, on_photo_captured)

    def take_photo(e):
        page.run_task(camera_dialog.open)

    def pick_photo(e):
        page.run_task(camera_dialog.pick_file)

    photo_btn = ft.OutlinedButton(content="Сделать фото", icon=ft.Icons.CAMERA_ALT, on_click=take_photo, width=170)
    attach_btn = ft.OutlinedButton(content="Прикрепить", icon=ft.Icons.ATTACH_FILE, on_click=pick_photo, width=170)

    # --- Геолокация ---
    geo = ftg.Geolocator(
        configuration=ftg.GeolocatorConfiguration(accuracy=ftg.GeolocatorPositionAccuracy.HIGH),
        on_error=lambda e: page.show_dialog(ft.SnackBar(ft.Text(f"Geolocator error: {e.data}"))),
    )
    page.services.append(geo)

    location_btn = ft.OutlinedButton(
        content="Моё местоположение",
        icon=ft.Icons.MY_LOCATION,
        width=170,
        on_click=lambda e: page.run_task(
            _get_current_location, page, geo, lat_field, lon_field,
            lambda msg: page.show_dialog(ft.SnackBar(ft.Text(msg))),
            lambda msg: page.show_dialog(ft.SnackBar(ft.Text(msg))),
        ),
    )

    pick_on_map_btn = ft.OutlinedButton(
        content="Выбрать на карте",
        icon=ft.Icons.MAP,
        width=170,
        on_click=lambda e: page.run_task(
            _open_map_for_pick_async, page, geo, lat_field, lon_field,
            lambda msg: page.show_dialog(ft.SnackBar(ft.Text(msg))),
            lambda msg: page.show_dialog(ft.SnackBar(ft.Text(msg))),
        ),
    )

    owner_col = _text_field("Владеющая организация", pillar.owner if pillar else None)
    number_owner_col = _text_field("Номер учёта у владельца", pillar.number_owner_pilar if pillar else None)
    owner_field = owner_col.controls[1]
    number_owner_field = number_owner_col.controls[1]

    material_col = _dropdown_field("Материал опоры", MATERIALS, pillar.material if pillar else None)
    height_col = _number_field("Высота, м", pillar.height if pillar else None)
    voltage_col = _dropdown_field("Класс напряжения", CLASS_VOLTAGES, pillar.class_voltage if pillar else None)
    
    material_dd = material_col.controls[1]
    height_field = height_col.controls[1]
    voltage_dd = voltage_col.controls[1]

    counters_meta = {
        "cnt_fastening": {"label": "Кол-во точек подвеса Ростелеком", "tooltip": "Количество точек крепления кабелей Ростелеком на этой опоре."},
        "cnt_vok_not_ab": {"label": "Кол-во оптических кабелей Ростелеком (не абон.)", "tooltip": "Количество оптических кабелей (ВОК) на опоре, исключая абонентские линии."},
        "cnt_mzhk_not_ab": {"label": "Кол-во медно-жильных кабелей Ростелеком (не абон.)", "tooltip": "Количество медно-жильных кабелей (МЖК) на опоре, исключая абонентские линии."},
        "cnt_ab_vok_mzhk": {"label": "Кол-во абонентских линий (оптика+медь)", "tooltip": "Суммарное количество абонентских линий на опоре."},
        "cnt_o_coup": {"label": "Кол-во оптических муфт Ростелеком", "tooltip": "Количество оптических муфт на опоре."},
        "cnt_vols_upmk": {"label": "Кол-во ВОЛС УПМК", "tooltip": "Количество ВОЛС УПМК на опоре."},
        "cnt_m_coup": {"label": "Кол-во муфт МЖК Ростелеком", "tooltip": "Количество муфт медно-жильных кабелей."},
        "cnt_mzhk_upmk": {"label": "Кол-во МЖК УПМК", "tooltip": "Количество МЖК УПМК на опоре."},
        "cnt_shk": {"label": "Кол-во шкафов Ростелеком", "tooltip": "Количество распределительных шкафов Ростелеком."},
        "cnt_ork": {"label": "Кол-во ОРК Ростелеком", "tooltip": "Количество оптических распределительных коробок."},
        "cnt_rk": {"label": "Кол-во РК Ростелеком", "tooltip": "Количество распределительных коробок."},
        "cnt_out_on_earth": {"label": "Кол-во выводов кабеля из грунта", "tooltip": "Количество выводов кабеля из грунта."},
    }

    counter_cols = {}
    counter_fields = {}
    for key, meta in counters_meta.items():
        val = getattr(pillar, key, 0) if pillar else 0
        col = _counter_field(meta["label"], val, tooltip=meta["tooltip"])
        counter_cols[key] = col
        counter_fields[key] = col.controls[1]

    return {
        "house_number_col": house_number_col, "house_number_field": house_number_field,
        "lat_col": lat_col, "lat_field": lat_field,
        "lon_col": lon_col, "lon_field": lon_field,
        "location_btn": location_btn, "pick_on_map_btn": pick_on_map_btn,
        "photo_btn": photo_btn, "attach_btn": attach_btn,
        "photo_preview": photo_preview, "captured_photo": captured_photo,
        "owner_col": owner_col, "owner_field": owner_field,
        "number_owner_col": number_owner_col, "number_owner_field": number_owner_field,
        "material_col": material_col, "material_dd": material_dd,
        "height_col": height_col, "height_field": height_field,
        "voltage_col": voltage_col, "voltage_dd": voltage_dd,
        "counter_cols": counter_cols, "counters": counter_fields,
    }


# ============================================================
# СБОРКА PAYLOAD
# ============================================================

def _build_payload(fields: dict, registry_id: int) -> dict:
    payload = {"registry_id": registry_id}

    house = (fields["house_number_field"].value or "").strip()
    if house:
        payload["house_number"] = house

    for key, name in (("lat_field", "latitude"), ("lon_field", "longitude"), ("height_field", "height")):
        val = _float_value(fields[key])
        if val is not None:
            payload[name] = val

    for key in ("owner_field", "number_owner_field"):
        val = (fields[key].value or "").strip()
        if val:
            payload[key.replace("_field", "")] = val

    if fields["material_dd"].value:
        payload["material"] = fields["material_dd"].value
    if fields["voltage_dd"].value:
        payload["class_voltage"] = fields["voltage_dd"].value

    for key, field in fields["counters"].items():
        val = _int_value(field)
        if val is not None and val != 0:
            payload[key] = val

    return payload


# ============================================================
# ПОСТРОЕНИЕ ФОРМЫ
# ============================================================

def _build_form(fields: dict) -> ft.Column:
    counters = fields["counter_cols"]
    return ft.Column(
        controls=[
            ft.ExpansionTile(
                title=ft.Text("Адрес, координаты и фото", size=14),
                expanded=True,
                controls=[
                    ft.Column(
                        controls=[
                            fields["house_number_col"],
                            fields["lat_col"],
                            fields["lon_col"],
                            ft.Row([fields["location_btn"], fields["pick_on_map_btn"]], spacing=8, wrap=True),
                            ft.Row([fields["photo_btn"], fields["attach_btn"]], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Row([fields["photo_preview"]], alignment=ft.MainAxisAlignment.CENTER),
                        ],
                        spacing=16,
                        tight=True,
                    )
                ],
            ),
            ft.ExpansionTile(
                title=ft.Text("Владелец и учёт", size=14),
                controls=[ft.Column([fields["owner_col"], fields["number_owner_col"]], spacing=16, tight=True)],
            ),
            ft.ExpansionTile(
                title=ft.Text("Характеристики опоры", size=14),
                controls=[ft.Column([fields["material_col"], fields["height_col"], fields["voltage_col"]], spacing=16, tight=True)],
            ),
            ft.ExpansionTile(
                title=ft.Text("Кабели и подвесы Ростелеком", size=14),
                controls=[
                    ft.Column(
                        controls=[
                            _section_hint("Укажите количество кабелей, точек подвеса и абонентских линий на этой опоре. Оставьте 0, если элемент отсутствует."),
                            counters["cnt_fastening"],
                            counters["cnt_vok_not_ab"],
                            counters["cnt_mzhk_not_ab"],
                            counters["cnt_ab_vok_mzhk"],
                        ],
                        spacing=16,
                        tight=True,
                    )
                ],
            ),
            ft.ExpansionTile(
                title=ft.Text("Оборудование Ростелеком", size=14),
                controls=[
                    ft.Column(
                        controls=[
                            _section_hint("Укажите количество муфт, шкафов, коробок и других устройств Ростелеком, размещённых на опоре. Оставьте 0, если элемента нет."),
                            *list(counters.values())[4:],
                        ],
                        spacing=16,
                        tight=True,
                    )
                ],
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        tight=True,
        spacing=16,
        width=FIELD_WIDTH,
        height=650,
    )


# ============================================================
# СОХРАНЕНИЯ
# ============================================================

async def _save_new(page, api: PillarsApi, registry_id: int, street_name: str, fields, on_success, show_error, show_info):
    try:
        payload = _build_payload(fields, registry_id)
    except ValueError as err:
        show_error(str(err))
        return

    try:
        new_pillar = await api.create_pillar(payload)
        photo_bytes = fields["captured_photo"]["bytes"]
        if photo_bytes:
            house = (fields["house_number_field"].value or "no_house").strip()
            safe_street = re.sub(r'[^a-zA-Z0-9а-яА-Я_\-]', '_', street_name)
            filename = f"{safe_street}_{house}.jpg"
            await api.upload_pillar_photo(new_pillar.id, photo_bytes, filename)
            
        page.pop_dialog()
        show_info("Опора добавлена")
        on_success()
    except ApiError as err:
        show_error(f"Ошибка: {err}")
    except Exception as err:
        show_error(f"Сеть недоступна: {err}")


async def _save_edit(page, api: PillarsApi, pillar: Pillar, street_name: str, fields, on_success, show_error, show_info):
    try:
        payload = _build_payload(fields, pillar.registry_id)
    except ValueError as err:
        show_error(str(err))
        return

    try:
        await api.update_pillar(pillar.id, payload)
        photo_bytes = fields["captured_photo"]["bytes"]
        if photo_bytes:
            house = (fields["house_number_field"].value or "no_house").strip()
            safe_street = re.sub(r'[^a-zA-Z0-9а-яА-Я_\-]', '_', street_name)
            filename = f"{safe_street}_{house}.jpg"
            await api.upload_pillar_photo(pillar.id, photo_bytes, filename)

        page.pop_dialog()
        show_info("Опора обновлена")
        on_success()
    except ApiError as err:
        show_error(f"Ошибка: {err}")
    except Exception as err:
        show_error(f"Сеть недоступна: {err}")


# ============================================================
# ДИАЛОГИ
# ============================================================

def open_add_dialog(page, api: PillarsApi, registry_id: int, street_name: str, on_success, show_error, show_info):
    fields = _build_fields(None, page)
    def save(e=None):
        page.run_task(_save_new, page, api, registry_id, street_name, fields, on_success, show_error, show_info)

    dialog = ft.AlertDialog(
        title=ft.Text("Новая опора", size=16),
        content=ft.Container(content=_build_form(fields), padding=DIALOG_PADDING),
        actions=[ft.TextButton("Отмена", on_click=lambda e: page.pop_dialog()), ft.FilledButton("Сохранить", on_click=save)],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)


def open_edit_dialog(page, api: PillarsApi, pillar: Pillar, street_name: str, on_success, show_error, show_info):
    fields = _build_fields(pillar, page)
    def save(e=None):
        page.run_task(_save_edit, page, api, pillar, street_name, fields, on_success, show_error, show_info)

    dialog = ft.AlertDialog(
        title=ft.Text(f"Опора #{pillar.id}", size=16),
        content=ft.Container(content=_build_form(fields), padding=DIALOG_PADDING),
        actions=[ft.TextButton("Отмена", on_click=lambda e: page.pop_dialog()), ft.FilledButton("Сохранить", on_click=save)],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)