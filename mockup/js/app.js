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
