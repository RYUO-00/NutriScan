"""Generate offline synthetic packaged-food labels and matching ground truth."""

import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config


WIDTH, HEIGHT = 1500, 1040
TEXT = [
    ("NUTRISCAN SAMPLE", 44, True),
    ("MASALA GRAIN CRUNCH", 42, True),
    ("Ingredients:", 28, True),
    ("Whole wheat flour, rice flour, sugar, palm oil,", 25, False),
    ("salt, spices, soy lecithin (322), sodium benzoate (E 211).", 25, False),
    ("Contains: Wheat, Soy, Milk, Peanut", 24, True),
    ("NUTRITION INFORMATION (per 100 g)", 27, True),
    ("Energy 425 kcal     Total Fat 17 g     Saturated Fat 5 g", 23, False),
    ("Trans Fat 0.1 g     Total Sugars 12 g     Sodium 580 mg", 23, False),
    ("Protein 7 g     Dietary Fibre 4 g", 23, False),
    ("Serving size 30 g     Best before: see pack", 19, False),
]
GROUND_TRUTH = {
    "ingredient_tokens": [
        "Whole wheat flour", "rice flour", "sugar", "palm oil", "salt", "spices",
        "soy lecithin (322)", "sodium benzoate (E 211)",
    ],
    "additive_codes": ["211", "322"],
    "allergen_groups": ["Wheat or Gluten", "Soy", "Milk", "Peanut"],
    "nutrients": {
        "energy": {"value": 425, "unit": "kcal", "basis": "100g"},
        "total_fat": {"value": 17, "unit": "g", "basis": "100g"},
        "saturated_fat": {"value": 5, "unit": "g", "basis": "100g"},
        "trans_fat": {"value": 0.1, "unit": "g", "basis": "100g"},
        "sugar": {"value": 12, "unit": "g", "basis": "100g"},
        "sodium": {"value": 580, "unit": "mg", "basis": "100g"},
        "protein": {"value": 7, "unit": "g", "basis": "100g"},
        "fibre": {"value": 4, "unit": "g", "basis": "100g"},
    },
}


def _font(size, bold=False):
    names = [
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in names:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _base_label(low_contrast=False):
    background = "#f4f1e9" if low_contrast else "#fffdf7"
    ink = "#777b78" if low_contrast else "#202a29"
    image = Image.new("RGB", (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((55, 50, WIDTH - 55, HEIGHT - 50), radius=18, outline="#6c766d", width=3)
    y = 95
    for text, size, bold in TEXT:
        color = ink if not (text.startswith("NUTRISCAN") and not low_contrast) else "#315f4d"
        draw.text((100, y), text, fill=color, font=_font(size, bold))
        y += size + (26 if size >= 27 else 20)
    draw.line((100, HEIGHT - 170, WIDTH - 100, HEIGHT - 170), fill="#b8beb8", width=2)
    draw.text((100, HEIGHT - 135), "Synthetic example for OCR testing · not a real product", fill=ink, font=_font(17))
    return image


def _variants():
    clear = _base_label()
    tilted = clear.rotate(4, expand=True, fillcolor="#e6e3db", resample=Image.Resampling.BICUBIC)

    noisy = clear.copy()
    array = np.asarray(noisy).astype(np.int16)
    rng = np.random.default_rng(2026)
    noise = rng.normal(0, 10, array.shape).astype(np.int16)
    noisy = Image.fromarray(np.clip(array + noise, 0, 255).astype(np.uint8))

    low_contrast = _base_label(low_contrast=True)
    low_contrast = ImageEnhance.Contrast(low_contrast).enhance(0.72)

    glare = clear.copy().convert("RGBA")
    overlay = Image.new("RGBA", glare.size, (255, 255, 255, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.ellipse((700, 80, 1450, 500), fill=(255, 255, 255, 155))
    overlay = overlay.filter(ImageFilter.GaussianBlur(45))
    glare = Image.alpha_composite(glare, overlay).convert("RGB")

    return {
        "clear_flat": clear,
        "slightly_tilted": tilted,
        "noisy": noisy,
        "low_contrast": low_contrast,
        "glare_like": glare,
    }


def main():
    config.SAMPLE_LABEL_DIR.mkdir(parents=True, exist_ok=True)
    config.GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    sample_dir = config.SAMPLE_LABEL_DIR
    for name, image in _variants().items():
        path = sample_dir / f"{name}.png"
        image.save(path, format="PNG", optimize=True)
        truth = {"image": path.name, **GROUND_TRUTH}
        (config.GROUND_TRUTH_DIR / f"{name}.json").write_text(
            json.dumps(truth, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    config.BASE_DIR.joinpath("static", "images").mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample_dir / "clear_flat.png", config.BASE_DIR / "static" / "images" / "sample_label.png")
    print("Created five synthetic label categories and matching ground-truth JSON; clear label copied to static/images/sample_label.png.")


if __name__ == "__main__":
    main()
