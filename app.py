"""Thin Flask routes and request validation for NutriScan."""

from datetime import datetime
from io import BytesIO
from pathlib import Path
import time
import uuid
import warnings

from flask import Flask, abort, jsonify, render_template, request, send_from_directory
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

import config
from matcher import decode_additives, match_allergens, match_ingredient_tokens
from nutrition import parse_nutrition
from ocr import OCRNoTextError, OCRSetupError, recognize_text
from parser import parse_label_text
from preprocess import PreprocessError, preprocess_image
from scoring import calculate_health_score
from storage import StorageError, add_scan, get_history, get_scan_by_id, initialize_history, load_knowledge


class UploadValidationError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _human_datetime(value):
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value
    return parsed.strftime("%d %b %Y, %I:%M %p").replace(", 0", ", ")


def _wants_json():
    return request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json"


def _error_response(message, status):
    if _wants_json() or request.path.startswith("/api/"):
        return jsonify({"error": message}), status
    return render_template("error.html", message=message), status


def _validate_upload(file_storage):
    if file_storage is None or not file_storage.filename:
        raise UploadValidationError("Choose a JPG or PNG label photo before scanning.")
    original_name = secure_filename(Path(file_storage.filename).name) or "label-image"
    extension = Path(original_name).suffix.lower()
    if extension not in config.ALLOWED_EXTENSIONS:
        raise UploadValidationError("Unsupported file type. Upload a JPG or PNG image.")
    mime_type = (file_storage.mimetype or "").split(";", 1)[0].strip().lower()
    extension_mime = "image/png" if extension == ".png" else "image/jpeg"
    if mime_type != extension_mime or mime_type not in config.ALLOWED_MIME_TYPES:
        raise UploadValidationError("The file extension and image MIME type do not match. Choose a genuine JPG or PNG image.")
    content = file_storage.stream.read(config.MAX_CONTENT_LENGTH + 1)
    if not content:
        raise UploadValidationError("The selected image is empty. Choose a label photo with readable text.")
    if len(content) > config.MAX_CONTENT_LENGTH:
        raise UploadValidationError("The image is larger than the 5 MB upload limit.", 413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(BytesIO(content))
            actual_format = image.format
            width, height = image.size
            if width * height > config.MAX_IMAGE_PIXELS:
                raise UploadValidationError("The image dimensions are too large to process safely.")
            image.verify()
            image = Image.open(BytesIO(content))
            image.load()
    except UploadValidationError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise UploadValidationError("The uploaded file could not be decoded as a valid image.") from exc
    expected_format = "PNG" if extension == ".png" else "JPEG"
    if actual_format != expected_format:
        raise UploadValidationError("The file extension does not match the decoded image format.")
    return content, original_name, extension


def _merge_additive_matches(code_matches, name_matches):
    merged = {item["ins_code"]: dict(item) for item in code_matches}
    for item in name_matches:
        code = item["ins_code"]
        if code in merged:
            merged[code].setdefault("matched_tokens", []).append(item["matched_token"])
            merged[code].setdefault("match_types", []).append(item["match_type"])
        else:
            merged[code] = {
                **item,
                "matched_code": None,
                "source_spans": [],
                "matched_tokens": [item["matched_token"]],
                "match_types": [item["match_type"]],
            }
    return list(merged.values())


def _asset_reference(path):
    return "uploads/" + Path(path).relative_to(config.UPLOAD_DIR).as_posix()


def _source_strings(additives, ingredient_flags, allergen_alerts, nutrients):
    sources = []
    for finding in additives:
        sources.extend((finding.get("source"), finding.get("category_source")))
    for finding in ingredient_flags:
        sources.append(finding.get("source"))
    for alert in allergen_alerts:
        sources.extend(alert.get("sources", []))
    for nutrient in nutrients:
        sources.append(nutrient.get("threshold_source"))
    return list(dict.fromkeys(source for source in sources if isinstance(source, str) and source.strip()))


def _highlight_findings(additives, ingredient_flags, allergen_alerts, unknown_codes):
    return {
        "additives": [
            {key: item.get(key) for key in ("name", "ins_code", "matched_code", "matched_tokens") if item.get(key) is not None}
            for item in additives
        ],
        "flags": [{"keyword": item["keyword"]} for item in ingredient_flags],
        "allergens": [{"matched_keywords": item["matched_keywords"]} for item in allergen_alerts],
        "unknown_codes": [{"code": item["code"]} for item in unknown_codes],
    }


def _run_pipeline(upload_path, processed_path, image_name, scan_id, selected_allergens, knowledge):
    started = time.perf_counter()
    prepared = preprocess_image(upload_path, processed_path=processed_path)
    ocr_result = recognize_text(prepared["processed"], prepared["original_gray"])
    parsed = parse_label_text(ocr_result["text"])
    named_additives, ingredient_flags, unrecognised_tokens = match_ingredient_tokens(
        parsed["ingredient_tokens"], knowledge["additives"], knowledge["ingredient_flags"]
    )
    coded_additives, unknown_codes = decode_additives(parsed["raw_text"], knowledge["additives"])
    additives = _merge_additive_matches(coded_additives, named_additives)
    allergens = match_allergens(
        parsed["ingredient_text"], parsed["contains_text"], knowledge["allergens"], selected_allergens
    )
    nutrients = parse_nutrition(parsed["nutrition_text"], knowledge["nutrition_limits"])
    score = calculate_health_score(additives, ingredient_flags, nutrients)
    diagnostics = {
        **prepared["diagnostics"],
        "ocr": {
            "mean_confidence": ocr_result["mean_confidence"],
            "retried": ocr_result["retried"],
            "attempt_count": ocr_result["attempt_count"],
            "psm": ocr_result["psm"],
            "used_original": ocr_result["used_original"],
            "attempts": ocr_result["attempts"],
        },
        "processing_seconds": round(time.perf_counter() - started, 3),
    }
    result = {
        "scan_id": scan_id,
        "scanned_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "image_name": image_name,
        "image_path": _asset_reference(upload_path),
        "processed_image_path": _asset_reference(processed_path),
        "user_allergens": selected_allergens,
        "raw_text": parsed["raw_text"],
        "normalized_text": parsed["normalized_text"],
        "ingredient_tokens": parsed["ingredient_tokens"],
        "ingredient_text": parsed["ingredient_text"],
        "contains_text": parsed["contains_text"],
        "nutrition_text": parsed["nutrition_text"],
        "additives": additives,
        "unknown_additive_codes": unknown_codes,
        "ingredient_flags": ingredient_flags,
        "allergen_alerts": allergens,
        "nutrients": nutrients,
        "sources": _source_strings(additives, ingredient_flags, allergens, nutrients),
        "highlight_findings": _highlight_findings(additives, ingredient_flags, allergens, unknown_codes),
        "health_score": score["health_score"],
        "starting_score": config.STARTING_SCORE,
        "score_band": score["score_band"],
        "score_breakdown": score["score_breakdown"],
        "score_totals": score["totals"],
        "unrecognised_tokens": unrecognised_tokens,
        "diagnostics": diagnostics,
        "disclaimer": "Informational screening only. Not medical advice and not a guarantee of food safety.",
    }
    return result


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        MAX_CONTENT_LENGTH=config.MAX_CONTENT_LENGTH + config.MULTIPART_OVERHEAD,
        JSON_SORT_KEYS=False,
    )
    if test_config:
        app.config.update(test_config)
    app.jinja_env.filters["human_datetime"] = _human_datetime
    app.config["KNOWLEDGE"] = load_knowledge()
    initialize_history()
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/scan")
    def scan():
        upload_path = processed_path = None
        scan_id = None
        try:
            content, image_name, extension = _validate_upload(request.files.get("image"))
            scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            selected = list(dict.fromkeys(request.form.getlist("user_allergens")))
            allowed_groups = {item["allergen_group"] for item in app.config["KNOWLEDGE"]["allergens"]}
            selected_allergens = [group for group in selected if group in allowed_groups]
            upload_path = config.UPLOAD_DIR / f"{scan_id}{extension}"
            processed_path = config.PROCESSED_DIR / f"{scan_id}_processed.png"
            upload_path.write_bytes(content)
            result = _run_pipeline(
                upload_path, processed_path, image_name, scan_id,
                selected_allergens, app.config["KNOWLEDGE"],
            )
            add_scan(result)
            if _wants_json():
                return jsonify(result), 200
            return render_template("result.html", result=result), 200
        except UploadValidationError as exc:
            return _error_response(str(exc), exc.status)
        except OCRSetupError as exc:
            _remove_files(upload_path, processed_path)
            return _error_response(str(exc), 503)
        except OCRNoTextError as exc:
            _remove_files(upload_path, processed_path)
            return _error_response(str(exc), 422)
        except PreprocessError as exc:
            _remove_files(upload_path, processed_path)
            return _error_response(str(exc), 422)
        except StorageError as exc:
            _remove_files(upload_path, processed_path)
            return _error_response(str(exc), 500)
        except OSError:
            _remove_files(upload_path, processed_path)
            return _error_response("The image could not be stored locally. Check the NutriScan uploads folder permissions.", 500)
        except Exception:
            _remove_files(upload_path, processed_path)
            app.logger.exception("Unexpected failure while processing scan %s", scan_id or "before-id")
            return _error_response("NutriScan could not complete this scan. Try another clear JPG or PNG label.", 500)

    @app.get("/history")
    def history_page():
        scan_id = request.args.get("scan_id")
        try:
            if scan_id:
                result = get_scan_by_id(scan_id)
                if result is None:
                    return render_template("error.html", message="That saved scan was not found."), 404
                return render_template("result.html", result=result)
            scans = sorted(get_history(), key=lambda item: item.get("scanned_at", ""), reverse=True)
            return render_template("history.html", scans=scans)
        except StorageError as exc:
            return render_template("error.html", message=str(exc)), 500

    @app.get("/uploads/<path:filename>")
    def uploaded_media(filename):
        return send_from_directory(config.UPLOAD_DIR, filename, conditional=True)

    @app.get("/api/history")
    def history_api():
        try:
            scans = sorted(get_history(), key=lambda item: item.get("scanned_at", ""), reverse=True)
        except StorageError as exc:
            return jsonify({"error": str(exc)}), 500
        return jsonify([
            {key: item.get(key) for key in ("scan_id", "scanned_at", "image_name", "health_score", "score_band")}
            for item in scans
        ])

    @app.get("/api/history/<scan_id>")
    def scan_api(scan_id):
        try:
            result = get_scan_by_id(scan_id)
        except StorageError as exc:
            return jsonify({"error": str(exc)}), 500
        if result is None:
            abort(404)
        return jsonify(result)

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "The requested scan was not found."}), 404
        return render_template("error.html", message="That page was not found."), 404

    @app.errorhandler(413)
    def too_large(_error):
        return _error_response("The request is larger than the 5 MB image upload limit.", 413)

    return app


def _remove_files(*paths):
    for path in paths:
        if path is not None:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass


try:
    app = create_app()
except StorageError as exc:
    raise SystemExit(f"NutriScan startup failed: {exc}") from None


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
