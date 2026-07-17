from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


@dataclass(frozen=True, slots=True)
class Field:
    key: str
    value: Any


@dataclass(frozen=True, slots=True)
class Table:
    headers: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]


@dataclass(slots=True)
class Section:
    key: str
    title: str
    fields: list[Field] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)

    def nonempty_fields(self) -> list[Field]:
        return [item for item in self.fields if _has_content(item.value)]


@dataclass(frozen=True, slots=True)
class Diagnostic:
    source: str
    message: str


@dataclass(slots=True)
class ReportData:
    language: str
    title: str
    generated_at: str
    subtitle: str | None = None
    selected_sections: tuple[str, ...] = ()
    sections: list[Section] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
