from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable

from .models import Diagnostic, Field, Section, Table
from .privacy import safe_error, sanitize_mapping


TITLE_LABELS = {
    "overview": {"en": "Device overview", "ru": "Обзор устройства"},
    "operating_system": {"en": "Operating system", "ru": "Операционная система"},
    "cpu": {"en": "Processor", "ru": "Процессор"},
    "memory": {"en": "Memory", "ru": "Оперативная память"},
    "graphics": {"en": "Graphics and displays", "ru": "Графика и дисплеи"},
    "firmware": {"en": "Motherboard and firmware", "ru": "Материнская плата и прошивка"},
    "storage": {"en": "Storage", "ru": "Накопители"},
    "network": {"en": "Network adapters", "ru": "Сетевые адаптеры"},
    "audio": {"en": "Audio devices", "ru": "Аудиоустройства"},
    "battery": {"en": "Battery and power", "ru": "Батарея и питание"},
    "drivers": {"en": "Devices and drivers", "ru": "Устройства и драйверы"},
    "security": {"en": "Security", "ru": "Безопасность"},
    "updates": {"en": "Installed Windows updates", "ru": "Установленные обновления Windows"},
    "software": {"en": "Installed software", "ru": "Установленные программы"},
}

PROPERTY_LABELS: dict[str, dict[str, str]] = {
    "Category": {"en": "Category", "ru": "Категория"},
    "Manufacturer": {"en": "Manufacturer", "ru": "Производитель"},
    "Model": {"en": "Model", "ru": "Модель"},
    "MarketingName": {"en": "Marketing name", "ru": "Название модели"},
    "SystemType": {"en": "System type", "ru": "Тип системы"},
    "TotalPhysicalMemory": {"en": "Total memory", "ru": "Общий объём памяти"},
    "NumberOfProcessors": {"en": "Processor sockets", "ru": "Процессорных сокетов"},
    "NumberOfLogicalProcessors": {"en": "Logical processors", "ru": "Логических процессоров"},
    "Caption": {"en": "Name", "ru": "Название"},
    "Version": {"en": "Version", "ru": "Версия"},
    "BuildNumber": {"en": "Build", "ru": "Сборка"},
    "OSArchitecture": {"en": "Architecture", "ru": "Архитектура"},
    "InstallDate": {"en": "Installation date", "ru": "Дата установки"},
    "LastBootUpTime": {"en": "Last boot", "ru": "Последняя загрузка"},
    "Locale": {"en": "Locale", "ru": "Локаль"},
    "Name": {"en": "Name", "ru": "Название"},
    "NumberOfCores": {"en": "Physical cores", "ru": "Физических ядер"},
    "MaxClockSpeed": {"en": "Maximum clock, MHz", "ru": "Максимальная частота, МГц"},
    "CurrentClockSpeed": {"en": "Current clock, MHz", "ru": "Текущая частота, МГц"},
    "VirtualizationFirmwareEnabled": {"en": "Firmware virtualization", "ru": "Виртуализация в прошивке"},
    "Capacity": {"en": "Capacity", "ru": "Объём"},
    "Speed": {"en": "Speed", "ru": "Скорость"},
    "ConfiguredClockSpeed": {"en": "Configured speed", "ru": "Настроенная частота"},
    "MemoryType": {"en": "Memory type", "ru": "Тип памяти"},
    "FormFactor": {"en": "Form factor", "ru": "Форм-фактор"},
    "DeviceLocator": {"en": "Slot", "ru": "Разъём"},
    "AdapterRAM": {"en": "Video memory", "ru": "Видеопамять"},
    "DriverVersion": {"en": "Driver version", "ru": "Версия драйвера"},
    "VideoModeDescription": {"en": "Video mode", "ru": "Видеорежим"},
    "CurrentHorizontalResolution": {"en": "Horizontal resolution", "ru": "Разрешение по горизонтали"},
    "CurrentVerticalResolution": {"en": "Vertical resolution", "ru": "Разрешение по вертикали"},
    "CurrentRefreshRate": {"en": "Refresh rate", "ru": "Частота обновления"},
    "Status": {"en": "Status", "ru": "Состояние"},
    "Product": {"en": "Product", "ru": "Продукт"},
    "SMBIOSBIOSVersion": {"en": "BIOS/UEFI version", "ru": "Версия BIOS/UEFI"},
    "ReleaseDate": {"en": "Release date", "ru": "Дата выпуска"},
    "FriendlyName": {"en": "Name", "ru": "Название"},
    "MediaType": {"en": "Media type", "ru": "Тип носителя"},
    "BusType": {"en": "Bus", "ru": "Шина"},
    "HealthStatus": {"en": "Health", "ru": "Состояние"},
    "OperationalStatus": {"en": "Operational status", "ru": "Рабочее состояние"},
    "Size": {"en": "Size", "ru": "Размер"},
    "DriveLetter": {"en": "Drive", "ru": "Диск"},
    "FileSystem": {"en": "File system", "ru": "Файловая система"},
    "SizeRemaining": {"en": "Free space", "ru": "Свободно"},
    "AdapterType": {"en": "Adapter type", "ru": "Тип адаптера"},
    "NetConnectionStatus": {"en": "Connection status", "ru": "Состояние подключения"},
    "ServiceName": {"en": "Service", "ru": "Служба"},
    "EstimatedChargeRemaining": {"en": "Charge, %", "ru": "Заряд, %"},
    "BatteryStatus": {"en": "Battery status", "ru": "Состояние батареи"},
    "DesignVoltage": {"en": "Design voltage", "ru": "Расчётное напряжение"},
    "ElementName": {"en": "Power plan", "ru": "Схема питания"},
    "DeviceName": {"en": "Device", "ru": "Устройство"},
    "DeviceClass": {"en": "Class", "ru": "Класс"},
    "DriverProviderName": {"en": "Driver provider", "ru": "Поставщик драйвера"},
    "DriverDate": {"en": "Driver date", "ru": "Дата драйвера"},
    "IsSigned": {"en": "Signed", "ru": "Подписан"},
    "Enabled": {"en": "Enabled", "ru": "Включено"},
    "Value": {"en": "Value", "ru": "Значение"},
    "HotFixID": {"en": "Update ID", "ru": "Идентификатор обновления"},
    "Description": {"en": "Description", "ru": "Описание"},
    "InstalledOn": {"en": "Installed on", "ru": "Дата установки"},
    "AntivirusSignatureLastUpdated": {"en": "Signature updated", "ru": "Обновление сигнатур"},
    "DisplayName": {"en": "Application", "ru": "Программа"},
    "DisplayVersion": {"en": "Version", "ru": "Версия"},
    "Publisher": {"en": "Publisher", "ru": "Издатель"},
}

