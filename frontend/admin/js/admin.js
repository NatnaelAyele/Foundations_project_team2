const $ = (selector, context = document) => context.querySelector(selector);
const $$ = (selector, context = document) => [...context.querySelectorAll(selector)];

function setText(selector, value) { const element = $(selector); if (element) element.textContent = value; }
function formatNumber(value) { return Number(value || 0).toLocaleString("en-US"); }
function formatKilograms(value) { return `${formatNumber(value)} kg`; }
function formatDate(value) {
  if (!value) return "—";
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}
function showToast(message) {
  const toast = $("#toast"); if (!toast) return;
  toast.textContent = message; toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 3500);
}
function handleError(error, fallback) {
  if (error.status === 401) { window.location.assign(FreshLinkAPI.loginUrl); return; }
  showToast(error.message || fallback);
}
function statusLabel(value) { return String(value || "Unknown").replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase()); }
function statusPill(value) {
  const normalized = String(value || "").toUpperCase();
  const kind = normalized === "ACTIVE" ? "status-active" : normalized.includes("PENDING") ? "status-pending" : normalized.includes("CONFIRM") ? "status-confirmed" : normalized.includes("PLAN") ? "status-planned" : "status-new";
  const pill = document.createElement("span"); pill.className = `status-pill ${kind}`; pill.textContent = statusLabel(value); return pill;
}
function tableMessage(body, columns, message) {
  body.replaceChildren(); const row = document.createElement("tr"); const cell = document.createElement("td");
  cell.colSpan = columns; cell.className = "table-message"; cell.textContent = message; row.appendChild(cell); body.appendChild(row);
}
function cell(row, value, className) { const item = document.createElement("td"); item.textContent = value || "—"; if (className) item.className = className; row.appendChild(item); return item; }

