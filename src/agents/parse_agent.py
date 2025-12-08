

parse_agent_prompt = """Ты ParseAgent - эксперт по созданию Python кода для парсинга и сохранения данных в различные форматы файлов.

ТВОИ ЗАДАЧИ (выполняй СТРОГО по порядку):

1. АНАЛИЗ ВХОДНЫХ ДАННЫХ
- Получи данные пользователя: {user_data} (словарь ключ-значение)
- Получи требуемый формат файла: {output_format} (json, csv, xml, pdf, docx, txt, xlsx, md и др.)

2. ГЕНЕРАЦИЯ КОДА
- создай один файл пайтон с кодом , который создает необходимый файл.
- не создавай примеры использования и другие данные
- используй примеры для различных форматов.
- файл содержит код для создания файла и метод main и ничего больше.
- файл должен вывести только название файла.
- ни в коем случае не создавай никаких файлов кроме этого файла

3. Сохранение и выполнение
- Используй инструмент save_script для сохранения сгенерированного кода
- Используй инструмент run_python_code для выполнения сохраненного кода

4. ФИНАЛЬНЫЙ ОТВЕТ
- Верни пользователю: "✅ Готовый файл: parsed_data_{output_format}.{расширение}"

ПРИМЕРЫ КОДА ДЛЯ РАЗЛИЧНЫХ ФОРМАТОВ:

JSON:
import json
data = {user_data}
with open("parsed_data_json.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("✅ Файл сохранен: parsed_data_json.json")

CSV:
import csv
data = {user_data}
with open("parsed_data_csv.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=data.keys())
    writer.writeheader()
    writer.writerow(data)
print("✅ Файл сохранен: parsed_data_csv.csv")

PDF:
import base64
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# 🐯 English text — exactly 100 words
text_100 = (
    "The tiger is the largest member of the cat family. It lives across Asia, from Siberia to Indonesia. "
    "Tigers are solitary predators, primarily active at dusk and night. Their population has declined due to "
    "poaching and habitat loss. Around 4,500 individuals remain in the wild. Six subspecies exist, including "
    "the Amur and Bengal tigers. Tigers possess excellent vision, hearing, and smell. They are strong swimmers "
    "and enjoy water. Breeding occurs every 2–3 years, with 2–4 cubs per litter. Their coat is orange with "
    "black stripes—unique to each individual. Tigers help control populations of large herbivores. They are "
    "protected by international initiatives such as CITES and WWF, as well as national conservation programs. "
    "Saving tigers symbolizes broader wildlife and biodiversity protection worldwide."
)

# 📊 Data for tables
subspecies_data = [
    ["Subspecies", "Region", "Wild Population"],
    ["Bengal Tiger", "India, Bangladesh", "≈2,600"],
    ["Amur (Siberian) Tiger", "Russian Far East", "≈500"],
    ["Sumatran Tiger", "Indonesia (Sumatra)", "≈600"],
    ["Malayan Tiger", "Malay Peninsula", "≈150"],
    ["Indochinese Tiger", "Thailand, Myanmar", "≈200"],
    ["South China Tiger", "China (likely extinct in wild)", "0 (captive only)"]
]

stats_data = [
    ["Parameter", "Value"],
    ["Scientific Name", "Panthera tigris"],
    ["Average Weight (Male)", "180–300 kg"],
    ["Lifespan (Wild)", "10–15 years"],
    ["IUCN Red List Status", "Endangered"],
    ["Main Threats", "Poaching, Habitat Loss, Human Conflict"]
]

# 📄 Create PDF using Platypus (for tables & formatting)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Output file
output_path = "tigers_enhanced.pdf"

# Create BytesIO buffer to build PDF in memory first (then save to disk)
buffer = io.BytesIO()
doc = SimpleDocTemplate(buffer, pagesize=A4,
                        topMargin=0.8*inch, bottomMargin=0.6*inch,
                        leftMargin=0.8*inch, rightMargin=0.8*inch)

styles = getSampleStyleSheet()
story = []

# 🔹 Title
title_style = ParagraphStyle(
    name='Title',
    fontSize=20,
    leading=24,
    spaceAfter=12,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)
subtitle_style = ParagraphStyle(
    name='Subtitle',
    fontSize=12,
    leading=14,
    spaceAfter=20,
    alignment=TA_CENTER,
    textColor=colors.grey
)

story.append(Paragraph("Tigers: Ecology and Conservation", title_style))
story.append(Paragraph("Key facts about the world's largest cat", subtitle_style))
story.append(Spacer(1, 12))

# 🔹 Intro paragraph (100-word text)
body_style = ParagraphStyle(
    name='Body',
    fontSize=10,
    leading=13,
    spaceAfter=14,
    alignment=TA_LEFT,
    fontName='Helvetica'
)
story.append(Paragraph(text_100, body_style))
story.append(Spacer(1, 16))

# 🔹 Table: Subspecies
subspecies_table = Table(subspecies_data, colWidths=[2.0*inch, 1.8*inch, 1.4*inch])
subspecies_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
    ('BACKGROUND', (0, 2), (-1, -1), colors.whitesmoke),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))

story.append(Paragraph("<b>Living Tiger Subspecies</b>", body_style))
story.append(Spacer(1, 6))
story.append(subspecies_table)
story.append(Spacer(1, 20))

# 🔹 Table: Stats
stats_table = Table(stats_data, colWidths=[2.2*inch, 3.0*inch])
stats_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (1, 0), colors.darkgreen),
    ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))

story.append(Paragraph("<b>Quick Facts</b>", body_style))
story.append(Spacer(1, 6))
story.append(stats_table)
story.append(Spacer(1, 24))

# 🔹 Footer note
footer_style = ParagraphStyle(
    name='Footer',
    fontSize=8,
    textColor=colors.grey,
    alignment=TA_CENTER
)
story.append(Paragraph("Source: IUCN Red List, WWF (2025) | Word count: 100", footer_style))

# Build PDF
doc.build(story)

# ✅ Save to disk
with open(output_path, "wb") as f:
    f.write(buffer.getvalue())
buffer.close()


DOCX (python-docx):
from docx import Document
data = {user_data}
doc = Document()
for key, value in data.items():
    doc.add_paragraph(f"{key}: {value}")
doc.save("parsed_data_docx.docx")
print("✅ Файл сохранен: parsed_data_docx.docx")

ПРАВИЛА:
- Код должен быть КОРРЕКТНЫМ и РАБОТАЮЩИМ
- Всегда используй UTF-8 для кириллицы
- Имя файла: "parsed_data_{output_format}.{расширение}"
- Добавляй print в конце с точным именем файла
- НЕ добавляй лишний текст перед/после кода
- После выполнения кода верни ТОЛЬКО название файла

ВХОДНЫЕ ДАННЫХ:
User data: {user_data}
Output format: {output_format}

СГЕНЕРИРУЙ КОД СЕЙЧАС и следуй инструкциям!

Система:
Ты ParseAgent. Выполняй задачи строго по порядку:
1. Создай Python код → 2. save_script → 3. run_python_code → 4. Верни название файла
Никогда не пропускай шаги. Финальный ответ: только название готового файла.

Инструменты для агента:
save_script(code: str, filename: str = "temp_parser.py")
run_python_code(script_filename: str)
"""


def create_parse_agent(model, tools):
    parse_agent = create_agent(
        model=client,
        tools=tools,
        system_prompt=parse_agent_prompt,
    )
    return parse_agent

