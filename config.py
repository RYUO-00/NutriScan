"""Central configuration for NutriScan paths and screening rules."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
HISTORY_PATH = DATA_DIR / "scan_history.json"
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = UPLOAD_DIR / "processed"
GROUND_TRUTH_DIR = BASE_DIR / "tests" / "ground_truth"
SAMPLE_LABEL_DIR = BASE_DIR / "tests" / "sample_labels"
RESULTS_DIR = BASE_DIR / "results"

MAX_CONTENT_LENGTH = 5 * 1024 * 1024
MULTIPART_OVERHEAD = 64 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}
MAX_IMAGE_PIXELS = 40_000_000

TESSERACT_CMD = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSERACT_LANG = "eng"
OCR_PSM = 6
OCR_RETRY_PSM = 11
OCR_WEAK_CHARACTERS = 30
OCR_MIN_CONFIDENCE = 45.0

PREPROCESS_LONG_SIDE = 1800
PREPROCESS_DENOISE_KERNEL = 3
PREPROCESS_CLAHE_LIMIT = 2.0
PREPROCESS_CLAHE_GRID = 8
PREPROCESS_ADAPTIVE_BLOCK = 31
PREPROCESS_ADAPTIVE_C = 11

FUZZY_THRESHOLD = 85
PERSPECTIVE_MIN_AREA_RATIO = 0.18
PERSPECTIVE_MAX_ANGLE_COSINE = 0.35

# All scoring weights and caps live here. The score is an informational heuristic.
STARTING_SCORE = 100
ADDITIVE_DEDUCTIONS = {"high": 15, "moderate": 8, "low": 3}
ADDITIVE_DEDUCTION_CAP = 60
HARMFUL_FLAG_DEDUCTION = 10
HARMFUL_FLAG_DEDUCTION_CAP = 30
HIGH_NUTRIENT_DEDUCTION = 15
MEDIUM_NUTRIENT_DEDUCTION = 7
BENEFICIAL_FLAG_BONUS = 2
BENEFICIAL_FLAG_BONUS_CAP = 10
SCORE_BANDS = ((80, "Good"), (50, "Moderate"), (0, "Poor"))

# Evaluation tolerances for the deterministic synthetic fixture set.
EVALUATION_NUTRIENT_ABS_TOLERANCE = 0.1
EVALUATION_NUTRIENT_REL_TOLERANCE = 0.10

# JSON nutrition records identify nutrients and their source notes. Numeric
# screening cutoffs are deliberately defined only here, never duplicated in JSON.
# Values are draft project assumptions pending source review; they are not limits.
NUTRITION_THRESHOLDS = {
    "energy": {"unit": "kcal", "basis": "100g", "medium_above": 250, "high_above": 400},
    "total_fat": {"unit": "g", "basis": "100g", "medium_above": 3, "high_above": 17.5},
    "saturated_fat": {"unit": "g", "basis": "100g", "medium_above": 1.5, "high_above": 5},
    "trans_fat": {"unit": "g", "basis": "100g", "medium_above": 0.5, "high_above": 2},
    "sugar": {"unit": "g", "basis": "100g", "medium_above": 5, "high_above": 22.5},
    "sodium": {"unit": "mg", "basis": "100g", "medium_above": 120, "high_above": 600},
    "protein": {"unit": "g", "basis": "100g", "medium_above": 5, "high_above": 10},
    "fibre": {"unit": "g", "basis": "100g", "medium_above": 3, "high_above": 6},
    "added_sugar": {"unit": "g", "basis": "100g", "medium_above": 5, "high_above": 22.5},
    "salt": {"unit": "g", "basis": "100g", "medium_above": 0.3, "high_above": 1.5},
}

# These label values are informational and never change the score. The energy
# cutoff remains a project assumption, so energy is shown only for context too.
INFORMATIONAL_NUTRIENTS = {"energy", "protein", "fibre"}
