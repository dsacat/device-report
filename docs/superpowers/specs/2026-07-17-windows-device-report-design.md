# Windows Device Report — Design Specification

## Purpose

Build a Windows console application that collects a broad, structured inventory of the current device and writes it to a polished DOCX report. The distributed application must be a single standalone executable named `DeviceReport.exe`; Python must not be installed on the target computer.

## Deliverable

- One user-facing file: `DeviceReport.exe`.
- Windows-only console application with a visible, detailed progress log.
- The executable always requests administrator privileges through its embedded manifest.
- The generated DOCX is saved in the same directory as the executable.
- No secondary runtime files are distributed with the executable.

The source repository may contain source code, tests, build configuration, documentation, and CI files. The one-file restriction applies to the distributed application.

## User Interface

The application supports both interactive and non-interactive language selection:

- `DeviceReport.exe --lang ru` creates a Russian report;
- `DeviceReport.exe --lang en` creates an English report;
- without `--lang`, the console shows `1 — Русский` and `2 — English`.

The console remains visible for the entire run. It reports startup checks, every collection section, warnings, DOCX generation, and the final output path. A failure in one section does not abort the whole report.

## Report Naming and Heading

The program obtains the device manufacturer and model when available. Empty, generic, duplicated, or placeholder values are omitted.

- With a useful device name/model: `<device> <YYYY-MM-DD_HH-MM-SS>.docx`.
- Without a useful device name/model: `<YYYY-MM-DD_HH-MM-SS>.docx`.

The first page uses the same device name as the main title and displays the report date and time next to or directly below it. If no useful device name exists, the date and time become the main heading.

## Information Collected

The report contains the following sections when Windows exposes the data:

1. Overview: manufacturer, model, device type, architecture, uptime and report time.
2. Operating system: edition, version, build, installation type, boot mode, locale, time zone and update state.
3. CPU: model, physical/logical core counts, clock information, architecture and supported virtualization status.
4. Memory: total/available memory, slot usage, module capacities, speeds, types and manufacturers.
5. Graphics: GPU names, driver versions, video memory, current resolution and display information.
6. Motherboard and firmware: board manufacturer/model, BIOS/UEFI vendor, version, release date and Secure Boot state.
7. Storage: physical drive models, media/bus types, capacity and health; volumes, file systems, capacity and free space.
8. Network: adapter names, link state, speed, connection type and driver information.
9. Audio: playback/capture device names, manufacturers and status.
10. Battery and power: battery presence, charge, health information when exposed, active power scheme and sleep capabilities.
11. Devices and drivers: important Plug and Play device categories, driver providers, versions, dates and error states.
12. Security: Windows Security/Defender status, firewall profiles, TPM availability, Secure Boot, BitLocker state and UAC state.
13. Installed Windows updates: update identifiers, descriptions and installation dates.
14. Software summary: installed applications and versions without user-specific paths or account data.
15. Diagnostics: failed collectors, unavailable Windows classes and non-sensitive warnings.

Collectors use built-in Windows facilities such as PowerShell/CIM, the registry and standard system commands. Results are normalized before rendering so the document layer does not depend on raw command output.

## Privacy Exclusions

The report must not collect or display:

- Windows or software product keys;
- account names, profile names or lists of local/domain users;
- passwords, tokens, browser data or credentials;
- IP addresses, MAC addresses, Wi-Fi SSIDs or saved wireless profiles;
- hardware serial numbers, UUIDs, asset tags or TPM ownership data;
- document lists, file contents, browsing history or personal folder paths;
- environment-variable values that may contain secrets.

Generic hardware identifiers may be included only when they cannot identify the individual device.

## Architecture

The implementation uses Python 3.11 and is packaged with PyInstaller using `--onefile`, `--console`, and `--uac-admin`. Runtime dependencies are bundled into the executable.

The code is divided into focused modules:

- CLI and language selection;
- command execution with timeouts and UTF-8/Windows-code-page handling;
- independent information collectors;
- privacy filtering and normalization;
- bilingual labels and messages;
- DOCX styling/rendering;
- application orchestration and diagnostics.

Collectors return typed section data rather than formatted paragraphs. The renderer consumes the normalized model and builds headings, summary tables, detail tables, status badges and a diagnostics appendix.

## DOCX Presentation

The report uses a restrained technical style:

- title page with device name and timestamp;
- automatic table of contents field where supported by Word;
- consistent Heading 1/2 hierarchy;
- compact overview cards/tables;
- alternating table-row shading;
- localized labels and status text;
- page header/footer with report title, timestamp and page field;
- explicit `Unavailable` / `Недоступно` values instead of blank cells;
- diagnostics at the end rather than raw stack traces in normal sections.

No template, icon, font or other resource file is required at runtime.

## Error Handling

- Every external command has a timeout.
- Each collector is isolated; one failure produces a diagnostic entry and collection continues.
- Missing commands, unsupported Windows versions and inaccessible CIM classes are treated as unavailable data.
- Invalid `--lang` values return a clear console error and non-zero exit code.
- Failure to write beside the executable is reported clearly; the program does not silently redirect the report elsewhere.
- Temporary files created internally by PyInstaller or DOCX generation are cleaned up normally and are not distributed artifacts.

## Testing

Automated tests run without requiring Windows hardware by mocking command output and registry access. They cover:

- language parsing and interactive selection;
- filename/title construction;
- privacy-field removal;
- parsing and normalization of representative CIM/PowerShell responses;
- partial collector failure and timeout behavior;
- Russian and English labels;
- DOCX structure and required headings;
- command-line exit codes.

Windows CI performs a PyInstaller smoke build, launches `DeviceReport.exe --help`, and verifies that the distribution contains exactly one executable. Manual acceptance testing runs the EXE as administrator on Windows and opens both RU and EN reports in Microsoft Word or LibreOffice.

## Repository and Release

- Repository name: `windows-device-report`.
- Executable name: `DeviceReport.exe`.
- Initial version branch: `v1.0.0`.
- README language: English.
- License: custom personal/home-use, non-commercial license; it must not be presented as an open-source license.

## Acceptance Criteria

- A Windows user receives and runs only `DeviceReport.exe`.
- Python is not required on the target device.
- UAC elevation is requested at startup.
- The console displays full progress throughout the run.
- RU/EN menu selection and `--lang ru/en` both work.
- A styled DOCX is saved beside the executable.
- Missing sections do not prevent the rest of the report from being produced.
- The report includes the defined hardware, firmware, operating system, security, driver and software sections.
- None of the privacy-excluded fields appear in the report or diagnostic logs.
