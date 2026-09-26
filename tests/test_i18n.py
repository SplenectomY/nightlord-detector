from nightlord_detector.i18n import lord_name, set_locale, t
from nightlord_detector.predict import format_overlay, predict


def test_japanese_overlay_header():
    set_locale("ja")
    try:
        text = format_overlay(predict(None, None, "any"))
        assert "ナイト1" in text or "予想" in text
        assert t("app.language") == "言語"
        assert "グラディウス" in lord_name("gladius", "Gladius")
    finally:
        set_locale("en")


def test_english_fallback_after_japanese():
    set_locale("ja")
    set_locale("en")
    text = format_overlay(predict(None, None, "any"))
    assert "Possible Nightlords" in text
