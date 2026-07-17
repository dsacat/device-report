from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from . import __version__
from .models import Diagnostic


_ERROR_CATEGORY = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:Error|Timeout)\b")


def _category(message: str) -> str:
    match = _ERROR_CATEGORY.search(str(message))
    return match.group(0) if match else "Error"


def write_error_log(
    output_directory: str | Path,
    diagnostics: list[Diagnostic],
    *,
    now: datetime | None = None,
) -> Path | None:
    if not diagnostics:
        return None
    generated = now or datetime.now().astimezone()
    logs = Path(output_directory) / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    path = logs / f"DeviceReport_errors_{generated:%Y-%m-%d_%H-%M-%S}.log"
    lines = [
        f"Generated: {generated:%Y-%m-%d %H:%M:%S}",
        f"DeviceReport: {__version__}",
        "",
    ]
    lines.extend(f"{item.source}: {_category(item.message)}" for item in diagnostics)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
