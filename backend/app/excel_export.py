from io import BytesIO
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

from app.models import Pillar, Registry


def generate_excel_bytes(pillars: list[Pillar], registry: Registry) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Реестр пролетов ВЛС"

    # Стили
    thin = Side(border_style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center_wrap = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Ширина колонок
    widths = {
        "A": 6, "B": 20, "C": 15, "D": 15, "E": 20, "F": 20, "G": 20,
        "H": 20, "I": 20, "J": 20, "K": 15, "L": 15, "M": 15, "N": 25,
        "O": 25, "P": 25, "Q": 25, "R": 25, "S": 25, "T": 25, "U": 25,
        "V": 25, "W": 25, "X": 25, "Y": 20, "Z": 30
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    # Шапка
    ws.merge_cells("A3:B3")
    ws["A3"] = "Реестр"
    ws["A3"].font = Font(bold=True, size=12)

    ws.merge_cells("A4:B4")
    ws["A4"] = "обследования опор"
    ws["A4"].font = Font(bold=True, size=12)

    ws["B7"] = "Филиал:"
    ws["C7"] = "Филиал в Тульской и Рязанской областях"

    ws["B8"] = "Сервичный центр/Центр эксплуатации:"
    ws["C8"] = "СЦ г. Скопин"

    ws["B9"] = "Участок обследования воздушной линии связи:"
    ws["C9"] = registry.street

    ws["B11"] = "Опись составил (ФИО, подпись):"
    ws["C11"] = ""
    ws["Y11"] = "Дата формирования документа:"
    ws["Z11"] = datetime.now().strftime('"____" _________________ %Y года')

    # Заголовки таблицы
    headers_row1 = {
        "A": "№ п/п", "B": "Наименование опоры,\nвнесенной в СЛТУ (EQM Атлас)",
        "C": "Координаты опоры (WGS84)", "D": "",
        "E": "Регион\n(область/край/республика)", "F": "Район", "G": "Населенный пункт",
        "H": "Адрес опоры", "I": "Владеющая организация", "J": "Номер учета у владельца при наличии",
        "K": "Материал опоры", "L": "Высота опоры, м.", "M": "Класс напряжения для ЛЭП, кВ",
        "N": "Кол-во точек подвеса\nРостелеком, шт.", "O": "Кол-во оптических\nкабелей Ростелеком\n(за исключением\nабонентских линий), шт",
        "P": "Кол-во медно-жильных\nкабелей Ростелеком\n(за исключением\nабонентских линий), шт.",
        "Q": "Кол-во абонентских линий Ростелеком\n(оптика+медь), шт.",
        "R": "Кол-во оптических муфт Ростелеком, шт", "S": "Кол-во ВОЛС УПМК (устройство для подвески муфт и запаса кабеля)",
        "T": "Кол-во муфт МЖК Ростелеком, шт", "U": "Кол-во МЖК УПМК (устройство для подвески муфт и запаса кабеля)",
        "V": "Кол-во шкафов Ростелеком, шт.", "W": "Кол-во ОРК Ростелеком, шт.",
        "X": "Кол-во РК Ростелеком, шт", "Y": "Кол-во выводов кабеля из грунта, шт",
        "Z": "Номер договора аренды", "AA": "Примечание, в том числе Дополнительное оборудование (видеокамеры, Кабельная площадка, лестница и т.д…)"
    }

    for col, text in headers_row1.items():
        ws[f"{col}13"] = text
        ws[f"{col}13"].font = Font(bold=True)
        ws[f"{col}13"].alignment = center_wrap

    ws.merge_cells("C13:D13")
    for col in ["A", "B", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA"]:
        ws.merge_cells(f"{col}13:{col}14")

    ws["C14"] = "Широта"
    ws["D14"] = "Долгота"
    ws["C14"].alignment = center_wrap
    ws["D14"].alignment = center_wrap

    # Данные
    start_row = 15
    for i, p in enumerate(pillars, start=start_row):
        ws[f"A{i}"] = i - start_row + 1
        ws[f"B{i}"] = ""
        
        # Координаты
        ws[f"C{i}"] = p.latitude
        ws[f"D{i}"] = p.longitude
        
        # Формат: 6 знаков после запятой
        ws[f"C{i}"].number_format = '0.000000'
        ws[f"D{i}"].number_format = '0.000000'

        # Извлекаем кириллическое значение из Enum
        ws[f"E{i}"] = registry.region.value if hasattr(registry.region, "value") else str(registry.region)
        ws[f"F{i}"] = registry.raion
        ws[f"G{i}"] = registry.city

        address = registry.street
        if p.house_number:
            address += f", {p.house_number}"
        ws[f"H{i}"] = address

        ws[f"I{i}"] = p.owner
        ws[f"J{i}"] = p.number_owner_pilar
        
        # Материал и напряжение тоже через .value
        ws[f"K{i}"] = p.material.value if p.material else ""
        ws[f"L{i}"] = p.height
        ws[f"M{i}"] = p.class_voltage.value if p.class_voltage else ""
        
        ws[f"N{i}"] = p.cnt_fastening
        ws[f"O{i}"] = p.cnt_vok_not_ab
        ws[f"P{i}"] = p.cnt_mzhk_not_ab
        ws[f"Q{i}"] = p.cnt_ab_vok_mzhk
        ws[f"R{i}"] = p.cnt_o_coup
        ws[f"S{i}"] = p.cnt_vols_upmk
        ws[f"T{i}"] = p.cnt_m_coup
        ws[f"U{i}"] = p.cnt_mzhk_upmk
        ws[f"V{i}"] = p.cnt_shk
        ws[f"W{i}"] = p.cnt_ork
        ws[f"X{i}"] = p.cnt_rk
        ws[f"Y{i}"] = p.cnt_out_on_earth
        ws[f"Z{i}"] = ""
        ws[f"AA{i}"] = ""

    # Применяем границы
    for row in ws.iter_rows(min_row=13, max_row=ws.max_row, min_col=1, max_col=27):
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(vertical="center", horizontal="center")

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()