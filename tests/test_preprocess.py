from preprocess import ocr_variant, deskew_for_ocr

import cv2
import numpy as np
import pytest

from preprocess import PreprocessError, preprocess_image


def test_preprocess_returns_binary_output_and_diagnostics(tmp_path):
    image = np.full((180, 420, 3), 245, dtype=np.uint8)
    cv2.putText(image, "Ingredients Wheat flour sugar", (12, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    path = tmp_path / "label.png"
    assert cv2.imwrite(str(path), image)
    result = preprocess_image(path, processed_path=tmp_path / "processed.png")
    assert result["processed"].ndim == 2
    assert set(np.unique(result["processed"])).issubset({0, 255})
    assert result["diagnostics"]["preprocessing_enabled"] is True
    assert (tmp_path / "processed.png").is_file()
    assert result["original"].shape[:2] == image.shape[:2]


def test_disabled_preprocessing_returns_grayscale_and_skips_perspective():
    image = np.full((80, 120, 3), 220, dtype=np.uint8)
    result = preprocess_image(image, enabled=False)
    assert result["processed"].ndim == 2
    assert result["diagnostics"]["perspective_corrected"] is False
    assert result["diagnostics"]["steps"] == ["grayscale", "resize"]


def test_adaptive_threshold_failure_uses_safe_fallback(monkeypatch):
    import preprocess

    def fail_threshold(*_args, **_kwargs):
        raise cv2.error("adaptive threshold unavailable")

    monkeypatch.setattr(preprocess.cv2, "adaptiveThreshold", fail_threshold)
    image = np.full((12, 12), 230, dtype=np.uint8)
    result = preprocess_image(image)
    assert result["processed"].shape == image.shape
    assert result["diagnostics"].get("adaptive_threshold_fallback") is True


def test_unreadable_image_has_friendly_error(tmp_path):
    path = tmp_path / "bad.png"
    path.write_bytes(b"not an image")
    with pytest.raises(PreprocessError, match="not a readable image"):
        preprocess_image(path)


@pytest.mark.parametrize("long_side, expected", [(3200, 3200), (5000, 4500)])
def test_ocr_resolution_is_independent_of_display_resize(long_side, expected):
    import config
    result = preprocess_image(np.full((200, long_side, 3), 220, dtype=np.uint8))
    assert max(result["original_gray"].shape) == expected
    assert max(result["processed"].shape) == config.PREPROCESS_LONG_SIDE
    assert max(result["display_gray"].shape) == config.PREPROCESS_LONG_SIDE
    assert result["diagnostics"]["ocr_width"] == expected


def test_requested_variants_preserve_input_and_geometry():
    image = np.full((120, 350), 190, dtype=np.uint8)
    cv2.putText(image, "Sugar 1.3g", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, 30, 1)
    before = image.copy()
    for name in ("gray", "contrast", "adaptive", "otsu"):
        output = ocr_variant(image, name)
        assert output.shape == image.shape
        assert np.array_equal(image, before)
        if name in {"adaptive", "otsu"}:
            assert set(np.unique(output)).issubset({0, 255})


def test_deskew_requires_consistent_lines():
    image = np.full((250, 400), 255, dtype=np.uint8)
    for y in [60, 100, 140, 180]:
        cv2.line(image, (30, y), (370, y + 30), 0, 2)
    corrected, angle = deskew_for_ocr(image)
    assert 3 < angle < 7
    assert corrected.shape == image.shape
    assert deskew_for_ocr(np.full_like(image, 255))[1] == 0
