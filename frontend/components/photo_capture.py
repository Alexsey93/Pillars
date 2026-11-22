import flet as ft
import flet_camera as fc
import flet_permission_handler as fph


class PhotoCaptureDialog:
    def __init__(self, page: ft.Page, on_capture):
        self.page = page
        self.on_capture = on_capture
        self.camera = None
        self.permission_handler = fph.PermissionHandler()
        self.page.services.append(self.permission_handler)
        
        self.file_picker = ft.FilePicker()
        self.page.services.append(self.file_picker)

    async def open(self):
        # 1. Запрашиваем разрешение (на телефоне)
        if not self.page.web:
            status = await self.permission_handler.request(fph.Permission.CAMERA)
            if status != fph.PermissionStatus.GRANTED:
                self.page.show_dialog(ft.SnackBar(ft.Text("Нет доступа к камере")))
                return

        # 2. Создаем виджет камеры
        self.camera = fc.Camera(
            expand=True,
            preview_enabled=True,
        )

        # 3. Функции управления
        async def take_photo(ev):
            try:
                image_bytes = await self.camera.take_picture()
                if image_bytes:
                    self.page.pop_dialog()
                    self.camera = None
                    self.on_capture(image_bytes)
                else:
                    self.page.show_dialog(ft.SnackBar(ft.Text("Не удалось сделать снимок")))
            except Exception as ex:
                self.page.show_dialog(ft.SnackBar(ft.Text(f"Ошибка камеры: {ex}")))

        def close_dialog(ev):
            self.page.pop_dialog()
            self.camera = None

        # 4. Элементы управления поверх камеры (Stack)
        close_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=ft.Colors.WHITE,
            icon_size=30,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            on_click=close_dialog,
            top=40,
            right=20,
        )
        
        capture_btn = ft.Container(
            content=ft.Icon(ft.Icons.CAMERA, color=ft.Colors.WHITE, size=40),
            width=80,
            height=80,
            border_radius=40,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            alignment=ft.Alignment.CENTER,
            on_click=lambda ev: self.page.run_task(take_photo, ev),
            bottom=40,
            left=0,
            right=0,
        )

        # 5. ПОЛНОЭКРАННЫЙ диалог
        dialog = ft.AlertDialog(
            inset_padding=0,
            content_padding=0,
            shape=ft.RoundedRectangleBorder(radius=0),
            bgcolor=ft.Colors.BLACK,
            content=ft.Stack(
                controls=[
                    self.camera,
                    close_btn,
                    capture_btn,
                ],
                expand=True,
            ),
            actions=[],
            actions_padding=0,
        )
        
        self.page.show_dialog(dialog)
        self.page.update()

        # 6. ИНИЦИАЛИЗИРУЕМ КАМЕРУ ТОЛЬКО ПОСЛЕ ТОГО, КАК ОНА НА ЭКРАНЕ
        try:
            cameras = await self.camera.get_available_cameras()
            if not cameras:
                self.page.pop_dialog()
                self.camera = None
                self.page.show_dialog(ft.SnackBar(ft.Text("Камера не найдена")))
                return

            await self.camera.initialize(
                description=cameras[0],
                resolution_preset=fc.ResolutionPreset.MEDIUM,
                enable_audio=False,
                image_format_group=fc.ImageFormatGroup.JPEG,
            )
        except Exception as ex:
            self.page.pop_dialog()
            self.camera = None
            self.page.show_dialog(ft.SnackBar(ft.Text(f"Ошибка инициализации камеры: {ex}")))

    async def pick_file(self, ev=None):
        files = await self.file_picker.pick_files(
            dialog_title="Выберите фото",
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE,
            with_data=True,
        )
        
        if not files:
            return

        file = files[0]
        if file.bytes:
            self.on_capture(file.bytes)
        elif file.path:
            try:
                with open(file.path, "rb") as f:
                    image_bytes = f.read()
                self.on_capture(image_bytes)
            except Exception as ex:
                self.page.show_dialog(ft.SnackBar(ft.Text(f"Ошибка чтения файла: {ex}")))
        else:
            self.page.show_dialog(ft.SnackBar(ft.Text("Не удалось получить данные файла")))