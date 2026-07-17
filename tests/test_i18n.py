import pytest

from device_report.i18n import normalize_language, translate


@pytest.mark.parametrize(("raw", "expected"), [("ru", "ru"), ("RU", "ru"), ("en", "en"), ("EN", "en")])
def test_normalize_language(raw, expected):
    assert normalize_language(raw) == expected


def test_normalize_language_rejects_unknown_value():
    with pytest.raises(ValueError, match="language"):
        normalize_language("de")


def test_translate_returns_localized_progress_text():
    assert translate("ru", "collecting", section="Процессор") == "Сбор: Процессор"
    assert translate("en", "collecting", section="CPU") == "Collecting: CPU"


def test_missing_translation_key_falls_back_to_key():
    assert translate("en", "unknown_key") == "unknown_key"