BYTE_PROPERTIES = {"TotalPhysicalMemory", "Capacity", "AdapterRAM", "Size", "SizeRemaining"}
DATE_PROPERTIES = {"InstallDate", "LastBootUpTime", "ReleaseDate", "DriverDate", "InstalledOn", "AntivirusSignatureLastUpdated"}
_JSON_DATE = re.compile(r"^/Date\((-?\d+)(?:[+-]\d{4})?\)/$")
_DMTF_DATE = re.compile(r"^(\d{14})\.\d{6}[+-]\d{3}$")


def format_bytes(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    unit = units[0]
    for unit in units:
        if abs(number) < 1024 or unit == units[-1]:
            break
        number /= 1024
    return f"{number:.2f} {unit}"


def _label(property_name: str, language: str) -> str:
    return PROPERTY_LABELS.get(property_name, {}).get(language, property_name)


def format_date_value(value: Any, language: str) -> str:
    parsed: date | datetime | None = None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        match = _JSON_DATE.fullmatch(text)
        try:
            if match:
                parsed = datetime.fromtimestamp(int(match.group(1)) / 1000).astimezone()
            elif re.fullmatch(r"\d{8}", text):
                parsed = datetime.strptime(text, "%Y%m%d").date()
            elif (match := _DMTF_DATE.fullmatch(text)):
                parsed = datetime.strptime(match.group(1), "%Y%m%d%H%M%S")
            elif "T" in text:
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone()
        except (OverflowError, OSError, ValueError):
            parsed = None
        if parsed is None:
            return text
    else:
        return str(value)
    if isinstance(parsed, datetime):
        return parsed.strftime("%d.%m.%Y %H:%M:%S" if language == "ru" else "%Y-%m-%d %H:%M:%S")
    return parsed.strftime("%d.%m.%Y" if language == "ru" else "%Y-%m-%d")


def _format_value(property_name: str, value: Any, language: str) -> Any:
    if value is None or value == "":
        return ""
    if property_name in BYTE_PROPERTIES:
        return format_bytes(value)
    if property_name in DATE_PROPERTIES:
        return format_date_value(value, language)
    if isinstance(value, bool):
        return ("Yes" if value else "No") if language == "en" else ("Да" if value else "Нет")
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value if item not in (None, ""))
    return value


