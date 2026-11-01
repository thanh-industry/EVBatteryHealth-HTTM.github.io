/*
 * EV Battery Failure Classification - mockup interaction layer.
 * Vanilla JS only, no dependencies. Every handler guards for the
 * element's existence so this single file can be shared by every page.
 * Nothing here calls a network or file API - this is a static mockup.
 */
(function () {
  "use strict";

  /* ---- Modal dialogs: [data-open-modal="id"] / [data-close-modal] ---- */
  document.querySelectorAll("[data-open-modal]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-open-modal");
      var dialog = document.getElementById(id);
      if (dialog && typeof dialog.showModal === "function") {
        dialog.showModal();
      }
    });
  });
  document.querySelectorAll("[data-close-modal]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var dialog = btn.closest("dialog");
      if (dialog) dialog.close();
    });
  });
  // Click on backdrop closes the dialog
  document.querySelectorAll("dialog.modal").forEach(function (dialog) {
    dialog.addEventListener("click", function (evt) {
      var rect = dialog.getBoundingClientRect();
      var inBounds = evt.clientX >= rect.left && evt.clientX <= rect.right &&
        evt.clientY >= rect.top && evt.clientY <= rect.bottom;
      if (!inBounds) dialog.close();
    });
  });

  /* ---- Run Classification: simulate a loading delay, then reveal result --- */
  var selectedRecord = null;

  /* Render the result panel from the record the user actually selected. Each
     Select button carries the real stored outcome for that battery (label,
     probability and timestamp as produced by the deployed model), so the
     mockup never shows a result belonging to a different serial. */
  var FAILURE_ICON = '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" ' +
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<polygon points="6.3 2 13.7 2 18 6.3 18 13.7 13.7 18 6.3 18 2 13.7 2 6.3"/>' +
    '<line x1="10" y1="7" x2="10" y2="11.2"/><line x1="10" y1="13.8" x2="10" y2="13.9"/></svg>';
  var OK_ICON = '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" ' +
    'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M10 2 3.5 4.4v4.9c0 4.1 2.8 6.9 6.5 8.9 3.7-2 6.5-4.8 6.5-8.9V4.4L10 2Z"/>' +
    '<polyline points="7.2 10 9.2 12 12.9 7.8"/></svg>';

  function renderResult() {
    var r = selectedRecord;
    if (!r || !r.label) return;
    var isFailure = r.label === "Failure";
    var badge = document.getElementById("result-badge");
    var hint = document.getElementById("result-hint");
    var rec = document.getElementById("result-record");
    var at = document.getElementById("result-at");
    var prob = document.getElementById("result-prob");
    var bar = document.getElementById("result-bar");
    var meter = document.getElementById("result-meter");
    if (badge) {
      badge.classList.toggle("is-failure", isFailure);
      badge.classList.toggle("is-ok", !isFailure);
      // The icon must change with the state, not just the colour: a warning
      // octagon beside the words "NO FAILURE" would contradict itself, and
      // colour alone is never allowed to carry the meaning.
      badge.innerHTML = (isFailure ? FAILURE_ICON : OK_ICON) +
        (isFailure ? " FAILURE" : " NO FAILURE");
    }
    if (hint) {
      hint.textContent = isFailure
        ? "The model predicts this battery is heading toward a failure. Record a maintenance assessment below."
        : "The model predicts no failure for this battery. Record a maintenance assessment if you inspected it anyway.";
    }
    if (rec) rec.textContent = r.serial + " / " + r.vehicle;
    if (at) at.textContent = r.at;
    if (prob) {
      prob.textContent = r.prob.toFixed(2) + "%";
      prob.classList.toggle("is-failure", isFailure);
      prob.classList.toggle("is-ok", !isFailure);
    }
    if (bar) {
      bar.setAttribute("width", String((r.prob / 100) * 400));
      bar.style.fill = isFailure ? "var(--c-failure)" : "var(--c-ok)";
    }
    if (meter) {
      meter.setAttribute("aria-label", "Failure probability " + r.prob.toFixed(2) +
        " percent, " + (isFailure ? "above" : "below") + " the 50 percent decision threshold");
    }
  }

  var runBtn = document.getElementById("run-classification-btn");
  if (runBtn) {
    var loadingPanel = document.getElementById("classification-loading");
    var resultPanel = document.getElementById("classification-result");
    runBtn.addEventListener("click", function () {
      if (resultPanel) resultPanel.hidden = true;
      if (loadingPanel) loadingPanel.hidden = false;
      runBtn.disabled = true;
      window.setTimeout(function () {
        if (loadingPanel) loadingPanel.hidden = true;
        if (resultPanel) {
          renderResult();
          resultPanel.hidden = false;
          resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
        }
        runBtn.disabled = false;
      }, 700);
    });
  }

  /* ---- Maintenance assessment form: show inline confirmation ---- */
  var assessForm = document.getElementById("assessment-form");
  if (assessForm) {
    var assessConfirm = document.getElementById("assessment-confirm");
    assessForm.addEventListener("submit", function (evt) {
      evt.preventDefault();
      assessForm.hidden = true;
      if (assessConfirm) {
        assessConfirm.hidden = false;
        assessConfirm.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
  }
  var assessAgainBtn = document.getElementById("assessment-edit-again");
  if (assessAgainBtn) {
    assessAgainBtn.addEventListener("click", function () {
      document.getElementById("assessment-confirm").hidden = true;
      assessForm.hidden = false;
    });
  }

  /* ---- Battery record search filter (UC-06) ---- */
  var recordSearch = document.getElementById("record-search");
  if (recordSearch) {
    var recordRows = document.querySelectorAll("#records-table tbody tr");
    var recordEmpty = document.getElementById("records-empty");
    recordSearch.addEventListener("input", function () {
      var q = recordSearch.value.trim().toLowerCase();
      var visibleCount = 0;
      recordRows.forEach(function (row) {
        var haystack = (row.getAttribute("data-search") || "").toLowerCase();
        var match = q === "" || haystack.indexOf(q) !== -1;
        row.classList.toggle("is-hidden-row", !match);
        if (match) visibleCount++;
      });
      if (recordEmpty) recordEmpty.hidden = visibleCount !== 0;
    });
  }

  /* ---- Run Classification step 1 search filter (same pattern as UC-06) ---- */
  var step1Search = document.getElementById("step1-search");
  if (step1Search) {
    var step1Rows = document.querySelectorAll("#step1-table tbody tr");
    step1Search.addEventListener("input", function () {
      var q = step1Search.value.trim().toLowerCase();
      step1Rows.forEach(function (row) {
        var haystack = (row.getAttribute("data-search") || "").toLowerCase();
        var match = q === "" || haystack.indexOf(q) !== -1;
        row.classList.toggle("is-hidden-row", !match);
      });
    });
  }

  /* ---- Run Classification: step 1 (select battery) -> step 2 (confirm + classify) --- */
  var step1 = document.getElementById("step-1");
  var step2 = document.getElementById("step-2");
  if (step1 && step2) {
    var serialLabel = document.getElementById("selected-record-serial");
    var vehicleLabel = document.getElementById("selected-record-vehicle");
    document.querySelectorAll(".select-record-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (serialLabel) serialLabel.textContent = btn.getAttribute("data-serial") || "";
        if (vehicleLabel) vehicleLabel.textContent = btn.getAttribute("data-vehicle") || "";
        selectedRecord = {
          serial: btn.getAttribute("data-serial") || "",
          vehicle: btn.getAttribute("data-vehicle") || "",
          label: btn.getAttribute("data-result") || "",
          prob: parseFloat(btn.getAttribute("data-prob")),
          at: btn.getAttribute("data-at") || ""
        };
        step1.hidden = true;
        step2.hidden = false;
        step2.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
    var changeRecordBtn = document.getElementById("change-record-btn");
    if (changeRecordBtn) {
      changeRecordBtn.addEventListener("click", function () {
        step2.hidden = true;
        step1.hidden = false;
        step1.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }

  /* ---- Numeric stepper buttons (+/-) next to key-parameter inputs ---- */
  document.querySelectorAll(".stepper-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.getAttribute("data-target"));
      if (!target) return;
      var step = parseFloat(target.getAttribute("step")) || 1;
      var min = target.hasAttribute("min") ? parseFloat(target.getAttribute("min")) : -Infinity;
      var max = target.hasAttribute("max") ? parseFloat(target.getAttribute("max")) : Infinity;
      var value = parseFloat(target.value) || 0;
      var decimals = (String(step).split(".")[1] || "").length;
      value += btn.getAttribute("data-step") === "inc" ? step : -step;
      value = Math.min(max, Math.max(min, value));
      target.value = value.toFixed(decimals);
    });
  });

  /* ---- Classification history filters (UC-09) ---- */
  var historyStatus = document.getElementById("history-filter-status");
  var historySearch = document.getElementById("history-filter-search");
  if (historyStatus || historySearch) {
    var historyRows = document.querySelectorAll("[data-history-row]");
    var historyEmpty = document.getElementById("history-empty");
    var applyHistoryFilters = function () {
      var status = historyStatus ? historyStatus.value : "all";
      var q = historySearch ? historySearch.value.trim().toLowerCase() : "";
      var visibleCount = 0;
      historyRows.forEach(function (row) {
        var rowStatus = row.getAttribute("data-status");
        var haystack = (row.getAttribute("data-search") || "").toLowerCase();
        var statusMatch = status === "all" || status === rowStatus;
        var searchMatch = q === "" || haystack.indexOf(q) !== -1;
        var match = statusMatch && searchMatch;
        row.classList.toggle("is-hidden-row", !match);
        if (match) visibleCount++;
      });
      if (historyEmpty) historyEmpty.hidden = visibleCount !== 0;
    };
    if (historyStatus) historyStatus.addEventListener("change", applyHistoryFilters);
    if (historySearch) historySearch.addEventListener("input", applyHistoryFilters);
  }
})();
