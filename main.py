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

Идея решения: оба CSV-файла приводятся к одному списку словарей
(название, автор, год, популярность, теги/издательство), а номера нужных
столбцов и правило варианта описаны в DATASETS. Дальше все задания работают
с этим списком и не зависят от того, какой из файлов выбран.
"""

from __future__ import annotations

import csv               # чтение CSV с разделителем ';'
import json              # сохранение словаря валют в JSON
import random            # воспроизводимая выборка 20 книг
import re                # поиск года регулярным выражением
import sys               # аргументы командной строки, stdin/stdout
import xml.dom.minidom as minidom   # разбор currency.xml (как рекомендовано в задании)
from pathlib import Path            # пути к файлам рядом со скриптом

HERE = Path(__file__).resolve().parent   # папка со скриптом и данными

VARIANT = 10                             # номер варианта (он же seed для random)
YEAR_PATTERN = re.compile(r"(\d{4})")    # четыре подряд идущие цифры = год

# Описание наборов данных: номера столбцов и правило ограничения выдачи.
DATASETS = {
    "ru": {
        "file": "books.csv",              # имя файла
        "delimiter": ";",                 # разделитель полей
        "encoding": "cp1251",             # кодировка файла
        "title": 1,                       # «Название»
        "author": 4,                      # «Автор (ФИО)»
        "author_short": 3,                # «Автор» — запасной вариант
        "year": 6,                        # «Дата поступления» вида 15.10.2021 9:22
        "popularity": 8,                  # «Кол-во выдач»
        "extra": 12,                      # «Жанр книги» — теги
        "extra_title": "Теги (жанры) без повторений",
        "min_year": 2018,                 # вариант 10: от 2018 года
        "id": 0,                          # столбец с ID
    },
    "en": {
        "file": "books-en.csv",
        "delimiter": ";",
        "encoding": "cp1251",
        "title": 1,                       # «Book-Title»
        "author": 2,                      # «Book-Author»
        "author_short": 2,
        "year": 3,                        # «Year-Of-Publication»
        "popularity": 5,                  # «Downloads»
        "extra": 4,                       # «Publisher» — издательства
        "extra_title": "Издательства без повторений",
        "min_year": 2000,                 # вариант 10: от 2000 года
        "id": 0,
    },
}


# --- чтение и нормализация CSV -------------------------------------------------
def parse_year(raw: str) -> int | None:
    """Достаёт год из строки: '15.10.2021 9:22' или '2002' -> int."""
    match = YEAR_PATTERN.search(raw or "")     # ищем первые четыре цифры
    return int(match.group(1)) if match else None   # нашли — число, иначе None


def load_books(mode: str) -> list[dict]:
    """Читает CSV и приводит записи к единому словарю."""
    config = DATASETS[mode]                    # настройки выбранного файла
    path = HERE / config["file"]               # полный путь к файлу

    books = []                                 # сюда сложим все записи
    with path.open("r", encoding=config["encoding"], newline="") as file:
        table = csv.reader(file, delimiter=config["delimiter"])   # читаем построчно
        next(table, None)                      # пропускаем строку заголовка
        for row in table:                      # каждая строка — одна книга
            if len(row) <= config["popularity"]:   # битая строка — пропускаем
                continue
            title = row[config["title"]].strip()                        # название
            author = row[config["author"]].strip() or \
                row[config["author_short"]].strip()                     # автор
            if not title:                      # без названия запись бесполезна
                continue
            author = author or "Автор не указан"      # пустого автора помечаем
            try:                               # популярность может быть пустой
                popularity = int(row[config["popularity"]].strip() or 0)
            except ValueError:
                popularity = 0                 # не число — считаем нулём
            books.append({                     # одна нормализованная запись
                "id": row[config["id"]].strip(),
                "title": title,
                "author": author,
                "year": parse_year(row[config["year"]]),        # год числом
                "popularity": popularity,
                "extra": row[config["extra"]].strip()
                if len(row) > config["extra"] else "",
            })
    return books


# --- задание 1: длинные названия ----------------------------------------------
def count_long_titles(books: list[dict], limit: int = 30) -> int:
    """Количество записей, у которых название длиннее limit символов."""
    long_titles = [book for book in books if len(book["title"]) > limit]   # фильтр
    print(f"1) Записей, у которых название длиннее {limit} символов: "
          f"{len(long_titles)} из {len(books)}")
    for book in long_titles[:5]:               # показываем несколько примеров
        print(f"   · {len(book['title']):3d} симв. — {book['title'][:80]}")
    if len(long_titles) > 5:                   # и сообщаем, сколько осталось
        print(f"   ... и ещё {len(long_titles) - 5}")
    return len(long_titles)


# --- задание 2: поиск по автору -----------------------------------------------
def search_by_author(books: list[dict], query: str, min_year: int) -> list[dict]:
    """Поиск по автору с ограничением выдачи: год не раньше min_year."""
    query = query.strip().lower()              # ищем без учёта регистра
    found = [
        book for book in books                 # условие: автор содержит запрос
        if query in book["author"].lower() and (book["year"] or 0) >= min_year
    ]
    found.sort(key=lambda book: (book["year"] or 0, book["author"]))   # сортируем
    return found


def print_search(query: str, min_year: int, found: list[dict]) -> None:
    """Печатает результаты поиска в виде таблицы «год | автор | название»."""
    print(f"2) Поиск по автору «{query}» с ограничением «от {min_year} года»: "
          f"найдено {len(found)}")
    for book in found:                         # одна строка на книгу
        print(f"   {book['year']} | {book['author']:<40.40} | {book['title'][:70]}")


def save_search(found: list[dict], path: Path) -> None:
    """Сохраняет найденные книги в текстовый файл."""
    with path.open("w", encoding="utf-8") as file:   # файл перезаписывается
        for book in found:                            # по одной записи на строку
            file.write(f"{book['year']} | {book['author']} | {book['title']}\n")


def interactive_search(books: list[dict], min_year: int) -> None:
    """Диалоговый поиск: пустая строка или 0 — выход."""
    print(f"Поиск книг по автору (ограничение: от {min_year} года). "
          f"0 или пустая строка — выход.")
    while True:                                # повторяем, пока не попросят выйти
        try:
            query = input("Введите автора: ").strip()   # запрос пользователя
        except EOFError:                       # конец ввода (Ctrl+Z) — выходим
            break
        if not query or query == "0":          # пустой ввод или 0 — выход
            break
        found = search_by_author(books, query, min_year)    # ищем
        if not found:                          # ничего не нашли
            print("   Ничего не найдено.")
            continue
        print_search(query, min_year, found)   # печатаем результаты
        save_search(found, HERE / "result.txt")   # и сохраняем их в файл


# --- задание 3: библиографические ссылки --------------------------------------
def make_bibliography(books: list[dict], count: int = 20) -> list[str]:
    """Генерирует count ссылок вида «<автор>. <название> - <год>»."""
    suitable = [book for book in books if book["year"]]      # только записи с годом
    generator = random.Random(VARIANT)         # фиксированный seed = вариант
    sample = generator.sample(suitable, min(count, len(suitable)))   # 20 записей

    references = []
    for book in sample:                        # собираем ссылку для каждой книги
        title = book["title"].rstrip(".")      # убираем точку в конце названия
        references.append(f"{book['author']}. {title} - {book['year']}")
    return references


def save_bibliography(references: list[str], path: Path | None = None) -> Path:
    """Сохраняет ссылки в файл с нумерацией строк."""
    path = path or HERE / "bibliography.txt"   # по умолчанию — рядом со скриптом
    with path.open("w", encoding="utf-8") as file:
        for number, reference in enumerate(references, start=1):   # с 1, а не с 0
            file.write(f"{number}. {reference}\n")                 # «1. ссылка»
    return path


# --- допзадание: уникальные значения и самые популярные книги ------------------
def unique_values(books: list[dict], mode: str) -> list[str]:
    """Теги (books.csv) или издательства (books-en.csv) без повторений."""
    values: set[str] = set()                   # множество само убирает повторы
    for book in books:
        if mode == "ru":                       # в books.csv теги через '#'
            values.update(tag.strip() for tag in book["extra"].split("#") if tag.strip())
        elif book["extra"]:                    # в books-en.csv — одно издательство
            values.add(book["extra"].strip())
    return sorted(values)                      # отсортированный список


def top_books(books: list[dict], count: int = 20) -> list[dict]:
    """Самые популярные книги: по числу выдач (books.csv) или скачиваний."""
    return sorted(books, key=lambda book: book["popularity"], reverse=True)[:count]


def print_extras(books: list[dict], mode: str) -> None:
    """Печатает оба допзадания: список без повторов и топ-20 книг."""
    values = unique_values(books, mode)        # уникальные теги/издательства
    print(f"Доп. задание 1) {DATASETS[mode]['extra_title']}: {len(values)}")
    for index, value in enumerate(values, start=1):    # нумерованный список
        print(f"   {index:2d}. {value}")

    print("\nДоп. задание 2) Самые популярные 20 книг:")
    for index, book in enumerate(top_books(books), start=1):   # топ по популярности
        print(f"   {index:2d}. {book['popularity']:5d} — {book['author'][:35]} — "
              f"{book['title'][:55]}")


# --- currency.xml: словарь «Name - CharCode» ----------------------------------
def parse_currencies(path: Path | None = None) -> dict[str, str]:
    """Разбор currency.xml: вариант 10 — словарь «Name - CharCode»."""
    path = path or HERE / "currency.xml"
    dom = minidom.parse(str(path))             # кодировку windows-1251 берём из заголовка
    dom.normalize()                            # убираем лишние текстовые узлы

    currencies: dict[str, str] = {}
    for node in dom.getElementsByTagName("Valute"):        # по одной валюте
        fields = {                                         # дочерние теги -> текст
            child.tagName: (child.firstChild.data if child.firstChild else "")
            for child in node.childNodes
            if child.nodeType == child.ELEMENT_NODE        # только теги, не текст
        }
        name = fields.get("Name", "").strip()              # название валюты
        char_code = fields.get("CharCode", "").strip()     # буквенный код
        if name and char_code:                             # обе части на месте
            currencies[name] = char_code                   # добавляем в словарь

    dom.unlink()                               # освобождаем документ
    return currencies


def print_currencies(currencies: dict[str, str]) -> None:
    """Печатает словарь и сохраняет его в JSON."""
    print(f"currency.xml: словарь «Name - CharCode», всего записей: {len(currencies)}")
    print("{")
    for name, code in currencies.items():      # по одной паре на строку
        print(f"    '{name}': '{code}',")
    print("}")

    path = HERE / "currencies.json"            # файл рядом со скриптом
    with path.open("w", encoding="utf-8") as file:
        json.dump(currencies, file, ensure_ascii=False, indent=2)   # русский без \u
    print(f"Словарь сохранён в {path.name}")


# --- точка входа ---------------------------------------------------------------
def main(argv: list[str]) -> int:
    try:                                       # чтобы русский текст не падал в файле
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    args = argv[1:]                            # всё, что передали после имени скрипта
    mode = "en" if "--en" in args else "ru"    # ключ --en переключает на books-en.csv
    author = None                              # автор из --author (если задан)
    for index, arg in enumerate(args):
        if arg == "--author" and index + 1 < len(args):   # флаг и значение за ним
            author = args[index + 1]

    if "--xml" not in args:                    # --xml — только разбор XML
        config = DATASETS[mode]                # настройки выбранного файла
        books = load_books(mode)               # читаем и нормализуем CSV
        print(f"Файл: {config['file']} ({len(books)} записей)\n")

        count_long_titles(books)               # задание 1
        print()

        min_year = config["min_year"]          # ограничение варианта
        if author:                             # неинтерактивный поиск
            found = search_by_author(books, author, min_year)
            print_search(author, min_year, found)
            save_search(found, HERE / "result.txt")
        elif sys.stdin.isatty():               # интерактивный — только в консоли
            interactive_search(books, min_year)
        print()

        references = make_bibliography(books)              # задание 3: 20 ссылок
        path = save_bibliography(references)
        print(f"3) Библиографические ссылки ({len(references)} шт.) — файл {path.name}:")
        for number, reference in enumerate(references, start=1):
            print(f"   {number:2d}. {reference}")
        print()

        print_extras(books, mode)              # допзадания
        print()

    print_currencies(parse_currencies())       # разбор currency.xml
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))           # запуск только при прямом вызове
