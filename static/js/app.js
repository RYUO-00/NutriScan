(() => {
  const allergenGroups = ["Milk", "Wheat or Gluten", "Soy", "Peanut", "Tree nut", "Egg", "Fish", "Shellfish", "Sesame", "Mustard", "Sulphite"];
  const holder = document.querySelector("#allergen-chips");
  const form = document.querySelector("#scan-form");
  const fileInput = document.querySelector("#label-image");
  const preview = document.querySelector("#preview");
  const previewWrap = document.querySelector("#preview-wrap");
  const specimen = document.querySelector("#sample-specimen");
  const dropzone = document.querySelector(".dropzone");
  const status = document.querySelector("#scan-status");

  if (holder) {
    let saved = [];
    try { saved = JSON.parse(localStorage.getItem("nutriscan-allergens") || "[]"); } catch { saved = []; }
    for (const group of allergenGroups) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "chip";
      button.dataset.allergen = group;
      button.setAttribute("aria-pressed", String(saved.includes(group)));
      const name = document.createElement("span");
      name.className = "chip-name";
      name.textContent = group;
      const state = document.createElement("span");
      state.className = "chip-state";
      state.textContent = "Selected";
      button.append(name, state);
      button.addEventListener("click", () => {
        button.setAttribute("aria-pressed", String(button.getAttribute("aria-pressed") !== "true"));
        saved = [...holder.querySelectorAll('[aria-pressed="true"]')].map(item => item.dataset.allergen);
        try { localStorage.setItem("nutriscan-allergens", JSON.stringify(saved)); } catch { /* Preferences are optional. */ }
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
    if (specimen) specimen.hidden = true;
    if (dropzone) {
      dropzone.classList.add("has-file");
      const title = dropzone.querySelector(".drop-title");
      if (title) title.textContent = `Selected: ${file.name}`;
    }
    const filename = document.querySelector("#preview-name");
    if (filename) filename.textContent = file.name;
  };

  fileInput?.addEventListener("change", () => showPreview(fileInput.files?.[0]));
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
    fileInput.dispatchEvent(new Event("change", { bubbles: true }));
  });

  const stageCopy = {
    uploading: "Uploading the label photo…",
    preprocessing: "Preparing the image…",
    reading_text: "Reading label text…",
    decoding: "Matching ingredients and allergens…",
    nutrition: "Reading nutrition values…",
    scoring: "Calculating the screening score…",
    saving: "Saving the result…",
    complete: "Scan complete. Opening the saved result…",
  };

  const makeProgressId = () => {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID().replaceAll("-", "");
    const bytes = new Uint8Array(16);
    globalThis.crypto.getRandomValues(bytes);
    return [...bytes].map(value => value.toString(16).padStart(2, "0")).join("");
  };

  const startScan = async () => {
    if (!form || !fileInput?.files?.length) {
      if (status) {
        status.textContent = "Choose a label photo before scanning.";
        status.classList.add("is-error");
      }
      fileInput?.focus();
      return;
    }
    const progress = document.querySelector("#scan-progress");
    const steps = progress ? [...progress.children] : [];
    const progressId = makeProgressId();
    const data = new FormData(form);
    data.append("progress_id", progressId);
    const selected = [...(holder?.querySelectorAll('[aria-pressed="true"]') || [])].map(button => button.dataset.allergen);
    selected.forEach(group => data.append("user_allergens", group));
    if (progress) progress.hidden = false;
    if (status) {
      status.classList.remove("is-error", "is-success");
      status.textContent = "Waiting for the upload…";
    }
    form.querySelectorAll("button").forEach(button => { button.disabled = true; });

    const setStage = stage => {
      const activeIndex = steps.findIndex(item => item.dataset.stage === stage);
      steps.forEach((item, index) => {
        item.classList.toggle("active", index === activeIndex);
        item.classList.toggle("complete", stage === "complete" || (activeIndex >= 0 && index < activeIndex));
      });
      if (status && stageCopy[stage]) status.textContent = stageCopy[stage];
    };

    const controller = new AbortController();
    let polling = true;
    const pollStages = async () => {
      while (polling) {
        try {
          const response = await fetch(`/api/scan-progress/${progressId}`, { cache: "no-store", signal: controller.signal });
          if (response.ok) {
            const payload = await response.json();
            setStage(payload.stage);
          }
        } catch (error) {
          if (error instanceof DOMException && error.name === "AbortError") return;
        }
        await new Promise(resolve => window.setTimeout(resolve, 180));
      }
    };
    const pollTask = pollStages();

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: data,
        headers: { "Accept": "application/json", "X-Requested-With": "XMLHttpRequest" },
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "NutriScan could not complete this scan.");
      setStage("complete");
      if (status) status.classList.add("is-success");
      polling = false;
      controller.abort();
      await pollTask;
      window.location.assign(`/history?scan_id=${encodeURIComponent(payload.scan_id)}`);
    } catch (error) {
      polling = false;
      controller.abort();
      await pollTask;
      if (progress) progress.hidden = true;
      if (status) {
        status.classList.remove("is-success");
        status.classList.add("is-error");
        status.textContent = error instanceof Error ? error.message : "NutriScan could not complete this scan. Try another photo.";
      }
      form.querySelectorAll("button").forEach(button => { button.disabled = false; });
    }
  };

  form?.addEventListener("submit", event => { event.preventDefault(); startScan(); });

  document.querySelector("#sample-button")?.addEventListener("click", async () => {
    const button = document.querySelector("#sample-button");
    try {
      button.disabled = true;
      const response = await fetch("/static/images/sample_label.png");
      if (!response.ok) throw new Error("The bundled sample label could not be loaded.");
      const sample = new File([await response.blob()], "nutriscan-sample.png", { type: "image/png" });
      const transfer = new DataTransfer();
      transfer.items.add(sample);
      fileInput.files = transfer.files;
      fileInput.dispatchEvent(new Event("change", { bubbles: true }));
      if (status) status.textContent = "Bundled sample label selected. Starting the scan…";
      form.requestSubmit();
    } catch (error) {
      if (status) {
        status.classList.add("is-error");
        status.textContent = error instanceof Error ? error.message : "The bundled sample label could not be loaded.";
      }
      button.disabled = false;
    }
  });

  const score = document.querySelector(".score-value[data-score-target]");
  if (score) {
    const target = Number(score.dataset.scoreTarget);
    const reducedMotion = globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (Number.isFinite(target) && !reducedMotion && globalThis.requestAnimationFrame) {
      const start = performance.now();
      const duration = 620;
      const tick = now => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - (1 - progress) ** 3;
        score.textContent = String(Math.round(target * eased));
        if (progress < 1) requestAnimationFrame(tick);
      };
      score.textContent = "0";
      requestAnimationFrame(tick);
    }
  }

  const slider = document.querySelector("#comparison-slider");
  const comparison = document.querySelector(".comparison");
  slider?.addEventListener("input", () => comparison?.style.setProperty("--split", `${slider.value}%`));

  const raw = document.querySelector("#raw-ocr");
  const findingsNode = document.querySelector("#detected-findings");
  if (!raw || !findingsNode) return;
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

    const clearLinked = () => document.querySelectorAll(".is-linked").forEach(node => node.classList.remove("is-linked"));
    const linkFinding = key => {
      clearLinked();
      document.querySelector(`[data-finding-key="${CSS.escape(key)}"]`)?.classList.add("is-linked");
      document.querySelectorAll("#raw-ocr mark").forEach(mark => {
        if (mark.dataset.findingKeys.split(" ").includes(key)) mark.classList.add("is-linked");
      });
    };
    document.querySelectorAll("[data-finding-key]").forEach(card => {
      const key = card.dataset.findingKey;
      card.addEventListener("mouseenter", () => linkFinding(key));
      card.addEventListener("mouseleave", clearLinked);
      card.addEventListener("focus", () => linkFinding(key));
      card.addEventListener("blur", clearLinked);
    });
    raw.querySelectorAll("mark").forEach(mark => {
      const keys = mark.dataset.findingKeys.split(" ").filter(Boolean);
      const key = keys[0];
      if (!key) return;
      mark.addEventListener("mouseenter", () => linkFinding(key));
      mark.addEventListener("mouseleave", clearLinked);
      mark.addEventListener("focus", () => linkFinding(key));
      mark.addEventListener("blur", clearLinked);
      mark.addEventListener("click", () => document.querySelector(`[data-finding-key="${CSS.escape(key)}"]`)?.focus());
    });
  } catch { /* Raw OCR remains readable if optional highlighting fails. */ }
})();
