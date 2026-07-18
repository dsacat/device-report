from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_pyinstaller_spec_builds_named_console_exe_with_uac():
    spec = read("DeviceReport.spec")

    assert "name='DeviceReport'" in spec
    assert "console=True" in spec
    assert "uac_admin=True" in spec
    assert "upx=False" in spec
    assert "src/device_report/__main__.py" in spec.replace("\\", "/")


def test_linux_pyinstaller_spec_builds_named_console_binary_without_elevation():
    spec = read("DeviceReport-linux.spec")

    assert "name='DeviceReport-linux-x86_64'" in spec
    assert "console=True" in spec
    assert "uac_admin" not in spec
    assert "version='windows-version-info.txt'" not in spec
    assert "src/device_report/__main__.py" in spec.replace("\\", "/")


def test_pyinstaller_specs_extract_docx_parts_for_template_relative_paths():
    for name in ("DeviceReport.spec", "DeviceReport-linux.spec"):
        spec = read(name)
        assert "module_collection_mode={'docx.parts': 'pyc'}" in spec


def test_windows_version_resource_populates_standard_file_information():
    info = read("windows-version-info.txt")

    for key in (
        "CompanyName",
        "FileDescription",
        "FileVersion",
        "InternalName",
        "LegalCopyright",
        "LegalTrademarks",
        "OriginalFilename",
        "PrivateBuild",
        "ProductName",
        "ProductVersion",
        "SpecialBuild",
        "Comments",
    ):
        assert f"StringStruct('{key}'" in info


def test_pyinstaller_entrypoint_uses_package_safe_absolute_import():
    entrypoint = read("src/device_report/__main__.py")

    assert "from device_report.cli import main" in entrypoint
    assert "from .cli import main" not in entrypoint


def test_build_script_tests_and_verifies_single_executable():
    script = read("build.cmd").lower()

    assert "requirements-build.txt" in script
    assert "python -m pytest" in script
    assert "python -m pyinstaller devicereport.spec" in script
    assert "dist\\devicereport.exe" in script
    assert "exactly one file" in script


def test_workflow_builds_windows_and_linux_and_publishes_both_binaries():
    workflow = read(".github/workflows/build-windows.yml")

    assert "windows-latest" in workflow
    assert "ubuntu-22.04" in workflow
    assert "python -m pytest" in workflow
    assert "python -m PyInstaller DeviceReport.spec" in workflow
    assert "python -m PyInstaller DeviceReport-linux.spec" in workflow
    assert "dist/DeviceReport.exe" in workflow
    assert "dist/DeviceReport-linux-x86_64" in workflow
    assert "DeviceReport-windows-x64" in workflow
    assert "DeviceReport-linux-x86_64" in workflow
    assert "--lang en --section overview" in workflow
    assert "*.docx" in workflow
    assert "if-no-files-found: error" in workflow
    assert "1.0.0-dev" in workflow
    assert "contents: write" in workflow
    assert "git checkout -B release-output origin/1.0.0" in workflow
    assert "git add README.md LICENSE DeviceReport.exe" in workflow
    assert "DeviceReport-linux-x86_64" in workflow
    assert "HEAD:refs/heads/1.0.0" in workflow
    assert "--force" not in workflow
    assert "github.event_name == 'push'" in workflow
    assert "feature/identity-fix" in workflow


def test_readme_documents_both_platforms_language_modes_and_privacy():
    readme = read("README.md")

    assert "DeviceReport.exe --lang ru" in readme
    assert "DeviceReport.exe --lang en" in readme
    assert "standalone executable" in readme
    assert "Python is not required" in readme
    assert "IP addresses" in readme
    assert "serial numbers" in readme
    assert "DeviceReport-linux-x86_64" in readme
    assert "chmod +x" in readme


def test_license_allows_personal_use_and_forbids_commercial_use():
    license_text = read("LICENSE").lower()

    assert "personal and household use" in license_text
    assert "commercial use is prohibited" in license_text
    assert "not an open-source license" in license_text


def test_build_requirements_are_pinned():
    requirements = [
        line.strip()
        for line in read("requirements-build.txt").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    assert requirements
    assert all("==" in requirement for requirement in requirements)
