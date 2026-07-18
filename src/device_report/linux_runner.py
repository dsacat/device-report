from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from .runner import CommandError, CommandResult, CommandTimeout


class LinuxRunner:
    def __init__(
        self,
        *,
        process: Callable[..., Any] = subprocess.run,
        timeout: int = 30,
        root: str | Path = "/",
        which: Callable[[str], str | None] = shutil.which,
    ) -> None:
        self._process = process
        self.timeout = timeout
        self.root = Path(root)
        self._which = which

    def _path(self, path: str | Path) -> Path:
        source = Path(path)
        if self.root == Path("/"):
            return source
        return self.root / str(source).lstrip("/")

    def read_optional(self, path: str | Path, *, binary: bool = False) -> str | bytes | None:
        try:
            target = self._path(path)
            if binary:
                return target.read_bytes()
            return target.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            return None

    def exists(self, path: str | Path) -> bool:
        return self._path(path).exists()

    def readlink_optional(self, path: str | Path) -> str | None:
        try:
            return self._path(path).resolve(strict=True).name
        except OSError:
            return None

    def glob(self, pattern: str) -> list[Path]:
        target_pattern = str(self._path(pattern))
        import glob

        matches = [Path(item) for item in glob.glob(target_pattern)]
        if self.root == Path("/"):
            return matches
        return [Path("/") / item.relative_to(self.root) for item in matches]

    def available(self, command: str) -> bool:
        return self._which(command) is not None

    def command(
        self,
        args: Iterable[str],
        *,
        timeout: int | None = None,
        ok_codes: tuple[int, ...] = (0,),
    ) -> CommandResult:
        command = [str(item) for item in args]
        try:
            completed = self._process(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout if timeout is None else timeout,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CommandTimeout("Linux command timed out") from exc
        except OSError as exc:
            raise CommandError("Linux command is unavailable") from exc
        if completed.returncode not in ok_codes:
            raise CommandError("Linux command failed")
        return CommandResult(stdout=completed.stdout or "", returncode=completed.returncode)

    def command_json(self, args: Iterable[str], *, timeout: int | None = None) -> Any:
        output = self.command(args, timeout=timeout).stdout.strip()
        try:
            return json.loads(output) if output else {}
        except json.JSONDecodeError as exc:
            raise CommandError("Linux command returned invalid JSON") from exc
