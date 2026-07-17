from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from .collectors import collect_all
from .docx_writer import write_docx
from .i18n import translate
from .privacy import safe_error
from .report import build_output_name, build_report_data, resolve_output_directory
from .runner import CommandRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="DeviceReport.exe",
        description="Create a bilingual privacy-safe Windows device report in DOCX format.",
    )
    parser.add_argument(
        "--lang",
        choices=("ru", "en"),
        help="report language; omit to choose interactively",
    )
    parser.add_argument(
        "--no-pause",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser


def choose_language(
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> str:
    output_fn(translate("en", "menu_title"))
    output_fn(translate("en", "menu_ru"))
    output_fn(translate("en", "menu_en"))
    while True:
        answer = input_fn(translate("en", "menu_prompt")).strip()
        if answer == "1":
            return "ru"
        if answer == "2":
            return "en"
        output_fn(translate("en", "menu_invalid"))


def run_application(
    language: str,
    *,
    runner: Any | None = None,
    collect_fn: Callable[..., Any] = collect_all,
    writer: Callable[..., Path] = write_docx,
    now: datetime | None = None,
    executable: str | Path | None = None,
    frozen: bool | None = None,
    cwd: str | Path | None = None,
    output_fn: Callable[[str], None] = print,
) -> int:
    generated = now or datetime.now().astimezone()
    output_fn(translate(language, "starting"))

    def progress(phase: str, title: str) -> None:
        if phase == "warning":
            output_fn(translate(language, "warning", message=title))
        else:
            output_fn(translate(language, phase, section=title))

    active_runner = runner or CommandRunner()
    try:
        sections, diagnostics = collect_fn(active_runner, language, progress=progress)
        report = build_report_data(language, sections, diagnostics, now=generated)
        device_title = report.title if report.title != report.generated_at else None
        directory = resolve_output_directory(
            executable=executable,
            frozen=frozen,
            cwd=cwd,
        )
        output_path = directory / build_output_name(device_title, generated)
        output_fn(translate(language, "writing"))
        result = writer(report, output_path)
    except Exception as exc:
        output_fn(translate(language, "fatal", message=safe_error(exc)))
        return 1
    output_fn(translate(language, "saved", path=Path(result).resolve()))
    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    run_fn: Callable[..., int] = run_application,
) -> int:
    args = build_parser().parse_args(argv)
    interactive = args.lang is None
    language = args.lang or choose_language(input_fn=input_fn, output_fn=output_fn)
    result = run_fn(language, output_fn=output_fn)
    if interactive and not args.no_pause:
        input_fn(translate(language, "press_enter"))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
