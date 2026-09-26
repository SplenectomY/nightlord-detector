"""Layout math is kept free of Tk so tests can pin the bottom-center default."""

from nightlord_detector.config import OverlayLayout, compute_overlay_rect, compute_roi_rect


def test_default_layout_sits_on_bottom_center_1080p():
    x, y, width, height = compute_overlay_rect(1920, 1080, OverlayLayout())
    assert width == 720
    assert height == 64
    assert x == (1920 - 720) // 2
    assert y == 1080 - 64 - 8
    assert y > 900


def test_offset_and_margin_can_be_tuned():
    layout = OverlayLayout(x_offset=-40, margin_bottom=12, width=800, height=56)
    x, y, width, height = compute_overlay_rect(2560, 1440, layout)
    assert (x, y, width, height) == (840, 1372, 800, 56)


def test_layout_clamps_to_the_screen():
    layout = OverlayLayout(x_offset=5000, margin_bottom=0, width=400, height=80)
    x, y, width, height = compute_overlay_rect(1920, 1080, layout)
    assert x == 1920 - 400
    assert y == 1080 - 80


def test_default_roi_matches_capture_pixel_math():
    x, y, width, height = compute_roi_rect(1920, 1080, 0.28, 0.04, 0.44, 0.10)
    assert (x, y, width, height) == (537, 43, 844, 108)


def test_roi_clamps_when_the_box_runs_off_screen():
    x, y, width, height = compute_roi_rect(1920, 1080, 0.90, 0.95, 0.40, 0.20)
    assert x == int(1920 * 0.90)
    assert y == int(1080 * 0.95)
    assert x + width == 1920
    assert y + height == 1080
