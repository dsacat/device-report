import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase

from device_report.linux_runner import LinuxRunner
from device_report.runner import CommandTimeout


class LinuxRunnerTests(TestCase):
    def test_reads_from_injected_root_and_parses_json_command(self):
        calls = []

        def process(args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout=json.dumps({"items": [1]}), stderr="")

        with TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "proc" / "example"
            target.parent.mkdir(parents=True)
            target.write_text("safe\n", encoding="utf-8")
            runner = LinuxRunner(root=root, process=process)

            self.assertEqual(runner.read_optional("/proc/example"), "safe")
            self.assertEqual(runner.command_json(["tool", "--json"]), {"items": [1]})

        self.assertEqual(calls[0][0], ["tool", "--json"])
        self.assertFalse(calls[0][1]["shell"])

    def test_converts_process_timeout_to_sanitized_timeout(self):
        def process(args, **kwargs):
            raise subprocess.TimeoutExpired(args, kwargs["timeout"])

        with self.assertRaises(CommandTimeout):
            LinuxRunner(process=process).command(["slow-command"])
