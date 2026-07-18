from __future__ import annotations

import locale
import os
import platform
import re
import shlex
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable

from .collectors import PROPERTY_LABELS, TITLE_LABELS, format_bytes
from .models import Diagnostic, Field, Section, Table
from .privacy import safe_error, sanitize_mapping
from .runner import CommandError


_TITLES = {key: dict(value) for key, value in TITLE_LABELS.items()}
_TITLES["updates"] = {"en": "Installed system updates", "ru": "Установленные обновления системы"}

_EXTRA_LABELS = {
    "Architecture": {"en": "Architecture", "ru": "Архитектура"},
    "Kernel": {"en": "Kernel", "ru": "Ядро"},
    "Distribution": {"en": "Distribution", "ru": "Дистрибутив"},
    "AvailableMemory": {"en": "Available memory", "ru": "Доступная память"},
    "SwapTotal": {"en": "Swap total", "ru": "Общий объём swap"},
    "SwapFree": {"en": "Swap free", "ru": "Свободно swap"},
    "Driver": {"en": "Driver", "ru": "Драйвер"},
    "Type": {"en": "Type", "ru": "Тип"},
    "State": {"en": "State", "ru": "Состояние"},
    "Package": {"en": "Package", "ru": "Пакет"},
    "Device": {"en": "Device", "ru": "Устройство"},
    "Rotational": {"en": "Rotational", "ru": "Вращающийся"},
    "ReadOnly": {"en": "Read only", "ru": "Только чтение"},
}

_SIZE_KEYS = {"TotalPhysicalMemory", "AvailableMemory", "SwapTotal", "SwapFree", "Size"}


def _label(name: str, language: str) -> str:
    labels = PROPERTY_LABELS.get(name, _EXTRA_LABELS.get(name, {}))
    return labels.get(language, name)


def _format(name: str, value: Any) -> Any:
    return format_bytes(value) if name in _SIZE_KEYS and value not in (None, "") else value


def _section_fields(key: str, language: str, values: dict[str, Any]) -> Section:
    safe = sanitize_mapping(values)
    fields = [
        Field(_label(name, language), _format(name, value))
        for name, value in safe.items()
        if value not in (None, "", [], {})
    ]
    return Section(key=key, title=_TITLES[key][language], fields=fields)


def _section_table(
    key: str,
    language: str,
    columns: tuple[str, ...],
    rows: Iterable[dict[str, Any]],
) -> Section:
    safe_rows = [sanitize_mapping(row) for row in rows]
    formatted = tuple(
        tuple(_format(column, row.get(column, "")) for column in columns)
        for row in safe_rows
        if any(row.get(column) not in (None, "", [], {}) for column in columns)
    )
    tables = [Table(tuple(_label(column, language) for column in columns), formatted)] if formatted else []
    return Section(key=key, title=_TITLES[key][language], tables=tables)


def _read_first(runner: Any, *paths: str) -> str | None:
    for path in paths:
        value = runner.read_optional(path)
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())
    return None


def _meminfo(runner: Any) -> dict[str, int]:
    source = runner.read_optional("/proc/meminfo") or ""
    values: dict[str, int] = {}
    for line in str(source).splitlines():
        match = re.match(r"^([A-Za-z_()]+):\s+(\d+)\s*(kB)?", line)
        if match:
            multiplier = 1024 if match.group(3) else 1
            values[match.group(1)] = int(match.group(2)) * multiplier
    return values


def collect_overview(runner: Any, language: str) -> Section:
    memory = _meminfo(runner)
    return _section_fields(
        "overview",
        language,
        {
            "Manufacturer": _read_first(runner, "/sys/class/dmi/id/sys_vendor", "/sys/devices/virtual/dmi/id/sys_vendor"),
            "Model": _read_first(runner, "/sys/class/dmi/id/product_name", "/sys/devices/virtual/dmi/id/product_name"),
            "SystemFamily": _read_first(runner, "/sys/class/dmi/id/product_family", "/sys/devices/virtual/dmi/id/product_family"),
            "ProductName": _read_first(runner, "/sys/class/dmi/id/product_name", "/sys/devices/virtual/dmi/id/product_name"),
            "ProductVersion": _read_first(runner, "/sys/class/dmi/id/product_version", "/sys/devices/virtual/dmi/id/product_version"),
            "SystemType": platform.machine(),
            "TotalPhysicalMemory": memory.get("MemTotal"),
            "NumberOfProcessors": os.cpu_count(),
            "NumberOfLogicalProcessors": os.cpu_count(),
        },
    )


