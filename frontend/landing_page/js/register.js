const registerGrid = document.querySelector(".register-grid");
const registerCards = document.querySelectorAll(".register-card");
const registerForms = document.querySelectorAll(".register-form");

const rules = {
  role: /^(hub_operator|truck_provider)$/,
  username: /^(?!.*\.\.)(?!.*\.$)[A-Za-z][A-Za-z0-9._]{3,29}$/,
  email: /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/,
  password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d\s])\S{8,64}$/,
  businessName: /^(?!\d+$)[A-Za-z0-9][A-Za-z0-9 .'-]{1,49}$/,
  phone: /^(?:\+?250|0)(?:7[2389])\d{7}$/,
  location: /^[A-Za-z][A-Za-z .'-]{1,49}$/,
  capacity: /^[1-9]\d{0,5}$/,
  plateNumber: /^RA[A-Z]\s?\d{3}[A-Z]$/,
};

const messages = {
  role: "Registration type is not valid.",
  username: "Use 4-30 characters, start with a letter, and use only letters, numbers, dots, or underscores.",
  email: "Enter a valid email address or leave this field empty.",
  password: "Use 8-64 characters with uppercase, lowercase, number, and symbol. No spaces.",
  confirm_password: "Passwords must match.",
  name: "Use 2-50 letters or numbers. Spaces, hyphens, apostrophes, and periods are allowed.",
  phone: "Use a Rwanda phone number like 0781234567 or +250781234567.",
  district: "Use 2-50 letters. Spaces, hyphens, apostrophes, and periods are allowed.",
  sector: "Use 2-50 letters. Spaces, hyphens, apostrophes, and periods are allowed.",
  cell: "Use 2-50 letters. Spaces, hyphens, apostrophes, and periods are allowed.",
  village: "Use 2-50 letters. Spaces, hyphens, apostrophes, and periods are allowed.",
  total_capacity_kg: "Enter a whole number between 1 and 999999.",
  capacity_kg: "Enter a whole number between 1 and 999999.",
  plate_number: "Use a plate number like RAB 245K.",
};

const fieldRules = {
  role: rules.role,
  username: rules.username,
  email: rules.email,
  password: rules.password,
  name: rules.businessName,
  phone: rules.phone,
  district: rules.location,
  sector: rules.location,
  cell: rules.location,
  village: rules.location,
  total_capacity_kg: rules.capacity,
  capacity_kg: rules.capacity,
  plate_number: rules.plateNumber,
};

function isRoleHash(hashValue) {
  return hashValue === "hub-registration" || hashValue === "truck-registration";
}

function showSelectedForm() {
  const selectedId = window.location.hash.replace("#", "");
  const hasSelectedRole = isRoleHash(selectedId);

  if (registerGrid) {
    if (hasSelectedRole) {
      registerGrid.classList.add("is-filtered");
    } else {
      registerGrid.classList.remove("is-filtered");
    }
  }

  registerCards.forEach((card) => {
    if (hasSelectedRole && card.id !== selectedId) {
      card.hidden = true;
    } else {
      card.hidden = false;
    }
  });
}

showSelectedForm();
window.addEventListener("hashchange", showSelectedForm);

function getErrorElement(input) {
  let error = input.nextElementSibling;

  if (!error || !error.classList.contains("field-error")) {
    error = document.createElement("p");
    error.className = "field-error";
    error.id = `${input.id || input.name}-error`;
    input.insertAdjacentElement("afterend", error);
  }

  return error;
}

function showError(input, message) {
  const error = getErrorElement(input);

  input.setAttribute("aria-invalid", "true");
  input.setAttribute("aria-describedby", error.id);
  error.textContent = message;
}

function clearError(input) {
  const error = input.nextElementSibling;

  input.removeAttribute("aria-invalid");
  input.removeAttribute("aria-describedby");

  if (error && error.classList.contains("field-error")) {
    error.textContent = "";
  }
}

function cleanValue(input) {
  if (input.name === "plate_number") {
    return input.value.trim().toUpperCase();
  }

  return input.value.trim();
}

function validateField(input, form) {
  const value = cleanValue(input);
  const rule = fieldRules[input.name];

  if (input.type !== "password") {
    input.value = value;
  }

  if (input.required && !value) {
    showError(input, "This field is required.");
    return false;
  }

  if (!value && input.name === "email") {
    clearError(input);
    return true;
  }

  if (input.name === "confirm_password") {
    const password = form.elements.password.value;

    if (value !== password) {
      showError(input, messages.confirm_password);
      return false;
    }

    clearError(input);
    return true;
  }

  if (rule && !rule.test(value)) {
    showError(input, messages[input.name]);
    return false;
  }

  clearError(input);
  return true;
}

function validateForm(form) {
  const fields = form.querySelectorAll("input");
  let isValid = true;

  fields.forEach((input) => {
    if (!validateField(input, form)) {
      isValid = false;
    }
  });

  return isValid;
}

function focusFirstInvalidField(form) {
  const firstInvalidField = form.querySelector('[aria-invalid="true"]');

  if (firstInvalidField) {
    firstInvalidField.focus();
  }
}

registerForms.forEach((form) => {
  form.noValidate = true;

  form.addEventListener("input", (event) => {
    const input = event.target;

    if (input.matches("input")) {
      form.classList.remove("is-valid");
      validateField(input, form);
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!validateForm(form)) {
      focusFirstInvalidField(form);
      return;
    }

    const button = form.querySelector("button[type='submit']");
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    payload.email = payload.email || null;

    if (payload.total_capacity_kg) {
      payload.total_capacity_kg = Number(payload.total_capacity_kg);
    }
    if (payload.capacity_kg) {
      payload.capacity_kg = Number(payload.capacity_kg);
    }

    button.disabled = true;
    const originalText = button.textContent;
    button.textContent = "Submitting...";

    try {
      await FreshLinkAPI.request("/api/registrations/providers", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      form.classList.add("is-valid");
      FreshLinkAPI.setFormNotice(
        form,
        "Registration successful. You can now log in.",
        "success"
      );
      form.reset();
    } catch (error) {
      FreshLinkAPI.setFormNotice(form, error.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = originalText;
    }
  });
});
