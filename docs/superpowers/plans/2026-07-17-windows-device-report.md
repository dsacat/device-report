# Windows Device Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bilingual Windows console collector that produces a privacy-safe DOCX hardware/software report and ships as one UAC-enabled `DeviceReport.exe`.

**Architecture:** Python modules isolate Windows command execution, normalized report data, privacy filtering, collectors, localization, DOCX rendering, and CLI orchestration. Collectors call PowerShell/CIM through an injected runner so Linux unit tests can use deterministic fixtures. PyInstaller bundles Python and all dependencies into one console executable.

**Tech Stack:** Python 3.11, `python-docx`, `psutil`, `pytest`, PyInstaller, PowerShell/CIM, GitHub Actions on Windows.

---

## File Map

- `pyproject.toml`: package metadata, dependencies, pytest configuration and console entry point.
- `src/device_report/models.py`: normalized report section/value data classes.
- `src/device_report/i18n.py`: Russian/English strings and language parsing.
- `src/device_report/privacy.py`: sensitive-field and sensitive-value filtering.
- `src/device_report/runner.py`: subprocess execution, timeouts and PowerShell JSON decoding.
- `src/device_report/collectors.py`: independent Windows inventory collectors.
- `src/device_report/report.py`: report assembly and diagnostics.
- `src/device_report/docx_writer.py`: styled DOCX generation.
- `src/device_report/cli.py`: argument parsing, interactive menu and progress output.
- `src/device_report/__main__.py`: `python -m device_report` entry point.
- `DeviceReport.spec`: one-file console/UAC PyInstaller configuration.
- `build.cmd`: reproducible Windows build command.
- `tests/`: behavior-first tests and representative Windows fixtures.
- `.github/workflows/build-windows.yml`: Windows test/build/artifact verification.
- `README.md`: English usage and build documentation.
- `LICENSE`: personal/home-use non-commercial license.

### Task 1: Package skeleton and normalized data model

**Files:**
- Create: `pyproject.toml`
- Create: `src/device_report/__init__.py`
- Create: `src/device_report/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing model tests**

```python
def test_section_omits_empty_rows():
    section = Section("cpu", [Field("name", "Ryzen"), Field("serial", "")])
    assert section.nonempty_fields() == [Field("name", "Ryzen")]
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_models.py -q`
Expected: import failure because `device_report.models` does not exist.

- [ ] **Step 3: Implement immutable `Field`, `Table`, `Section`, `Diagnostic`, and `ReportData` data classes**

`Section.nonempty_fields()` must remove `None`, empty strings and empty collections without removing numeric zero or `False`.

- [ ] **Step 4: Verify GREEN and commit**

Run: `python -m pytest tests/test_models.py -q`
Expected: all model tests pass.

Commit: `feat: add normalized report data model`

### Task 2: Bilingual CLI language behavior

**Files:**
- Create: `src/device_report/i18n.py`
- Create: `src/device_report/cli.py`
- Test: `tests/test_i18n.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for `--lang` and menu selection**

```python
@pytest.mark.parametrize(("raw", "expected"), [("ru", "ru"), ("EN", "en")])
def test_normalize_language(raw, expected):
    assert normalize_language(raw) == expected

def test_menu_accepts_one_for_russian():
    assert choose_language(input_fn=lambda _: "1", output_fn=lambda _: None) == "ru"
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_i18n.py tests/test_cli.py -q`
Expected: missing functions/modules.

- [ ] **Step 3: Implement translations, `normalize_language`, parser and interactive menu**

Invalid `--lang` must produce exit code 2 through `argparse`. Menu input repeats until `1` or `2` is entered.

- [ ] **Step 4: Verify GREEN and commit**

Commit: `feat: add bilingual console language selection`

### Task 3: Privacy filtering

**Files:**
- Create: `src/device_report/privacy.py`
- Test: `tests/test_privacy.py`

- [ ] **Step 1: Write failing tests for excluded identifiers**

```python
@pytest.mark.parametrize("key", ["SerialNumber", "UUID", "MACAddress", "IPAddress", "ProductKey", "UserName"])
def test_sensitive_keys_are_removed(key):
    assert sanitize_mapping({key: "secret", "Name": "GPU"}) == {"Name": "GPU"}
```

Also test nested mappings/lists, profile paths, Wi-Fi SSIDs and environment values.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_privacy.py -q`
Expected: missing `sanitize_mapping`.

- [ ] **Step 3: Implement recursive key/value filtering**

Use normalized case-insensitive key matching and replace suspicious free-text values with omission; never log the removed value.

- [ ] **Step 4: Verify GREEN and commit**

Commit: `feat: filter sensitive device information`

### Task 4: Safe Windows command runner

**Files:**
- Create: `src/device_report/runner.py`
- Test: `tests/test_runner.py`

- [ ] **Step 1: Write failing tests for success, timeout, command failure and JSON decoding**

```python
def test_json_object_is_normalized_to_list(fake_process):
    runner = CommandRunner(process=fake_process(stdout='{"Name":"CPU"}'))
    assert runner.powershell_json("Get-CimInstance X") == [{"Name": "CPU"}]
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_runner.py -q`
Expected: missing runner.

- [ ] **Step 3: Implement `CommandResult`, `CommandError`, `CommandTimeout`, and `CommandRunner`**

PowerShell invocation uses `-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass` and UTF-8 JSON. Every call has a finite timeout and captures stdout/stderr without `shell=True`.

- [ ] **Step 4: Verify GREEN and commit**

Commit: `feat: add timeout-safe Windows command runner`

### Task 5: Device collectors

**Files:**
- Create: `src/device_report/collectors.py`
- Create: `tests/fixtures/cim_samples.py`
- Test: `tests/test_collectors.py`

- [ ] **Step 1: Add failing tests for overview, OS, CPU, memory, graphics, firmware, storage, network, audio, battery, drivers, security, updates and software**

Each test injects a fake runner keyed by collector command and asserts normalized `Section` output. Include missing-class and partial-data cases.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_collectors.py -q`
Expected: missing collector functions.

