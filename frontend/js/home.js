const API_BASE_URL = "http://127.0.0.1:5000";

function getUser() {
  const raw = localStorage.getItem("dms_user");
  return raw ? JSON.parse(raw) : null;
}

async function loadITRecentRequests(user) {
  const container = document.getElementById("it-recent-requests");
  container.innerHTML = "<p class='muted'>Loading...</p>";

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/requests`);
    const text = await res.text();
    console.log("IT requests raw:", res.status, text);

    if (!res.ok) throw new Error(`Failed: ${res.status}`);

    const requests = JSON.parse(text);

    // Filter only OPEN and UNASSIGNED
    const openRequests = requests.filter(
      r => r.status === "open" && !r.resolved_by
    );

    const recent = openRequests.slice(0, 3); // only first 3

    if (recent.length === 0) {
      container.innerHTML = "<p class='muted'>No open requests.</p>";
      return;
    }

    container.innerHTML = "";
    recent.forEach(r => {
      const div = document.createElement("div");
      div.className = "list-item";
      div.innerHTML = `
        <strong>Request #${r.request_id}</strong>
        <span class="status-badge status-${r.status}">
          ${r.status.replace("_", " ")}
        </span>
        <span class="priority-badge priority-${r.priority}">
          ${r.priority}
        </span>
        <br>
        <small>
          ${r.device.type} ${r.device.serial_number}<br>
          ${r.location.building.name} / ${r.location.room.name}
        </small>
      `;
      container.appendChild(div);
    });

  } catch (err) {
    console.error(err);
    container.innerHTML = "<p class='form-error'>Failed to load IT requests.</p>";
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const user = getUser();

  // If not logged in, send them back
  if (!user || !user.person_id) {
    window.location.href = "login.html";
    return;
  }

  // Show header user info
  const userInfoEl = document.getElementById("user-info");
  const rolesText = (user.roles || []).join(", ");
  userInfoEl.textContent = `${user.first_name} ${user.last_name} (${rolesText})`;
  // ---- IT Technician Panel visibility ----
  const itPanel = document.getElementById("it-panel");
  const isIT = Array.isArray(user.roles) && user.roles.includes("it_technician");

  if (itPanel) {
    itPanel.style.display = isIT ? "block" : "none";
  }

  if (isIT) {
  loadITRecentRequests(user);
  }
  // Load devices
  const devicesList = document.getElementById("devices-list");
  devicesList.innerHTML = "<p class='placeholder'>Loading devices...</p>";

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/devices`);
    const devices = await res.json();

    if (!res.ok) throw new Error("Failed to load devices");

    devicesList.innerHTML = "";
    devices.forEach(d => {
      const div = document.createElement("div");
      div.className = "list-item";
      div.innerHTML = `
        <strong>${d.type.toUpperCase()}</strong> — ${d.serial_number}<br>
        <small>${d.building.name} / ${d.room.name} — status: ${d.status}</small>
      `;
      devicesList.appendChild(div);
    });
  } catch (err) {
    console.error(err);
    devicesList.innerHTML = "<p class='form-error'>Could not load devices.</p>";
  }

  // Load requests created by this user
  const requestsList = document.getElementById("requests-list");
  requestsList.innerHTML = "<p class='placeholder'>Loading requests...</p>";

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/requests/created-by/${user.person_id}`);
    const data = await res.json();

    if (!res.ok) {
      requestsList.innerHTML = `<p class='form-error'>${data.error || "Could not load requests."}</p>`;
      return;
    }

    const requests = data.requests || [];
    requestsList.innerHTML = "";

    if (requests.length === 0) {
      requestsList.innerHTML = "<p class='placeholder'>No requests created by you.</p>";
      return;
    }

    requests.forEach(r => {
      const div = document.createElement("div");
      div.className = "list-item";
      div.innerHTML = `
        <strong>Request #${r.request_id}</strong> — ${r.status} (${r.priority})<br>
        <small>${r.device.type} ${r.device.serial_number} — ${r.location.building.name}/${r.location.room.name}</small><br>
        <small>${r.description}</small>
      `;
      requestsList.appendChild(div);
    });

  } catch (err) {
    console.error(err);
    requestsList.innerHTML = "<p class='form-error'>Could not load requests.</p>";
  }
});