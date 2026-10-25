#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Лабораторная работа №2. Вариант 10.

Данные и ограничения варианта:
    books.csv    — книги, поступившие в библиотеку начиная с 2018 года
    books-en.csv — книги, изданные начиная с 2000 года
    currency.xml — словарь «Name - CharCode»

Запуск:
    python main.py                  # все задания по books.csv (+ currency.xml)
    python main.py --en             # то же по books-en.csv
    python main.py --author Иванов  # только поиск по автору
    python main.py --xml            # только разбор currency.xml
"""

from __future__ import annotations

import csv
import json
import random
import re
import sys
import xml.dom.minidom as minidom
from pathlib import Path

HERE = Path(__file__).resolve().parent

VARIANT = 10
YEAR_PATTERN = re.compile(r"(\d{4})")

# Описание наборов данных: номера столбцов и правило ограничения выдачи.
DATASETS = {
    "ru": {
        "file": "books.csv",
        "delimiter": ";",
        "encoding": "cp1251",
        "title": 1,
        "author": 4,
        "author_short": 3,
        "year": 6,          # «Дата поступления» вида 15.10.2021 9:22
        "popularity": 8,    # «Кол-во выдач»
        "extra": 12,        # «Жанр книги» — теги
        "extra_title": "Теги (жанры) без повторений",
        "min_year": 2018,   # вариант 10: от 2018 года
        "id": 0,
    },
    "en": {
        "file": "books-en.csv",
        "delimiter": ";",
        "encoding": "cp1251",
        "title": 1,
        "author": 2,
        "author_short": 2,
        "year": 3,          # «Year-Of-Publication»
        "popularity": 5,    # «Downloads»
        "extra": 4,         # «Publisher» — издательства
        "extra_title": "Издательства без повторений",
        "min_year": 2000,   # вариант 10: от 2000 года
        "id": 0,
    },
}


# --- чтение и нормализация CSV -------------------------------------------------
def parse_year(raw: str) -> int | None:
    """Достаёт год из строки: '15.10.2021 9:22' или '2002' -> int."""
    match = YEAR_PATTERN.search(raw or "")
    return int(match.group(1)) if match else None


def load_books(mode: str) -> list[dict]:
    """Читает CSV и приводит записи к единому словарю."""
    config = DATASETS[mode]
    path = HERE / config["file"]

    books = []
    with path.open("r", encoding=config["encoding"], newline="") as file:
        table = csv.reader(file, delimiter=config["delimiter"])
        next(table, None)  # заголовок
        for row in table:
            if len(row) <= config["popularity"]:
                continue
            title = row[config["title"]].strip()
            author = row[config["author"]].strip() or row[config["author_short"]].strip()
            if not title:
                continue
            author = author or "Автор не указан"
            try:
                popularity = int(row[config["popularity"]].strip() or 0)
            except ValueError:
                popularity = 0
            books.append({
                "id": row[config["id"]].strip(),
                "title": title,
                "author": author,
                "year": parse_year(row[config["year"]]),
                "popularity": popularity,
                "extra": row[config["extra"]].strip() if len(row) > config["extra"] else "",
            })
    return books


# --- задание 1: длинные названия ----------------------------------------------
def count_long_titles(books: list[dict], limit: int = 30) -> int:
    """Количество записей, у которых название длиннее limit символов."""
    long_titles = [book for book in books if len(book["title"]) > limit]
    print(f"1) Записей, у которых название длиннее {limit} символов: "
          f"{len(long_titles)} из {len(books)}")
    for book in long_titles[:5]:
        print(f"   · {len(book['title']):3d} симв. — {book['title'][:80]}")
    if len(long_titles) > 5:
        print(f"   ... и ещё {len(long_titles) - 5}")
    return len(long_titles)


# --- задание 2: поиск по автору -----------------------------------------------
def search_by_author(books: list[dict], query: str, min_year: int) -> list[dict]:
    """Поиск по автору с ограничением выдачи: год не раньше min_year."""
    query = query.strip().lower()
    found = [
        book for book in books
        if query in book["author"].lower() and (book["year"] or 0) >= min_year
    ]
    found.sort(key=lambda book: (book["year"] or 0, book["author"]))
    return found


def print_search(query: str, min_year: int, found: list[dict]) -> None:
    print(f"2) Поиск по автору «{query}» с ограничением «от {min_year} года»: "
          f"найдено {len(found)}")
    for book in found:
        print(f"   {book['year']} | {book['author']:<40.40} | {book['title'][:70]}")


def save_search(found: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as file:
        for book in found:
            file.write(f"{book['year']} | {book['author']} | {book['title']}\n")


def interactive_search(books: list[dict], min_year: int) -> None:
    """Диалоговый поиск: пустая строка или 0 — выход."""
    print(f"Поиск книг по автору (ограничение: от {min_year} года). "
          f"0 или пустая строка — выход.")
    while True:
        try:
            query = input("Введите автора: ").strip()
        except EOFError:
            break
        if not query or query == "0":
            break
        found = search_by_author(books, query, min_year)
        if not found:
            print("   Ничего не найдено.")
            continue
        print_search(query, min_year, found)
        save_search(found, HERE / "result.txt")


# --- задание 3: библиографические ссылки --------------------------------------
def make_bibliography(books: list[dict], count: int = 20) -> list[str]:
    """Генерирует count ссылок вида «<автор>. <название> - <год>»."""
    suitable = [book for book in books if book["year"]]
    generator = random.Random(VARIANT)          # воспроизводимая выборка
    sample = generator.sample(suitable, min(count, len(suitable)))

    references = []
    for book in sample:
        title = book["title"].rstrip(".")
        references.append(f"{book['author']}. {title} - {book['year']}")
    return references


def save_bibliography(references: list[str], path: Path | None = None) -> Path:
    path = path or HERE / "bibliography.txt"
    with path.open("w", encoding="utf-8") as file:
        for number, reference in enumerate(references, start=1):
            file.write(f"{number}. {reference}\n")
    return path


# --- допзадание: уникальные значения и самые популярные книги ------------------
def unique_values(books: list[dict], mode: str) -> list[str]:
    """Теги (books.csv) или издательства (books-en.csv) без повторений."""
    values: set[str] = set()
    for book in books:
        if mode == "ru":
            values.update(tag.strip() for tag in book["extra"].split("#") if tag.strip())
        elif book["extra"]:
            values.add(book["extra"].strip())
    return sorted(values)


def top_books(books: list[dict], count: int = 20) -> list[dict]:
    """Самые популярные книги: по числу выдач (books.csv) или скачиваний."""
    return sorted(books, key=lambda book: book["popularity"], reverse=True)[:count]


def print_extras(books: list[dict], mode: str) -> None:
    values = unique_values(books, mode)
    print(f"Доп. задание 1) {DATASETS[mode]['extra_title']}: {len(values)}")
    for index, value in enumerate(values, start=1):
        print(f"   {index:2d}. {value}")

    print("\nДоп. задание 2) Самые популярные 20 книг:")
    for index, book in enumerate(top_books(books), start=1):
        print(f"   {index:2d}. {book['popularity']:5d} — {book['author'][:35]} — "
              f"{book['title'][:55]}")


# --- currency.xml: словарь «Name - CharCode» ----------------------------------
def parse_currencies(path: Path | None = None) -> dict[str, str]:
    """Разбор currency.xml: вариант 10 — словарь «Name - CharCode»."""
    path = path or HERE / "currency.xml"
    dom = minidom.parse(str(path))          # кодировка windows-1251 из заголовка
    dom.normalize()

    currencies: dict[str, str] = {}
    for node in dom.getElementsByTagName("Valute"):
        fields = {
            child.tagName: (child.firstChild.data if child.firstChild else "")
            for child in node.childNodes
            if child.nodeType == child.ELEMENT_NODE
        }
        name = fields.get("Name", "").strip()
        char_code = fields.get("CharCode", "").strip()
        if name and char_code:
            currencies[name] = char_code

    dom.unlink()
    return currencies


def print_currencies(currencies: dict[str, str]) -> None:
    print(f"currency.xml: словарь «Name - CharCode», всего записей: {len(currencies)}")
    print("{")
    for name, code in currencies.items():
        print(f"    '{name}': '{code}',")
    print("}")

    path = HERE / "currencies.json"
    with path.open("w", encoding="utf-8") as file:
        json.dump(currencies, file, ensure_ascii=False, indent=2)
    print(f"Словарь сохранён в {path.name}")


# --- точка входа ---------------------------------------------------------------
def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    args = argv[1:]
    mode = "en" if "--en" in args else "ru"
    author = None
    for index, arg in enumerate(args):
        if arg == "--author" and index + 1 < len(args):
            author = args[index + 1]

    if "--xml" not in args:
        config = DATASETS[mode]
        books = load_books(mode)
        print(f"Файл: {config['file']} ({len(books)} записей)\n")

        count_long_titles(books)
        print()

        min_year = config["min_year"]
        if author:
            found = search_by_author(books, author, min_year)
            print_search(author, min_year, found)
            save_search(found, HERE / "result.txt")
        elif sys.stdin.isatty():
            interactive_search(books, min_year)
        print()

        references = make_bibliography(books)
        path = save_bibliography(references)
        print(f"3) Библиографические ссылки ({len(references)} шт.) — файл {path.name}:")
        for number, reference in enumerate(references, start=1):
            print(f"   {number:2d}. {reference}")
        print()

        print_extras(books, mode)
        print()

    print_currencies(parse_currencies())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