- [ ] **Step 3: Implement one collector function per report section**

Use explicit PowerShell property selection so sensitive fields are never requested. Apply `sanitize_mapping` before normalization as defense in depth. Keep queries read-only.

- [ ] **Step 4: Implement `collect_all` with isolation and progress callbacks**

```python
def collect_all(runner, progress):
    sections, diagnostics = [], []
    for collector in COLLECTORS:
        try:
            sections.append(collector(runner))
        except Exception as exc:
            diagnostics.append(Diagnostic(collector.__name__, safe_error(exc)))
    return sections, diagnostics
```

- [ ] **Step 5: Verify GREEN and commit**

Commit: `feat: collect Windows hardware and software inventory`

### Task 6: Report assembly, device name and output path

**Files:**
- Create: `src/device_report/report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Write failing filename and placeholder-filter tests**

```python
def test_device_title_omits_generic_values():
    assert build_device_title("System manufacturer", "System Product Name") is None

def test_output_name_uses_safe_device_and_timestamp():
    assert build_output_name("Lenovo ThinkPad T14", FIXED_TIME).name == "Lenovo ThinkPad T14 2026-07-17_18-30-00.docx"
```

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_report.py -q`
Expected: missing report functions.

- [ ] **Step 3: Implement title cleanup, Windows-safe filename generation and `build_report_data`**

Output base directory is `Path(sys.executable).resolve().parent` when frozen and the current project directory during source execution.

- [ ] **Step 4: Verify GREEN and commit**

Commit: `feat: assemble localized device report`

### Task 7: Styled DOCX writer

**Files:**
- Create: `src/device_report/docx_writer.py`
- Test: `tests/test_docx_writer.py`

- [ ] **Step 1: Write failing DOCX structure tests**

Generate into `tmp_path`, reopen with `python-docx`, and assert the localized title, all section headings, table cells, diagnostics heading, header/footer text and absence of excluded sentinel secrets.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_docx_writer.py -q`
Expected: missing writer.

- [ ] **Step 3: Implement document styling and rendering**

Create styles programmatically. Add title/timestamp, TOC field, Heading 1/2 sections, two-column field tables, multi-column detail tables, alternating row shading, repeated header rows, page fields and diagnostics.

- [ ] **Step 4: Verify GREEN and commit**

Commit: `feat: render styled bilingual DOCX reports`

### Task 8: Application orchestration and exit behavior

**Files:**
- Modify: `src/device_report/cli.py`
- Create: `src/device_report/__main__.py`
- Test: `tests/test_application.py`

- [ ] **Step 1: Write failing end-to-end tests with injected collectors/writer**

Test successful generation, partial collector failure, output write failure, `--help`, `--lang ru`, `--lang en`, and interactive selection. Assert full progress lines and non-zero fatal exit codes.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_application.py -q`
Expected: missing orchestration behavior.

- [ ] **Step 3: Implement `main(argv=None, ...) -> int`**

Print localized progress for every section, preserve diagnostics, save beside EXE and print the absolute final path. Pause only for interactive runs, not `--help` or automated argument mode.

- [ ] **Step 4: Verify GREEN and commit**

Commit: `feat: complete DeviceReport console workflow`

### Task 9: One-file Windows build and documentation

**Files:**
- Create: `DeviceReport.spec`
- Create: `build.cmd`
- Create: `.github/workflows/build-windows.yml`
- Create: `README.md`
- Create: `LICENSE`
- Test: `tests/test_packaging.py`

- [ ] **Step 1: Write packaging metadata tests**

Assert the spec enables console and UAC, executable name is `DeviceReport`, build script uses the spec, README documents both language modes, and license prohibits commercial use.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_packaging.py -q`
Expected: required files are absent.

- [ ] **Step 3: Add PyInstaller spec and build script**

`build.cmd` creates `.venv`, installs the locked build requirements, runs tests, invokes `python -m PyInstaller DeviceReport.spec --clean --noconfirm`, and verifies `dist` contains only `DeviceReport.exe`.

- [ ] **Step 4: Add Windows CI, English README and personal-use license**

CI uses `windows-latest`, Python 3.11, runs all tests, builds the EXE, runs `DeviceReport.exe --help`, verifies the one-file distribution and uploads only the EXE artifact.

- [ ] **Step 5: Verify GREEN and commit**

Commit: `build: add one-file Windows release workflow`

### Task 10: Final verification and GitHub publication

**Files:**
- Modify: version metadata only if verification requires it.

- [ ] **Step 1: Run the complete local verification suite**

```bash
python -m pytest -q
python -m compileall -q src tests
python -m device_report --help
python -m build
```

- [ ] **Step 2: Inspect privacy and packaging invariants**

Search source/tests/docs for accidental secrets or collection of excluded identifiers. Inspect wheel/sdist contents and confirm there are no caches or generated reports.

- [ ] **Step 3: Publish**

Create repository `windows-device-report`, push branch `v1.0.0`, and configure the Windows workflow. Wait for the workflow and verify its artifact contains exactly `DeviceReport.exe` before reporting completion.

## Self-Review Result

- Every design-spec section maps to a task above.
- Interfaces remain consistent: collectors return `Section`, orchestration builds `ReportData`, and the writer consumes `ReportData`.
- Privacy filtering occurs both before normalization and in end-to-end document assertions.
- No runtime resource/template files are required.
- The plan has no deferred implementation placeholders.
