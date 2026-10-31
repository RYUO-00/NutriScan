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
