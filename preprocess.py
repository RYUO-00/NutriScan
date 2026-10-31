"""OpenCV preprocessing with original-image retention and diagnostics."""

from pathlib import Path

import cv2
import numpy as np

import config


class PreprocessError(ValueError):
    """Raised when an image cannot safely be decoded or transformed."""


def _read_image(source):
    if isinstance(source, np.ndarray):
        image = source.copy()
    else:
        path = Path(source)
        try:
            raw = np.fromfile(path, dtype=np.uint8)
        except OSError as exc:
            raise PreprocessError("The uploaded image could not be read.") from exc
        image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if image is None or image.size == 0 or image.ndim not in (2, 3):
        raise PreprocessError("The uploaded file is not a readable image.")
    height, width = image.shape[:2]
    if width < 1 or height < 1 or width * height > config.MAX_IMAGE_PIXELS:
        raise PreprocessError("The image dimensions are not supported. Choose a smaller image.")
    if image.ndim == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image


def _order_quad(points):
    points = np.asarray(points, dtype="float32")
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).reshape(-1)
    return np.array([
        points[np.argmin(sums)],
        points[np.argmin(diffs)],
        points[np.argmax(sums)],
        points[np.argmax(diffs)],
    ], dtype="float32")


def _perspective_correct(gray):
    height, width = gray.shape[:2]
    edged = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 40, 130)
    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    min_area = width * height * config.PERSPECTIVE_MIN_AREA_RATIO
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:12]:
        if cv2.contourArea(contour) < min_area:
            continue
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(polygon) != 4 or not cv2.isContourConvex(polygon):
            continue
        quad = _order_quad(polygon.reshape(4, 2))
        edges = [np.linalg.norm(quad[(i + 1) % 4] - quad[i]) for i in range(4)]
        if min(edges) < min(width, height) * 0.12:
            continue
        angle_cosines = []
        for i in range(4):
            current = quad[i]
            before = quad[(i - 1) % 4] - current
            after = quad[(i + 1) % 4] - current
            denom = float(np.linalg.norm(before) * np.linalg.norm(after))
            angle_cosines.append(abs(float(np.dot(before, after)) / denom) if denom else 1.0)
        if max(angle_cosines) > config.PERSPECTIVE_MAX_ANGLE_COSINE:
            continue
        # Reject slivers and highly degenerate shapes; retain ordinary perspective.
        aspect = max(edges) / max(min(edges), 1.0)
        if aspect > 8:
            continue
        target_width = max(int((edges[0] + edges[2]) / 2), 1)
        target_height = max(int((edges[1] + edges[3]) / 2), 1)
        target = np.array([[0, 0], [target_width - 1, 0], [target_width - 1, target_height - 1], [0, target_height - 1]], dtype="float32")
        matrix = cv2.getPerspectiveTransform(quad, target)
        corrected = cv2.warpPerspective(gray, matrix, (target_width, target_height), borderMode=cv2.BORDER_REPLICATE)
        return corrected, True
    return gray, False


def preprocess_image(source, *, enabled=True, processed_path=None):
    """Return original/processed arrays, an optional saved PNG, and diagnostics."""
    image = _read_image(source)
    original_height, original_width = image.shape[:2]
    original_color = image if image.ndim == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    original_for_display = original_color.copy()
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    scale = min(1.0, config.PREPROCESS_LONG_SIDE / max(gray.shape))
    if scale < 1.0:
        size = (max(1, round(gray.shape[1] * scale)), max(1, round(gray.shape[0] * scale)))
        original_color = cv2.resize(original_color, size, interpolation=cv2.INTER_AREA)
        gray = cv2.resize(gray, size, interpolation=cv2.INTER_AREA)

    diagnostics = {
        "input_width": original_width,
        "input_height": original_height,
        "output_width": int(gray.shape[1]),
        "output_height": int(gray.shape[0]),
        "resized": scale < 1.0,
        "preprocessing_enabled": bool(enabled),
        "perspective_corrected": False,
        "steps": [],
    }
    if enabled:
        denoised = cv2.medianBlur(gray, config.PREPROCESS_DENOISE_KERNEL)
        clahe = cv2.createCLAHE(
            clipLimit=config.PREPROCESS_CLAHE_LIMIT,
            tileGridSize=(config.PREPROCESS_CLAHE_GRID, config.PREPROCESS_CLAHE_GRID),
        )
        enhanced = clahe.apply(denoised)
        try:
            enhanced, corrected = _perspective_correct(enhanced)
            diagnostics["perspective_corrected"] = corrected
        except cv2.error:
            # Perspective detection is optional; a failed transform must not stop a scan.
            diagnostics["perspective_corrected"] = False
            diagnostics["perspective_fallback"] = True
        block = config.PREPROCESS_ADAPTIVE_BLOCK
        if block % 2 == 0:
            block += 1
        try:
            processed = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                block, config.PREPROCESS_ADAPTIVE_C,
            )
        except cv2.error:
            # Tiny images cannot support the configured neighborhood; use a safe global threshold.
            _, processed = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            diagnostics["adaptive_threshold_fallback"] = True
        diagnostics["steps"] = ["grayscale", "resize", "median denoise", "CLAHE contrast", "adaptive threshold"]
        if diagnostics["perspective_corrected"]:
            diagnostics["steps"].insert(4, "perspective correction")
    else:
        processed = gray.copy()
        diagnostics["steps"] = ["grayscale", "resize"]

    if processed_path is not None:
        path = Path(processed_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        ok, encoded = cv2.imencode(".png", processed)
        if not ok:
            raise PreprocessError("The processed image could not be saved for comparison.")
        try:
            path.write_bytes(encoded.tobytes())
        except OSError as exc:
            raise PreprocessError("The processed image could not be saved for comparison.") from exc

    return {
        "original": original_for_display,
        "original_gray": gray.copy(),
        "processed": processed,
        "diagnostics": diagnostics,
    }
