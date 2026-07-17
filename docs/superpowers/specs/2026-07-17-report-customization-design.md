# DeviceReport 1.0.0 Report Customization Design

## Goal

Improve the Windows 1.0.0 console workflow and DOCX presentation, let interactive users include all report sections or choose them individually, identify Lenovo systems by both marketing name and machine-type code, create privacy-safe error logs under `logs`, and add complete Windows version metadata while removing the PyInstaller icon.

## Interactive section selection

The no-argument double-click workflow remains a numbered bilingual console wizard:

1. Choose Russian or English.
2. Choose `Include all sections` or `Select sections`.
3. When custom selection is chosen, answer yes/no for each available section in report order.
4. Display a compact numbered summary of enabled sections.
5. Start collection immediately when at least one section is enabled.

The section prompts include all fourteen existing collectors: overview, operating system, CPU, memory, graphics/displays, motherboard/firmware, storage, network, audio, battery/power, devices/drivers, security, installed updates, and installed software. Invalid input repeats only the current question. A custom selection with zero enabled sections shows a localized warning and restarts section selection.

To preserve scriptability, `--lang ru|en` continues to select all sections without prompting. A new `--select` option requests the section wizard when a language is supplied on the command line. A new repeatable `--section KEY` option selects exact section keys non-interactively; it is mutually exclusive with `--select`. `--section` rejects unknown keys through `argparse`.

The collector dispatcher accepts an ordered set of selected keys and never invokes disabled collectors. Progress numbering uses the number of enabled collectors, for example `[03/10]` rather than `[03/14]`.

## Console presentation

The console uses Unicode-safe plain text and no terminal-control dependency. It displays a bordered product header, consistent numbered menu choices, a selected-sections summary, numbered collection progress, warning lines, the DOCX path, and the error-log path when one exists. Output remains readable when redirected to a text file or used in a basic Windows console.

No ANSI color is required because color support varies between Windows console hosts. The visual hierarchy comes from spacing, short labels, separators, and progress counters.

## Device identity and Lenovo behavior

The overview collector adds a separate privacy-safe CIM query:

```powershell
Get-CimInstance Win32_ComputerSystemProduct |
    Select-Object Vendor,Name,Version
```

It never requests `IdentifyingNumber`, `UUID`, serial numbers, or SKUs. For Lenovo devices, `Version` commonly contains the marketing name, such as `IdeaPad 3 15ARE05`, while `Win32_ComputerSystem.Model` contains the machine-type code, such as `81W4`.

Report identity uses these priorities:

- main title: useful system-product `Version`, then useful computer-system model;
- subtitle: manufacturer plus computer-system model when it differs from the title;
- fallback: the existing manufacturer/model title behavior when the marketing field is missing or generic.

For the target example, the DOCX title block is:

```text
IdeaPad 3 15ARE05
LENOVO 81W4
Generated 2026-07-17 18:30:00
```

The main title is the largest line. The subtitle is smaller and muted. Both values pass through the existing privacy sanitizer and filename sanitizer. The generated DOCX filename uses the main title plus date and time.

## DOCX visual refresh

The report keeps its current structured tables, header/footer, page numbering, and table-of-contents field. The refresh adds:

- a compact cover block with main title, subtitle, generation time, and a thin accent divider;
- clearer heading sizes and spacing;
- a restrained dark-blue accent palette with high-contrast table headers;
- consistent cell padding and alternating row shading;
- improved empty-section and diagnostics presentation;
- a short enabled-sections summary near the beginning of the report.

The document remains printable in grayscale and does not embed external images, fonts, or personal branding.

## Date normalization

All collected date fields pass through one centralized date formatter before entering the report model. Raw provider encodings must never appear in the DOCX. The formatter recognizes:

- PowerShell JSON dates such as `/Date(1770135776000)/` and `/Date(1770135776000+0300)/`;
- ISO 8601 timestamps, including timezone suffixes;
- CIM/DMTF timestamps when a provider returns them as text;
- registry-style application dates in `YYYYMMDD` form;
- already parsed Python `date` and `datetime` values.

Epoch milliseconds are converted to the report's local timezone. Russian output uses `DD.MM.YYYY HH:MM:SS`; English output uses `YYYY-MM-DD HH:MM:SS`. Date-only values omit the time. Unknown or malformed values remain sanitized text rather than causing a collector failure.

Date normalization applies to Windows installation time, last boot, BIOS release, driver dates, installed updates, application installation dates, security signature times, and any future property whose name is registered as a date field.

## Error-only logs

No log is created when the run has no errors. When at least one collector diagnostic or fatal application error occurs, create:

```text
<output directory>\logs\DeviceReport_errors_YYYY-MM-DD_HH-MM-SS.log
```

The `logs` directory is created lazily only when the log is required. The UTF-8 log contains only:

- report date and time;
- application version;
- collector key or `application` source;
- sanitized exception class or diagnostic category.

It never contains collected device values, command text, PowerShell stderr, user names, profile paths, IP/MAC addresses, serials, UUIDs, environment variables, or output document contents. Logging failures produce a console warning but do not replace the primary application result.

## Windows executable metadata and icon

PyInstaller receives `icon='NONE'`, which suppresses the PyInstaller icon and leaves Windows to show its generic executable icon. A UTF-8 version resource file supplies:

- `CompanyName`: `dsa_cat`
- `FileDescription`: `Privacy-safe bilingual Windows device inventory report`
- `FileVersion`: `1.0.0.0`
- `InternalName`: `DeviceReport`
- `LegalCopyright`: `Copyright © 2026 dsa_cat`
- `OriginalFilename`: `DeviceReport.exe`
- `ProductName`: `DeviceReport`
- `ProductVersion`: `1.0.0.0`
- `Comments`: `Personal and household use only`

The executable remains a one-file console application with the administrator manifest enabled.

## Architecture changes

- `cli.py` owns wizard input, selection summary, and progress formatting.
- `collectors.py` exposes stable collector keys/titles and filters collection by selected keys.
- `report.py` resolves main title/subtitle and timestamped output names.
- `models.py` adds an optional report subtitle and selected-section metadata.
- `docx_writer.py` renders the refreshed title block and document styles.
- a new `error_log.py` writes sanitized error-only logs.
- `DeviceReport.spec` references the version resource and disables the bundled icon.

Existing dependency-injection seams remain so every interaction can be tested without collecting from the development machine.

## Testing and release

Tests are written before production changes. Coverage includes full/custom selection, invalid input, zero-selection retry, CLI compatibility, collector filtering, progress numbering, Lenovo identity priority, subtitle rendering, timestamped filenames, PowerShell/ISO/CIM/registry date normalization in both languages, lazy `logs` creation, sanitization, logging failure behavior, version-resource contents, and icon suppression.

GitHub Actions must pass the complete test suite, build `DeviceReport.exe`, smoke-test `--help`, and publish a clean `1.0.0` branch containing only `DeviceReport.exe`, `README.md`, and `LICENSE`. Source, tests, specifications, and workflow remain in `1.0.0-dev`.

## Out of scope

- changing the personal-use license terms;
- collecting new sensitive identifiers;
- a graphical Windows interface;
- saving or remembering section selections between runs;
- creating logs for successful runs;
- Linux implementation, which remains a separate paused workstream.
