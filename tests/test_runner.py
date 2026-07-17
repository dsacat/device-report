import subprocess
from types import SimpleNamespace

import pytest

from device_report.runner import CommandError, CommandRunner, CommandTimeout


def completed(*, stdout="", stderr="", returncode=0):
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


def test_json_object_is_normalized_to_list():
    calls = []

    def process(args, **kwargs):
        calls.append((args, kwargs))
        return completed(stdout='{"Name":"CPU"}')

    runner = CommandRunner(process=process)

    assert runner.powershell_json("Get-CimInstance X") == [{"Name": "CPU"}]
    args, kwargs = calls[0]
    assert args[0].lower().endswith("powershell.exe")
    assert "-NoProfile" in args
    assert "ConvertTo-Json" in args[-1]
    assert kwargs["timeout"] == 30
    assert kwargs["shell"] is False


def test_json_array_and_empty_output_are_supported():
    outputs = iter(['[{"Name":"A"},{"Name":"B"}]', ""])
    runner = CommandRunner(process=lambda *args, **kwargs: completed(stdout=next(outputs)))

    assert runner.powershell_json("query") == [{"Name": "A"}, {"Name": "B"}]
    assert runner.powershell_json("query") == []


def test_nonzero_exit_raises_generic_command_error():
    runner = CommandRunner(
        process=lambda *args, **kwargs: completed(
            returncode=1,
            stderr=r"Access denied for C:\Users\Alice",
        )
    )

    with pytest.raises(CommandError, match="PowerShell command failed") as caught:
        runner.powershell_json("query")

    assert "Alice" not in str(caught.value)


def test_timeout_is_wrapped_without_command_text():
    def process(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="secret command", timeout=2)

    runner = CommandRunner(process=process, timeout=2)

    with pytest.raises(CommandTimeout, match="timed out") as caught:
        runner.powershell_json("query")

    assert "secret" not in str(caught.value)


def test_invalid_json_raises_command_error():
    runner = CommandRunner(process=lambda *args, **kwargs: completed(stdout="not-json"))

    with pytest.raises(CommandError, match="invalid JSON"):
        runner.powershell_json("query")
