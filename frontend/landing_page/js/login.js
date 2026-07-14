const loginForm = document.querySelector("#login-form");

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const button = loginForm.querySelector("button[type='submit']");
    const loginId = loginForm.elements.login_id.value.trim();
    const password = loginForm.elements.password.value;

    if (!loginId || !password) {
      FreshLinkAPI.setFormNotice(loginForm, "Enter your login details.", "error");
      return;
    }

    button.disabled = true;
    button.textContent = "Logging in...";

    try {
      const result = await FreshLinkAPI.request("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ login_id: loginId, password }),
      });
      window.location.assign(result.dashboard_url);
    } catch (error) {
      FreshLinkAPI.setFormNotice(loginForm, error.message, "error");
      button.disabled = false;
      button.textContent = "Login";
    }
  });
}
