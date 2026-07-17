from __future__ import annotations

import ipaddress
import re
from collections.abc import Mapping
from typing import Any


_SENSITIVE_KEYS = {
    "account",
    "assettag",
    "biosserialnumber",
    "deviceserialnumber",
    "email",
    "hardwareuuid",
    "ipaddress",
    "ipv4address",
    "ipv6address",
    "machineguid",
    "macaddress",
    "productid",
    "productkey",
    "profilepath",
    "serial",
    "serialnumber",
    "sid",
    "ssid",
    "systemuuid",
    "user",
    "username",
    "uuid",
    "wifissid",
}

_WINDOWS_PROFILE = re.compile(r"(?i)(?:[a-z]:\\|/)(?:users|documents and settings)[\\/][^\\/]+")
_IPV4 = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
_MAC = re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])")
_EMAIL = re.compile(r"(?i)\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_IPV6_CANDIDATE = re.compile(
    r"(?i)(?<![0-9a-f:.%])(?:[0-9a-f]{0,4}:){2,}[0-9a-f:.%]*(?![0-9a-f:.%])"
)


def _normalize_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _is_sensitive_key(key: Any) -> bool:
    normalized = _normalize_key(key)
    return normalized in _SENSITIVE_KEYS or normalized.endswith("serialnumber")


def _is_sensitive_text(value: str) -> bool:
    if any(pattern.search(value) for pattern in (_WINDOWS_PROFILE, _IPV4, _MAC, _EMAIL)):
        return True
    for candidate in _IPV6_CANDIDATE.findall(value):
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if address.version == 6:
            return True
    return False


def _sanitize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return sanitize_mapping(value)
    if isinstance(value, list):
        return [cleaned for item in value if (cleaned := _sanitize(item)) is not None]
    if isinstance(value, tuple):
        return tuple(cleaned for item in value if (cleaned := _sanitize(item)) is not None)
    if isinstance(value, str) and _is_sensitive_text(value):
        return None
    return value


def sanitize_mapping(source: Mapping[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in source.items():
        if _is_sensitive_key(key):
            continue
        safe_value = _sanitize(value)
        if safe_value is not None:
            cleaned[str(key)] = safe_value
    return cleaned


def safe_error(error: BaseException) -> str:
    """Return a diagnostic label without exception data or command output."""
    return type(error).__name__
