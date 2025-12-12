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

function statusBadge(status) {
  return `<span class="badge badge-${status}">${status}</span>`;
}

async function fetchAllRequests() {
  const res = await fetch(`${API_BASE_URL}/api/v1/requests`);
  const data = await res.json().catch(() => []);
  if (!res.ok) throw new Error(data.error || "Failed to load requests");
  return data;
}

async function acceptRequest(reqId, techId) {
  const res = await fetch(`${API_BASE_URL}/api/v1/requests/${reqId}/accept`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tech_id: techId })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Accept failed");
}

async function resolveRequest(reqId, techId, comments) {
  const res = await fetch(`${API_BASE_URL}/api/v1/requests/${reqId}/resolve`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resolved_by: techId, comments })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Resolve failed");
}

function renderOpenCard(r, user) {
  const div = document.createElement("div");
  div.className = "list-item";

  div.innerHTML = `
    <div class="row-between">
      <strong>Request #${r.request_id}</strong>
      ${statusBadge(r.status)}
    </div>
    <small>${r.device.type} ${r.device.serial_number} — ${r.location.building.name}/${r.location.room.name}</small><br>
    <small>${r.description}</small><br>
    <small class="muted">priority: ${r.priority}</small>
    <div class="form-actions" style="margin-top:10px;">
      <button class="btn btn-small btn-primary">Accept</button>
    </div>
  `;

  div.querySelector("button").addEventListener("click", async () => {
    try {
      div.querySelector("button").disabled = true;
      await acceptRequest(r.request_id, user.person_id);
      await loadAndRender(user);
    } catch (e) {
      alert(e.message);
      div.querySelector("button").disabled = false;
    }
  });

  return div;
}

function renderMyAssignedCard(r, user) {
  const div = document.createElement("div");
  div.className = "list-item";

  div.innerHTML = `
    <div class="row-between">
      <strong>Request #${r.request_id}</strong>
      ${statusBadge(r.status)}
    </div>
    <small>${r.device.type} ${r.device.serial_number} — ${r.location.building.name}/${r.location.room.name}</small><br>
    <small>${r.description}</small><br>
    <small class="muted">priority: ${r.priority}</small>

    <div class="form-actions" style="margin-top:10px; display:flex; gap:8px; align-items:center;">
      <input class="input-small" type="text" placeholder="Add comment..." />
      <button class="btn btn-small btn-primary">Resolve</button>
    </div>
  `;

  const input = div.querySelector("input");
  const btn = div.querySelector("button");

  btn.addEventListener("click", async () => {
    try {
      btn.disabled = true;
      await resolveRequest(r.request_id, user.person_id, input.value.trim());
      await loadAndRender(user);
    } catch (e) {
      alert(e.message);
      btn.disabled = false;
    }
  });

  return div;
}

function renderResolvedCard(r) {
  const div = document.createElement("div");
  div.className = "list-item";

  const resolverText = r.resolved_by
    ? `${r.resolved_by.first_name} ${r.resolved_by.last_name}`
    : "—";

  div.innerHTML = `
    <div class="row-between">
      <strong>Request #${r.request_id}</strong>
      ${statusBadge(r.status)}
    </div>
    <small>${r.device.type} ${r.device.serial_number} — ${r.location.building.name}/${r.location.room.name}</small><br>
    <small>${r.description}</small><br>
    <small class="muted">priority: ${r.priority} | resolved by: ${resolverText}</small>
  `;

  return div;
}

async function loadAndRender(user) {
  const openBox = document.getElementById("open-requests");
  const myBox = document.getElementById("my-requests");
  const resolvedBox = document.getElementById("resolved-requests");

  openBox.innerHTML = `<p class="placeholder">Loading...</p>`;
  myBox.innerHTML = `<p class="placeholder">Loading...</p>`;
  resolvedBox.innerHTML = `<p class="placeholder">Loading...</p>`;

  try {
    const all = await fetchAllRequests();

    // Open + unassigned
    const open = all.filter(r => r.status === "open" && !r.resolved_by);

    // Assigned to me (in progress)
    const mine = all.filter(
      r => r.status === "in_progress" &&
           r.resolved_by &&
           r.resolved_by.id === user.person_id
    );

    // Recently resolved (last 5)
    const resolved = all
      .filter(r => r.status === "resolved")
      .slice(0, 5);

    // Render open
    openBox.innerHTML = "";
    if (open.length === 0) {
      openBox.innerHTML = `<p class="placeholder">No open requests.</p>`;
    } else {
      open.forEach(r => openBox.appendChild(renderOpenCard(r, user)));
    }

    // Render mine
    myBox.innerHTML = "";
    if (mine.length === 0) {
      myBox.innerHTML = `<p class="placeholder">No requests assigned to you.</p>`;
    } else {
      mine.forEach(r => myBox.appendChild(renderMyAssignedCard(r, user)));
    }

    // Render resolved
    resolvedBox.innerHTML = "";
    if (resolved.length === 0) {
      resolvedBox.innerHTML = `<p class="placeholder">No resolved requests yet.</p>`;
    } else {
      resolved.forEach(r => resolvedBox.appendChild(renderResolvedCard(r)));
    }

  } catch (e) {
    openBox.innerHTML = `<p class="form-error">${e.message}</p>`;
    myBox.innerHTML = `<p class="form-error">${e.message}</p>`;
    resolvedBox.innerHTML = `<p class="form-error">${e.message}</p>`;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const user = getUser();

  if (!user || !user.person_id) {
    window.location.href = "login.html";
    return;
  }

  const isIT = Array.isArray(user.roles) && user.roles.includes("it_technician");
  if (!isIT) {
    window.location.href = "home.html";
    return;
  }

  setUserInfo(user);
  await loadAndRender(user);
});