def _parse_os_release(source: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in source.splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"\'')
    return values


def collect_operating_system(runner: Any, language: str) -> Section:
    release = _parse_os_release(str(runner.read_optional("/etc/os-release") or ""))
    uptime_source = str(runner.read_optional("/proc/uptime") or "").split()
    boot = None
    if uptime_source:
        try:
            boot = (datetime.now().astimezone() - timedelta(seconds=float(uptime_source[0]))).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    locale_name = locale.getlocale()[0]
    return _section_fields(
        "operating_system",
        language,
        {
            "Caption": release.get("PRETTY_NAME") or release.get("NAME") or "Linux",
            "Version": release.get("VERSION_ID") or release.get("VERSION"),
            "BuildNumber": platform.release(),
            "OSArchitecture": platform.machine(),
            "LastBootUpTime": boot,
            "Locale": locale_name,
        },
    )


def collect_cpu(runner: Any, language: str) -> Section:
    source = str(runner.read_optional("/proc/cpuinfo") or "")
    blocks = [block for block in source.split("\n\n") if block.strip()]
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for block in blocks:
        values = {}
        for line in block.splitlines():
            if ":" in line:
                name, value = line.split(":", 1)
                values[name.strip()] = value.strip()
        name = values.get("model name") or values.get("Processor") or values.get("cpu model")
        if not name or name in seen:
            continue
        seen.add(name)
        rows.append(
            {
                "Name": name,
                "Manufacturer": values.get("vendor_id") or values.get("CPU implementer"),
                "NumberOfCores": values.get("cpu cores"),
                "NumberOfLogicalProcessors": os.cpu_count(),
                "CurrentClockSpeed": values.get("cpu MHz"),
            }
        )
    return _section_table(
        "cpu",
        language,
        ("Name", "Manufacturer", "NumberOfCores", "NumberOfLogicalProcessors", "CurrentClockSpeed"),
        rows,
    )


def collect_memory(runner: Any, language: str) -> Section:
    values = _meminfo(runner)
    return _section_fields(
        "memory",
        language,
        {
            "TotalPhysicalMemory": values.get("MemTotal"),
            "AvailableMemory": values.get("MemAvailable"),
            "SwapTotal": values.get("SwapTotal"),
            "SwapFree": values.get("SwapFree"),
        },
    )


def collect_graphics(runner: Any, language: str) -> Section:
    rows: list[dict[str, Any]] = []
    if runner.available("lspci"):
        output = runner.command(["lspci", "-mm"], timeout=15).stdout
        for line in output.splitlines():
            try:
                parts = shlex.split(line)
            except ValueError:
                continue
            if len(parts) >= 4 and any(kind in parts[1].casefold() for kind in ("vga", "3d", "display")):
                rows.append({"Category": "GPU", "Name": parts[3], "Manufacturer": parts[2], "Status": "Available"})
    return _section_table("graphics", language, ("Category", "Name", "Manufacturer", "Status"), rows)


def collect_firmware(runner: Any, language: str) -> Section:
    rows = [
        {
            "Category": "Motherboard",
            "Manufacturer": _read_first(runner, "/sys/class/dmi/id/board_vendor"),
            "Product": _read_first(runner, "/sys/class/dmi/id/board_name"),
            "Version": _read_first(runner, "/sys/class/dmi/id/board_version"),
        },
        {
            "Category": "BIOS/UEFI",
            "Manufacturer": _read_first(runner, "/sys/class/dmi/id/bios_vendor"),
            "SMBIOSBIOSVersion": _read_first(runner, "/sys/class/dmi/id/bios_version"),
            "ReleaseDate": _read_first(runner, "/sys/class/dmi/id/bios_date"),
            "Status": "UEFI" if runner.exists("/sys/firmware/efi") else "Legacy/unknown",
        },
    ]
    return _section_table(
        "firmware",
        language,
        ("Category", "Manufacturer", "Product", "Version", "SMBIOSBIOSVersion", "ReleaseDate", "Status"),
        rows,
    )


def _flatten_block_devices(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        rows.append(
            {
                "Device": item.get("name"),
                "Type": item.get("type"),
                "Size": item.get("size"),
                "FileSystem": item.get("fstype"),
                "Model": item.get("model"),
                "BusType": item.get("tran"),
                "Rotational": item.get("rota"),
                "ReadOnly": item.get("ro"),
            }
        )
        rows.extend(_flatten_block_devices(item.get("children") or []))
    return rows


def collect_storage(runner: Any, language: str) -> Section:
    rows: list[dict[str, Any]] = []
    if runner.available("lsblk"):
        data = runner.command_json(
            ["lsblk", "--json", "--bytes", "--output", "NAME,TYPE,SIZE,FSTYPE,MODEL,TRAN,ROTA,RO"]
        )
        rows = _flatten_block_devices(data.get("blockdevices", [])) if isinstance(data, dict) else []
    return _section_table(
        "storage",
        language,
        ("Device", "Type", "Size", "FileSystem", "Model", "BusType", "Rotational", "ReadOnly"),
        rows,
    )


def collect_network(runner: Any, language: str) -> Section:
    rows: list[dict[str, Any]] = []
    for entry in runner.glob("/sys/class/net/*"):
        name = entry.name
        if name == "lo":
            continue
        driver = runner.readlink_optional(f"{entry}/device/driver") if hasattr(runner, "readlink_optional") else None
        rows.append(
            {
                "Name": name,
                "Status": _read_first(runner, f"{entry}/operstate"),
                "Speed": _read_first(runner, f"{entry}/speed"),
                "Driver": driver,
                "Type": _read_first(runner, f"{entry}/type"),
            }
        )
    return _section_table("network", language, ("Name", "Type", "Status", "Speed", "Driver"), rows)


def collect_audio(runner: Any, language: str) -> Section:
    source = str(runner.read_optional("/proc/asound/cards") or "")
    rows = [
        {"Name": " ".join(line.split())}
        for line in source.splitlines()
        if line.strip() and re.match(r"^\s*\d+\s+\[", line)
    ]
    return _section_table("audio", language, ("Name",), rows)


def collect_battery(runner: Any, language: str) -> Section:
    rows: list[dict[str, Any]] = []
    for entry in runner.glob("/sys/class/power_supply/*"):
        kind = _read_first(runner, f"{entry}/type")
        if kind not in {"Battery", "Mains", "USB"}:
            continue
        rows.append(
            {
                "Category": kind,
                "Name": entry.name,
                "Manufacturer": _read_first(runner, f"{entry}/manufacturer"),
                "Model": _read_first(runner, f"{entry}/model_name"),
                "BatteryStatus": _read_first(runner, f"{entry}/status"),
                "EstimatedChargeRemaining": _read_first(runner, f"{entry}/capacity"),
            }
        )
    return _section_table(
        "battery",
        language,
        ("Category", "Name", "Manufacturer", "Model", "BatteryStatus", "EstimatedChargeRemaining"),
        rows,
    )


def collect_drivers(runner: Any, language: str) -> Section:
    rows: list[dict[str, Any]] = []
    for entry in runner.glob("/sys/bus/pci/devices/*"):
        driver = runner.readlink_optional(f"{entry}/driver") if hasattr(runner, "readlink_optional") else None
        rows.append(
            {
                "DeviceName": entry.name,
                "Manufacturer": _read_first(runner, f"{entry}/vendor"),
                "Product": _read_first(runner, f"{entry}/device"),
                "Driver": driver,
            }
        )
    return _section_table("drivers", language, ("DeviceName", "Manufacturer", "Product", "Driver"), rows)


def collect_security(runner: Any, language: str) -> Section:
    rows: list[dict[str, Any]] = [
        {"Name": "UEFI", "Enabled": runner.exists("/sys/firmware/efi"), "Value": "Firmware mode"},
        {"Name": "Kernel lockdown", "Value": _read_first(runner, "/sys/kernel/security/lockdown")},
        {"Name": "AppArmor", "Enabled": _read_first(runner, "/sys/module/apparmor/parameters/enabled") == "Y"},
        {"Name": "SELinux", "Value": _read_first(runner, "/sys/fs/selinux/enforce")},
    ]
    if runner.available("systemctl"):
        for service in ("firewalld", "ufw"):
            try:
                active = runner.command(["systemctl", "is-active", service], timeout=5, ok_codes=(0, 3)).stdout.strip()
            except CommandError:
                continue
            rows.append({"Name": f"Firewall {service}", "Enabled": active == "active", "Value": active})
    return _section_table("security", language, ("Name", "Enabled", "Value"), rows)


def _package_rows(output: str, *, updates: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        source = line.strip()
        if not source or source.casefold().startswith(("listing", "last metadata", "warning")):
            continue
        if "\t" in source:
            package, version, *_ = source.split("\t") + [""]
        elif "/" in source and " " in source:
            package, remainder = source.split("/", 1)
            version = remainder.split()[1] if len(remainder.split()) > 1 else remainder
        else:
            parts = source.split()
            package = parts[0]
            version = parts[1] if len(parts) > 1 else ""
        rows.append({"Package": package, "Version": version, "Status": "Update available" if updates else "Installed"})
    return rows[:10000]


def _package_command(runner: Any, *, updates: bool) -> str:
    if runner.available("dpkg-query"):
        if updates and runner.available("apt"):
            return runner.command(["apt", "list", "--upgradable"], timeout=30).stdout
        if not updates:
            return runner.command(["dpkg-query", "-W", "-f=${Package}\t${Version}\n"], timeout=45).stdout
    if runner.available("rpm") and not updates:
        return runner.command(["rpm", "-qa", "--qf", "%{NAME}\t%{VERSION}-%{RELEASE}\n"], timeout=45).stdout
    if runner.available("dnf") and updates:
        return runner.command(["dnf", "--cacheonly", "check-update"], timeout=45, ok_codes=(0, 100)).stdout
    if runner.available("pacman"):
        return runner.command(["pacman", "-Qu" if updates else "-Q"], timeout=45, ok_codes=(0, 1)).stdout
    return ""


def collect_updates(runner: Any, language: str) -> Section:
    return _section_table(
        "updates",
        language,
        ("Package", "Version", "Status"),
        _package_rows(_package_command(runner, updates=True), updates=True),
    )


def collect_software(runner: Any, language: str) -> Section:
    return _section_table(
        "software",
        language,
        ("Package", "Version", "Status"),
        _package_rows(_package_command(runner, updates=False), updates=False),
    )


@dataclass(frozen=True, slots=True)
class LinuxCollectorSpec:
    key: str
    collector: Callable[[Any, str], Section]

    @property
    def titles(self) -> dict[str, str]:
        return _TITLES[self.key]

    def collect(self, runner: Any, language: str) -> Section:
        return self.collector(runner, language)


COLLECTOR_SPECS = (
    LinuxCollectorSpec("overview", collect_overview),
    LinuxCollectorSpec("operating_system", collect_operating_system),
    LinuxCollectorSpec("cpu", collect_cpu),
    LinuxCollectorSpec("memory", collect_memory),
    LinuxCollectorSpec("graphics", collect_graphics),
    LinuxCollectorSpec("firmware", collect_firmware),
    LinuxCollectorSpec("storage", collect_storage),
    LinuxCollectorSpec("network", collect_network),
    LinuxCollectorSpec("audio", collect_audio),
    LinuxCollectorSpec("battery", collect_battery),
    LinuxCollectorSpec("drivers", collect_drivers),
    LinuxCollectorSpec("security", collect_security),
    LinuxCollectorSpec("updates", collect_updates),
    LinuxCollectorSpec("software", collect_software),
)


def collect_all(
    runner: Any,
    language: str,
    *,
    progress: Callable[[str, str], None] | None = None,
    selected_keys: tuple[str, ...] | list[str] | set[str] | None = None,
) -> tuple[list[Section], list[Diagnostic]]:
    notify = progress or (lambda phase, title: None)
    selected = None if selected_keys is None else set(selected_keys)
    available = {spec.key for spec in COLLECTOR_SPECS}
    unknown = set() if selected is None else selected - available
    if unknown:
        raise ValueError(f"unknown collector key: {sorted(unknown)[0]}")
    sections: list[Section] = []
    diagnostics: list[Diagnostic] = []
    for spec in COLLECTOR_SPECS:
        if selected is not None and spec.key not in selected:
            continue
        title = spec.titles[language]
        notify("collecting", title)
        try:
            sections.append(spec.collect(runner, language))
        except Exception as exc:
            diagnostics.append(Diagnostic(spec.key, safe_error(exc)))
            notify("warning", title)
        else:
            notify("collected", title)
    return sections, diagnostics
