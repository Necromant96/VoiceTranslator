# -*- coding: utf-8 -*-
"""Генератор презентации «Голосовой переводчик диалогов в реальном времени»."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

PRIMARY   = RGBColor(0x15, 0x65, 0xC0)   # глубокий синий
SECONDARY = RGBColor(0x00, 0x89, 0x7B)   # бирюзовый
BLUE      = RGBColor(0x1E, 0x88, 0xE5)   # сторона A
GREEN     = RGBColor(0x43, 0xA0, 0x47)   # сторона B
DARK      = RGBColor(0x26, 0x32, 0x38)
GRAY      = RGBColor(0x5F, 0x6A, 0x72)
LIGHT     = RGBColor(0xEE, 0xF1, 0xF7)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
RED_SOFT  = RGBColor(0xE0, 0x40, 0x40)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]

def add_slide():
    return prs.slides.add_slide(BLANK)

def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08):
    sp = slide.shapes.add_shape(shape, x, y, w, h)
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(1)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    sp.shadow.inherit = False
    return sp

def text(slide, x, y, w, h, s, size=18, color=DARK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, font="Calibri", line_spacing=1.0):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    first = True
    for line in s.split("\n"):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.line_spacing = line_spacing
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.name = font
        r.font.color.rgb = color
    return tb

def bullets(slide, x, y, w, h, items, size=18, color=DARK, indent_size=None, spacing=6):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for it in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(spacing)
        lvl = 0
        if isinstance(it, tuple):
            it, lvl = it
        mark = "●  " if lvl == 0 else "–  "
        if lvl == 0:
            r1 = p.add_run(); r1.text = mark; r1.font.size = Pt(size); r1.font.color.rgb = SECONDARY; r1.font.bold = True
        else:
            r1 = p.add_run(); r1.text = "      "; r1.font.size = Pt(size - 2)
        r2 = p.add_run()
        r2.text = it
        r2.font.size = Pt(size if lvl == 0 else (indent_size or size - 2))
        r2.font.color.rgb = color
        r2.font.name = "Calibri"
        if lvl == 1:
            p.level = 1
    return tb

def header(slide, num, title, subtitle=""):
    rect(slide, 0, 0, SLIDE_W, Inches(0.18), PRIMARY, shape=MSO_SHAPE.RECTANGLE)
    text(slide, Inches(0.5), Inches(0.35), Inches(10), Inches(0.7), title,
         size=30, color=PRIMARY, bold=True)
    if subtitle:
        text(slide, Inches(0.5), Inches(0.98), Inches(12.3), Inches(0.4), subtitle,
             size=14, color=GRAY)
    text(slide, Inches(12.3), Inches(7.05), Inches(0.9), Inches(0.35), str(num),
         size=12, color=GRAY, align=PP_ALIGN.RIGHT)

def chip(slide, x, y, w, h, s, fill=SECONDARY, size=13):
    sp = rect(slide, x, y, w, h, fill, radius=0.5)
    tf = sp.text_frame
    tf.word_wrap = False
    tf.margin_left = Emu(0); tf.margin_right = Emu(0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = s
    r.font.size = Pt(size); r.font.color.rgb = WHITE; r.font.bold = True
    return sp

# ================= 1. ТИТУЛЬНЫЙ СЛАЙД =================
s = add_slide()
rect(s, 0, 0, SLIDE_W, SLIDE_H, PRIMARY, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, Inches(6.9), SLIDE_W, Inches(0.6), SECONDARY, shape=MSO_SHAPE.RECTANGLE)
rect(s, Inches(4.42), Inches(1.7), Inches(4.5), Inches(1.5), WHITE, radius=0.25)
text(s, Inches(4.42), Inches(1.95), Inches(4.5), Inches(1.0), "🎤 →  А  ⇄  B",
     size=44, color=PRIMARY, bold=True, align=PP_ALIGN.CENTER)
text(s, Inches(0.9), Inches(3.6), Inches(11.5), Inches(0.9),
     "Голосовой переводчик диалогов", size=44, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
text(s, Inches(0.9), Inches(4.55), Inches(11.5), Inches(0.6),
     "в реальном времени", size=30, color=RGBColor(0xBF, 0xE4, 0xF7), align=PP_ALIGN.CENTER)
text(s, Inches(0.9), Inches(5.55), Inches(11.5), Inches(0.5),
     "Мобильное приложение для Android  •  Kotlin, без зависимостей  •  ноябрь 2026",
     size=16, color=RGBColor(0xD9, 0xEA, 0xFB), align=PP_ALIGN.CENTER)
text(s, Inches(0.9), Inches(7.0), Inches(11.5), Inches(0.4),
     "Два человека • Два языка • Один телефон",
     size=14, color=WHITE, bold=True, align=PP_ALIGN.CENTER)

# ================= 2. ПРОБЛЕМА =================
s = add_slide()
header(s, 2, "Проблема", "Почему обычные переводчики не подходят для живого диалога")
rect(s, Inches(0.5), Inches(1.6), Inches(6.1), Inches(4.9), LIGHT)
text(s, Inches(0.8), Inches(1.85), Inches(5.5), Inches(0.5), "Ситуация:", size=20, color=PRIMARY, bold=True)
bullets(s, Inches(0.8), Inches(2.4), Inches(5.4), Inches(3.9), [
    "Собеседники не понимают язык друг друга",
    "Говорим по очереди, переговариваемся через телефон",
    "Нужно быстро и без лишних кнопок",
], size=17)
rect(s, Inches(6.9), Inches(1.6), Inches(5.9), Inches(4.9), LIGHT)
text(s, Inches(7.2), Inches(1.85), Inches(5.3), Inches(0.5), "Что мешают обычные переводчики:", size=20, color=SECONDARY, bold=True)
bullets(s, Inches(7.2), Inches(2.4), Inches(5.3), Inches(3.9), [
    "Режим диалога спрятан в меню, управление общим микрофоном запутывает",
    "Не всегда понятно, кто сейчас говорит и на кого перевод",
    "Куча лишних функций: камера, офлайн-пакеты, аккаунты, реклама",
    "Возьмёшь телефон в руку — и разговор превращается в нажатие кнопок",
], size=17)

# ================= 3. РЕШЕНИЕ =================
s = add_slide()
header(s, 3, "Решение — наш переводчик", "Одна кнопка на каждого собеседника: пошёл и заговорил")
# два микрофона
box_a = rect(s, Inches(0.7), Inches(1.7), Inches(5.9), Inches(2.6), RGBColor(0xE1, 0xF2, 0xFB))
text(s, Inches(1.0), Inches(1.95), Inches(5.3), Inches(0.4), "Собеседник A 🇷🇺 (русский)", size=18, color=BLUE, bold=True)
chip(s, Inches(1.0), Inches(2.55), Inches(3.4), Inches(0.8), "🎤  Говорить (A)", fill=BLUE, size=18)
text(s, Inches(1.0), Inches(3.55), Inches(5.3), Inches(0.6), "☐ Непрерывный режим — микрофон всегда включён",
     size=13, color=GRAY)
box_b = rect(s, Inches(6.8), Inches(1.7), Inches(5.9), Inches(2.6), RGBColor(0xE3, 0xEF, 0xDF))
text(s, Inches(7.1), Inches(1.95), Inches(5.3), Inches(0.4), "Собеседник B 🇬🇧 (english)", size=18, color=GREEN, bold=True)
chip(s, Inches(7.1), Inches(2.55), Inches(3.4), Inches(0.8), "🎤  Говорить (B)", fill=GREEN, size=18)
text(s, Inches(7.1), Inches(3.55), Inches(5.3), Inches(0.6), "☐ Непрерывный режим — микрофон всегда включён",
     size=13, color=GRAY)
bullets(s, Inches(0.7), Inches(4.6), Inches(12.0), Inches(2.5), [
    "Нажали кнопку → человек А говорит → перевод появляется в чате и звучит на языке B",
    "Аналогично для B, у каждой стороны — свой язык и свой микрофон",
    "Автоозвучка на языке собеседника, история диалога с оригиналами и переводами",
    "15 языков, копирование всего диалога, кнопка ⇄ меняет языки местами",
    "Установка APK без аккаунтов, регистрации и API-ключей — работает сразу",
], size=17)

# ================= 4. КАК УСТРОЕНО (АРХИТЕКТУРА) =================
s = add_slide()
header(s, 4, "Как устроено", "Схема обработки одной реплики")
# поток
boxes = [
    ("🎤 Речь", "Микрофон телефона", BLUE),
    ("📝 Распознавание", "SpeechRecognizer\n(сервис Google в Android)", PRIMARY),
    ("🌐 Перевод", "Google Translate\nрезерв: MyMemory", SECONDARY),
    ("🔊 Озвучка", "TextToSpeech\n(синтез речи Android)", PRIMARY),
]
x = Inches(0.55)
y = Inches(1.9)
w = Inches(2.75)
gap = Inches(0.35)
for title_, sub, color in boxes:
    rect(s, x, y, w, Inches(1.7), color)
    text(s, x, y + Inches(0.15), w, Inches(0.5), title_, size=17, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(s, x, y + Inches(0.72), w, Inches(0.9), sub, size=12, color=RGBColor(0xE8, 0xF3, 0xFF), align=PP_ALIGN.CENTER)
    if x < Inches(10):
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x + w + Inches(0.02), y + Inches(0.65), Inches(0.3), Inches(0.4))
        ar.fill.solid(); ar.fill.fore_color.rgb = GRAY; ar.line.fill.background(); ar.shadow.inherit = False
    x += w + gap
rect(s, Inches(0.55), Inches(4.0), Inches(12.3), Inches(2.9), LIGHT)
text(s, Inches(0.85), Inches(4.2), Inches(11.7), Inches(0.4), "Что ещё происходит внутри:", size=16, color=PRIMARY, bold=True)
bullets(s, Inches(0.85), Inches(4.65), Inches(11.7), Inches(2.2), [
    "Реплика и её перевод добавляются в «чат» (ListView): оригинал + перевод, цвет стороны A/B",
    "Финальный текст распознан → перевод в отдельном потоке (интерфейс не подвисает)",
    "Озвучка ставится в очередь TTS; пока способ звучит — микрофон ждёт, чтобы не ловить голос переводчика",
    "Ошибки сети/распознавания → автоматический повтор; выполнено всё в одном Activity (~500 строк Kotlin)",
], size=15)

# ================= 5. НА ЧЁМ НАПИСАНО =================
s = add_slide()
header(s, 5, "На чём написано", "Стек и структура проекта")
items = [
    ("Kotlin", "весь код приложения, современный язык от Google для Android"),
    ("Android SDK 36", "API системы: SpeechRecognizer, TextToSpeech, View-компоненты"),
    ("Gradle 9.1 + AGP 8.13", "сборка проекта и APK"),
    ("без зависимостей", "ни одной сторонней библиотеки — только стандартные средства Android"),
]
y = Inches(1.75)
for t1, t2 in items:
    rect(s, Inches(0.6), y, Inches(3.4), Inches(1.0), PRIMARY, radius=0.18)
    text(s, Inches(0.7), y + Inches(0.27), Inches(3.2), Inches(0.5), t1, size=17, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(s, Inches(4.25), y + Inches(0.18), Inches(4.4), Inches(0.75), t2, size=14, color=DARK)
    y += Inches(1.18)
rect(s, Inches(8.9), Inches(1.75), Inches(3.9), Inches(4.55), DARK, radius=0.06)
text(s, Inches(9.15), Inches(1.95), Inches(3.4), Inches(0.4), "📁 Структура проекта", size=15, color=WHITE, bold=True)
text(s, Inches(9.15), Inches(2.55), Inches(3.5), Inches(3.6),
     "MainActivity.kt\n   логика: аудио → текст\n\nSpeechRecognizer\n   распознавание\n\nTextToSpeech\n   озвучка\n\nres/layout/\n   экран, чат, кнопки\n\nres/drawable/\n   стиль и кнопки UI",
     size=12, color=RGBColor(0xD5, 0xDE, 0xE6), font="Consolas")

# ================= 6. ER-ДИАГРАММА =================
s = add_slide()
header(s, 6, "ER-диаграмма данных", "Сущности приложения и связи между ними")

def entity(x, y, w, title_, rows, color):
    hh = Inches(0.5)
    bh = Inches(0.42) * len(rows)
    rect(s, x, y, w, hh, color, radius=0.08)
    rect(s, x, y + hh, w, bh, WHITE, line=color, shape=MSO_SHAPE.RECTANGLE)
    text(s, x, y + Inches(0.1), w, Inches(0.4), title_, size=15, color=WHITE,
         bold=True, align=PP_ALIGN.CENTER, font="Consolas")
    yy = y + hh + Inches(0.05)
    for fname, ftype, badge in rows:
        text(s, x + Inches(0.15), yy, w - Inches(0.3), Inches(0.4),
             (badge + " " if badge else "") + fname + " : " + ftype,
             size=12, color=DARK, font="Consolas")
        yy += Inches(0.42)

def conn(x1, y1, x2, y2, label):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                               Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = GRAY
    c.line.width = Pt(2)
    text(s, Inches((x1 + x2) / 2 - 1.1), Inches((y1 + y2) / 2 - 0.5),
         Inches(2.2), Inches(0.35), label, size=11, color=PRIMARY,
         bold=True, align=PP_ALIGN.CENTER)

# Сущности
entity(Inches(0.6), Inches(2.6), Inches(3.1), "LANGUAGE", [
    ("code", "String", "PK"),
    ("name", "String", ""),
], SECONDARY)

entity(Inches(5.05), Inches(2.3), Inches(3.2), "DIALOGUE", [
    ("id", "Long", "PK"),
    ("date_start", "DateTime", ""),
    ("lang_A", "-> Language", "FK"),
    ("lang_B", "-> Language", "FK"),
], PRIMARY)

entity(Inches(9.25), Inches(1.95), Inches(3.5), "MESSAGE", [
    ("id", "Long", "PK"),
    ("dialogue_id", "-> Dialogue", "FK"),
    ("speaker", "Int (0=A, 1=B)", ""),
    ("original_text", "String", ""),
    ("translated_text", "String", ""),
    ("created_at", "DateTime", ""),
], BLUE)

# Связи
conn(3.7, 3.05, 5.05, 3.1, "lang_A   1 : N")
conn(3.7, 3.5, 5.05, 3.55, "lang_B   1 : N")
conn(8.25, 3.4, 9.25, 3.4, "contains   1 : N")

# Легенда и пояснение
rect(s, Inches(0.55), Inches(5.35), Inches(12.25), Inches(1.55), LIGHT)
text(s, Inches(0.85), Inches(5.5), Inches(11.7), Inches(0.4),
     "PK — первичный ключ,  FK — внешний ключ (ссылка),  N — «много»",
     size=12.5, color=GRAY)
text(s, Inches(0.85), Inches(5.95), Inches(11.7), Inches(0.9),
     "В текущей версии диалог хранится в памяти (ArrayList). ER-модель — основа для\n"
     "сохранения истории в локальную базу (Room/SQLite): «Сохранённые диалоги» —\n"
     "первый пункт из планов развития приложения.",
     size=13.5, color=DARK)

# ================= 7. КЛЮЧЕВЫЕ ТЕХНИЧЕСКИЕ РЕШЕНИЯ =================
s = add_slide()
header(s, 7, "Ключевые технические решения")
cards = [
    ("🔁 Непрерывный режим",
     "После каждой реплики и паузы синтезатор сообщает о конце озвучки —\nи микрофон включается заново сам.\nПолучается живой разговор без кнопок.",
     PRIMARY),
    ("🛡 Устойчивость",
     "Ошибки распознавания (тишина, занятый сервис, сеть) обрабатываются\nпо типам: пауза разной длины, авто-повтор.\nДва переводчика: основной + резерв.",
     SECONDARY),
    ("🚫 Не мешаем друг другу",
     "Распознавание ждёт завершения озвучки, иначе микрофон слышит\nголос самого телефона.\nTTS, API-запросы и UI разнесены по потокам.",
     BLUE),
]
x = Inches(0.55)
for t1, t2, color in cards:
    rect(s, x, Inches(1.8), Inches(4.0), Inches(3.6), LIGHT)
    rect(s, x, Inches(1.8), Inches(4.0), Inches(0.85), color, radius=0.15)
    text(s, x + Inches(0.15), Inches(1.95), Inches(3.7), Inches(0.55), t1, size=16, color=WHITE, bold=True)
    text(s, x + Inches(0.2), Inches(2.85), Inches(3.6), Inches(2.4), t2, size=13.5, color=DARK)
    x += Inches(4.19)
rect(s, Inches(0.55), Inches(5.7), Inches(12.25), Inches(1.15), RGBColor(0xFF, 0xF3, 0xE0))
text(s, Inches(0.85), Inches(5.85), Inches(11.7), Inches(0.9),
     "⚙️ Нет API-ключей и регистрации: используем встроенные в Android сервисы Google. Приложение работает на любом телефоне с Android 7.0+, устанавливается одним APK-файлом.",
     size=15, color=DARK)

# ================= 7. КОНКУРЕНТЫ =================
s = add_slide()
header(s, 8, "Конкуренты", "Сравнение с популярными переводчиками")
rows, cols = 8, 5
tx, ty = Inches(0.5), Inches(1.75)
tbl_shape = s.shapes.add_table(rows, cols, tx, ty, Inches(12.4), Inches(4.6))
tbl = tbl_shape.table
tbl.columns[0].width = Inches(3.7)
for i in range(1, 5):
    tbl.columns[i].width = Inches(2.175)
data = [
    ["Критерий", "Наше приложение", "Google Translate", "Yandex Translate", "SayHi Translate"],
    ["Режим двух собеседников A↔B", "✔ отдельная кнопка каждому", "✔ общий диалог", "✔ общий диалог", "✔ общий диалог"],
    ["Непрерывный режим без нажатий", "✔ для каждой стороны", "частично", "частично", "✔ (с ограничениями)"],
    ["Автоозвучка на языке собеседника", "✔", "✔", "✔", "✔"],
    ["История: оригинал + перевод в одном списке", "✔", "частично", "✔", "✔"],
    ["Реклама и покупки", "нет", "нет", "нет", "реклама / премиум"],
    ["Регистрация и аккаунты", "не нужны", "нужен Google-аккаунт (часто)", "нужен Я.аккаунт", "не нужны"],
    ["Размер APK", "≈ 1 МБ", "≈ 120 МБ", "≈ 90 МБ", "≈ 50 МБ"],
]
for r_ in range(rows):
    for c_ in range(cols):
        cell = tbl.cell(r_, c_)
        cell.text = data[r_][c_]
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = cell.text_frame.paragraphs[0]
        para.alignment = PP_ALIGN.CENTER if c_ > 0 else PP_ALIGN.LEFT
        para.font.size = Pt(13 if r_ > 0 else 13.5)
        para.font.bold = (r_ == 0) or (c_ == 1)
        if r_ == 0:
            cell.fill.solid(); cell.fill.fore_color.rgb = PRIMARY
            para.font.color.rgb = WHITE
        elif c_ == 1:
            cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(0xE8, 0xF5, 0xE9)
            para.font.color.rgb = RGBColor(0x1B, 0x5E, 0x20)
        else:
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if r_ % 2 else RGBColor(0xF4, 0xF6, 0xFA)
            para.font.color.rgb = DARK

# ================= 8. ПОЧЕМУ НАШЕ ЛУЧШЕ =================
s = add_slide()
header(s, 9, "Почему наше приложение лучше")
rect(s, Inches(0.5), Inches(1.6), Inches(12.35), Inches(5.4), LIGHT)
points = [
    ("1", "Целевое назначение", "Создан ровно для одного сценария — живой диалог двух людей. Не надо искать «режим спасательной фразы» или переключать языки."),
    ("2", "Ноль барьеров", "Никакой рекламы, покупок, регистрации и аккаунтов. Установили APK — и сразу говорите. Работает без Google Play (важно для Huawei)."),
    ("3", "Простота", "Один экран и две большие кнопки. Поймёт любой: ребёнок и дедушка. Вся история видна на одном экране."),
    ("4", "Экономия места", "≈ 1 МБ против 50–120 МБ у конкурентов — нагрузка на память телефонов в разы меньше."),
    ("5", "Открытость и развитие", "Исходный код есть и его легко доработать: добавить языки, тёмную тему, офлайн-перевод. Конкуренты — закрытые приложения."),
]
y = Inches(1.9)
for num, t1, t2 in points:
    chip(s, Inches(0.8), y, Inches(0.5), Inches(0.5), num, fill=SECONDARY, size=18)
    text(s, Inches(1.5), y - Inches(0.03), Inches(11.2), Inches(0.4), t1, size=17, color=PRIMARY, bold=True)
    text(s, Inches(1.5), y + Inches(0.4), Inches(11.2), Inches(0.5), t2, size=14.5, color=DARK)
    y += Inches(1.02)

# ================= 9. РЕЗУЛЬТАТЫ =================
s = add_slide()
header(s, 10, "Что уже готово")
stats = [
    ("≈ 1 МБ", "размер приложения", PRIMARY),
    ("15", "языков", BLUE),
    ("0", "рекламы и ключей", GREEN),
    ("1 APK", "установка из файла", SECONDARY),
]
x = Inches(0.7)
w = Inches(2.85)
gap = Inches(0.2)
for big, small, color in stats:
    rect(s, x, Inches(1.7), w, Inches(1.9), color, radius=0.12)
    text(s, x, Inches(2.05), w, Inches(0.8), big, size=34, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    text(s, x, Inches(2.95), w, Inches(0.4), small, size=14, color=RGBColor(0xE8, 0xF3, 0xFF), align=PP_ALIGN.CENTER)
    x += w + gap
rect(s, Inches(0.7), Inches(4.1), Inches(11.95), Inches(2.7), LIGHT)
bullets(s, Inches(1.0), Inches(4.35), Inches(11.3), Inches(2.3), [
    "Собран и протестирован APK (Gradle): успешно, устанавливается на Android 7.0+",
    "Полная история диалога, копирование в буфер обмена",
    "Дизайн: чат-пузыри по сторонам, градиентная шапка, цветные кнопки-микрофоны",
    "Планы развития: определение того, кто говорит (без кнопок), офлайн-перевод ML Kit, тёмная тема, сохранение истории",
], size=16)

# ================= 10. СПАСИБО =================
s = add_slide()
rect(s, 0, 0, SLIDE_W, SLIDE_H, PRIMARY, shape=MSO_SHAPE.RECTANGLE)
rect(s, 0, Inches(0.0), SLIDE_W, Inches(0.18), SECONDARY, shape=MSO_SHAPE.RECTANGLE)
text(s, Inches(0.9), Inches(2.6), Inches(11.5), Inches(1.0), "Спасибо за внимание!", size=44, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
text(s, Inches(0.9), Inches(3.8), Inches(11.5), Inches(0.5),
     "🎤 Говорите — я переведу", size=24, color=RGBColor(0xBF, 0xE4, 0xF7), align=PP_ALIGN.CENTER)
text(s, Inches(0.9), Inches(5.0), Inches(11.5), Inches(0.4),
     "Готов показать приложение в живой демонстрации", size=16, color=RGBColor(0xD9, 0xEA, 0xFB), align=PP_ALIGN.CENTER)

prs.save(r"Презентация_Голосовой_переводчик.pptx")
print("OK")
