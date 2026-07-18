from __future__ import annotations

import argparse
import inspect
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from . import __version__
from .backend import Backend, resolve_backend
from .docx_writer import write_docx
from .i18n import translate
from .error_log import write_error_log
from .models import Diagnostic
from .privacy import safe_error
from .report import build_output_name, build_report_data, resolve_output_directory


def build_parser(backend: Backend | None = None) -> argparse.ArgumentParser:
    active_backend = backend or resolve_backend()
    parser = argparse.ArgumentParser(
        prog=active_backend.executable_name,
        description="Create a bilingual privacy-safe device report in DOCX format.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=(
            f"DeviceReport {__version__} | Author: dsa_cat | "
            f"License: personal and household use only | Platform: {active_backend.platform_label}"
        ),
    )
    parser.add_argument(
        "--lang",
        choices=("ru", "en"),
        help="report language; omit to choose interactively",
    )
    parser.add_argument("--select", action="store_true", help="choose report sections interactively")
    parser.add_argument(
        "--section", action="append", choices=tuple(spec.key for spec in active_backend.specs),
        help="include one section; may be repeated",
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
    output_fn("╔══════════════════════════════════════╗")
    output_fn("║          DeviceReport 1.0.0          ║")
    output_fn("╚══════════════════════════════════════╝")
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


def _answer_one_or_two(prompt: str, *, input_fn: Callable[[str], str], output_fn: Callable[[str], None]) -> str:
    while True:
        answer = input_fn(prompt).strip()
        if answer in {"1", "2"}:
            return answer
        output_fn(translate("en", "menu_invalid"))


def choose_sections(
    language: str,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    specs: tuple[Any, ...] | None = None,
) -> tuple[str, ...]:
    active_specs = specs or resolve_backend().specs
    output_fn("")
    output_fn(translate(language, "sections_mode"))
    output_fn(translate(language, "sections_all"))
    output_fn(translate(language, "sections_custom"))
    mode = _answer_one_or_two(translate("en", "menu_prompt"), input_fn=input_fn, output_fn=output_fn)
    if mode == "1":
        selected = tuple(spec.key for spec in active_specs)
    else:
        while True:
            selected = tuple(
                spec.key
                for index, spec in enumerate(active_specs, 1)
                if _answer_one_or_two(
                    translate(language, "section_prompt", index=index, total=len(active_specs), section=spec.titles[language]),
                    input_fn=input_fn,
                    output_fn=output_fn,
                ) == "1"
            )
            if selected:
                break
            output_fn(translate(language, "sections_empty"))
    output_fn(translate(language, "sections_selected", count=len(selected)))
    for index, key in enumerate(selected, 1):
        output_fn(f"  {index:02d}. {next(spec.titles[language] for spec in active_specs if spec.key == key)}")
    return selected


def run_application(
    language: str,
    *,
    backend: Backend | None = None,
    runner: Any | None = None,
    collect_fn: Callable[..., Any] | None = None,
    identity_fn: Callable[[Any, str], Any] | None = None,
    writer: Callable[..., Path] = write_docx,
    now: datetime | None = None,
    executable: str | Path | None = None,
    frozen: bool | None = None,
    cwd: str | Path | None = None,
    output_fn: Callable[[str], None] = print,
    selected_keys: tuple[str, ...] | None = None,
) -> int:
    active_backend = backend or resolve_backend()
    active_collect = collect_fn or active_backend.collect_all
    active_identity = identity_fn or active_backend.collect_identity
    generated = now or datetime.now().astimezone()
    output_fn(translate(language, "starting"))

    progress_index = 0
    total = len(selected_keys) if selected_keys is not None else 0

    def progress(phase: str, title: str) -> None:
        nonlocal progress_index
        if phase == "collecting":
            progress_index += 1
        display_title = f"[{progress_index:02d}/{total:02d}] {title}" if total else title
        if phase == "warning":
            output_fn(translate(language, "warning", message=display_title))
        else:
            output_fn(translate(language, phase, section=display_title))

    active_runner = runner or active_backend.runner_factory()
    directory = resolve_output_directory(
        executable=executable,
        frozen=frozen,
        cwd=cwd,
    )
    try:
        collect_arguments = {"progress": progress}
        if "selected_keys" in inspect.signature(active_collect).parameters:
            collect_arguments["selected_keys"] = selected_keys
        sections, diagnostics = active_collect(active_runner, language, **collect_arguments)
        identity_section = None
        if selected_keys is not None and "overview" not in selected_keys:
            try:
                identity_section = active_identity(active_runner, language)
            except Exception as exc:
                diagnostics.append(Diagnostic("identity", safe_error(exc)))
        identity_sections = [identity_section, *sections] if identity_section is not None else sections
        report = build_report_data(language, identity_sections, diagnostics, now=generated)
        report.sections = sections
        report.selected_sections = tuple(section.title for section in sections)
        device_title = report.title if report.title != report.generated_at else None
        output_path = directory / build_output_name(device_title, generated)
        output_fn(translate(language, "writing"))
        result = writer(report, output_path)
        output_fn(translate(language, "saved", path=Path(result).resolve()))
        try:
            log_path = write_error_log(directory, diagnostics, now=generated)
        except OSError:
            output_fn(translate(language, "log_failed"))
        else:
            if log_path is not None:
                output_fn(translate(language, "log_saved", path=log_path.resolve()))
    except Exception as exc:
        category = safe_error(exc)
        try:
            log_path = write_error_log(directory, [Diagnostic("application", category)], now=generated)
        except OSError:
            output_fn(translate(language, "log_failed"))
        else:
            if log_path is not None:
                output_fn(translate(language, "log_saved", path=log_path.resolve()))
        output_fn(translate(language, "fatal", message=category))
        return 1
    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    run_fn: Callable[..., int] = run_application,
) -> int:
    backend = resolve_backend()
    parser = build_parser(backend)
    args = parser.parse_args(argv)
    if args.select and args.section:
        parser.error("--select and --section cannot be used together")
    interactive = args.lang is None
    language = args.lang or choose_language(input_fn=input_fn, output_fn=output_fn)
    selected = tuple(dict.fromkeys(args.section)) if args.section else (
        choose_sections(language, input_fn=input_fn, output_fn=output_fn, specs=backend.specs)
        if interactive or args.select else tuple(spec.key for spec in backend.specs)
    )
    run_arguments: dict[str, Any] = {"output_fn": output_fn}
    signature = inspect.signature(run_fn)
    if "selected_keys" in signature.parameters or any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in signature.parameters.values()
    ):
        run_arguments["selected_keys"] = selected
    if "backend" in signature.parameters or any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in signature.parameters.values()
    ):
        run_arguments["backend"] = backend
    result = run_fn(language, **run_arguments)
    if interactive and not args.no_pause:
        input_fn(translate(language, "press_enter"))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
