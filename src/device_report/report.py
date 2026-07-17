from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import Diagnostic, ReportData, Section


_GENERIC_DEVICE_VALUES = {
    "default string",
    "not applicable",
    "not available",
    "oem",
    "system manufacturer",
    "system product name",
    "to be filled by o.e.m",
    "to be filled by o.e.m.",
    "to be filled by oem",
    "unknown",
}

_INVALID_FILENAME = re.compile(r"[<>:\"/\\|?*\x00-\x1f]+")


def _useful_device_value(value: object) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).split()).strip()
    if not normalized or normalized.casefold() in _GENERIC_DEVICE_VALUES:
        return None
    return normalized


def build_device_title(manufacturer: object, model: object) -> str | None:
    maker = _useful_device_value(manufacturer)
    product = _useful_device_value(model)
    if maker and product:
        if product.casefold().startswith(maker.casefold()):
            return product
        return f"{maker} {product}"
    return product or maker


def _safe_filename_component(value: str) -> str:
    cleaned = _INVALID_FILENAME.sub(" ", value)
    cleaned = " ".join(cleaned.split()).strip(" .")
    return cleaned[:120].rstrip(" .")


def build_output_name(device_title: str | None, now: datetime) -> Path:
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    prefix = _safe_filename_component(device_title) if device_title else ""
    filename = f"{prefix} {timestamp}".strip() + ".docx"
    return Path(filename)


def _overview_values(sections: Iterable[Section]) -> tuple[object, object, tuple[object, ...]]:
    overview = next((section for section in sections if section.key == "overview"), None)
    if overview is None:
        return None, None, ()
    values = {field.key.casefold(): field.value for field in overview.fields}
    manufacturer = values.get("manufacturer", values.get("производитель"))
    model = values.get("model", values.get("модель"))
    marketing_candidates = (
        values.get("product name", values.get("название устройства")),
        values.get("system family", values.get("семейство устройства")),
        values.get("product version", values.get("версия продукта")),
        values.get("marketing name", values.get("название модели")),
    )
    return manufacturer, model, marketing_candidates


def _best_marketing_title(candidates: Iterable[object], manufacturer: object, model: object) -> str | None:
    excluded = {
        value.casefold()
        for value in (_useful_device_value(manufacturer), _useful_device_value(model))
        if value
    }
    useful: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        value = _useful_device_value(candidate)
        if not value:
            continue
        folded = value.casefold()
        if folded in excluded or folded in seen:
            continue
        if re.fullmatch(r"(?:version\s*)?v?\d+(?:[._-]\d+)*", folded):
            continue
        seen.add(folded)
        useful.append(value)
    if not useful:
        return None

    def score(value: str) -> tuple[int, int, int, int]:
        words = value.split()
        return (
            int(any(character.isalpha() for character in value) and len(words) > 1),
            len(words),
            sum(character.isalpha() for character in value),
            len(value),
        )

    return max(useful, key=score)


def build_report_data(
    language: str,
    sections: list[Section],
    diagnostics: list[Diagnostic],
    *,
    now: datetime | None = None,
) -> ReportData:
    generated = now or datetime.now().astimezone()
    generated_at = generated.strftime("%Y-%m-%d %H:%M:%S")
    manufacturer, model, marketing_candidates = _overview_values(sections)
    machine_title = build_device_title(manufacturer, model)
    marketing_title = _best_marketing_title(marketing_candidates, manufacturer, model)
    title = marketing_title or machine_title or generated_at
    subtitle = machine_title if marketing_title and machine_title and machine_title.casefold() != marketing_title.casefold() else None
    return ReportData(
        language=language,
        title=title,
        subtitle=subtitle,
        generated_at=generated_at,
        selected_sections=tuple(section.title for section in sections),
        sections=sections,
        diagnostics=diagnostics,
    )


def resolve_output_directory(
    *,
    executable: str | os.PathLike[str] | None = None,
    frozen: bool | None = None,
    cwd: str | os.PathLike[str] | None = None,
) -> Path:
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    if is_frozen:
        return Path(executable or sys.executable).resolve().parent
    return Path(cwd or os.getcwd()).resolve()
