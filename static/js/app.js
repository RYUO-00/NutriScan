(() => {
  const groups = ["Milk", "Wheat or Gluten", "Soy", "Peanut", "Tree nut", "Egg", "Fish", "Shellfish", "Sesame", "Mustard", "Sulphite"];
  const holder = document.querySelector("#allergen-chips");
  const form = document.querySelector("#scan-form");
  const fileInput = document.querySelector("#label-image");
  const preview = document.querySelector("#preview");
  const previewWrap = document.querySelector("#preview-wrap");

  if (holder) {
    let saved = [];
    try { saved = JSON.parse(localStorage.getItem("nutriscan-allergens") || "[]"); } catch { saved = []; }
    for (const group of groups) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "chip";
      button.textContent = group;
      button.setAttribute("aria-pressed", String(saved.includes(group)));
      button.addEventListener("click", () => {
        const active = button.getAttribute("aria-pressed") === "true";
        button.setAttribute("aria-pressed", String(!active));
        saved = [...holder.querySelectorAll('[aria-pressed="true"]')].map(item => item.textContent);
        localStorage.setItem("nutriscan-allergens", JSON.stringify(saved));
      });
      holder.append(button);
    }
  }

  const showPreview = file => {
    if (!file || !preview || !previewWrap) return;
    if (preview.dataset.objectUrl) URL.revokeObjectURL(preview.dataset.objectUrl);
    const objectUrl = URL.createObjectURL(file);
    preview.dataset.objectUrl = objectUrl;
    preview.src = objectUrl;
    previewWrap.hidden = false;
    document.querySelector("#preview-name").textContent = file.name;
    dropzone?.classList.add("has-file");
  };
  fileInput?.addEventListener("change", () => {
    if (fileInput.files?.[0]) showPreview(fileInput.files[0]);
    else dropzone?.classList.remove("has-file");
  });

  const dropzone = document.querySelector(".dropzone");
  dropzone?.addEventListener("dragover", event => { event.preventDefault(); dropzone.classList.add("dragging"); });
  dropzone?.addEventListener("dragleave", () => dropzone.classList.remove("dragging"));
  dropzone?.addEventListener("drop", event => {
    event.preventDefault();
    dropzone.classList.remove("dragging");
    const file = event.dataTransfer?.files?.[0];
    if (!file || !fileInput) return;
    const transfer = new DataTransfer();
    transfer.items.add(file);
    fileInput.files = transfer.files;
    showPreview(file);
  });

  const startScan = async () => {
    if (!form || !fileInput?.files?.length) {
      document.querySelector("#scan-status").textContent = "Choose a label photo before scanning.";
      fileInput?.focus();
      return;
    }
    const status = document.querySelector("#scan-status");
    const progress = document.querySelector("#scan-progress");
    const steps = progress ? [...progress.children] : [];
    const stageSteps = {
      uploading: [0, "Checking the image…"],
      preprocessing: [1, "Preparing the image…"],
      reading_text: [2, "Reading label text…"],
      decoding: [3, "Matching ingredients and allergens…"],
      nutrition: [4, "Reading nutrition values…"],
      scoring: [5, "Calculating the screening score…"],
      saving: [6, "Saving the result…"],
    };
    const data = new FormData(form);
    const progressId = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    data.append("progress_id", progressId);
    try {
      const selected = [...(holder?.querySelectorAll('[aria-pressed="true"]') || [])].map(button => button.textContent);
      selected.forEach(group => data.append("user_allergens", group));
    } catch { /* Allergen preferences are optional. */ }
    if (progress) progress.hidden = false;
    const updateStage = stage => {
      if (stage === "complete") {
        status.textContent = "Scan complete. Opening the saved result…";
        steps.forEach(item => { item.classList.remove("active"); item.classList.add("complete"); });
        return;
      }
      const stageInfo = stageSteps[stage];
      if (!stageInfo) return;
      const [index, label] = stageInfo;
      status.textContent = label;
      steps.forEach((item, i) => {
        item.classList.toggle("active", i === index);
        item.classList.toggle("complete", i < index);
      });
    };
    let requestFinished = false;
    const pause = milliseconds => new Promise(resolve => window.setTimeout(resolve, milliseconds));
    const progressPoller = (async () => {
      while (!requestFinished) {
        try {
          const response = await fetch(`/api/scan-progress/${encodeURIComponent(progressId)}`, { headers: { "Accept": "application/json" } });
          if (response.ok) updateStage((await response.json()).stage);
        } catch { /* The scan request will report a readable error if it fails. */ }
        if (!requestFinished) await pause(250);
      }
    })();
    form.querySelectorAll("button").forEach(button => { button.disabled = true; });
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: data,
        headers: { "Accept": "application/json", "X-Requested-With": "XMLHttpRequest" },
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "NutriScan could not complete this scan.");
      updateStage("complete");
      window.location.assign(`/history?scan_id=${encodeURIComponent(payload.scan_id)}`);
    } catch (error) {
      if (progress) progress.hidden = true;
      status.textContent = error instanceof Error ? error.message : "NutriScan could not complete this scan. Try another photo.";
      form.querySelectorAll("button").forEach(button => { button.disabled = false; });
    } finally {
      requestFinished = true;
      await progressPoller;
    }
  };

  form?.addEventListener("submit", event => { event.preventDefault(); startScan(); });

  document.querySelector("#sample-button")?.addEventListener("click", async () => {
    const button = document.querySelector("#sample-button");
    const status = document.querySelector("#scan-status");
    try {
      button.disabled = true;
      const response = await fetch("/static/images/sample_label.png");
      if (!response.ok) throw new Error("The bundled sample label could not be loaded.");
      const sample = new File([await response.blob()], "nutriscan-sample.png", { type: "image/png" });
      const transfer = new DataTransfer();
      transfer.items.add(sample);
      fileInput.files = transfer.files;
      showPreview(sample);
      status.textContent = "Bundled sample label selected. Starting the scan…";
      form.requestSubmit();
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : "The bundled sample label could not be loaded.";
      button.disabled = false;
    }
  });

  const slider = document.querySelector("#comparison-slider");
  const comparison = document.querySelector(".comparison");
  slider?.addEventListener("input", () => comparison?.style.setProperty("--split", `${slider.value}%`));

  const raw = document.querySelector("#raw-ocr");
  const findingsNode = document.querySelector("#detected-findings");
  if (raw && findingsNode) {
    try {
      const findings = JSON.parse(findingsNode.textContent || "{}");
      const descriptors = [
        ...(findings.additives || []).map((item, index) => ({ key: `additive-${index}`, terms: [item.name, item.ins_code, item.matched_code, ...(item.matched_tokens || [])] })),
        ...(findings.flags || []).map((item, index) => ({ key: `flag-${index}`, terms: [item.keyword] })),
        ...(findings.allergens || []).map((item, index) => ({ key: `allergen-${index}`, terms: [item.allergen_group, ...(item.matched_keywords || [])] })),
        ...(findings.unknown_codes || []).map((item, index) => ({ key: `unknown-${index}`, terms: [item.code, item.label] })),
      ];
      const termKeys = new Map();
      for (const descriptor of descriptors) {
        for (const term of descriptor.terms.filter(value => typeof value === "string" && value.trim().length > 1)) {
          const normalized = term.trim().toLowerCase();
          if (!termKeys.has(normalized)) termKeys.set(normalized, new Set());
          termKeys.get(normalized).add(descriptor.key);
        }
      }
      const terms = [...termKeys.keys()].sort((a, b) => b.length - a.length);
      const source = raw.textContent || "";
      const lower = source.toLowerCase();
      const fragment = document.createDocumentFragment();
      let cursor = 0;
      while (cursor < source.length) {
        let bestStart = -1;
        let bestTerm = "";
        for (const term of terms) {
          const start = lower.indexOf(term, cursor);
          if (start >= 0 && (bestStart < 0 || start < bestStart || (start === bestStart && term.length > bestTerm.length))) {
            bestStart = start;
            bestTerm = term;
          }
        }
        if (bestStart < 0) { fragment.append(document.createTextNode(source.slice(cursor))); break; }
        if (bestStart > cursor) fragment.append(document.createTextNode(source.slice(cursor, bestStart)));
        const mark = document.createElement("mark");
        mark.textContent = source.slice(bestStart, bestStart + bestTerm.length);
        mark.dataset.findingKeys = [...(termKeys.get(bestTerm) || [])].join(" ");
        mark.tabIndex = 0;
        mark.setAttribute("aria-label", `Matched ${mark.textContent}. Focus to highlight the related note.`);
        fragment.append(mark);
        cursor = bestStart + bestTerm.length;
      }
      raw.replaceChildren(fragment);
      const findingCards = [...document.querySelectorAll("[data-finding-key]")];
      const marks = [...raw.querySelectorAll("mark[data-finding-keys]")];
      const setLinked = keys => {
        const active = new Set(keys);
        findingCards.forEach(card => card.classList.toggle("is-linked", active.has(card.dataset.findingKey)));
        marks.forEach(mark => mark.classList.toggle("is-linked", mark.dataset.findingKeys.split(" ").some(key => active.has(key))));
      };
      findingCards.forEach(card => {
        const key = card.dataset.findingKey;
        card.addEventListener("mouseenter", () => setLinked([key]));
        card.addEventListener("mouseleave", () => setLinked([]));
        card.addEventListener("focus", () => setLinked([key]));
        card.addEventListener("blur", () => setLinked([]));
      });
      marks.forEach(mark => {
        const keys = mark.dataset.findingKeys.split(" ").filter(Boolean);
        mark.addEventListener("mouseenter", () => setLinked(keys));
        mark.addEventListener("mouseleave", () => setLinked([]));
        mark.addEventListener("focus", () => setLinked(keys));
        mark.addEventListener("blur", () => setLinked([]));
      });
    } catch { /* Raw OCR remains readable if optional highlighting fails. */ }
  }

  const scoreValue = document.querySelector("#health-score-value");
  if (scoreValue) {
    const target = Number(scoreValue.dataset.score);
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (Number.isFinite(target) && !reduceMotion) {
      const start = performance.now();
      const duration = 720;
      scoreValue.textContent = "0";
      const count = now => {
        const progress = Math.min(1, (now - start) / duration);
        const eased = 1 - (1 - progress) ** 3;
        scoreValue.textContent = String(Math.round(target * eased));
        if (progress < 1) window.requestAnimationFrame(count);
      };
      window.requestAnimationFrame(count);
    }
  }
})();
