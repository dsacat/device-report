# DeviceReport 1.0.0

DeviceReport creates a structured bilingual DOCX inventory of a Windows or Linux computer. It is distributed as one standalone executable per platform and displays every collection stage in a terminal window.

Python is not required on the computer that runs either binary.

## Usage

On Windows, double-click `DeviceReport.exe`. It requests administrator access so Windows can expose all supported system providers.

On Linux, make the downloaded file executable and start it from a terminal; `sudo` is not required:

```bash
chmod +x DeviceReport-linux-x86_64
./DeviceReport-linux-x86_64
```

Choose a language:

```text
1 — Русский
2 — English
```

After choosing a language, select either all report sections or a custom set. In custom mode every section has an individual yes/no prompt, so Windows updates, installed software, drivers, or any other section can be omitted.

The language can also be selected non-interactively:

```powershell
DeviceReport.exe --lang ru
DeviceReport.exe --lang en
```

```bash
./DeviceReport-linux-x86_64 --lang ru
./DeviceReport-linux-x86_64 --lang en
```

Both builds expose embedded product information:

```text
DeviceReport.exe --version
./DeviceReport-linux-x86_64 --version
```

The generated DOCX is saved beside the running executable. Its name contains the best useful product name supplied by the computer firmware, followed by the report date and time.

Device identity is manufacturer-independent. DeviceReport checks the system product name, family, product version, manufacturer, and low-level model, then shows the best human-readable name as the large title and a different manufacturer/model code below it. For example, it can show `IdeaPad 3 15ARE05` above `LENOVO 81W4`, `Aspire A515-57` above `Acer N20C5`, or `Latitude 7490` above a Dell model code. Identity is still collected safely when the visible Overview section is disabled.

The cover contains the device identity and report date, but does not print a list of enabled tabs. The selected sections themselves remain in the document and table of contents.

Provider dates are normalized into readable localized values. Raw provider values such as PowerShell `/Date(1770135776000)/` are never written to the report.

If collection errors occur, a privacy-safe error-only log is created under `logs` beside the report. Successful runs create no log and no `logs` directory.

## Report contents

The report attempts to include:

- device overview and operating-system version;
- CPU, memory, graphics and displays;
- motherboard, BIOS/UEFI and Secure Boot state;
- physical storage, volumes and health information;
- network and audio adapters;
- battery and active power scheme;
- important devices and signed drivers;
- available platform security information such as Secure Boot, firewall, encryption, Defender/BitLocker/UAC on Windows, and Linux security modules;
- installed system updates and machine-wide applications/packages;
- a diagnostics section for unavailable platform providers.

Collectors are isolated. An unavailable CIM class, kernel interface, command, or platform component adds a diagnostic entry without stopping the rest of the report. Linux collection uses local `/proc`, `/sys`, `/etc/os-release`, and common utilities without automatic elevation or online scanning.

## Privacy

The program intentionally excludes sensitive or identifying information. It does not request or report:

- product keys or credentials;
- account and profile names;
- IP addresses or MAC addresses;
- Wi-Fi SSIDs and saved wireless profiles;
- hardware serial numbers, system UUIDs or asset tags;
- personal files, browser history or document lists.

The report stays on the local computer unless the user moves or shares it.

## Release files

Branch `1.0.0` contains final deliverables only:

- `DeviceReport.exe` — Windows 10/11 x64;
- `DeviceReport-linux-x86_64` — glibc-based Linux x86_64;
- `README.md` and `LICENSE`.

Source code, tests, specifications, and build workflows are kept in `1.0.0-dev`.

## Build from source

### Windows

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

### Linux

On Linux x86_64 with Python 3.11:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-build.txt
python -m pip install --no-deps -e .
python -m pytest -q
python -m PyInstaller DeviceReport-linux.spec --clean --noconfirm
./dist/DeviceReport-linux-x86_64 --version
```

The official Linux binary is built on Ubuntu 22.04 for compatibility with glibc 2.35 or newer. Hardware sections depend on the kernel interfaces and utilities available on the target distribution; missing sources produce sanitized diagnostics rather than stopping the report.

## Development

Source execution is intended for development and testing:

```text
PYTHONPATH=src python -m device_report --lang en
```

The project targets Python 3.11 on Windows 10/11 x64 and glibc-based Linux x86_64. Automated unit tests use deterministic mocked CIM, `/proc`, and `/sys` results and therefore do not collect information from the development machine.

## License

This project uses a custom personal and household use license. Commercial use is prohibited. See [LICENSE](LICENSE).
