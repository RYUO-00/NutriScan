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
  };
  fileInput?.addEventListener("change", () => showPreview(fileInput.files?.[0]));

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
    const progressLabels = [
      "Checking the upload…", "Preparing the image…", "Reading label text…", "Matching ingredients and allergens…", "Parsing nutrition values…", "Calculating the screening score…", "Saving the result…",
    ];
    const data = new FormData(form);
    try {
      const selected = [...(holder?.querySelectorAll('[aria-pressed="true"]') || [])].map(button => button.textContent);
      selected.forEach(group => data.append("user_allergens", group));
    } catch { /* Allergen preferences are optional. */ }
    if (progress) progress.hidden = false;
    let index = 0;
    const updateStage = () => {
      status.textContent = progressLabels[index];
      steps.forEach((item, i) => {
        item.classList.toggle("active", i === index);
        item.classList.toggle("complete", i < index);
      });
      index = (index + 1) % progressLabels.length;
    };
    updateStage();
    const timer = window.setInterval(updateStage, 900);
    form.querySelectorAll("button").forEach(button => { button.disabled = true; });
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: data,
        headers: { "Accept": "application/json", "X-Requested-With": "XMLHttpRequest" },
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "NutriScan could not complete this scan.");
      window.clearInterval(timer);
      steps.forEach(item => { item.classList.remove("active"); item.classList.add("complete"); });
      status.textContent = "Scan complete. Opening the saved result…";
      window.location.assign(`/history?scan_id=${encodeURIComponent(payload.scan_id)}`);
    } catch (error) {
      window.clearInterval(timer);
      if (progress) progress.hidden = true;
      status.textContent = error instanceof Error ? error.message : "NutriScan could not complete this scan. Try another photo.";
      form.querySelectorAll("button").forEach(button => { button.disabled = false; });
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
