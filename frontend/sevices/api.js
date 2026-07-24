(function () {
  const loginUrl = "/landing_page/login.html";

  function messageFrom(data, fallback) {
    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data?.detail) && data.detail.length) {
      return data.detail
        .map((item) => item.msg || "Invalid request")
        .join(" ");
    }

    return fallback;
  }

  async function request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const requestOptions = {
      ...options,
      headers,
      credentials: "include",
    };

    if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    let response;
    try {
      response = await fetch(path, requestOptions);
    } catch (error) {
      const networkError = new Error("Unable to reach FreshLink. Please try again.");
      networkError.status = 0;
      throw networkError;
    }

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await response.json()
      : null;

    if (!response.ok) {
      const error = new Error(messageFrom(data, "Something went wrong. Please try again."));
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  }

  function setFormNotice(form, message, type) {
    let notice = form.querySelector(".api-form-notice");
    if (!notice) {
      notice = document.createElement("p");
      notice.className = "api-form-notice";
      notice.setAttribute("role", "status");
      form.prepend(notice);
    }

    notice.textContent = message;
    notice.dataset.type = type;
  }

  async function logout() {
    try {
      await request("/api/auth/logout", { method: "POST" });
    } finally {
      window.location.assign(loginUrl);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-logout]").forEach((control) => {
      control.addEventListener("click", (event) => {
        event.preventDefault();
        logout();
      });
    });
  });

  window.FreshLinkAPI = { loginUrl, request, setFormNotice, logout };
})();
