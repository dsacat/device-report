from datetime import datetime
from pathlib import Path

from device_report.models import Diagnostic, Field, Section
from device_report.report import (
    build_device_title,
    build_output_name,
    build_report_data,
    resolve_output_directory,
)


FIXED_TIME = datetime(2026, 7, 17, 18, 30, 0)


def test_device_title_omits_generic_values():
    assert build_device_title("System manufacturer", "System Product Name") is None
    assert build_device_title("To be filled by O.E.M.", "Default string") is None


def test_device_title_combines_useful_values_without_duplication():
    assert build_device_title("Lenovo", "ThinkPad T14") == "Lenovo ThinkPad T14"
    assert build_device_title("Dell", "Dell Precision 7680") == "Dell Precision 7680"
    assert build_device_title("", "Surface Pro 9") == "Surface Pro 9"


def test_output_name_uses_safe_device_and_timestamp():
    result = build_output_name("Dell Inc. / XPS:15?", FIXED_TIME)

    assert result == Path("Dell Inc. XPS 15 2026-07-17_18-30-00.docx")


def test_output_name_uses_only_timestamp_without_device():
    assert build_output_name(None, FIXED_TIME) == Path("2026-07-17_18-30-00.docx")


def test_report_data_derives_english_device_title_from_overview():
    overview = Section(
        key="overview",
        title="Device overview",
        fields=[Field("Manufacturer", "Lenovo"), Field("Model", "ThinkPad T14")],
    )
    diagnostics = [Diagnostic("battery", "Unavailable")]

    report = build_report_data("en", [overview], diagnostics, now=FIXED_TIME)

    assert report.title == "Lenovo ThinkPad T14"
    assert report.generated_at == "2026-07-17 18:30:00"
    assert report.diagnostics == diagnostics


def test_report_data_uses_timestamp_as_title_without_device_name():
    report = build_report_data("ru", [], [], now=FIXED_TIME)

    assert report.title == "2026-07-17 18:30:00"


def test_frozen_output_directory_is_next_to_executable(tmp_path):
    executable = tmp_path / "bin" / "DeviceReport.exe"

    assert resolve_output_directory(executable=executable, frozen=True) == executable.parent


def test_source_output_directory_uses_given_working_directory(tmp_path):
    assert resolve_output_directory(cwd=tmp_path, frozen=False) == tmp_path.resolve()
