// login.js – handles POST /api/v1/login

const API_BASE_URL = "http://127.0.0.1:5000";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");
    const errorEl = document.getElementById("login-error");

    form.addEventListener("submit", async (event) => {
        event.preventDefault(); // stop normal form submit

        errorEl.textContent = ""; // clear old error

        const email = document.getElementById("login-email").value.trim();
        const password = document.getElementById("login-password").value;

        if (!email || !password) {
            errorEl.textContent = "Please enter both email and password.";
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                // backend uses { "error": "..." }
                errorEl.textContent = data.error || "Login failed.";
                return;
            }

            // Save user info in localStorage so home.html can use it
            const userInfo = {
                person_id: data.person_id,
                first_name: data.first_name,
                last_name: data.last_name,
                roles: data.roles || []
            };

            localStorage.setItem("dms_user", JSON.stringify(userInfo));

            // Redirect to home page
            window.location.href = "home.html";

        } catch (err) {
            console.error("Login error:", err);
            errorEl.textContent = "Could not connect to the server. Please try again.";
        }
    });
});