# DeviceReport Linux Port Design

## Goal

Ship DeviceReport 1.0.0 as standalone Windows x64 and Linux x86_64 executables. Both builds use the same bilingual console wizard, privacy rules, DOCX renderer, device-title logic, timestamped filenames, and error-only logs.

## Platform architecture

The application resolves a backend from `sys.platform`. The existing PowerShell/CIM implementation remains the Windows backend. A new Linux backend reads safe operating-system interfaces such as `/proc`, `/sys`, `/etc/os-release`, and non-interactive local commands. Both backends expose the same section keys and return the existing `Section` and `Diagnostic` models, so report generation and DOCX rendering remain platform-independent.

Linux collection never requires `sudo`. Missing commands or unreadable kernel files affect only their section and create a sanitized diagnostic. No backend collects host names, user names, home paths, addresses, MAC addresses, Wi-Fi names, hardware serials, UUIDs, asset tags, or package-manager credentials.

## Linux sections

- Overview: DMI manufacturer, model, product family/version, architecture, processor counts, and total memory.
- Operating system: distribution, version, kernel, architecture, boot time, and locale.
- Processor and memory: `/proc/cpuinfo` and `/proc/meminfo` summaries.
- Graphics, audio, firmware, storage, network, battery, and drivers: safe `/sys` data plus local tools when available.
- Security: Secure Boot availability, kernel lockdown, SELinux/AppArmor state, firewall service state, and encrypted block-device presence.
- Updates and software: local package-manager output with bounded execution time; users can disable either section in the wizard.

Device identity prioritizes a useful product name, then system family, then product version. Codes equal to the low-level model are ignored as marketing titles. The selected Overview section is not required for naming; a small safe identity probe runs separately when Overview is disabled.

## Packaging and release

PyInstaller produces `DeviceReport.exe` on `windows-latest` and `DeviceReport-linux-x86_64` on `ubuntu-latest`. Windows version resources populate company, description, versions, filename, copyright, comments, trademarks, private-build, and special-build fields. Both binaries support `--version`, which prints product, version, author, license scope, and current platform.

A final release job downloads both CI artifacts and updates branch `1.0.0` without force-pushing. That branch contains exactly:

- `DeviceReport.exe`
- `DeviceReport-linux-x86_64`
- `README.md`
- `LICENSE`

All source, tests, specifications, and workflows remain in `1.0.0-dev`. After a successful release publish, known intermediate feature branches are deleted. Permanent branches `main`, `1.0.0-dev`, and `1.0.0` remain.

## Verification

Unit tests mock every Linux file/command interface and verify cross-vendor identity, privacy exclusions, backend dispatch, section filtering, CLI compatibility, and cover contents. CI runs the complete test suite on Windows and Linux, builds both one-file executables, smoke-tests `--help` and `--version`, verifies artifact names, and publishes only after both build jobs pass.
