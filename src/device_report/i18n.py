from __future__ import annotations

from typing import Any


STRINGS: dict[str, dict[str, str]] = {
    "ru": {
        "app_name": "Отчёт об устройстве Windows",
        "menu_title": "Выберите язык отчёта / Choose report language:",
        "menu_ru": "1 — Русский",
        "menu_en": "2 — English",
        "menu_prompt": "Ваш выбор / Your choice: ",
        "menu_invalid": "Введите 1 или 2 / Enter 1 or 2.",
        "starting": "Запуск сбора информации...",
        "collecting": "Сбор: {section}",
        "collected": "Готово: {section}",
        "unavailable": "Недоступно",
        "warning": "Предупреждение: {message}",
        "writing": "Создание DOCX-отчёта...",
        "saved": "Отчёт сохранён: {path}",
        "fatal": "Не удалось создать отчёт: {message}",
        "press_enter": "Нажмите Enter для выхода...",
        "report_date": "Дата отчёта",
        "diagnostics": "Диагностика",
        "source": "Источник",
        "message": "Сообщение",
        "value": "Значение",
        "property": "Параметр",
    },
    "en": {
        "app_name": "Windows Device Report",
        "menu_title": "Выберите язык отчёта / Choose report language:",
        "menu_ru": "1 — Русский",
        "menu_en": "2 — English",
        "menu_prompt": "Ваш выбор / Your choice: ",
        "menu_invalid": "Введите 1 или 2 / Enter 1 or 2.",
        "starting": "Starting device information collection...",
        "collecting": "Collecting: {section}",
        "collected": "Completed: {section}",
        "unavailable": "Unavailable",
        "warning": "Warning: {message}",
        "writing": "Creating DOCX report...",
        "saved": "Report saved: {path}",
        "fatal": "Could not create the report: {message}",
        "press_enter": "Press Enter to exit...",
        "report_date": "Report date",
        "diagnostics": "Diagnostics",
        "source": "Source",
        "message": "Message",
        "value": "Value",
        "property": "Property",
    },
}


def normalize_language(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("language must be 'ru' or 'en'")
    normalized = value.strip().lower()
    if normalized not in STRINGS:
        raise ValueError("language must be 'ru' or 'en'")
    return normalized


def translate(language: str, key: str, **values: Any) -> str:
    normalized = normalize_language(language)
    template = STRINGS[normalized].get(key, key)
    return template.format(**values)
