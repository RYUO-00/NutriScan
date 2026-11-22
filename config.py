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
OCR_MAX_LONG_SIDE = 4500
OCR_TARGET_WORD_HEIGHT = 30
OCR_ILLUMINATION_SIGMA = 30
OCR_PSM = 6
OCR_RETRY_PSM = 11
OCR_WEAK_CHARACTERS = 30
OCR_MIN_CONFIDENCE = 45.0
# Numeric tokens need a stronger evidence gate than whole-page OCR. Tesseract
# confidence is only a heuristic, not a guarantee that decimals are correct.
OCR_MIN_NUMERIC_CONFIDENCE = 65.0
OCR_LAYOUT_PSM = 3
OCR_UPSCALE_LONG_SIDE = 2400
OCR_UPSCALE_MAX_SCALE = 3
OCR_PANEL_UPSCALE_LONG_SIDE = 3000
# Bounded grayscale rescue for incomplete panels; retain real pixels and units.
OCR_RESCUE_LONG_SIDE = 3000
OCR_RESCUE_PSMS = (6, 4)
OCR_RESCUE_BORDER = 20
OCR_TIMEOUT_SECONDS = 15

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
# Sources for the concentration bins are assigned below. The remaining legacy
# trans-fat bins and all composite point weights are project assumptions.
NUTRITION_THRESHOLDS = {
    "energy": {"unit": "kcal", "basis": "100g", "medium_above": 250, "high_above": 400},
    "total_fat": {"unit": "g", "basis": "100g", "medium_above": 3, "high_above": 17.5},
    "saturated_fat": {"unit": "g", "basis": "100g", "medium_above": 1.5, "high_above": 5},
    "trans_fat": {"unit": "g", "basis": "100g", "medium_above": 0.5, "high_above": 2},
    "sugar": {"unit": "g", "basis": "100g", "medium_above": 5, "high_above": 22.5},
    "sodium": {"unit": "mg", "basis": "100g", "medium_above": 120, "high_above": 600},
    "protein": {"unit": "g", "basis": "100g", "medium_above": 5, "high_above": 10},
    "fibre": {"unit": "g", "basis": "100g", "medium_above": 3, "high_above": 6},
    "salt": {"unit": "g", "basis": "100g", "medium_above": 0.3, "high_above": 1.5},
}

# UK front-of-pack guidance tables 2/3: concentration categories only. The
# composite 15/7 point mapping above remains an academic project heuristic.
UK_FOP_SOURCE = "UK Department of Health, Guide to creating a front of pack nutrition label (2016), tables 2 and 3: https://assets.publishing.service.gov.uk/media/5a80cd03ed915d74e33fc7c5/FoP_Nutrition_labelling_UK_guidance.pdf"
FDA_ADDED_SUGAR_SOURCE = "US FDA, Added Sugars on the Nutrition Facts Label: 50 g Daily Value, <=5% DV low and >=20% DV high per serving: https://www.fda.gov/food/nutrition-facts-label/added-sugars-nutrition-facts-label"
for nutrient_key in ("total_fat", "saturated_fat", "sugar", "salt", "sodium"):
    NUTRITION_THRESHOLDS[nutrient_key]["source"] = UK_FOP_SOURCE + ("; sodium cutoffs expressed from salt using salt = 2.5 x sodium." if nutrient_key == "sodium" else "")
NUTRITION_THRESHOLDS["trans_fat"]["source"] = "Project assumption - needs verification (legacy trans-fat concentration bins). WHO's <1% energy intake guidance is not a per-100-g cutoff: https://www.who.int/news-room/fact-sheets/detail/trans-fat"
LIQUID_NUTRITION_THRESHOLDS = {
    "total_fat": {"unit": "g", "basis": "100ml", "medium_above": 1.5, "high_above": 8.75, "source": UK_FOP_SOURCE},
    "saturated_fat": {"unit": "g", "basis": "100ml", "medium_above": 0.75, "high_above": 2.5, "source": UK_FOP_SOURCE},
    "sugar": {"unit": "g", "basis": "100ml", "medium_above": 2.5, "high_above": 11.25, "source": UK_FOP_SOURCE},
    "salt": {"unit": "g", "basis": "100ml", "medium_above": 0.3, "high_above": 0.75, "source": UK_FOP_SOURCE},
    "sodium": {"unit": "mg", "basis": "100ml", "medium_above": 120, "high_above": 300, "source": UK_FOP_SOURCE + "; sodium cutoffs expressed from salt using salt = 2.5 x sodium."},
}
ADDED_SUGAR_DAILY_VALUE_G = 50
ADDED_SUGAR_THRESHOLD = {"unit": "g", "basis": "per_serving", "medium_above": ADDED_SUGAR_DAILY_VALUE_G * 0.05, "high_above": ADDED_SUGAR_DAILY_VALUE_G * 0.20, "high_inclusive": True, "source": FDA_ADDED_SUGAR_SOURCE}
NUTRITION_THRESHOLDS["added_sugar"] = ADDED_SUGAR_THRESHOLD

# These label values are informational and never change the score. The energy
# cutoff remains a project assumption, so energy is shown only for context too.
INFORMATIONAL_NUTRIENTS = {"energy", "protein", "fibre", "potassium"}

# Project coverage policy, not a medical standard or score penalty. A partial
# label cannot earn a published 100 solely through absent deductions.
SCORE_CORE_NUTRIENTS = ("total_fat", "saturated_fat", "trans_fat", "sugar", "sodium")
SCORE_NUTRIENT_ALTERNATIVES = {"sodium": ("sodium", "salt")}
# Majority of the five core fields supports a neutral partial score. A verified
# adverse nutrition reading may also support a provisional score below 100.
# This is a coverage policy, not a new nutrient penalty or medical threshold.
SCORE_MIN_CORE_FIELDS = 3
SCORE_NON_ADDITIVE_GROUPS = (("sugar", "added_sugar"),)
SCORE_LIMITED_COVERAGE_PERCENT = 60
SCORE_LIMITED_BAND = "Moderate"
ANALYSIS_VERSION = 6
