import pytest

from device_report.cli import build_parser, choose_language


def test_menu_accepts_one_for_russian():
    assert choose_language(input_fn=lambda _: "1", output_fn=lambda _: None) == "ru"


def test_menu_accepts_two_for_english():
    assert choose_language(input_fn=lambda _: "2", output_fn=lambda _: None) == "en"


def test_menu_repeats_after_invalid_value():
    answers = iter(["x", "", "2"])
    output = []

    language = choose_language(input_fn=lambda _: next(answers), output_fn=output.append)

    assert language == "en"
    assert output.count("Введите 1 или 2 / Enter 1 or 2.") == 2


@pytest.mark.parametrize("language", ["ru", "en"])
def test_parser_accepts_supported_language(language):
    args = build_parser().parse_args(["--lang", language])
    assert args.lang == language


def test_parser_rejects_unknown_language():
    with pytest.raises(SystemExit) as caught:
        build_parser().parse_args(["--lang", "de"])
    assert caught.value.code == 2
