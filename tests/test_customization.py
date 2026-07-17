from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from device_report.cli import choose_sections, run_application
from device_report.collectors import COLLECTOR_SPECS, collect_all, collect_security, format_date_value
from device_report.error_log import write_error_log
from device_report.models import Diagnostic, Field, Section
from device_report.report import build_report_data


FIXED = datetime(2026, 7, 17, 18, 30, tzinfo=timezone.utc)


class DateFormattingTests(TestCase):
    def test_powershell_json_date_is_readable_in_both_languages(self):
        value = "/Date(1770135776000)/"
        local = datetime.fromtimestamp(1770135776)
        self.assertEqual(format_date_value(value, "en"), local.strftime("%Y-%m-%d %H:%M:%S"))
        self.assertEqual(format_date_value(value, "ru"), local.strftime("%d.%m.%Y %H:%M:%S"))

    def test_registry_date_is_date_only(self):
        self.assertEqual(format_date_value("20260717", "en"), "2026-07-17")
        self.assertEqual(format_date_value("20260717", "ru"), "17.07.2026")

    def test_malformed_date_stays_visible(self):
        self.assertEqual(format_date_value("unknown", "en"), "unknown")

    def test_defender_signature_date_is_normalized(self):
        class Runner:
            def powershell_json(self, script):
                return [{"Name": "Microsoft Defender", "Enabled": True, "AntivirusSignatureLastUpdated": "/Date(1770135776000)/"}]

        section = collect_security(Runner(), "en")
        self.assertIn("Signature updated", section.tables[0].headers)
        self.assertNotIn("/Date(", repr(section.tables[0].rows))


class SelectionTests(TestCase):
    def test_custom_selection_can_disable_updates(self):
        answers = iter(["2"] + ["2" if spec.key == "updates" else "1" for spec in COLLECTOR_SPECS])
        selected = choose_sections("en", input_fn=lambda _: next(answers), output_fn=lambda _: None)
        self.assertNotIn("updates", selected)
        self.assertIn("overview", selected)

    def test_filtered_collection_never_calls_disabled_collector(self):
        class Runner:
            def __init__(self): self.scripts = []
            def powershell_json(self, script):
                self.scripts.append(script)
                return []

        runner = Runner()
        sections, diagnostics = collect_all(runner, "en", selected_keys=("overview", "cpu"))
        self.assertEqual([section.key for section in sections], ["overview", "cpu"])
        self.assertEqual(len(runner.scripts), 2)
        self.assertEqual(diagnostics, [])


class IdentityTests(TestCase):
    def test_marketing_name_is_title_and_machine_type_is_subtitle(self):
        overview = Section("overview", "Device overview", fields=[
            Field("Manufacturer", "LENOVO"),
            Field("Model", "81W4"),
            Field("Marketing name", "IdeaPad 3 15ARE05"),
        ])
        report = build_report_data("en", [overview], [], now=FIXED)
        self.assertEqual(report.title, "IdeaPad 3 15ARE05")
        self.assertEqual(report.subtitle, "LENOVO 81W4")

    def test_cross_vendor_marketing_identity_uses_best_human_readable_name(self):
        overview = Section("overview", "Device overview", fields=[
            Field("Manufacturer", "Acer"),
            Field("Model", "N20C5"),
            Field("System family", "Aspire 5"),
            Field("Product name", "Aspire A515-57"),
            Field("Product version", "V1.0"),
        ])

        report = build_report_data("en", [overview], [], now=FIXED)

        self.assertEqual(report.title, "Aspire A515-57")
        self.assertEqual(report.subtitle, "Acer N20C5")

    def test_identity_is_collected_even_when_overview_is_not_selected(self):
        captured = []

        def collect_selected(runner, language, *, progress, selected_keys):
            return [Section("cpu", "Processor")], []

        def collect_identity(runner, language):
            return Section("overview", "Device overview", fields=[
                Field("Manufacturer", "Dell Inc."),
                Field("Model", "0ABC"),
                Field("Product name", "Latitude 7490"),
            ])

        def writer(report, path):
            captured.append(report)
            return path

        with TemporaryDirectory() as directory:
            result = run_application(
                "en",
                runner=object(),
                collect_fn=collect_selected,
                identity_fn=collect_identity,
                writer=writer,
                now=FIXED,
                cwd=directory,
                selected_keys=("cpu",),
                output_fn=lambda _: None,
            )

        self.assertEqual(result, 0)
        self.assertEqual(captured[0].title, "Latitude 7490")
        self.assertEqual(captured[0].subtitle, "Dell Inc. 0ABC")
        self.assertEqual([section.key for section in captured[0].sections], ["cpu"])

    def test_overview_query_uses_cross_vendor_safe_identity_fields(self):
        overview = next(spec for spec in COLLECTOR_SPECS if spec.key == "overview")
        for field in ("SystemFamily", "SystemProductName", "ProductVersion"):
            self.assertIn(field, overview.script)
        self.assertNotIn("UUID", overview.script)
        self.assertNotIn("Serial", overview.script)


class ErrorLogTests(TestCase):
    def test_no_diagnostics_create_no_logs_directory(self):
        with TemporaryDirectory() as directory:
            result = write_error_log(Path(directory), [], now=FIXED)
            self.assertIsNone(result)
            self.assertFalse((Path(directory) / "logs").exists())

    def test_errors_create_timestamped_sanitized_log(self):
        with TemporaryDirectory() as directory:
            result = write_error_log(
                Path(directory), [Diagnostic("updates", "PermissionError C:/Users/Alice")], now=FIXED
            )
            self.assertEqual(result.parent.name, "logs")
            self.assertEqual(result.name, "DeviceReport_errors_2026-07-17_18-30-00.log")
            content = result.read_text(encoding="utf-8")
            self.assertIn("updates: PermissionError", content)
            self.assertNotIn("Alice", content)


class PackagingTests(TestCase):
    def test_spec_has_no_pyinstaller_icon_and_uses_version_resource(self):
        root = Path(__file__).resolve().parents[1]
        spec = (root / "DeviceReport.spec").read_text(encoding="utf-8")
        self.assertIn("icon='NONE'", spec)
        self.assertIn("version='windows-version-info.txt'", spec)
        info = (root / "windows-version-info.txt").read_text(encoding="utf-8")
        for value in ("dsa_cat", "DeviceReport.exe", "1.0.0.0", "Personal and household use only"):
            self.assertIn(value, info)

    def test_release_fetch_populates_remote_tracking_ref(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/build-windows.yml").read_text(encoding="utf-8")
        self.assertIn("1.0.0:refs/remotes/origin/1.0.0", workflow)

    def test_release_removes_completed_service_branches(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/build-windows.yml").read_text(encoding="utf-8")
        self.assertIn("git push origin --delete feature/report-customization", workflow)
