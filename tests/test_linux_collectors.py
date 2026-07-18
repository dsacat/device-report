from unittest import TestCase

from device_report.linux_collectors import COLLECTOR_SPECS, collect_all, collect_overview


class FakeLinuxRunner:
    def __init__(self):
        self.reads = {
            "/sys/class/dmi/id/sys_vendor": "LENOVO",
            "/sys/class/dmi/id/product_name": "81W4",
            "/sys/class/dmi/id/product_family": "IdeaPad 3 15ARE05",
            "/sys/class/dmi/id/product_version": "IdeaPad 3 15ARE05",
            "/proc/meminfo": "MemTotal:       16384000 kB\nMemAvailable:    8192000 kB\n",
        }
        self.commands = []

    def read_optional(self, path):
        return self.reads.get(str(path))

    def exists(self, path):
        return False

    def glob(self, pattern):
        return []

    def available(self, command):
        return False


class LinuxCollectorTests(TestCase):
    def test_overview_collects_safe_cross_vendor_identity(self):
        section = collect_overview(FakeLinuxRunner(), "en")
        values = {field.key: field.value for field in section.fields}

        self.assertEqual(values["Manufacturer"], "LENOVO")
        self.assertEqual(values["Model"], "81W4")
        self.assertEqual(values["System family"], "IdeaPad 3 15ARE05")
        self.assertNotIn("Serial", repr(section))
        self.assertNotIn("UUID", repr(section))

    def test_selected_collection_never_calls_disabled_collectors(self):
        runner = FakeLinuxRunner()
        sections, diagnostics = collect_all(runner, "en", selected_keys=("overview",))

        self.assertEqual([section.key for section in sections], ["overview"])
        self.assertEqual(diagnostics, [])

    def test_linux_backend_exposes_same_fourteen_section_keys(self):
        self.assertEqual(len(COLLECTOR_SPECS), 14)
        self.assertEqual(COLLECTOR_SPECS[0].key, "overview")
        self.assertEqual(COLLECTOR_SPECS[-1].key, "software")
