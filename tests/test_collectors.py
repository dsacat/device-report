from types import SimpleNamespace

import pytest

import device_report.collectors as collectors
from device_report.models import Diagnostic, Field, Section


class FakeRunner:
    def __init__(self, responses=None, failure=None):
        self.responses = responses or {}
        self.failure = failure
        self.scripts = []

    def powershell_json(self, script, **kwargs):
        self.scripts.append(script)
        if self.failure:
            raise self.failure
        for marker, response in self.responses.items():
            if marker in script:
                return response
        return []


def field_values(section):
    return {item.key: item.value for item in section.fields}


def test_overview_normalizes_fields_and_formats_memory():
    runner = FakeRunner(
        {
            "Win32_ComputerSystem": [
                {
                    "Manufacturer": "Lenovo",
                    "Model": "ThinkPad T14",
                    "SystemType": "x64-based PC",
                    "TotalPhysicalMemory": 17_179_869_184,
                    "NumberOfProcessors": 1,
                    "NumberOfLogicalProcessors": 16,
                }
            ]
        }
    )

    section = collectors.collect_overview(runner, "en")

    assert section.key == "overview"
    assert section.title == "Device overview"
    assert field_values(section)["Total memory"] == "16.00 GiB"
    assert "SerialNumber" not in runner.scripts[0]
    assert "UUID" not in runner.scripts[0]


def test_memory_collector_returns_localized_table_without_sensitive_columns():
    runner = FakeRunner(
        {
            "Win32_PhysicalMemory": [
                {
                    "Manufacturer": "Kingston",
                    "Capacity": 8_589_934_592,
                    "Speed": 3200,
                    "ConfiguredClockSpeed": 2933,
                    "DeviceLocator": "DIMM 0",
                }
            ]
        }
    )

    section = collectors.collect_memory(runner, "ru")

    assert section.title == "Оперативная память"
    assert section.tables[0].headers == (
        "Производитель",
        "Объём",
        "Скорость",
        "Настроенная частота",
        "Тип памяти",
        "Форм-фактор",
        "Разъём",
    )
    assert section.tables[0].rows[0][1] == "8.00 GiB"
    assert "SerialNumber" not in runner.scripts[0]
    assert "PartNumber" not in runner.scripts[0]


def test_declared_collectors_cover_every_required_section():
    expected = {
        "overview",
        "operating_system",
        "cpu",
        "memory",
        "graphics",
        "firmware",
        "storage",
        "network",
        "audio",
        "battery",
        "drivers",
        "security",
        "updates",
        "software",
    }

    assert {spec.key for spec in collectors.COLLECTOR_SPECS} == expected


@pytest.mark.parametrize(
    "forbidden",
    ["SerialNumber", "UUID", "MACAddress", "IPAddress", "UserName", "ProductKey", "SSID"],
)
def test_collector_queries_never_request_sensitive_fields(forbidden):
    assert all(forbidden.lower() not in spec.script.lower() for spec in collectors.COLLECTOR_SPECS)


def test_collect_all_isolates_failure_and_continues(monkeypatch):
    first = SimpleNamespace(
        key="first",
        titles={"en": "First", "ru": "Первый"},
        collect=lambda runner, language: Section("first", "First", [Field("Name", "A")]),
    )

    def fail(runner, language):
        raise RuntimeError(r"secret C:\Users\Alice")

    second = SimpleNamespace(
        key="second",
        titles={"en": "Second", "ru": "Второй"},
        collect=fail,
    )
    third = SimpleNamespace(
        key="third",
        titles={"en": "Third", "ru": "Третий"},
        collect=lambda runner, language: Section("third", "Third"),
    )
    monkeypatch.setattr(collectors, "COLLECTOR_SPECS", (first, second, third))
    progress = []

    sections, diagnostics = collectors.collect_all(
        FakeRunner(),
        "en",
        progress=lambda phase, title: progress.append((phase, title)),
    )

    assert [section.key for section in sections] == ["first", "third"]
    assert diagnostics == [Diagnostic(source="second", message="RuntimeError")]
    assert progress == [
        ("collecting", "First"),
        ("collected", "First"),
        ("collecting", "Second"),
        ("warning", "Second"),
        ("collecting", "Third"),
        ("collected", "Third"),
    ]


def test_empty_collector_result_is_preserved_as_empty_section():
    section = collectors.collect_audio(FakeRunner(), "en")

    assert section.key == "audio"
    assert section.title == "Audio devices"
    assert section.fields == []
    assert section.tables == []
