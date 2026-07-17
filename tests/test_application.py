from datetime import datetime
from pathlib import Path

import pytest

from device_report.cli import main, run_application
from device_report.models import Diagnostic, Field, Section


FIXED_TIME = datetime(2026, 7, 17, 18, 30, 0)


def fake_collect(runner, language, *, progress):
    title = "Device overview" if language == "en" else "Обзор устройства"
    progress("collecting", title)
    progress("collected", title)
    return [
        Section(
            key="overview",
            title=title,
            fields=[
                Field("Manufacturer" if language == "en" else "Производитель", "Lenovo"),
                Field("Model" if language == "en" else "Модель", "ThinkPad T14"),
            ],
        )
    ], [Diagnostic("battery", "CommandTimeout")]


def test_run_application_writes_beside_executable_and_prints_full_progress(tmp_path):
    output = []
    writes = []
    executable = tmp_path / "DeviceReport.exe"

    def writer(report, path):
        writes.append((report, Path(path)))
        return Path(path)

    result = run_application(
        "en",
        runner=object(),
        collect_fn=fake_collect,
        writer=writer,
        now=FIXED_TIME,
        executable=executable,
        frozen=True,
        output_fn=output.append,
    )

    assert result == 0
    assert writes[0][1] == tmp_path / "Lenovo ThinkPad T14 2026-07-17_18-30-00.docx"
    assert writes[0][0].diagnostics == [Diagnostic("battery", "CommandTimeout")]
    assert output == [
        "Starting device information collection...",
        "Collecting: Device overview",
        "Completed: Device overview",
        "Creating DOCX report...",
        f"Report saved: {writes[0][1]}",
        f"Error log saved: {tmp_path / 'logs' / 'DeviceReport_errors_2026-07-17_18-30-00.log'}",
    ]


def test_run_application_reports_write_failure_without_private_details(tmp_path):
    output = []

    def broken_writer(report, path):
        raise PermissionError(r"Denied C:\Users\Alice")

    result = run_application(
        "en",
        runner=object(),
        collect_fn=fake_collect,
        writer=broken_writer,
        now=FIXED_TIME,
        cwd=tmp_path,
        frozen=False,
        output_fn=output.append,
    )

    assert result == 1
    assert output[-1] == "Could not create the report: PermissionError"
    assert "Alice" not in "\n".join(output)


def test_main_with_lang_runs_without_interactive_input():
    calls = []

    result = main(
        ["--lang", "ru"],
        input_fn=lambda prompt: pytest.fail("input must not be called"),
        output_fn=lambda line: None,
        run_fn=lambda language, output_fn: calls.append(language) or 0,
    )

    assert result == 0
    assert calls == ["ru"]


def test_main_without_lang_uses_menu_and_pauses_after_run():
    answers = iter(["2", "1", ""])
    calls = []

    result = main(
        [],
        input_fn=lambda prompt: next(answers),
        output_fn=lambda line: None,
        run_fn=lambda language, output_fn: calls.append(language) or 0,
    )

    assert result == 0
    assert calls == ["en"]


def test_main_no_pause_skips_final_prompt_after_menu():
    answers = iter(["1", "1"])

    result = main(
        ["--no-pause"],
        input_fn=lambda prompt: next(answers),
        output_fn=lambda line: None,
        run_fn=lambda language, output_fn: 0,
    )

    assert result == 0


def test_help_exits_without_running_application():
    with pytest.raises(SystemExit) as caught:
        main(["--help"], run_fn=lambda *args, **kwargs: pytest.fail("must not run"))
    assert caught.value.code == 0
