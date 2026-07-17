# DeviceReport 1.0.0 Customization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a polished Windows DeviceReport 1.0.0 with selectable report sections, normalized dates, Lenovo marketing/model hierarchy, error-only logs, refreshed DOCX styles, and complete icon-free EXE metadata.

**Architecture:** Keep collection, report assembly, rendering, logging, and CLI interaction independently testable. Extend the existing models minimally, centralize date parsing in the collector formatting layer, and preserve non-interactive `--lang` compatibility.

**Tech Stack:** Python 3.11, python-docx, PyInstaller 6.21, PowerShell/CIM, pytest, GitHub Actions.

---

### Task 1: Normalize every date representation

**Files:** `src/device_report/collectors.py`, `tests/test_collectors.py`

- [ ] Add failing parameterized tests for `/Date(milliseconds)/`, offset JSON dates, ISO, DMTF, `YYYYMMDD`, malformed values, and RU/EN output.
- [ ] Run `python -m pytest tests/test_collectors.py -q` and confirm date cases fail.
- [ ] Implement `format_date_value(value, language)` and route every registered date property through it.
- [ ] Run focused and full tests; commit `fix: normalize collected date values`.

Expected registrations: `InstallDate`, `LastBootUpTime`, `ReleaseDate`, `DriverDate`, `InstalledOn`, and security/update date values with explicit property aliases.

### Task 2: Filter collectors and number progress

**Files:** `src/device_report/collectors.py`, `tests/test_collectors.py`

- [ ] Add failing tests proving selected keys preserve canonical order, disabled collectors are never invoked, unknown keys fail clearly, and progress receives `(index, total)`.
- [ ] Run focused tests and confirm RED.
- [ ] Extend `collect_all(..., selected_keys=None)` and progress notification without changing collector isolation.
- [ ] Run focused/full tests; commit `feat: filter report collectors`.

### Task 3: Add interactive section wizard and CLI selection

**Files:** `src/device_report/cli.py`, `src/device_report/i18n.py`, `tests/test_cli.py`, `tests/test_application.py`, `tests/test_i18n.py`

- [ ] Add failing tests for all/custom choice, per-section yes/no, invalid input retry, zero-selection retry, summary output, `--select`, repeatable `--section`, and `--lang` selecting all without prompts.
- [ ] Run focused tests and confirm RED.
- [ ] Implement `choose_sections`, parser options, selection summary, and `[NN/TT]` progress formatting with localized strings.
- [ ] Pass selected keys from `main` to `run_application` and then to collection while keeping injected test functions compatible.
- [ ] Run focused/full tests; commit `feat: add report section wizard`.

### Task 4: Collect and resolve marketing identity

**Files:** `src/device_report/collectors.py`, `src/device_report/models.py`, `src/device_report/report.py`, `tests/test_collectors.py`, `tests/test_report.py`

- [ ] Add failing tests for the safe `Win32_ComputerSystemProduct` query, Lenovo `IdeaPad 3 15ARE05` main title, `LENOVO 81W4` subtitle, generic-value fallback, and absence of UUID/serial properties.
- [ ] Run focused tests and confirm RED.
- [ ] Add sanitized marketing fields to overview, optional `ReportData.subtitle`, and deterministic title/subtitle resolution.
- [ ] Run focused/full tests; commit `feat: display marketing model and machine type`.

### Task 5: Render refreshed DOCX

**Files:** `src/device_report/docx_writer.py`, `tests/test_docx_writer.py`

- [ ] Add failing DOCX XML/style tests for title, subtitle, timestamp, accent divider, enabled-section summary, heading spacing, and table styling.
- [ ] Run focused tests and confirm RED.
- [ ] Implement the title block and restrained dark-blue style refresh using python-docx only.
- [ ] Run focused/full tests; commit `style: refresh DeviceReport document`.

### Task 6: Write privacy-safe error-only logs

**Files:** `src/device_report/error_log.py`, `src/device_report/cli.py`, `src/device_report/i18n.py`, `tests/test_error_log.py`, `tests/test_application.py`

- [ ] Add failing tests that no diagnostics create no directory, diagnostics create `logs/DeviceReport_errors_<timestamp>.log`, content contains only timestamp/version/source/safe category, and logging failure does not replace report outcome.
- [ ] Run focused tests and confirm RED.
- [ ] Implement the UTF-8 log writer and integrate it after collection and on fatal application failure.
- [ ] Run focused/full tests; commit `feat: add error-only logs`.

### Task 7: Remove icon and add EXE version information

**Files:** `windows-version-info.txt`, `DeviceReport.spec`, `tests/test_packaging.py`

- [ ] Add failing packaging tests for `icon='NONE'`, version file reference, author/company, description, copyright, product/file version, original filename, and comments.
- [ ] Run packaging tests and confirm RED.
- [ ] Create the PyInstaller `VSVersionInfo` resource and reference it from `EXE(version=..., icon='NONE')`.
- [ ] Run packaging/full tests; commit `build: add executable metadata without icon`.

### Task 8: Update README and release contract

**Files:** `README.md`, `.github/workflows/build-windows.yml`, `tests/test_packaging.py`

- [ ] Add failing documentation tests for section selection, Lenovo title hierarchy, normalized dates, conditional `logs` folder, EXE properties, and clean release/dev branches.
- [ ] Update README and keep CI publishing only `DeviceReport.exe`, README, and LICENSE to `1.0.0`.
- [ ] Run full tests; commit `docs: document customizable reports`.

### Task 9: Verify, integrate, and publish

- [ ] Run full pytest, compileall, source `--help`, and privacy-focused tests.
- [ ] Merge `feature/report-customization` into local `1.0.0-dev` without rewriting history.
- [ ] Upload the new source commit to GitHub `1.0.0-dev` and monitor Windows Actions.
- [ ] Confirm the workflow tests, builds, smoke-tests, and safely updates `1.0.0` with exactly three files.
- [ ] Download the final EXE, compute SHA-256, replace the saved deliverable, and provide links.
