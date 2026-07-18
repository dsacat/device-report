# DeviceReport Linux Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce privacy-safe standalone DeviceReport 1.0.0 binaries for Windows x64 and Linux x86_64 from one platform-dispatched codebase.

**Architecture:** Preserve the current Windows collector and shared report pipeline, add a Linux collector with the same section contract, and resolve the backend at runtime. Build both platforms in independent CI jobs and publish them through one gated release job.

**Tech Stack:** Python 3.11, python-docx, PyInstaller 6.21, PowerShell/CIM, Linux `/proc` and `/sys`, pytest, GitHub Actions.

---

### Task 1: Finalize cross-vendor identity ranking

**Files:**
- Modify: `src/device_report/report.py`
- Test: `tests/test_customization.py`

- [ ] Add an HP-style failing test where a verbose firmware family must not replace a useful product name.
- [ ] Prefer the first human-readable identity candidate in the defined source order, with compact codes falling back to later human-readable candidates.
- [ ] Run the identity tests and commit the fix.

### Task 2: Add platform backend resolution

**Files:**
- Create: `src/device_report/backend.py`
- Modify: `src/device_report/cli.py`
- Test: `tests/test_backend.py`

- [ ] Add failing tests for Windows/Linux resolution and unsupported-platform errors.
- [ ] Define a backend object containing section specs, collection function, identity function, runner factory, and platform label.
- [ ] Route parser choices, section prompts, collection, and `--version` through the active backend.
- [ ] Run focused tests and commit.

### Task 3: Implement safe Linux collection primitives

**Files:**
- Create: `src/device_report/linux_runner.py`
- Create: `src/device_report/linux_collectors.py`
- Test: `tests/test_linux_runner.py`
- Test: `tests/test_linux_collectors.py`

- [ ] Add failing tests for bounded command execution, safe text/JSON reads, DMI identity, `/proc` parsing, and disabled-section filtering.
- [ ] Implement injectable file and process access with sanitized command errors.
- [ ] Implement all fourteen Linux sections using only safe fields and no privilege escalation.
- [ ] Verify sensitive keys and values never enter returned models; run focused tests and commit.

### Task 4: Add Linux packaging and complete metadata

**Files:**
- Create: `DeviceReport-linux.spec`
- Modify: `windows-version-info.txt`
- Modify: `pyproject.toml`
- Test: `tests/test_packaging.py`

- [ ] Add failing assertions for the Linux spec, generic package metadata, standard Windows version strings, and platform-aware `--version` output.
- [ ] Add the Linux one-file spec and fill every applicable Windows string resource.
- [ ] Smoke-build the Linux ELF locally, run `--help` and `--version`, and commit.

### Task 5: Build and publish both platforms

**Files:**
- Modify: `.github/workflows/build-windows.yml`
- Modify: `README.md`
- Test: `tests/test_packaging.py`

- [ ] Add failing workflow tests for separate Windows/Linux build jobs, two artifacts, a gated publish job, four exact release files, and feature-branch cleanup.
- [ ] Refactor CI into Windows build, Linux build, and release jobs without force-pushing.
- [ ] Document Linux usage, permissions, output location, build commands, metadata, and platform limitations.
- [ ] Run all tests, compileall, build/smoke-test Linux, and commit.

### Task 6: Integrate, release, and clean branches

- [ ] Push the feature commit and open a PR against `1.0.0-dev`.
- [ ] Require complete Windows and Linux CI success before merging.
- [ ] Verify the push workflow publishes exactly two binaries plus README and LICENSE.
- [ ] Download both release binaries, verify formats, hashes, metadata/version output, and absence of a Windows icon resource.
- [ ] Delete all known intermediate feature branches and verify only `main`, `1.0.0-dev`, and `1.0.0` remain.