@dataclass(frozen=True, slots=True)
class CollectorSpec:
    key: str
    script: str
    properties: tuple[str, ...]
    table: bool = True

    @property
    def titles(self) -> dict[str, str]:
        return TITLE_LABELS[self.key]

    def collect(self, runner: Any, language: str) -> Section:
        raw_rows = runner.powershell_json(self.script)
        rows = [sanitize_mapping(row) for row in raw_rows]
        title = self.titles[language]
        if not rows:
            return Section(key=self.key, title=title)
        if not self.table:
            source = rows[0]
            fields = [
                Field(_label(name, language), _format_value(name, source.get(name), language))
                for name in self.properties
                if source.get(name) not in (None, "", [], {})
            ]
            return Section(key=self.key, title=title, fields=fields)
        headers = tuple(_label(name, language) for name in self.properties)
        formatted_rows = tuple(
            tuple(_format_value(name, row.get(name), language) for name in self.properties)
            for row in rows
            if any(row.get(name) not in (None, "", [], {}) for name in self.properties)
        )
        tables = [Table(headers=headers, rows=formatted_rows)] if formatted_rows else []
        return Section(key=self.key, title=title, tables=tables)


COLLECTOR_SPECS = (
    CollectorSpec(
        "overview",
        "$system=Get-CimInstance Win32_ComputerSystem; $product=Get-CimInstance Win32_ComputerSystemProduct; [pscustomobject]@{Manufacturer=$system.Manufacturer;Model=$system.Model;MarketingName=$product.Version;SystemType=$system.SystemType;TotalPhysicalMemory=$system.TotalPhysicalMemory;NumberOfProcessors=$system.NumberOfProcessors;NumberOfLogicalProcessors=$system.NumberOfLogicalProcessors}",
        ("Manufacturer", "Model", "MarketingName", "SystemType", "TotalPhysicalMemory", "NumberOfProcessors", "NumberOfLogicalProcessors"),
        table=False,
    ),
    CollectorSpec(
        "operating_system",
        "Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture,InstallDate,LastBootUpTime,Locale",
        ("Caption", "Version", "BuildNumber", "OSArchitecture", "InstallDate", "LastBootUpTime", "Locale"),
        table=False,
    ),
    CollectorSpec(
        "cpu",
        "Get-CimInstance Win32_Processor | Select-Object Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,CurrentClockSpeed,VirtualizationFirmwareEnabled",
        ("Name", "Manufacturer", "NumberOfCores", "NumberOfLogicalProcessors", "MaxClockSpeed", "CurrentClockSpeed", "VirtualizationFirmwareEnabled"),
    ),
    CollectorSpec(
        "memory",
        "Get-CimInstance Win32_PhysicalMemory | Select-Object Manufacturer,Capacity,Speed,ConfiguredClockSpeed,MemoryType,FormFactor,DeviceLocator",
        ("Manufacturer", "Capacity", "Speed", "ConfiguredClockSpeed", "MemoryType", "FormFactor", "DeviceLocator"),
    ),
    CollectorSpec(
        "graphics",
        "$gpu = Get-CimInstance Win32_VideoController | Select-Object @{N='Category';E={'GPU'}},Name,AdapterRAM,DriverVersion,VideoModeDescription,CurrentHorizontalResolution,CurrentVerticalResolution,CurrentRefreshRate,Status; $monitor = Get-CimInstance Win32_DesktopMonitor | Select-Object @{N='Category';E={'Monitor'}},Name,Manufacturer,Status; @($gpu)+@($monitor)",
        ("Category", "Name", "Manufacturer", "AdapterRAM", "DriverVersion", "VideoModeDescription", "CurrentHorizontalResolution", "CurrentVerticalResolution", "CurrentRefreshRate", "Status"),
    ),
    CollectorSpec(
        "firmware",
        "$board = Get-CimInstance Win32_BaseBoard | Select-Object @{N='Category';E={'Motherboard'}},Manufacturer,Product,Version,Status; $bios = Get-CimInstance Win32_BIOS | Select-Object @{N='Category';E={'BIOS/UEFI'}},Manufacturer,SMBIOSBIOSVersion,ReleaseDate,Status; @($board)+@($bios)",
        ("Category", "Manufacturer", "Product", "Version", "SMBIOSBIOSVersion", "ReleaseDate", "Status"),
    ),
    CollectorSpec(
        "storage",
        "$disk = Get-PhysicalDisk | Select-Object @{N='Category';E={'Physical disk'}},FriendlyName,MediaType,BusType,HealthStatus,OperationalStatus,Size; $volume = Get-Volume | Select-Object @{N='Category';E={'Volume'}},DriveLetter,FileSystem,HealthStatus,Size,SizeRemaining; @($disk)+@($volume)",
        ("Category", "FriendlyName", "DriveLetter", "MediaType", "BusType", "FileSystem", "HealthStatus", "OperationalStatus", "Size", "SizeRemaining"),
    ),
    CollectorSpec(
        "network",
        "Get-CimInstance Win32_NetworkAdapter | Where-Object PhysicalAdapter | Select-Object Name,Manufacturer,AdapterType,NetConnectionStatus,Speed,ServiceName",
        ("Name", "Manufacturer", "AdapterType", "NetConnectionStatus", "Speed", "ServiceName"),
    ),
    CollectorSpec(
        "audio",
        "Get-CimInstance Win32_SoundDevice | Select-Object Name,Manufacturer,Status",
        ("Name", "Manufacturer", "Status"),
    ),
    CollectorSpec(
        "battery",
        "$battery = Get-CimInstance Win32_Battery | Select-Object @{N='Category';E={'Battery'}},Name,BatteryStatus,EstimatedChargeRemaining,DesignVoltage,Status; $plan = Get-CimInstance -Namespace root\\cimv2\\power -Class Win32_PowerPlan | Where-Object IsActive | Select-Object @{N='Category';E={'Power plan'}},ElementName; @($battery)+@($plan)",
        ("Category", "Name", "BatteryStatus", "EstimatedChargeRemaining", "DesignVoltage", "ElementName", "Status"),
    ),
    CollectorSpec(
        "drivers",
        "Get-CimInstance Win32_PnPSignedDriver | Where-Object DeviceName | Select-Object DeviceName,DeviceClass,Manufacturer,DriverProviderName,DriverVersion,DriverDate,IsSigned",
        ("DeviceName", "DeviceClass", "Manufacturer", "DriverProviderName", "DriverVersion", "DriverDate", "IsSigned"),
    ),
    CollectorSpec(
        "security",
        "$items=@(); try {$mp=Get-MpComputerStatus; $items += [pscustomobject]@{Name='Microsoft Defender antivirus';Enabled=$mp.AntivirusEnabled;AntivirusSignatureLastUpdated=$mp.AntivirusSignatureLastUpdated}} catch {}; try {Get-NetFirewallProfile | ForEach-Object {$items += [pscustomobject]@{Name=('Firewall '+$_.Name);Enabled=$_.Enabled;Value=$_.DefaultInboundAction}}} catch {}; try {$t=Get-Tpm; $items += [pscustomobject]@{Name='TPM';Enabled=$t.TpmPresent;Value=$t.TpmReady}} catch {}; try {$s=Confirm-SecureBootUEFI; $items += [pscustomobject]@{Name='Secure Boot';Enabled=$s;Value=$s}} catch {}; try {Get-BitLockerVolume | ForEach-Object {$items += [pscustomobject]@{Name=('BitLocker '+$_.MountPoint);Enabled=($_.ProtectionStatus -eq 'On');Value=$_.VolumeStatus}}} catch {}; $uac=(Get-ItemProperty 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -ErrorAction SilentlyContinue).EnableLUA; $items += [pscustomobject]@{Name='User Account Control';Enabled=($uac -eq 1);Value=$uac}; $items",
        ("Name", "Enabled", "Value", "AntivirusSignatureLastUpdated"),
    ),
    CollectorSpec(
        "updates",
        "Get-CimInstance Win32_QuickFixEngineering | Select-Object HotFixID,Description,InstalledOn | Sort-Object InstalledOn -Descending",
        ("HotFixID", "Description", "InstalledOn"),
    ),
    CollectorSpec(
        "software",
        "$paths=@('HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*','HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'); Get-ItemProperty $paths -ErrorAction SilentlyContinue | Where-Object DisplayName | Select-Object DisplayName,DisplayVersion,Publisher,InstallDate | Sort-Object DisplayName -Unique",
        ("DisplayName", "DisplayVersion", "Publisher", "InstallDate"),
    ),
)

