const totalInput = document.getElementById("totalCapacity");
const availableInput = document.getElementById("availableCapacity");
const notesInput = document.getElementById("notes");
const hubSelect = document.getElementById("hubName");
const form = document.getElementById("capacityForm");
const confirmBanner = document.getElementById("confirmBanner");

function updateCapacityVisual() {
  const total = Number(totalInput.value) || 0;
  const available = Number(availableInput.value) || 0;
  document.getElementById("capCurrent").textContent = available.toLocaleString();
  document.getElementById("capTotalLabel").textContent = `/ ${total.toLocaleString()} kg total`;
  const fill = document.getElementById("capBarFill");
  const status = document.getElementById("capStatus");
  if (!total) {
    fill.style.width = "0%";
    fill.classList.remove("over-limit");
    status.textContent = "Enter your hub's numbers to preview.";
    status.classList.remove("warn");
    return;
  }
  const percentage = Math.min((available / total) * 100, 100);
  fill.style.width = `${percentage}%`;
  if (available > total) {
    fill.classList.add("over-limit");
    status.textContent = "Available capacity cannot exceed total capacity.";
    status.classList.add("warn");
  } else {
    fill.classList.remove("over-limit");
    status.classList.remove("warn");
    status.textContent = `${Math.round(percentage)}% of capacity is free for incoming produce.`;
  }
}

function setBanner(message, type) {
  confirmBanner.textContent = message;
  confirmBanner.classList.add("visible");
  confirmBanner.dataset.type = type;
}

async function loadCapacity() {
  try {
    const capacity = await FreshLinkAPI.request("/api/hub/capacity");
    hubSelect.replaceChildren(new Option(capacity.name, capacity.hub_id, true, true));
    totalInput.value = capacity.total_capacity_kg;
    availableInput.value = capacity.available_capacity_kg;
    notesInput.value = capacity.notes || "";
    updateCapacityVisual();
  } catch (error) {
    if (error.status === 401) window.location.assign(FreshLinkAPI.loginUrl);
    else setBanner(error.message || "Unable to load hub capacity.", "error");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const total = Number(totalInput.value);
  const available = Number(availableInput.value);
  if (available > total) {
    updateCapacityVisual();
    return;
  }
  const submit = form.querySelector("button[type='submit']");
  submit.disabled = true;
  try {
    await FreshLinkAPI.request("/api/hub/capacity", {
      method: "PATCH",
      body: JSON.stringify({
        total_capacity_kg: total,
        available_capacity_kg: available,
        produce_type: "tomatoes",
        notes: notesInput.value.trim() || null,
      }),
    });
    setBanner("Capacity updated successfully.", "success");
  } catch (error) {
    if (error.status === 401) window.location.assign(FreshLinkAPI.loginUrl);
    else setBanner(error.message || "Unable to save capacity.", "error");
  } finally {
    submit.disabled = false;
  }
});

[totalInput, availableInput].forEach((input) => input.addEventListener("input", updateCapacityVisual));
loadCapacity();
