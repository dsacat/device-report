from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase

from device_report.backend import resolve_backend
from device_report.cli import build_parser


class BackendTests(TestCase):
    def test_resolves_windows_and_linux_backends_with_matching_section_keys(self):
        windows = resolve_backend("win32")
        linux = resolve_backend("linux")

        self.assertEqual(windows.platform_label, "Windows x64")
        self.assertEqual(linux.platform_label, "Linux x86_64")
        self.assertEqual(
            [spec.key for spec in windows.specs],
            [spec.key for spec in linux.specs],
        )

    def test_rejects_unsupported_platform(self):
        with self.assertRaisesRegex(RuntimeError, "Unsupported platform"):
            resolve_backend("darwin")

    def test_version_output_contains_product_author_license_and_platform(self):
        output = StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as caught:
            build_parser(resolve_backend("linux")).parse_args(["--version"])

        self.assertEqual(caught.exception.code, 0)
        for value in ("DeviceReport 1.0.0", "dsa_cat", "personal and household", "Linux x86_64"):
            self.assertIn(value, output.getvalue())