_SPECS_BY_KEY = {spec.key: spec for spec in COLLECTOR_SPECS}


def _collect(key: str, runner: Any, language: str) -> Section:
    return _SPECS_BY_KEY[key].collect(runner, language)


def collect_overview(runner: Any, language: str) -> Section:
    return _collect("overview", runner, language)


def collect_operating_system(runner: Any, language: str) -> Section:
    return _collect("operating_system", runner, language)


def collect_cpu(runner: Any, language: str) -> Section:
    return _collect("cpu", runner, language)


def collect_memory(runner: Any, language: str) -> Section:
    return _collect("memory", runner, language)


def collect_graphics(runner: Any, language: str) -> Section:
    return _collect("graphics", runner, language)


def collect_firmware(runner: Any, language: str) -> Section:
    return _collect("firmware", runner, language)


def collect_storage(runner: Any, language: str) -> Section:
    return _collect("storage", runner, language)


def collect_network(runner: Any, language: str) -> Section:
    return _collect("network", runner, language)


def collect_audio(runner: Any, language: str) -> Section:
    return _collect("audio", runner, language)


def collect_battery(runner: Any, language: str) -> Section:
    return _collect("battery", runner, language)


def collect_drivers(runner: Any, language: str) -> Section:
    return _collect("drivers", runner, language)


