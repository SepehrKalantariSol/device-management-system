const API_BASE = "http://127.0.0.1:5000";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("signup-form");
  const errorEl = document.getElementById("signup-error");
  const successEl = document.getElementById("signup-success");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    errorEl.textContent = "";
    successEl.textContent = "";

    const payload = {
      first_name: document.getElementById("first-name").value.trim(),
      last_name: document.getElementById("last-name").value.trim(),
      email: document.getElementById("signup-email").value.trim(),
      password: document.getElementById("signup-password").value,
      phone_number: document.getElementById("phone-number").value.trim() || null,
      address: document.getElementById("address").value.trim() || null,
      staff_type: document.querySelector('input[name="staff_type"]:checked').value,
      specialization: document.getElementById("specialization").value.trim() || null
    };

    // Basic client-side validation
    if (!payload.first_name || !payload.last_name || !payload.email || !payload.password) {
      errorEl.textContent = "Please fill in all required fields.";
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/v1/persons`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        errorEl.textContent = data.error || "Account creation failed.";
        return;
      }

      successEl.textContent = "Account created successfully. Redirecting to login…";

      setTimeout(() => {
        window.location.href = "login.html";
      }, 900);

    } catch (err) {
      errorEl.textContent = "Unable to connect to the server. Please try again later.";
    }
  });
});