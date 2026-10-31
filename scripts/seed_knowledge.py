"""Create the initial, reviewable JSON knowledge files.

This is a one-time seed utility. The application reads the JSON files only.
Identity labels are from Codex INS nomenclature; screening risk labels remain
explicit project assumptions and must be reviewed before academic submission.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config


ADDITIVES = """
100i|Curcumin
100ii|Turmeric
101ii|Riboflavin 5'-phosphate sodium
102|Tartrazine
104|Quinoline yellow
107|Yellow 2G
110|Sunset yellow FCF
120|Carmines
122|Azorubine (Carmoisine)
123|Amaranth
124|Ponceau 4R
127|Erythrosine
129|Allura red AC
131|Patent blue V
132|Indigotine (Indigo carmine)
133|Brilliant blue FCF
140|Chlorophylls
141i|Chlorophylls, copper complexes
141ii|Chlorophyllins, copper complexes, potassium and sodium salts
142|Green S
143|Fast green FCF
150a|Caramel I - plain caramel
150b|Caramel II - sulphite caramel
150c|Caramel III - ammonia caramel
150d|Caramel IV - sulphite ammonia caramel
151|Brilliant black (Black PN)
153|Vegetable carbon
155|Brown HT
160a|Carotenes
160ai|Carotenes, beta-, synthetic
160aii|Carotenes, beta-, vegetable
160aiii|Carotenes, beta-, Blakeslea trispora
160aiv|Beta-carotene-rich extract from Dunaliella salina
160bi|Annatto extracts, bixin-based
160bii|Annatto extracts, norbixin-based
160ci|Paprika oleoresin
160cii|Paprika extract
160di|Lycopene, synthetic
160dii|Lycopene, tomato
160e|Carotenal, beta-apo-8-
160f|Carotenoic acid, ethyl ester, beta-apo-8-
161bi|Lutein from Tagetes erecta
161bii|Tagetes extract
161hi|Zeaxanthin, synthetic
162|Beet red
163|Anthocyanins
170i|Calcium carbonate
200|Sorbic acid
201|Sodium sorbate
202|Potassium sorbate
203|Calcium sorbate
210|Benzoic acid
211|Sodium benzoate
212|Potassium benzoate
213|Calcium benzoate
220|Sulphur dioxide
221|Sodium sulfite
222|Sodium hydrogen sulfite
223|Sodium metabisulfite
224|Potassium metabisulfite
234|Nisin
235|Natamycin (Pimaricin)
242|Dimethyl dicarbonate
249|Potassium nitrite
250|Sodium nitrite
251|Sodium nitrate
252|Potassium nitrate
260|Acetic acid, glacial
261|Potassium acetates
262|Sodium acetates
263|Calcium acetate
270|Lactic acid
280|Propionic acid
281|Sodium propionate
282|Calcium propionate
283|Potassium propionate
290|Carbon dioxide
296|Malic acid
297|Fumaric acid
300|Ascorbic acid
301|Sodium ascorbate
302|Calcium ascorbate
304|Ascorbyl palmitate
306|Tocopherol-rich extract
307c|Tocopherol concentrate, mixed
310|Propyl gallate
311|Octyl gallate
312|Dodecyl gallate
315|Erythorbic acid
316|Sodium erythorbate
319|Tertiary butylhydroquinone (TBHQ)
320|Butylated hydroxyanisole (BHA)
321|Butylated hydroxytoluene (BHT)
322|Lecithins
325|Sodium lactate
326|Potassium lactate
327|Calcium lactate
330|Citric acid
331|Sodium citrates
332|Potassium citrates
333|Calcium citrates
334|Tartaric acid (L(+)-)
335|Sodium tartrates
336|Potassium tartrates
337|Sodium potassium tartrate
338|Phosphoric acid
339|Sodium phosphates
340|Potassium phosphates
341|Calcium phosphates
350|Sodium malates
351|Potassium malates
355|Adipic acid
380|Triammonium citrate
400|Alginic acid
401|Sodium alginate
402|Potassium alginate
403|Ammonium alginate
404|Calcium alginate
405|Propylene glycol alginate
406|Agar
407|Carrageenan
410|Locust bean gum
412|Guar gum
413|Tragacanth gum
414|Gum arabic (Acacia gum)
415|Xanthan gum
416|Karaya gum
418|Gellan gum
420|Sorbitol
421|Mannitol
422|Glycerol
440|Pectins
450i|Disodium diphosphate
450iii|Tetrasodium diphosphate
451i|Pentasodium triphosphate
452i|Sodium polyphosphates
460|Microcrystalline cellulose
461|Methyl cellulose
464|Hydroxypropyl methyl cellulose
466|Sodium carboxymethyl cellulose
470a|Salts of myristic, palmitic and stearic acids
471|Mono- and diglycerides of fatty acids
472a|Acetic and fatty acid esters of glycerol
472e|Diacetyl tartaric and fatty acid esters of glycerol (DATEM)
473|Sucrose esters of fatty acids
475|Polyglycerol esters of fatty acids
476|Polyglycerol polyricinoleate (PGPR)
481|Sodium stearoyl-2-lactylate
482|Calcium stearoyl-2-lactylate
491|Sorbitan monostearate
500|Sodium carbonates
501|Potassium carbonates
503|Ammonium carbonates
508|Potassium chloride
509|Calcium chloride
511|Magnesium chloride
514|Sodium sulfates
516|Calcium sulfate
524|Sodium hydroxide
525|Potassium hydroxide
526|Calcium hydroxide
529|Calcium oxide
551|Silicon dioxide (silica)
552|Calcium silicate
553|Magnesium silicates
554|Sodium aluminosilicate
575|Glucono delta-lactone
576|Sodium gluconate
578|Calcium gluconate
620|Glutamic acid
621|Monosodium glutamate
627|Disodium guanylate
631|Disodium inosinate
635|Disodium 5'-ribonucleotides
950|Acesulfame potassium
951|Aspartame
955|Sucralose
960|Steviol glycosides
965|Maltitol
968|Erythritol
""".strip().splitlines()


ALLERGENS = [
    ("Milk", "milk"), ("Milk", "milk powder"), ("Milk", "whey"),
    ("Milk", "casein"), ("Milk", "caseinate"), ("Milk", "lactose"),
    ("Milk", "milk solids"), ("Milk", "whey powder"),
    ("Wheat or Gluten", "wheat"), ("Wheat or Gluten", "wheat flour"),
    ("Wheat or Gluten", "atta"), ("Wheat or Gluten", "maida"),
    ("Wheat or Gluten", "semolina"), ("Wheat or Gluten", "durum wheat"),
    ("Wheat or Gluten", "barley"), ("Wheat or Gluten", "rye"),
    ("Wheat or Gluten", "oats"), ("Wheat or Gluten", "gluten"),
    ("Soy", "soy"), ("Soy", "soybean"), ("Soy", "soya"),
    ("Soy", "soy protein"), ("Soy", "soy lecithin"),
    ("Peanut", "peanut"), ("Peanut", "groundnut"),
    ("Tree nut", "almond"), ("Tree nut", "cashew"),
    ("Tree nut", "pistachio"), ("Tree nut", "walnut"),
    ("Tree nut", "hazelnut"), ("Tree nut", "pecan"),
    ("Tree nut", "brazil nut"), ("Tree nut", "macadamia"),
    ("Egg", "egg"), ("Egg", "egg white"), ("Egg", "egg yolk"),
    ("Fish", "fish"), ("Fish", "fish sauce"),
    ("Shellfish", "shrimp"), ("Shellfish", "prawn"),
    ("Shellfish", "crab"), ("Shellfish", "crustacean"),
    ("Sesame", "sesame"), ("Mustard", "mustard"),
    ("Sulphite", "sulphite"),
]


CAUTION_FLAGS = [
    "added sugar", "sugar", "glucose syrup", "glucose-fructose syrup",
    "maltodextrin", "invert syrup", "liquid glucose", "dextrose",
    "fructose syrup", "jaggery", "honey", "refined wheat flour", "maida",
    "rice flour", "starch", "modified starch", "potato starch", "palm oil",
    "palmolein", "coconut oil", "hydrogenated vegetable fat", "vanaspati",
    "edible vegetable oil", "refined palm oil", "refined soybean oil", "salt",
    "sodium chloride", "baking soda", "caramel syrup", "shortening", "butter",
    "cream", "cheese powder", "cheese seasoning", "flavour enhancer",
    "artificial flavour", "added colour", "preservatives", "monosodium glutamate",
    "phosphates",
]
CAUTION_REASONS = {
    "added sugar": "The label explicitly identifies added sugar; the nutrition panel gives the declared sugar values.",
    "sugar": "Sugar is listed as a direct ingredient, but the ingredient list does not state its exact amount.",
    "glucose syrup": "Glucose syrup is listed; its quantity is not given in the ingredient list.",
    "glucose-fructose syrup": "This syrup contains both glucose and fructose in its name; its quantity is not stated.",
    "maltodextrin": "Maltodextrin is listed as a starch-derived ingredient; its quantity is not stated.",
    "invert syrup": "Invert syrup is listed as a sugar syrup; the ingredient list does not give its quantity.",
    "liquid glucose": "Liquid glucose is listed; its quantity is not given in the ingredient list.",
    "dextrose": "Dextrose is listed as a named sugar; its quantity is not stated in the ingredient list.",
    "fructose syrup": "Fructose syrup is listed; its quantity is not given in the ingredient list.",
    "jaggery": "Jaggery is listed as a sweetening ingredient; its quantity is not stated.",
    "honey": "Honey is listed as a sweetening ingredient; its quantity is not stated.",
    "refined wheat flour": "Refined wheat flour is listed; ingredient order does not show its exact share of the product.",
    "maida": "Maida is a refined wheat flour named on the label; its exact share is not stated.",
    "rice flour": "Rice flour is listed; the ingredient list does not state its proportion in the product.",
    "starch": "Starch is listed without a source or quantity, so its type and share are unclear from this entry.",
    "modified starch": "Modified starch is listed, but this wording does not identify its source or quantity.",
    "potato starch": "Potato starch is listed; the ingredient list does not state its proportion.",
    "palm oil": "Palm oil is named on the label; the ingredient list does not state its amount.",
    "palmolein": "Palmolein is named on the label; the ingredient list does not state its amount.",
    "coconut oil": "Coconut oil is named on the label; the ingredient list does not state its amount.",
    "hydrogenated vegetable fat": "The label identifies hydrogenated vegetable fat but does not state its amount or hydrogenation level.",
    "vanaspati": "Vanaspati is named on the label; the ingredient list does not give its amount or composition.",
    "edible vegetable oil": "The label gives a general vegetable-oil term, so the specific oil is not identified here.",
    "refined palm oil": "Refined palm oil is named on the label; the ingredient list does not state its amount.",
    "refined soybean oil": "Refined soybean oil is named on the label; the ingredient list does not state its amount.",
    "salt": "Salt is listed; use a declared salt value on the nutrition panel to assess its quantity.",
    "sodium chloride": "Sodium chloride is the named salt ingredient; its amount is not stated in the ingredient list.",
    "baking soda": "Baking soda is listed as a leavening ingredient; its amount is not stated.",
    "caramel syrup": "Caramel syrup is listed, but this entry does not state its amount or role in the recipe.",
    "shortening": "Shortening is listed as a fat ingredient; its specific composition and amount are not stated.",
    "butter": "Butter is listed as an ingredient; its amount is not stated in the ingredient list.",
    "cream": "Cream is listed as an ingredient; its amount is not stated in the ingredient list.",
    "cheese powder": "Cheese powder is listed; its amount and contribution to the product are not stated.",
    "cheese seasoning": "Cheese seasoning is listed as a compound ingredient; its component amounts are not shown here.",
    "flavour enhancer": "The label uses a general flavour-enhancer term without naming the specific additive.",
    "artificial flavour": "The label identifies an artificial flavour but does not name the flavouring substance.",
    "added colour": "The label identifies an added colour without naming the colour or its code in this entry.",
    "preservatives": "The label uses a general preservative term, so the specific preservative is not identified here.",
    "monosodium glutamate": "Monosodium glutamate is named; the ingredient list does not state the amount used.",
    "phosphates": "The label uses the group term phosphates without identifying the specific phosphate additive.",
}
BENEFICIAL_FLAGS = [
    "whole wheat flour", "whole grain oats", "oats", "ragi", "finger millet",
    "whole millet", "jowar", "bajra", "brown rice", "brown rice flour",
    "chickpeas", "bengal gram", "lentils", "red lentils", "green gram", "peas",
    "roasted chana", "peanuts", "almonds", "cashew", "sesame seeds", "flaxseed",
    "chia seeds", "pumpkin seeds",
]
HARMFUL_FLAGS = ["partially hydrogenated vegetable oil"]


def write_json(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


CODEX_FUNCTIONAL_CLASSES = {
    "Colour": "100i 100ii 101ii 102 104 107 110 120 122 123 124 127 129 131 132 133 140 141i 141ii 142 143 150a 150b 150c 150d 151 153 155 160a 160ai 160aii 160aiii 160aiv 160bi 160bii 160ci 160cii 160di 160dii 160e 160f 161bi 161bii 161hi 162 163 170i",
    "Preservative": "200 201 202 203 210 211 212 213 220 221 222 223 224 234 235 242 249 250 251 252 280 281 282 283",
    "Acidity regulator": "260 261 262 263 270 296 297 325 326 327 330 331 332 333 334 335 336 337 338 339 340 341 350 351 355 380 500 501 503 524 525 526 529 575",
    "Antioxidant": "300 301 302 304 306 307c 310 311 312 315 316 319 320 321",
    "Emulsifier": "322 470a 471 472a 472e 473 475 476 481 482 491",
    "Carbonating agent": "290",
    "Gelling agent": "400 406 407 418 440",
    "Thickener": "401 402 403 405 410 412 413 414 415 416 461 464 466",
    "Firming agent": "404 508 509 511 516 578",
    "Sweetener": "420 421 950 951 955 960 965 968",
    "Humectant": "422",
    "Emulsifying salt": "450i 450iii 451i 452i",
    "Anticaking agent": "460 551 552 553 554",
    "Raising agent": "500 501 503",
    "Sequestrant": "576",
    "Flavour enhancer": "620 621 627 631 635",
}

ADDITIVE_CLASS_REVIEW = {
    "170i": "Codex lists several functional classes for calcium carbonate, so this dataset does not select a single one.",
    "338": "The Codex entry lists multiple functions for phosphoric acid; confirm the intended primary class for this record.",
    "339": "The sodium phosphate group has several Codex functional classes; confirm the intended primary class for this group record.",
    "340": "The potassium phosphate group has several Codex functional classes; confirm the intended primary class for this group record.",
    "341": "The calcium phosphate group has several Codex functional classes; confirm the intended primary class for this group record.",
    "450i": "Diphosphates have several Codex functional classes; confirm the intended primary class for this group record.",
    "450iii": "Diphosphates have several Codex functional classes; confirm the intended primary class for this group record.",
    "451i": "Triphosphates have several Codex functional classes; confirm the intended primary class for this group record.",
    "452i": "Polyphosphates have several Codex functional classes; confirm the intended primary class for this group record.",
    "516": "Codex lists multiple functional classes for calcium sulfate; confirm the intended primary class for this record.",
    "576": "Codex lists several functional classes for sodium gluconate; confirm the intended primary class for this record.",
}


def functional_class_for(code):
    """Return an explicit Codex class, or None when the group needs review."""
    if code in ADDITIVE_CLASS_REVIEW:
        return None
    for functional_class, codes in CODEX_FUNCTIONAL_CLASSES.items():
        if code in codes.split():
            return functional_class
    return None


ADDITIVE_SYNONYMS = {
    "322": ["soy lecithin", "soya lecithin"],
}


def build():
    additives = []
    for index, row in enumerate(ADDITIVES, 1):
        code, name = row.split("|", 1)
        functional_class = functional_class_for(code)
        review_reason = ADDITIVE_CLASS_REVIEW.get(code)
        if functional_class is None and review_reason is None:
            review_reason = "No confident code-specific functional class was assigned; verify against the Codex INS table."
        additives.append({
            "id": index,
            "ins_code": code,
            "name": name,
            "synonyms": ADDITIVE_SYNONYMS.get(code, []),
            "category": functional_class or "Class under review",
            "category_source": "Codex Alimentarius CXG 36-1989, functional class column.",
            "category_review_reason": review_reason,
            "risk_level": "low",
            "reason": "Identity screening only: a label code does not reveal the amount used or the food category. This provisional low screening label is not a toxicological assessment.",
            "source": (
                "Codex Alimentarius CXG 36-1989 (INS identity only); Project assumption - needs verification (risk label and synonym expansion)."
                if code in ADDITIVE_SYNONYMS
                else "Codex Alimentarius CXG 36-1989 (INS identity only); Project assumption - needs verification (risk label)."
            ),
        })

    allergen_source = "FSSAI Labelling and Display Regulations, 2020, regulation 5(14) for listed groups; Project assumption - needs verification (keyword expansion)."
    allergens = [
        {"id": i, "allergen_group": group, "keyword": keyword, "source": allergen_source}
        for i, (group, keyword) in enumerate(ALLERGENS, 1)
    ]

    flags = []
    for kind, words in (("harmful", HARMFUL_FLAGS), ("caution", CAUTION_FLAGS), ("beneficial", BENEFICIAL_FLAGS)):
        for keyword in words:
            if kind == "harmful":
                reason = "Screen for potentially industrial trans fat from partially hydrogenated oil; the image cannot confirm processing conditions or dose."
            elif kind == "beneficial":
                reason = "This ingredient can contribute whole grains, fibre, protein, or unsaturated fats; its quantity and the full product still matter."
            else:
                reason = CAUTION_REASONS[keyword]
            flags.append({
                "id": len(flags) + 1,
                "keyword": keyword,
                "flag_type": kind,
                "reason": reason,
                "source": "Project assumption - needs verification (screening keyword and flag).",
            })

    limits = []
    for key, values in config.NUTRITION_THRESHOLDS.items():
        limits.append({
            "nutrient": key,
            "unit": values["unit"],
            "per_basis": values["basis"],
            "config_key": key,
            "source": "Project assumption - needs verification (screening cutoff; numeric values are defined only in config.py).",
        })

    if set(CAUTION_REASONS) != set(CAUTION_FLAGS):
        raise SystemExit("Every caution flag must have one specific reason.")
    if len(additives) != 180 or len(allergens) != 45 or len(flags) != 65 or len(limits) != 10:
        raise SystemExit(f"Seed counts are {len(additives)}/{len(allergens)}/{len(flags)}/{len(limits)}; expected 180/45/65/10.")

    files = {
        "additives.json": additives,
        "allergens.json": allergens,
        "ingredient_flags.json": flags,
        "nutrition_limits.json": limits,
    }
    for filename, records in files.items():
        write_json(config.KNOWLEDGE_DIR / filename, records)

    assumptions = []
    for filename, records in files.items():
        for record in records:
            if "project assumption" in record["source"].lower():
                label = record.get("name") or record.get("keyword") or record["nutrient"]
                key = record.get("ins_code") or record.get("id")
                assumptions.append(f"- `{filename}` record {key} ({label}): {record['source']}")
    unclassified = [
        f"- INS {item['ins_code']} {item['name']}: {item['category_review_reason']}"
        for item in additives if item["category_review_reason"]
    ]
    review = [
        "# Data Review Queue",
        "",
        "Additive identity and functional-class sources are recorded in the JSON data. The provisional screening labels, keyword expansions, and nutrition cutoffs remain project assumptions and require review before academic submission.",
        "",
        "## Additive functional classes needing review",
        "",
        *(unclassified or ["No additive functional classes are awaiting review."]),
        "",
        "## Project-assumption records",
        "",
        f"Assumption records: {len(assumptions)} of 300.",
        "",
        *assumptions,
        "",
    ]
    (config.BASE_DIR / "DATA_REVIEW.md").write_text("\n".join(review), encoding="utf-8")
    print(f"Wrote {len(additives)} additives, {len(allergens)} allergen keywords, {len(flags)} ingredient flags, and {len(limits)} nutrition entries.")
    print(f"Review queue: {len(assumptions)} assumption records.")


if __name__ == "__main__":
    build()
