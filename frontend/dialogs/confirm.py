import flet as ft


def open_confirm_dialog(
    page: ft.Page,
    title: str,
    message: str,
    on_confirm,
    confirm_label: str = "Удалить",
    confirm_color=ft.Colors.RED_400,
):
    dialog = ft.AlertDialog(
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: page.pop_dialog()),
            ft.FilledButton(
                confirm_label,
                style=ft.ButtonStyle(bgcolor=confirm_color),
                on_click=lambda e: on_confirm(),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dialog)