function initTheme() {
  const button = $("#themeToggle"); if (!button) return;
  button.addEventListener("click", () => {
    const next = (document.documentElement.getAttribute("data-theme") || "light") === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("freshlink-theme", next); } catch (error) {}
  });
}
function initSidebar() {
  const sidebar = $("#sidebar"); if (!sidebar) return;
  $("#sidebarCollapse")?.addEventListener("click", () => sidebar.classList.toggle("collapsed"));
  try { const width = localStorage.getItem("freshlink-sidebar-w"); if (width) document.documentElement.style.setProperty("--sb-w", `${width}px`); } catch (error) {}
  const handle = $("#resizeHandle");
  if (handle) handle.addEventListener("mousedown", (event) => {
    if (sidebar.classList.contains("collapsed")) return;
    const resize = (move) => document.documentElement.style.setProperty("--sb-w", `${Math.max(200, Math.min(420, move.clientX))}px`);
    const stop = () => { const width = getComputedStyle(document.documentElement).getPropertyValue("--sb-w").trim().replace("px", ""); try { localStorage.setItem("freshlink-sidebar-w", width); } catch (error) {} window.removeEventListener("mousemove", resize); window.removeEventListener("mouseup", stop); };
    event.preventDefault(); window.addEventListener("mousemove", resize); window.addEventListener("mouseup", stop);
  });
  const backdrop = document.createElement("div"); backdrop.className = "backdrop"; document.body.appendChild(backdrop);
  const close = () => { sidebar.classList.remove("open"); backdrop.classList.remove("show"); };
  $("#menuToggle")?.addEventListener("click", () => { sidebar.classList.add("open"); backdrop.classList.add("show"); });
  backdrop.addEventListener("click", close);
}
function initGreeting() {
  const hour = new Date().getHours(); setText("#greeting", `${hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening"}, Admin`);
  setText("#todayDate", new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" }));
}

function renderRecentFarmers(body, farmers) {
  if (!farmers.length) return tableMessage(body, 5, "No farmers have been registered yet.");
  body.replaceChildren(); farmers.forEach((farmer) => { const row = document.createElement("tr"); cell(row, farmer.name); cell(row, farmer.sector); cell(row, farmer.village); cell(row, farmer.phone); const status = document.createElement("td"); status.appendChild(statusPill(farmer.status)); row.appendChild(status); body.appendChild(row); });
}
function renderRecentForecasts(body, forecasts) {
  if (!forecasts.length) return tableMessage(body, 5, "No forecasts have been submitted yet.");
  body.replaceChildren(); forecasts.forEach((forecast) => { const row = document.createElement("tr"); cell(row, forecast.farmer_name); cell(row, formatDate(forecast.harvest_date)); cell(row, formatKilograms(forecast.quantity_kg)); cell(row, forecast.needs_transport ? "Yes" : "No", forecast.needs_transport ? "tag-yes" : "tag-no"); cell(row, forecast.needs_storage ? "Yes" : "No", forecast.needs_storage ? "tag-yes" : "tag-no"); body.appendChild(row); });
}
async function loadDashboard() {
  const farmerBody = $("#recent-farmers-body"); if (!farmerBody) return;
  const forecastBody = $("#recent-forecasts-body");
  try {
    const summary = await FreshLinkAPI.request("/api/admin/dashboard/summary");
    setText("#farmer-total", formatNumber(summary.farmers.total)); setText("#forecast-total", formatNumber(summary.forecasts.total)); setText("#transport-needed", formatNumber(summary.forecasts.needing_transport)); setText("#storage-needed", formatNumber(summary.forecasts.needing_storage));
    setText("#farmers-week-note", `+${formatNumber(summary.farmers.registered_this_week)} this week`); setText("#forecasts-week-note", `+${formatNumber(summary.forecasts.submitted_this_week)} this week`);
    const engine = $("#engine-status"); if (engine) { engine.replaceChildren(); const dot = document.createElement("span"); dot.className = summary.engine.available ? "dot ok" : "dot"; engine.append(dot, ` ${summary.engine.available ? "Engine available" : "Engine unavailable"}`); engine.title = summary.engine.message; }
    renderRecentFarmers(farmerBody, summary.recent_farmers); renderRecentForecasts(forecastBody, summary.recent_forecasts);
  } catch (error) { tableMessage(farmerBody, 5, "Unable to load recent farmers."); if (forecastBody) tableMessage(forecastBody, 5, "Unable to load recent forecasts."); handleError(error, "Unable to load dashboard data."); }
}

function watchForm(form) { $$("input, select, textarea", form).forEach((field) => ["input", "change"].forEach((event) => field.addEventListener(event, () => field.closest(".field")?.classList.remove("error")))); }
function validate(form) {
  let valid = true; $$("input[required], select[required], textarea[required]", form).forEach((field) => { if (field.type === "radio") return; const ok = field.value.trim() !== ""; field.closest(".field")?.classList.toggle("error", !ok); if (!ok) valid = false; });
  [...new Set($$("input[type='radio'][required]", form).map((field) => field.name))].forEach((name) => { const fields = $$(`input[name="${name}"]`, form); const selected = fields.some((field) => field.checked); fields[0]?.closest(".field")?.classList.toggle("error", !selected); if (!selected) valid = false; }); return valid;
}
async function loadSectors(select) {
  try { const result = await FreshLinkAPI.request("/api/admin/sectors?district=Kamonyi"); select.replaceChildren(new Option("Select sector", "", true, true)); select.options[0].disabled = true; result.items.forEach((sector) => select.add(new Option(sector.name, sector.name))); } catch (error) { select.replaceChildren(new Option("Unable to load sectors", "", true, true)); select.options[0].disabled = true; handleError(error, "Unable to load sectors."); }
}
function initFarmerForm() {
  const form = $("#register-farmer-form"); if (!form) return; loadSectors($("#rf-sector", form)); watchForm(form);
  form.addEventListener("submit", async (event) => { event.preventDefault(); if (!validate(form)) return; const button = $("button[type='submit']", form); button.disabled = true; FreshLinkAPI.setFormNotice(form, "Registering farmer…", "loading"); try { const farmer = await FreshLinkAPI.request("/api/admin/farmers", { method: "POST", body: JSON.stringify(Object.fromEntries(new FormData(form))) }); form.reset(); $("#register-success")?.classList.add("show"); FreshLinkAPI.setFormNotice(form, `${farmer.name} was registered successfully.`, "success"); showToast("Farmer registered."); } catch (error) { FreshLinkAPI.setFormNotice(form, error.message || "Unable to register farmer.", "error"); handleError(error, "Unable to register farmer."); } finally { button.disabled = false; } });
}
function renderFarmers(body, farmers) { if (!farmers.length) return tableMessage(body, 6, "No farmers match your search."); body.replaceChildren(); farmers.forEach((farmer) => { const row = document.createElement("tr"); [farmer.name, farmer.sector, farmer.cell, farmer.village, farmer.phone].forEach((value) => cell(row, value)); const status = document.createElement("td"); status.appendChild(statusPill(farmer.status)); row.appendChild(status); body.appendChild(row); }); }
function initFarmerList() { const body = $("#farmer-table-body"), input = $("#farmer-search"); if (!body || !input) return; let timer; const load = async () => { tableMessage(body, 6, "Loading farmers…"); try { const query = new URLSearchParams({ page_size: "100" }); if (input.value.trim()) query.set("search", input.value.trim()); const result = await FreshLinkAPI.request(`/api/admin/farmers?${query}`); renderFarmers(body, result.items); $("#farmer-no-results").style.display = "none"; } catch (error) { tableMessage(body, 6, "Unable to load farmers."); handleError(error, "Unable to load farmers."); } }; input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(load, 250); }); load(); }

