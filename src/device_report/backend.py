from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class Backend:
    platform_label: str
    executable_name: str
    specs: tuple[Any, ...]
    collect_all: Callable[..., Any]
    collect_identity: Callable[[Any, str], Any]
    runner_factory: Callable[[], Any]


def resolve_backend(platform_name: str | None = None) -> Backend:
    selected = platform_name or sys.platform
    if selected == "win32" or selected.startswith("cygwin"):
        from .collectors import COLLECTOR_SPECS, collect_all, collect_overview
        from .runner import CommandRunner

        return Backend(
            platform_label="Windows x64",
            executable_name="DeviceReport.exe",
            specs=COLLECTOR_SPECS,
            collect_all=collect_all,
            collect_identity=collect_overview,
            runner_factory=CommandRunner,
        )
    if selected.startswith("linux"):
        from .linux_collectors import COLLECTOR_SPECS, collect_all, collect_overview
        from .linux_runner import LinuxRunner

        return Backend(
            platform_label="Linux x86_64",
            executable_name="DeviceReport-linux-x86_64",
            specs=COLLECTOR_SPECS,
            collect_all=collect_all,
            collect_identity=collect_overview,
            runner_factory=LinuxRunner,
        )
    raise RuntimeError(f"Unsupported platform: {selected}")
