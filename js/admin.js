// FreshLink Admin Operations Workspace
// I put all the shared behavior in one file so every page loads the same script tag.

// I only needed a simple show/hide here since the project is mostly used on desktop.
document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.querySelector(".nav-toggle");
  var links = document.querySelector(".nav-links");

  if (toggle && links) {
    toggle.addEventListener("click", function () {
      links.classList.toggle("nav-open");
      // I toggled display directly because the mobile menu isn't styled as a full overlay yet.
      if (links.classList.contains("nav-open")) {
        links.style.display = "flex";
        links.style.flexDirection = "column";
        links.style.position = "absolute";
        links.style.top = "72px";
        links.style.left = "0";
        links.style.right = "0";
        links.style.background = "#ffffff";
        links.style.borderBottom = "1px solid var(--color-border)";
        links.style.padding = "12px";
      } else {
        links.style.display = "none";
      }
    });
  }

  // I also let tapping a dropdown label on touch screens open the submenu, since hover doesn't exist there.
  var dropdownTriggers = document.querySelectorAll(".has-dropdown > .nav-link");
  dropdownTriggers.forEach(function (trigger) {
    trigger.addEventListener("click", function (e) {
      if (window.innerWidth <= 720) {
        e.preventDefault();
        var parent = trigger.parentElement;
        parent.classList.toggle("dropdown-open");
        var dropdown = parent.querySelector(".dropdown");
        if (dropdown) {
          dropdown.style.opacity = parent.classList.contains("dropdown-open") ? "1" : "";
          dropdown.style.visibility = parent.classList.contains("dropdown-open") ? "visible" : "";
          dropdown.style.position = "static";
          dropdown.style.boxShadow = "none";
          dropdown.style.transform = "none";
          dropdown.style.display = parent.classList.contains("dropdown-open") ? "block" : "none";
        }
      }
    });
  });
});

// ---------- Generic field validation helper ----------
// I kept validation simple because the backend is not connected yet, this just checks for empty required fields.
function validateForm(formEl) {
  var isValid = true;
  var requiredFields = formEl.querySelectorAll("[required]");

  requiredFields.forEach(function (field) {
    var errorText = field.closest(".field") ? field.closest(".field").querySelector(".field-error-text") : null;
    var value = field.type === "radio" ? getRadioValue(formEl, field.name) : field.value.trim();

    if (!value) {
      isValid = false;
      field.classList.add("field-error");
      if (errorText) errorText.classList.add("show");
    } else {
      field.classList.remove("field-error");
      if (errorText) errorText.classList.remove("show");
    }
  });

  return isValid;
}

function getRadioValue(formEl, name) {
  var checked = formEl.querySelector('input[name="' + name + '"]:checked');
  return checked ? checked.value : "";
}

// ---------- Register Farmer form ----------
var registerForm = document.getElementById("register-farmer-form");
if (registerForm) {
  registerForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var ok = validateForm(registerForm);
    var successBox = document.getElementById("register-success");

    if (ok) {
      // I showed this message to make the form feel responsive after submission, even without a backend.
      successBox.classList.add("show");
      successBox.textContent = "Farmer saved. The record will appear in View Farmers once the backend is connected.";
      registerForm.reset();
      window.scrollTo({ top: successBox.offsetTop - 120, behavior: "smooth" });
    } else {
      if (successBox) successBox.classList.remove("show");
    }
  });
}

// ---------- Harvest Forecast form ----------
var forecastForm = document.getElementById("forecast-form");
if (forecastForm) {
  forecastForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var ok = validateForm(forecastForm);
    var successBox = document.getElementById("forecast-success");

    if (ok) {
      successBox.classList.add("show");
      successBox.textContent = "Forecast submitted. It will appear in View Forecasts once the backend is connected.";
      forecastForm.reset();
      window.scrollTo({ top: successBox.offsetTop - 120, behavior: "smooth" });
    } else {
      if (successBox) successBox.classList.remove("show");
    }
  });
}

// ---------- Farmer records search ----------
// I filtered on name, village, and phone since those are what an admin would actually search by.
var farmerSearch = document.getElementById("farmer-search");
if (farmerSearch) {
  farmerSearch.addEventListener("input", function () {
    filterTable("farmer-table-body", farmerSearch.value, "farmer-no-results");
  });
}

// ---------- Forecast records search ----------
var forecastSearch = document.getElementById("forecast-search");
if (forecastSearch) {
  forecastSearch.addEventListener("input", function () {
    filterTable("forecast-table-body", forecastSearch.value, "forecast-no-results");
  });
}

function filterTable(tbodyId, query, noResultsId) {
  var tbody = document.getElementById(tbodyId);
  if (!tbody) return;

  var rows = tbody.querySelectorAll("tr");
  var normalizedQuery = query.trim().toLowerCase();
  var visibleCount = 0;

  rows.forEach(function (row) {
    var rowText = row.textContent.toLowerCase();
    var matches = rowText.indexOf(normalizedQuery) !== -1;
    row.style.display = matches ? "" : "none";
    if (matches) visibleCount++;
  });

  // I added a no-results state so the page doesn't look broken when a search comes up empty.
  var noResultsEl = document.getElementById(noResultsId);
  if (noResultsEl) {
    noResultsEl.classList.toggle("show", visibleCount === 0);
  }
}
