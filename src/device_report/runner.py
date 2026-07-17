from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class CommandError(RuntimeError):
    pass


class CommandTimeout(CommandError):
    pass


@dataclass(frozen=True, slots=True)
class CommandResult:
    stdout: str
    returncode: int


class CommandRunner:
    def __init__(
        self,
        *,
        process: Callable[..., Any] = subprocess.run,
        timeout: int = 30,
        powershell: str = "powershell.exe",
    ) -> None:
        self._process = process
        self.timeout = timeout
        self.powershell = powershell

    def _invoke(self, args: list[str], *, timeout: int | None = None) -> CommandResult:
        try:
            completed = self._process(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout if timeout is None else timeout,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CommandTimeout("PowerShell command timed out") from exc
        except OSError as exc:
            raise CommandError("PowerShell is unavailable") from exc
        if completed.returncode != 0:
            raise CommandError("PowerShell command failed")
        return CommandResult(stdout=completed.stdout or "", returncode=completed.returncode)

    def powershell_json(self, script: str, *, timeout: int | None = None) -> list[dict[str, Any]]:
        wrapped = (
            "$ErrorActionPreference='Stop';"
            "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
            f"$result = @({script});"
            "$result | ConvertTo-Json -Depth 8 -Compress"
        )
        args = [
            self.powershell,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            wrapped,
        ]
        output = self._invoke(args, timeout=timeout).stdout.lstrip("\ufeff").strip()
        if not output:
            return []
        try:
            value = json.loads(output)
        except json.JSONDecodeError as exc:
            raise CommandError("PowerShell returned invalid JSON") from exc
        if value is None:
            return []
        if isinstance(value, dict):
            return [value]
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            return value
        raise CommandError("PowerShell returned an unexpected JSON value")
