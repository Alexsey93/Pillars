import os
import json
import httpx
import flet as ft
from datetime import datetime, timedelta, timezone
from packaging.version import Version, InvalidVersion

GITHUB_REPO = "Alexsey93/Pillars"  # твой репозиторий
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Как часто проверять обновления (не чаще раза в сутки)
_CHECK_INTERVAL = timedelta(hours=24)
_STATE_FILE_NAME = "pillars_updater_state.json"


async def _docs_dir(page: ft.Page) -> str:
    """Папка документов приложения (для хранения состояния и скачанного APK)."""
    try:
        return await page.get_application_documents_directory()
    except Exception:
        return os.path.expanduser("~")


async def _state_path(page: ft.Page) -> str:
    return os.path.join(await _docs_dir(page), _STATE_FILE_NAME)


async def _load_state(page: ft.Page) -> dict:
    path = await _state_path(page)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


async def _save_state(page: ft.Page, state: dict) -> None:
    path = await _state_path(page)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _current_version_from_toml() -> str:
    """Fallback-версия из pyproject.toml (когда get_package_info() недоступен, например на ПК)."""
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        toml_path = os.path.join(here, "pyproject.toml")
        with open(toml_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("version ="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return "0.0.0"


async def _current_version(page: ft.Page) -> str:
    """Версия приложения: из пакета, иначе из pyproject.toml, иначе 0.0.0."""
    try:
        info = await page.get_package_info()
        v = getattr(info, "version", None) or ""
        if v:
            return v
    except Exception:
        pass
    return _current_version_from_toml()


async def _fetch_latest_release() -> dict | None:
    """Запрос последнего релиза из GitHub Releases."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                GITHUB_API, headers={"Accept": "application/vnd.github+json"}
            )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def _find_apk_url(release: dict) -> str | None:
    """Ищет ссылку на .apk среди ассетов релиза."""
    for asset in release.get("assets", []):
        name = asset.get("name", "").lower()
        if name.endswith(".apk"):
            return asset.get("browser_download_url")
    return None


async def _download_and_install(page: ft.Page, apk_url: str) -> None:
    """Скачивает APK во временную папку и открывает системный установщик."""
    try:
        page.show_dialog(ft.SnackBar(ft.Text("Скачивание обновления…")))
        docs = await _docs_dir(page)
        local_path = os.path.join(docs, "update.apk")
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            async with client.stream("GET", apk_url) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    async for chunk in r.aiter_bytes(8192):
                        f.write(chunk)
        await page.launch_url(f"file://{local_path}")
    except Exception as ex:
        page.show_dialog(ft.SnackBar(ft.Text(f"Ошибка обновления: {ex}")))


async def check_for_updates(page: ft.Page):
    """Проверяет GitHub Releases и предлагает обновиться, если есть новая версия."""
    current = await _current_version(page)

    release = await _fetch_latest_release()
    if release is None:
        return  # нет релизов или ошибка сети — молча выходим

    tag = (release.get("tag_name") or "").lstrip("v")
    if not tag:
        return

    try:
        if Version(tag) <= Version(current):
            return  # уже актуально
    except InvalidVersion:
        return  # тег не по SemVer — пропускаем

    apk_url = _find_apk_url(release)
    if not apk_url:
        return

    # Показываем диалог с предложением обновиться
    async def on_update(e):
        page.pop_dialog()
        page.run_task(_download_and_install, page, apk_url)

    dialog = ft.AlertDialog(
        title=ft.Text("Доступно обновление"),
        content=ft.Text(
            f"Текущая версия: {current}\n"
            f"Новая версия: {tag}\n\n"
            f"{release.get('body', '')[:500]}"
        ),
        actions=[
            ft.TextButton("Позже", on_click=lambda e: page.pop_dialog()),
            ft.FilledButton("Обновить", on_click=lambda e: page.run_task(on_update, e)),
        ],
    )
    page.show_dialog(dialog)


async def check_for_updates_direct(page: ft.Page) -> str:
    """Проверяет обновления в обход throttling (ручная проверка пользователем).

    Возвращает:
        'updated' — есть новая версия, диалог показали
        'uptodate' — уже актуально
        'error_api' — ошибка GitHub API
        'error_no_tag' — нет тега в релизе
        'error_uptodate' — уже актуально (сравнение версий)
        'error_invalid_version' — некорректный SemVer
        'error_no_apk' — нет APK-ассета в релизе
    """
    print("[DEBUG updater] check_for_updates_direct started")
    current = await _current_version(page)
    print(f"[DEBUG updater] current version: {current}")

    release = await _fetch_latest_release()
    if release is None:
        print("[DEBUG updater] _fetch_latest_release returned None")
        return 'error_api'

    tag = (release.get("tag_name") or "").lstrip("v")
    print(f"[DEBUG updater] tag from release: '{tag}'")
    if not tag:
        print("[DEBUG updater] no tag")
        return 'error_no_tag'

    try:
        if Version(tag) <= Version(current):
            print(f"[DEBUG updater] {tag} <= {current}, uptodate")
            return 'uptodate'
    except InvalidVersion:
        print("[DEBUG updater] InvalidVersion")
        return 'error_invalid_version'

    apk_url = _find_apk_url(release)
    print(f"[DEBUG updater] apk_url: {apk_url}")
    if not apk_url:
        print("[DEBUG updater] no apk asset found")
        return 'error_no_apk'

    # Показываем диалог с предложением обновиться
    async def on_update(e):
        page.pop_dialog()
        page.run_task(_download_and_install, page, apk_url)

    dialog = ft.AlertDialog(
        title=ft.Text("Доступно обновление"),
        content=ft.Text(
            f"Текущая версия: {current}\n"
            f"Новая версия: {tag}\n\n"
            f"{release.get('body', '')[:500]}"
        ),
        actions=[
            ft.TextButton("Позже", on_click=lambda e: page.pop_dialog()),
            ft.FilledButton("Обновить", on_click=lambda e: page.run_task(on_update, e)),
        ],
    )
    page.show_dialog(dialog)
    print("[DEBUG updater] dialog shown, returning 'updated'")
    return 'updated'


async def check_for_updates_throttled(page: ft.Page):
    """Проверяет обновления не чаще одного раза в _CHECK_INTERVAL.

    Сохраняет время последней проверки в локальном файле, чтобы при каждом
    запуске приложения не стучаться в GitHub API по пустому.
    """
    state = await _load_state(page)
    last_check_str = state.get("last_check")
    if last_check_str:
        try:
            last_check = datetime.fromisoformat(last_check_str)
            if datetime.now(timezone.utc) - last_check < _CHECK_INTERVAL:
                return  # проверяли недавно — пропускаем
        except Exception:
            pass

    await check_for_updates(page)

    # Отмечаем время проверки
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    await _save_state(page, state)