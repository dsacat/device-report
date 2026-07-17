# Windows Device Report

Windows Device Report creates a structured bilingual DOCX inventory of a Windows computer. It is distributed as a single standalone executable, always runs with administrator privileges, and displays every collection stage in a full console window.

Python is not required on the computer that runs `DeviceReport.exe`.

## Usage

Double-click `DeviceReport.exe` and choose a language:

```text
1 — Русский
2 — English
```

The language can also be selected from a terminal:

```powershell
DeviceReport.exe --lang ru
DeviceReport.exe --lang en
```

The generated DOCX is saved beside `DeviceReport.exe`. Its name contains the useful manufacturer/model values when Windows provides them, followed by the report date and time.

## Report contents

The report attempts to include:

- device overview and Windows version;
- CPU, memory, graphics and displays;
- motherboard, BIOS/UEFI and Secure Boot state;
- physical storage, volumes and health information;
- network and audio adapters;
- battery and active power scheme;
- important devices and signed drivers;
- Defender, firewall, TPM, BitLocker and UAC status;
- installed Windows updates and machine-wide applications;
- a diagnostics section for unavailable Windows providers.

Collectors are isolated. An unavailable CIM class or Windows component adds a diagnostic entry without stopping the rest of the report.

## Privacy

The program intentionally excludes sensitive or identifying information. It does not request or report:

- product keys or credentials;
- account and profile names;
- IP addresses or MAC addresses;
- Wi-Fi SSIDs and saved wireless profiles;
- hardware serial numbers, system UUIDs or asset tags;
- personal files, browser history or document lists.

The report stays on the local computer unless the user moves or shares it.

## Build from source

Building requires Windows, Python 3.11 and the Python launcher. Run:

```cmd
build.cmd
```

The script creates an isolated build environment, installs the pinned dependencies, runs the tests, builds through PyInstaller, and verifies that `dist` contains only `DeviceReport.exe`.

Equivalent manual commands:

```cmd
py -3.11 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements-build.txt
python -m pip install --no-deps -e .
python -m pytest -q
python -m PyInstaller DeviceReport.spec --clean --noconfirm
```

PyInstaller embeds the Python interpreter, `python-docx`, and the required runtime modules into the executable. The embedded UAC manifest requests administrator access at startup.

## Development

Source execution is intended for development and testing:

```powershell
$env:PYTHONPATH = "src"
python -m device_report --lang en
```

The project targets Python 3.11 and Windows 10/11. Automated unit tests use deterministic mocked CIM results and therefore do not collect information from the development machine.

## License

This project uses a custom personal and household use license. Commercial use is prohibited. See [LICENSE](LICENSE).

