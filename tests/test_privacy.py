import pytest

from device_report.privacy import safe_error, sanitize_mapping


@pytest.mark.parametrize(
    "key",
    [
        "SerialNumber",
        "UUID",
        "MACAddress",
        "IPAddress",
        "ProductKey",
        "UserName",
        "SID",
        "AssetTag",
    ],
)
def test_sensitive_keys_are_removed(key):
    assert sanitize_mapping({key: "secret", "Name": "GPU"}) == {"Name": "GPU"}


def test_sensitive_keys_are_removed_recursively_from_lists():
    source = {
        "Adapters": [
            {"Name": "Ethernet", "MACAddress": "AA:BB:CC:DD:EE:FF"},
            {"Name": "Wi-Fi", "IPAddress": ["192.0.2.10"]},
        ],
        "Model": "Example",
    }

    assert sanitize_mapping(source) == {
        "Adapters": [{"Name": "Ethernet"}, {"Name": "Wi-Fi"}],
        "Model": "Example",
    }


@pytest.mark.parametrize(
    "value",
    [
        r"C:\Users\Alice\AppData\Local\Vendor",
        "AA:BB:CC:DD:EE:FF",
        "192.168.1.44",
        "user@example.test",
    ],
)
def test_sensitive_free_text_values_are_omitted(value):
    assert sanitize_mapping({"Description": value, "Status": "OK"}) == {"Status": "OK"}


def test_safe_error_does_not_expose_command_or_path_details():
    error = RuntimeError(r"PowerShell failed for C:\Users\Alice with token abc123")

    assert safe_error(error) == "RuntimeError"


def test_time_and_version_text_are_not_mistaken_for_ipv6():
    source = {"InstalledOn": "2026-07-17 18:30:00", "Version": "1.2.3"}

    assert sanitize_mapping(source) == source


@pytest.mark.parametrize("value", ["2001:db8::1", "fe80::a1%12"])
def test_ipv6_values_are_removed(value):
    assert sanitize_mapping({"Description": value}) == {}
