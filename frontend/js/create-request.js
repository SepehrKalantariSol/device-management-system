const API_BASE = "http://127.0.0.1:5000";

function getUser() {
  const raw = localStorage.getItem("dms_user");
  return raw ? JSON.parse(raw) : null;
}

document.addEventListener("DOMContentLoaded", async () => {
  const user = getUser();

  // Must be logged in
  if (!user || !user.person_id) {
    window.location.href = "login.html";
    return;
  }

  const deviceSelect = document.getElementById("req-device");
  const form = document.getElementById("create-request-form");
  const errEl = document.getElementById("req-error");
  const okEl = document.getElementById("req-success");

  // -------- Load devices dropdown --------
  try {
    const res = await fetch(`${API_BASE}/api/v1/devices`);
    const devices = await res.json();

    if (!res.ok) throw new Error("Failed to load devices");

    deviceSelect.innerHTML = `<option value="">Select a device...</option>`;

    devices.forEach(d => {
      const label = `${d.type.toUpperCase()} — ${d.serial_number} (${d.building.name} / ${d.room.name})`;
      const opt = document.createElement("option");
      opt.value = d.id;
      opt.textContent = label;
      deviceSelect.appendChild(opt);
    });
  } catch (e) {
    deviceSelect.innerHTML = `<option value="">Could not load devices</option>`;
    errEl.textContent = "Could not load devices. Please try again later.";
    return;
  }

  // -------- Submit create request --------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errEl.textContent = "";
    okEl.textContent = "";

    const payload = {
      device_id: Number(deviceSelect.value),
      created_by: user.person_id,
      priority: document.getElementById("req-priority").value,
      rq_type: document.getElementById("req-type").value,
      description: document.getElementById("req-description").value.trim(),
    };

    if (!payload.device_id || !payload.description) {
      errEl.textContent = "Please select a device and enter a description.";
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/v1/requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        errEl.textContent = data.error || "Could not create request.";
        return;
      }

      okEl.textContent = `Request created successfully (ID: ${data.request_id}). Redirecting...`;

      setTimeout(() => {
        window.location.href = "home.html";
      }, 900);

    } catch (err) {
      errEl.textContent = "Network error: could not reach the server.";
    }
  });
});