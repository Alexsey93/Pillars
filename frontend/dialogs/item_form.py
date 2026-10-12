import flet as ft
import flet_geolocator as ftg

from api import PillarsApi, ApiError
from config import REGIONS, MATERIALS, CLASS_VOLTAGES
from dialogs.map_picker import open_map_picker
from models import Pillar

FIELD_WIDTH = 360
HINT_STYLE = ft.TextStyle(size=13, color=ft.Colors.GREY_600)
DIALOG_PADDING = ft.Padding(left=16, top=20, right=16, bottom=8)


# ============================================================
# ГЕОЛОКАЦИЯ
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


# ============================================================
# КАРТА
# ============================================================

async def _open_map_for_pick_async(
    page, geo, lat_field, lon_field, show_error, show_info
):
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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ПОЛЕЙ
# ============================================================

def _number_field(label: str, value, is_int: bool = False) -> ft.TextField:
    if value is None:
        text = ""
    elif is_int:
        text = str(int(value))
    else:
        text = str(value)
    return ft.TextField(
        hint_text=label,
        hint_style=HINT_STYLE,
        value=text,
        keyboard_type=ft.KeyboardType.NUMBER,
        width=FIELD_WIDTH,
    )


def _text_field(label: str, value) -> ft.TextField:
    return ft.TextField(
        hint_text=label,
        hint_style=HINT_STYLE,
        value=value or "",
        width=FIELD_WIDTH,
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
# ПОСТРОЕНИЕ ПОЛЕЙ
# ============================================================

def _build_fields(pillar: Pillar | None, page: ft.Page):
    region_dd = ft.Dropdown(
        hint_text="Регион *",
        hint_style=HINT_STYLE,
        options=[ft.dropdown.Option(r) for r in REGIONS],
        value=pillar.region if pillar else None,
        width=FIELD_WIDTH,
    )
    raion_field = _text_field("Район", pillar.raion if pillar else None)
    city_field = _text_field("Населённый пункт", pillar.city if pillar else None)
    address_field = _text_field("Улица", pillar.address if pillar else None)
    lat_field = _number_field("Широта", pillar.latitude if pillar else None)
    lon_field = _number_field("Долгота", pillar.longitude if pillar else None)

    geo = ftg.Geolocator(
        configuration=ftg.GeolocatorConfiguration(
            accuracy=ftg.GeolocatorPositionAccuracy.HIGH
        ),
        on_error=lambda e: page.show_dialog(
            ft.SnackBar(ft.Text(f"Geolocator error: {e.data}"))
        ),
    )
    page.services.append(geo)

    location_btn = ft.OutlinedButton(
        content="Моё местоположение",
        icon=ft.Icons.MY_LOCATION,
        width=170,
        on_click=lambda e: page.run_task(
            _get_current_location,
            page, geo, lat_field, lon_field,
            lambda msg: page.show_dialog(ft.SnackBar(ft.Text(msg))),
            lambda msg: page.show_dialog(ft.SnackBar(ft.Text(msg))),
        ),
    )

    pick_on_map_btn = ft.OutlinedButton(
        content="Выбрать на карте",
        icon=ft.Icons.MAP,
        width=170,
        on_click=lambda e: page.run_task(
            _open_map_for_pick_async,
            page, geo, lat_field, lon_field,
            lambda msg: page.show_dialog(ft.SnackBar(ft.Text(msg))),
            lambda msg: page.show_dialog(ft.SnackBar(ft.Text(msg))),
        ),
    )

    owner_field = _text_field(
        "Владеющая организация", pillar.owner if pillar else None
    )
    number_owner_field = _text_field(
        "Номер учёта у владельца",
        pillar.number_owner_pilar if pillar else None,
    )

    material_dd = ft.Dropdown(
        hint_text="Материал опоры",
        hint_style=HINT_STYLE,
        options=[ft.dropdown.Option(m) for m in MATERIALS],
        value=pillar.material if pillar else None,
        width=FIELD_WIDTH,
    )
    height_field = _number_field("Высота, м", pillar.height if pillar else None)
    voltage_dd = ft.Dropdown(
        hint_text="Класс напряжения",
        hint_style=HINT_STYLE,
        options=[ft.dropdown.Option(v) for v in CLASS_VOLTAGES],
        value=pillar.class_voltage if pillar else None,
        width=FIELD_WIDTH,
    )

    counters = {
        "cnt_fastening": "Кол-во точек подвеса Ростелеком",
        "cnt_vok_not_ab": "Кол-во оптических кабелей Ростелеком (не абон.)",
        "cnt_mzhk_not_ab": "Кол-во медно-жильных кабелей Ростелеком (не абон.)",
        "cnt_ab_vok_mzhk": "Кол-во абонентских линий (оптика+медь)",
        "cnt_o_coup": "Кол-во оптических муфт Ростелеком",
        "cnt_vols_upmk": "Кол-во ВОЛС УПМК",
        "cnt_m_coup": "Кол-во муфт МЖК Ростелеком",
        "cnt_mzhk_upmk": "Кол-во МЖК УПМК",
        "cnt_shk": "Кол-во шкафов Ростелеком",
        "cnt_ork": "Кол-во ОРК Ростелеком",
        "cnt_rk": "Кол-во РК Ростелеком",
        "cnt_out_on_earth": "Кол-во выводов кабеля из грунта",
    }
    counter_fields = {}
    for key, label in counters.items():
        val = getattr(pillar, key, 0) if pillar else 0
        counter_fields[key] = _number_field(label, val, is_int=True)

    return {
        "region_dd": region_dd,
        "raion_field": raion_field,
        "city_field": city_field,
        "address_field": address_field,
        "lat_field": lat_field,
        "lon_field": lon_field,
        "location_btn": location_btn,
        "pick_on_map_btn": pick_on_map_btn,
        "owner_field": owner_field,
        "number_owner_field": number_owner_field,
        "material_dd": material_dd,
        "height_field": height_field,
        "voltage_dd": voltage_dd,
        "counters": counter_fields,
    }


# ============================================================
# СБОРКА PAYLOAD
# ============================================================

def _build_payload(fields: dict) -> dict:
    region = fields["region_dd"].value
    if not region:
        raise ValueError("Регион обязателен")

    payload = {"region": region}

    for key in (
        "raion_field",
        "city_field",
        "address_field",
        "owner_field",
        "number_owner_field",
    ):
        val = (fields[key].value or "").strip()
        if val:
            payload[key.replace("_field", "")] = val

    for key, name in (
        ("lat_field", "latitude"),
        ("lon_field", "longitude"),
        ("height_field", "height"),
    ):
        val = _float_value(fields[key])
        if val is not None:
            payload[name] = val

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
    counters = fields["counters"]
    return ft.Column(
        controls=[
            ft.ExpansionTile(
                title=ft.Text("Локация", size=14),
                expanded=True,
                controls=[
                    fields["region_dd"],
                    fields["raion_field"],
                    fields["city_field"],
                    fields["address_field"],
                    fields["lat_field"],
                    fields["lon_field"],
                    ft.Row(
                        controls=[
                            fields["location_btn"],
                            fields["pick_on_map_btn"],
                        ],
                        spacing=8,
                        wrap=True,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ],
            ),
            ft.ExpansionTile(
                title=ft.Text("Владелец и учёт", size=14),
                controls=[
                    fields["owner_field"],
                    fields["number_owner_field"],
                ],
            ),
            ft.ExpansionTile(
                title=ft.Text("Характеристики опоры", size=14),
                controls=[
                    fields["material_dd"],
                    fields["height_field"],
                    fields["voltage_dd"],
                ],
            ),
            ft.ExpansionTile(
                title=ft.Text("Кабели и подвесы Ростелеком", size=14),
                controls=[
                    counters["cnt_fastening"],
                    counters["cnt_vok_not_ab"],
                    counters["cnt_mzhk_not_ab"],
                    counters["cnt_ab_vok_mzhk"],
                ],
            ),
            ft.ExpansionTile(
                title=ft.Text("Оборудование Ростелеком", size=14),
                controls=list(counters.values())[4:],
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        tight=True,
        spacing=8,
        width=FIELD_WIDTH,
        height=500,
    )


# ============================================================
# АСИНХРОННЫЕ СОХРАНЕНИЯ
# ============================================================

async def _save_new(page, api: PillarsApi, fields, on_success, show_error, show_info):
    try:
        payload = _build_payload(fields)
    except ValueError as err:
        show_error(str(err))
        return

    try:
        await api.create_pillar(payload)
        page.pop_dialog()
        show_info("Опора добавлена")
        on_success()
    except ApiError as err:
        show_error(f"Ошибка: {err}")
    except Exception as err:
        show_error(f"Сеть недоступна: {err}")


async def _save_edit(
    page, api: PillarsApi, pillar: Pillar, fields, on_success, show_error, show_info
):
    try:
        payload = _build_payload(fields)
    except ValueError as err:
        show_error(str(err))
        return

    try:
        await api.update_pillar(pillar.id, payload)
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

def open_add_dialog(page, api: PillarsApi, on_success, show_error, show_info):
    fields = _build_fields(None, page)

    def save(e=None):
        page.run_task(
            _save_new, page, api, fields, on_success, show_error, show_info
        )

    dialog = ft.AlertDialog(
        title=ft.Text("Новая опора", size=16),
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


def open_edit_dialog(
    page, api: PillarsApi, pillar: Pillar, on_success, show_error, show_info
):
    fields = _build_fields(pillar, page)

    def save(e=None):
        page.run_task(
            _save_edit, page, api, pillar, fields, on_success, show_error, show_info
        )

    dialog = ft.AlertDialog(
        title=ft.Text(f"Опора #{pillar.id}", size=16),
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