const API_BASE_URL = "http://127.0.0.1:5000";

function getUser() {
  const raw = localStorage.getItem("dms_user");
  return raw ? JSON.parse(raw) : null;
}

function setUserInfo(user) {
  const el = document.getElementById("user-info");
  if (!el) return;
  const rolesText = (user.roles || []).join(", ");
  el.textContent = `${user.first_name} ${user.last_name} (${rolesText})`;
}

document.addEventListener("DOMContentLoaded", async () => {
  const user = getUser();
  if (!user || !user.person_id) return (window.location.href = "login.html");

  setUserInfo(user);

  const errEl = document.getElementById("profile-error");
  const okEl = document.getElementById("profile-success");
  errEl.textContent = "";
  okEl.textContent = "";

  // Load current profile
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/persons/${user.person_id}`);
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || "Failed to load profile");

    document.getElementById("first-name").value = data.first_name || "";
    document.getElementById("last-name").value = data.last_name || "";
    document.getElementById("email").value = data.email || "";
    document.getElementById("phone").value = data.phone_number || "";
    document.getElementById("address").value = data.address || "";

  } catch (e) {
    errEl.textContent = e.message;
  }

  // Save changes
  document.getElementById("profile-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    errEl.textContent = "";
    okEl.textContent = "";

    const payload = {
      first_name: document.getElementById("first-name").value.trim(),
      last_name: document.getElementById("last-name").value.trim(),
      phone_number: document.getElementById("phone").value.trim() || null,
      address: document.getElementById("address").value.trim() || null
    };

    const newPass = document.getElementById("password").value;
    if (newPass && newPass.trim().length > 0) payload.password = newPass;

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/persons/${user.person_id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "Update failed");

      okEl.textContent = "Profile updated successfully ✅";

      // Update localStorage name shown in header across pages
      user.first_name = payload.first_name;
      user.last_name = payload.last_name;
      localStorage.setItem("dms_user", JSON.stringify(user));
      setUserInfo(user);

      document.getElementById("password").value = "";

    } catch (e) {
      errEl.textContent = e.message;
    }
  });
});