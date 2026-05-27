from app.api.v1.endpoints.quiz import _is_valid_reading_option


def test_reading_options_reject_latin_source_text():
    assert _is_valid_reading_option("むかう") is True
    assert _is_valid_reading_option("サイト") is True
    assert _is_valid_reading_option("site") is False
    assert _is_valid_reading_option("Christmas・Xmas") is False
    assert _is_valid_reading_option("(フ) kilomètre") is False
