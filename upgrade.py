#!/usr/bin/env python3
import ast
import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime

APP = pathlib.Path("/srv/clouddata/library/flibusta-app/app")
SOURCE = APP / "server_new.py"
TARGET = APP / "server.py"

if not SOURCE.is_file():
    sys.exit("ОШИБКА: server_new.py не найден")

original = SOURCE.read_text(encoding="utf-8")

# Проверяем ожидаемую структуру приложения.
required = [
    "def build_search(params):",
    "def show_catalog(self, params):",
    "def download_book(self):",
    "GENRE_CODES = genre_options()",
]

for marker in required:
    if marker not in original:
        sys.exit("Неизвестная версия приложения: " + marker)

# Добавляем группировку жанров.
categories = {
    "Фантастика и фэнтези": (
        "sf", "fantasy", "russian_fantasy"
    ),
    "Детективы и триллеры": (
        "det", "thriller"
    ),
    "Любовные романы": (
        "love"
    ),
    "Проза": (
        "prose"
    ),
    "Приключения": (
        "adv"
    ),
    "История": (
        "history", "sci_history"
    ),
    "Наука и образование": (
        "sci", "science", "ref", "computers"
    ),
    "Психология": (
        "psy", "psychology"
    ),
    "Бизнес": (
        "business", "economics"
    ),
    "Детская литература": (
        "child", "children"
    ),
    "Юмор": (
        "humor"
    ),
    "Поэзия": (
        "poetry"
    ),
}

category_code = repr(categories)

helpers = '''
CATEGORIES = CATEGORY_DATA

def category_for(code):
    for title, prefixes in CATEGORIES.items():
        if any(code.startswith(p) for p in prefixes):
            return title
    return "Другие жанры"

def category_catalog(selected=None):
    from urllib.parse import urlencode

    if not selected:
        items = [
            '<h2>📚 Жанры</h2>',
            '<div class="genre-grid">'
        ]
        for title in list(CATEGORIES) + ["Другие жанры"]:
            url = "?" + urlencode({"category": title})
            items.append(
                '<a class="genre-link" href="' +
                esc(url) + '">' + esc(title) + '</a>'
            )
        items.append("</div>")
        return "".join(items)

    codes = [
        code for code in GENRE_CODES
        if category_for(code) == selected
    ]

    items = [
        '<a href="/">← Все категории</a>',
        '<h2>' + esc(selected) + '</h2>',
        '<div class="genre-grid">'
    ]

    for code in codes:
        url = "?" + urlencode({"genre": code})
        items.append(
            '<a class="genre-link" href="' +
            esc(url) + '">' +
            esc(genre_name(code)) + '</a>'
        )

    items.append("</div>")
    return "".join(items)
'''

helpers = helpers.replace("CATEGORY_DATA", category_code)

anchor = "class Handler(BaseHTTPRequestHandler):"
if original.count(anchor) != 1:
    sys.exit("Ошибка структуры Handler")

original = original.replace(anchor, helpers + "\n" + anchor)

# Встраиваем каталог категорий в HTML.
anchor = '<p class="subtitle">Поиск и скачивание книг</p>'
if original.count(anchor) != 1:
    sys.exit("Не найден заголовок каталога")

original = original.replace(
    anchor,
    anchor + """
{category_catalog(
    params.get("category", [""])[0] or None
)}
"""
)

# Скрываем выдачу книг на странице категорий.
anchor = "rows, has_next, page, filters = build_search(params)"
if original.count(anchor) != 1:
    sys.exit("Не найдена обработка поиска")

original = original.replace(
    anchor,
    anchor + '''
        if params.get("category"):
            rows = []
            has_next = False
'''
)

# Добавляем оформление жанров.
anchor = "@media(max-width:600px)"
if original.count(anchor) != 1:
    sys.exit("Не найден блок мобильных стилей")

original = original.replace(
    anchor,
    """.genre-grid{{
    display:grid;
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:10px;
    margin:16px 0 24px
}}
.genre-link{{
    display:block;
    padding:16px;
    border-radius:10px;
    background:#1e293b;
    color:#5eead4;
    text-decoration:none
}}
""" + anchor
)

# Проверяем синтаксис до установки.
ast.parse(original)

backup = APP / (
    "server.py.backup-" +
    datetime.now().strftime("%Y%m%d-%H%M%S")
)

shutil.copy2(TARGET, backup)

staged = APP / "server_staged.py"
staged.write_text(original, encoding="utf-8")

subprocess.run(
    [sys.executable, "-m", "py_compile", str(staged)],
    check=True
)

print("Подготовлено:", staged)
print("Резервная копия:", backup)
print("Работающий сайт пока не изменён.")
