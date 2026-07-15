const adminLoginForm = document.querySelector("#admin-login-form");

if (adminLoginForm) {
  adminLoginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const button = adminLoginForm.querySelector("button[type='submit']");
    const loginId = adminLoginForm.elements.login_id.value.trim();
    const password = adminLoginForm.elements.password.value;

    if (!loginId || !password) {
      FreshLinkAPI.setFormNotice(adminLoginForm, "Enter your login details.", "error");
      return;
    }

    button.disabled = true;
    button.textContent = "Logging in...";

    try {
      const result = await FreshLinkAPI.request("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ login_id: loginId, password }),
      });

      if (result.role !== "admin") {
        await FreshLinkAPI.request("/api/auth/logout", { method: "POST" });
        FreshLinkAPI.setFormNotice(
          adminLoginForm,
          "This page is for administrator accounts only.",
          "error"
        );
        return;
      }

      window.location.assign(result.dashboard_url);
    } catch (error) {
      FreshLinkAPI.setFormNotice(
        adminLoginForm,
        error.message || "Unable to log in.",
        "error"
      );
    } finally {
      button.disabled = false;
      button.textContent = "Login as Admin";
    }
  });
}
