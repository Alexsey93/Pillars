import flet as ft
import flet_map as ftm

FALLBACK_LAT = 61.524
FALLBACK_LON = 105.318
FALLBACK_ZOOM = 4
DEFAULT_ZOOM = 16

MAP_PADDING = ft.Padding(left=16, top=0, right=16, bottom=0)


def open_map_picker(
    page: ft.Page,
    initial_lat: float | None,
    initial_lon: float | None,
    on_pick,
):
    has_coords = initial_lat is not None and initial_lon is not None

    if has_coords:
        start_lat = initial_lat
        start_lon = initial_lon
        start_zoom = DEFAULT_ZOOM
    else:
        start_lat = FALLBACK_LAT
        start_lon = FALLBACK_LON
        start_zoom = FALLBACK_ZOOM

    marker_layer_ref = ft.Ref[ftm.MarkerLayer]()
    selected = {"lat": start_lat, "lon": start_lon}

    def build_marker(lat: float, lon: float) -> ftm.Marker:
        return ftm.Marker(
            content=ft.Icon(
                ft.Icons.LOCATION_ON,
                color=ft.Colors.RED_400,
                size=36,
            ),
            coordinates=ftm.MapLatitudeLongitude(lat, lon),
            alignment=ft.Alignment.CENTER,
        )

    def handle_tap(e: ftm.MapTapEvent):
        coords = e.coordinates
        selected["lat"] = coords.latitude
        selected["lon"] = coords.longitude
        marker_layer_ref.current.markers = [
            build_marker(coords.latitude, coords.longitude)
        ]
        page.update()

    map_control = ftm.Map(
        expand=True,
        initial_center=ftm.MapLatitudeLongitude(start_lat, start_lon),
        initial_zoom=start_zoom,
        interaction_configuration=ftm.InteractionConfiguration(
            flags=ftm.InteractionFlag.ALL
        ),
        on_tap=handle_tap,
        layers=[
            ftm.TileLayer(
                url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                user_agent_package_name="Pillars/1.0",
            ),
            ftm.MarkerLayer(
                ref=marker_layer_ref,
                markers=[build_marker(start_lat, start_lon)] if has_coords else [],
            ),
        ],
    )

    def on_confirm(e):
        page.pop_dialog()
        on_pick(selected["lat"], selected["lon"])

    dialog = ft.AlertDialog(
        title=ft.Text("Выберите точку на карте", size=16),
        content=ft.Container(
            content=map_control,
            width=600,
            height=500,
            padding=MAP_PADDING,
        ),
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: page.pop_dialog()),
            ft.FilledButton("Выбрать", on_click=on_confirm),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)