async function loadFarmerOptions(select) { try { const result = await FreshLinkAPI.request("/api/admin/farmers?page_size=100"); select.replaceChildren(new Option("Select a registered farmer", "", true, true)); select.options[0].disabled = true; result.items.forEach((farmer) => select.add(new Option(`${farmer.name} — ${farmer.sector}`, farmer.farmer_id))); } catch (error) { select.replaceChildren(new Option("Unable to load farmers", "", true, true)); select.options[0].disabled = true; handleError(error, "Unable to load registered farmers."); } }
function initForecastForm() { const form = $("#forecast-form"); if (!form) return; loadFarmerOptions($("#fc-farmer", form)); watchForm(form); form.addEventListener("submit", async (event) => { event.preventDefault(); if (!validate(form)) return; const button = $("button[type='submit']", form), data = new FormData(form); button.disabled = true; FreshLinkAPI.setFormNotice(form, "Saving forecast…", "loading"); try { const forecast = await FreshLinkAPI.request("/api/admin/forecasts", { method: "POST", body: JSON.stringify({ farmer_id: Number(data.get("farmer_id")), quantity_kg: Number(data.get("quantity_kg")), harvest_date: data.get("harvest_date"), needs_transport: data.get("needs_transport") === "yes", needs_storage: data.get("needs_storage") === "yes", notes: data.get("notes")?.trim() || null }) }); form.reset(); $("#forecast-success")?.classList.add("show"); FreshLinkAPI.setFormNotice(form, `Forecast for ${forecast.farmer_name} was saved.`, "success"); showToast("Forecast saved."); } catch (error) { FreshLinkAPI.setFormNotice(form, error.message || "Unable to save forecast.", "error"); handleError(error, "Unable to save forecast."); } finally { button.disabled = false; } }); }
function renderForecasts(body, forecasts) { if (!forecasts.length) return tableMessage(body, 5, "No forecasts match your search."); body.replaceChildren(); forecasts.forEach((forecast) => { const row = document.createElement("tr"); cell(row, forecast.farmer_name); cell(row, forecast.sector); cell(row, formatDate(forecast.harvest_date)); cell(row, formatKilograms(forecast.quantity_kg)); const status = document.createElement("td"); status.appendChild(statusPill(forecast.status)); row.appendChild(status); body.appendChild(row); }); }
function initForecastList() { const body = $("#forecast-table-body"), input = $("#forecast-search"); if (!body || !input) return; let timer; const load = async () => { tableMessage(body, 5, "Loading forecasts…"); try { const query = new URLSearchParams({ page_size: "100" }); if (input.value.trim()) query.set("search", input.value.trim()); const result = await FreshLinkAPI.request(`/api/admin/forecasts?${query}`); renderForecasts(body, result.items); $("#forecast-no-results").style.display = "none"; } catch (error) { tableMessage(body, 5, "Unable to load forecasts."); handleError(error, "Unable to load forecasts."); } }; input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(load, 250); }); load(); }

function reportBar(label, value, maximum, className = "") { const row = document.createElement("div"); row.className = "bar-row"; const name = document.createElement("span"); name.className = "bar-label"; name.textContent = label; const track = document.createElement("div"); track.className = "bar-track"; const fill = document.createElement("span"); fill.className = `bar-fill ${className}`.trim(); fill.style.width = `${maximum ? value / maximum * 100 : 0}%`; track.appendChild(fill); const total = document.createElement("span"); total.className = "bar-value"; total.textContent = formatNumber(value); row.append(name, track, total); return row; }
function renderReportBars(container, items, valueKey, emptyMessage, className = "") { if (!container) return; container.replaceChildren(); if (!items.length) { const message = document.createElement("p"); message.className = "hint"; message.textContent = emptyMessage; container.appendChild(message); return; } const maximum = Math.max(...items.map((item) => Number(item[valueKey]) || 0)); items.forEach((item, index) => container.appendChild(reportBar(item.sector || statusLabel(item.reason), Number(item[valueKey]), maximum, className || (index % 2 ? "secondary" : "")))); }
async function loadReports() { if (!$("#report-total-harvest")) return; try { const report = await FreshLinkAPI.request("/api/admin/reports"); setText("#report-total-harvest", formatKilograms(report.total_harvest_kg)); setText("#report-trips-coordinated", report.trips_coordinated === null ? "Unavailable" : formatNumber(report.trips_coordinated)); setText("#report-matched", report.successfully_matched_percent === null ? "Unavailable" : `${formatNumber(report.successfully_matched_percent)}%`); setText("#report-excluded", report.excluded_unmatched === null ? "Unavailable" : formatNumber(report.excluded_unmatched)); renderReportBars($("#report-sector-bars"), report.harvest_by_sector, "quantity_kg", "No harvest forecasts fall within this month."); renderReportBars($("#report-exclusion-bars"), report.exclusion_reasons, "count", "No engine coordination data is available yet.", "accent"); setText("#report-matching-note", report.matching_blocker || ""); } catch (error) { handleError(error, "Unable to load report data."); } }

document.addEventListener("DOMContentLoaded", () => { initTheme(); initSidebar(); initGreeting(); loadDashboard(); initFarmerForm(); initFarmerList(); initForecastForm(); initForecastList(); loadReports(); });
