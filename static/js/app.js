(() => {
  const groups = ["Milk", "Wheat or Gluten", "Soy", "Peanut", "Tree nut", "Egg", "Fish", "Shellfish", "Sesame", "Mustard", "Sulphite"];
  const stageNames = {
    image_validation: "Image validation",
    image_preprocessing: "Image preprocessing",
    text_extraction: "Text extraction",
    ingredient_additive_analysis: "Ingredient and additive analysis",
    nutrition_screening: "Nutrition screening",
    result_generation: "Result generation",
  };
  const holder = document.querySelector("#allergen-chips");
  const form = document.querySelector("#scan-form");
  const fileInput = document.querySelector("#label-image");
  const preview = document.querySelector("#preview");
  const previewWrap = document.querySelector("#preview-wrap");
  const previewName = document.querySelector("#preview-name");

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
        button.setAttribute("aria-pressed", String(button.getAttribute("aria-pressed") !== "true"));
        saved = [...holder.querySelectorAll('[aria-pressed="true"]')].map(item => item.textContent);
        try { localStorage.setItem("nutriscan-allergens", JSON.stringify(saved)); } catch { /* Preferences remain usable when storage is unavailable. */ }
      });
      holder.append(button);
    }
  }

  const clearPreview = () => {
    if (preview?.dataset.objectUrl) URL.revokeObjectURL(preview.dataset.objectUrl);
    if (preview) {
      preview.removeAttribute("src");
      delete preview.dataset.objectUrl;
    }
    if (previewWrap) previewWrap.hidden = true;
    if (previewName) previewName.textContent = "";
    if (fileInput) fileInput.value = "";
  };

  const showPreview = file => {
    if (!file || !preview || !previewWrap) return;
    if (preview.dataset.objectUrl) URL.revokeObjectURL(preview.dataset.objectUrl);
    const objectUrl = URL.createObjectURL(file);
    preview.dataset.objectUrl = objectUrl;
    preview.src = objectUrl;
    preview.alt = `Preview of ${file.name}`;
    previewWrap.hidden = false;
    if (previewName) previewName.textContent = file.name;
  };
  fileInput?.addEventListener("change", () => showPreview(fileInput.files?.[0]));
  document.querySelector("#remove-preview")?.addEventListener("click", clearPreview);

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
    const status = document.querySelector("#scan-status");
    const progress = document.querySelector("#scan-progress");
    const steps = progress ? [...progress.querySelectorAll("[data-stage]")] : [];
    if (!form || !fileInput?.files?.length) {
      if (status) status.textContent = "Choose a label photo before scanning.";
      fileInput?.focus();
      return;
    }

    const data = new FormData(form);
    const progressBytes = new Uint8Array(16);
    if (globalThis.crypto?.getRandomValues) globalThis.crypto.getRandomValues(progressBytes);
    else progressBytes.forEach((_value, index) => { progressBytes[index] = Math.floor(Math.random() * 256); });
    const progressId = [...progressBytes].map(value => value.toString(16).padStart(2, "0")).join("");
    const progressUrl = form.dataset.progressUrl?.replace("__progress_id__", encodeURIComponent(progressId));
    data.append("progress_id", progressId);
    try {
      const selected = [...(holder?.querySelectorAll('[aria-pressed="true"]') || [])].map(button => button.textContent);
      selected.forEach(group => data.append("user_allergens", group));
    } catch { /* Allergen preferences are optional. */ }

    if (progress) progress.hidden = false;
    if (status) status.textContent = "Uploading the label photo…";
    form.querySelectorAll("button").forEach(button => { button.disabled = true; });

    let stopPolling = false;
    const paintProgress = payload => {
      const complete = new Set(payload.completed_stages || []);
      steps.forEach(item => {
        const stage = item.dataset.stage;
        item.classList.toggle("complete", complete.has(stage));
        item.classList.toggle("active", payload.active_stage === stage);
      });
      if (!status) return;
      if (payload.state === "complete") status.textContent = "Scan complete. Opening the saved result…";
      else if (payload.state === "error") status.textContent = payload.error || "The scan could not be completed.";
      else if (payload.active_stage) status.textContent = `${stageNames[payload.active_stage] || "Processing"}…`;
      else status.textContent = "Upload received. Waiting for image validation…";
    };
    const pollProgress = async () => {
      while (!stopPolling && progressUrl) {
        try {
          const response = await fetch(progressUrl, { cache: "no-store" });
          if (response.ok) paintProgress(await response.json());
        } catch { /* The scan request remains the source of truth if polling is unavailable. */ }
        if (!stopPolling) await new Promise(resolve => window.setTimeout(resolve, 240));
      }
    };
    const pollTask = pollProgress();
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: data,
        headers: { "Accept": "application/json", "X-Requested-With": "XMLHttpRequest" },
      });
      const payload = await response.json();
      stopPolling = true;
      await pollTask;
      if (!response.ok) throw new Error(payload.error || "NutriScan could not complete this scan.");
      paintProgress({ completed_stages: Object.keys(stageNames), active_stage: null, state: "complete" });
      const resultUrl = form.dataset.resultUrl?.replace("__scan_id__", encodeURIComponent(payload.scan_id));
      if (!resultUrl) throw new Error("The saved result could not be opened.");
      window.location.assign(resultUrl);
    } catch (error) {
      stopPolling = true;
      await pollTask;
      if (progress) progress.hidden = true;
      if (status) status.textContent = error instanceof Error ? error.message : "NutriScan could not complete this scan. Try another photo.";
      form.querySelectorAll("button").forEach(button => { button.disabled = false; });
    }
  };

  form?.addEventListener("submit", event => { event.preventDefault(); startScan(); });

  document.querySelector("#sample-button")?.addEventListener("click", async () => {
    const button = document.querySelector("#sample-button");
    const status = document.querySelector("#scan-status");
    try {
      button.disabled = true;
      const response = await fetch(button.dataset.sampleUrl);
      if (!response.ok) throw new Error("The bundled sample label could not be loaded.");
      const sample = new File([await response.blob()], "nutriscan-sample.png", { type: "image/png" });
      const transfer = new DataTransfer();
      transfer.items.add(sample);
      fileInput.files = transfer.files;
      showPreview(sample);
      if (status) status.textContent = "Sample label selected. Starting the scan…";
      form.requestSubmit();
    } catch (error) {
      if (status) status.textContent = error instanceof Error ? error.message : "The bundled sample label could not be loaded.";
      button.disabled = false;
    }
  });

  const slider = document.querySelector("#comparison-slider");
  const comparison = document.querySelector(".comparison");
  const comparisonHelp = document.querySelector("#comparison-help");
  const stackBreakpoint = window.matchMedia("(max-width: 700px)");
  const setComparisonOrientation = () => {
    if (!comparison) return;
    comparison.dataset.stack = String(stackBreakpoint.matches);
    if (comparisonHelp) comparisonHelp.textContent = stackBreakpoint.matches
      ? "Move the slider to adjust the height of the stacked original and processed images."
      : "Move the slider to reveal more of the processed image within the shared frame.";
  };
  setComparisonOrientation();
  stackBreakpoint.addEventListener?.("change", setComparisonOrientation);
  slider?.addEventListener("input", () => {
    comparison?.style.setProperty("--split", `${slider.value}%`);
    slider.setAttribute("aria-valuetext", `${slider.value}% comparison split`);
  });
  document.querySelectorAll(".comparison-image").forEach(image => {
    const showFallback = () => {
      image.hidden = true;
      const fallback = image.parentElement?.querySelector("[data-image-fallback]");
      if (fallback) fallback.hidden = false;
    };
    image.addEventListener("error", showFallback, { once: true });
    if (image.complete && image.naturalWidth === 0) showFallback();
  });
  document.querySelectorAll(".archive-thumb-image").forEach(image => {
    image.addEventListener("error", () => {
      image.hidden = true;
      const fallback = image.parentElement?.querySelector("[data-thumb-fallback]");
      if (fallback) fallback.hidden = false;
    }, { once: true });
    if (image.complete && image.naturalWidth === 0) {
      image.hidden = true;
      const fallback = image.parentElement?.querySelector("[data-thumb-fallback]");
      if (fallback) fallback.hidden = false;
    }
  });

  const raw = document.querySelector("#raw-ocr");
  const findingsNode = document.querySelector("#detected-findings");
  if (raw && findingsNode) {
    try {
      const findings = JSON.parse(findingsNode.textContent || "{}");
      const terms = [
        ...(findings.additives || []).flatMap(item => [item.name, item.ins_code, item.matched_code, ...(item.matched_tokens || [])]),
        ...(findings.flags || []).map(item => item.keyword),
        ...(findings.allergens || []).flatMap(item => item.matched_keywords || []),
        ...(findings.unknown_codes || []).map(item => item.code),
      ].filter(term => typeof term === "string" && term.trim().length > 1);
      const uniqueTerms = [...new Set(terms.map(term => term.trim()))].sort((a, b) => b.length - a.length);
      const source = raw.textContent || "";
      const lower = source.toLowerCase();
      const fragment = document.createDocumentFragment();
      let cursor = 0;
      while (cursor < source.length) {
        let bestStart = -1;
        let bestTerm = "";
        for (const term of uniqueTerms) {
          const start = lower.indexOf(term.toLowerCase(), cursor);
          if (start >= 0 && (bestStart < 0 || start < bestStart || (start === bestStart && term.length > bestTerm.length))) {
            bestStart = start;
            bestTerm = term;
          }
        }
        if (bestStart < 0) { fragment.append(document.createTextNode(source.slice(cursor))); break; }
        if (bestStart > cursor) fragment.append(document.createTextNode(source.slice(cursor, bestStart)));
        const mark = document.createElement("mark");
        mark.textContent = source.slice(bestStart, bestStart + bestTerm.length);
        fragment.append(mark);
        cursor = bestStart + bestTerm.length;
      }
      raw.replaceChildren(fragment);
    } catch { /* Raw OCR remains readable if optional highlighting fails. */ }
  }
})();