def collect_security(runner: Any, language: str) -> Section:
    return _collect("security", runner, language)


def collect_updates(runner: Any, language: str) -> Section:
    return _collect("updates", runner, language)


def collect_software(runner: Any, language: str) -> Section:
    return _collect("software", runner, language)


def collect_all(
    runner: Any,
    language: str,
    *,
    progress: Callable[[str, str], None] | None = None,
    selected_keys: tuple[str, ...] | list[str] | set[str] | None = None,
) -> tuple[list[Section], list[Diagnostic]]:
    notify = progress or (lambda phase, title: None)
    sections: list[Section] = []
    diagnostics: list[Diagnostic] = []
    selected = None if selected_keys is None else set(selected_keys)
    unknown = set() if selected is None else selected.difference(spec.key for spec in COLLECTOR_SPECS)
    if unknown:
        raise ValueError(f"unknown collector key: {sorted(unknown)[0]}")
    for spec in COLLECTOR_SPECS:
        if selected is not None and spec.key not in selected:
            continue
        title = spec.titles[language]
        notify("collecting", title)
        try:
            sections.append(spec.collect(runner, language))
        except Exception as exc:
            diagnostics.append(Diagnostic(source=spec.key, message=safe_error(exc)))
            notify("warning", title)
        else:
            notify("collected", title)
    return sections, diagnostics
