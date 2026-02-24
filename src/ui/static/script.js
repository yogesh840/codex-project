const TARGET_SENTENCE = "The quick brown fox jumps over the lazy dog. This is my HID Guardian baseline test.";
let riskGauge, riskTrend, keyTrend, cursorTrend, deviceTrend;
let baselinedKeys = [], baselinedCursor = [], downTimes = {}, clickCounter = 0, typingStart = null;
let tableState = { key: "ts", asc: false };

const severityClass = (lvl) => lvl === "High" ? "sev-high" : lvl === "Medium" ? "sev-medium" : "sev-low";
const toPct = (v) => `${Math.round((Number(v) || 0) * 100)}%`;

function levelColor(score) {
  if (score >= 0.7) return "#ff4444";
  if (score >= 0.3) return "#ffd166";
  return "#00ff88";
}

function initDashboardCharts() {
  const baseOpts = { responsive: true, maintainAspectRatio: false, animation: { duration: 650 }, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 1 } } };
  riskTrend = new Chart(document.getElementById("riskTrend"), { type: "line", data: { labels: [], datasets: [{ data: [], borderColor: "#00d4ff", tension: .35, fill: true, backgroundColor: "rgba(0,212,255,.15)" }] }, options: baseOpts });
  keyTrend = new Chart(document.getElementById("keystrokeTrend"), { type: "line", data: { labels: [], datasets: [{ data: [], borderColor: "#ff7b7b", tension: .35 }] }, options: baseOpts });
  cursorTrend = new Chart(document.getElementById("cursorTrend"), { type: "line", data: { labels: [], datasets: [{ data: [], borderColor: "#00ff88", tension: .35 }] }, options: baseOpts });
  deviceTrend = new Chart(document.getElementById("deviceTrend"), { type: "bar", data: { labels: [], datasets: [{ data: [], backgroundColor: "#ffd166" }] }, options: baseOpts });
  riskGauge = new Chart(document.getElementById("riskGauge"), {
    type: "doughnut",
    data: { labels: ["Risk", "Safe"], datasets: [{ data: [0, 100], backgroundColor: ["#00ff88", "#26375b"], borderWidth: 0, cutout: "72%" }] },
    options: { rotation: -90, circumference: 180, plugins: { legend: { display: false } }, animation: { duration: 700 } }
  });
}

function showToast(message) {
  const host = document.getElementById("toastHost");
  const el = document.createElement("div");
  el.className = "alert-toast";
  el.textContent = message;
  host.prepend(el);
  setTimeout(() => el.remove(), 3500);
}

function sortRows(rows) {
  const { key, asc } = tableState;
  return rows.sort((a, b) => {
    const av = a[key] ?? ""; const bv = b[key] ?? "";
    if (typeof av === "number" || key === "risk_score") return asc ? Number(av) - Number(bv) : Number(bv) - Number(av);
    return asc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
  });
}

function renderEvents(alerts) {
  const rows = alerts.map((a) => {
    const module = a.device_score > 0.1 ? "USB" : a.cursor_score > a.keystroke_score ? "Cursor" : "Keystroke";
    return { ...a, module };
  });
  const sorted = sortRows(rows);
  const html = sorted.map((a) => `<tr>
    <td>${a.ts || "--"}</td><td>${a.username || "anonymous"}</td><td>${toPct(a.risk_score)}</td>
    <td><i class="fa-solid ${a.module === "USB" ? "fa-usb" : a.module === "Cursor" ? "fa-computer-mouse" : "fa-keyboard"} me-1"></i>${a.module}</td>
    <td><span class="badge ${severityClass(a.risk_level)}">${a.risk_level}</span></td>
    <td><button class="btn btn-sm btn-outline-info" onclick="showToast('${(a.explanation || "No explanation").replace(/'/g, "") }')">Inspect</button></td>
  </tr>`).join("");
  document.getElementById("eventsBody").innerHTML = html;
}

function fallbackHistory() {
  const points = [];
  for (let i = 0; i < 30; i++) {
    const s = 0.45 + 0.35 * Math.sin(i / 3);
    points.push({ ts: `T-${30 - i}s`, risk_score: Math.max(0.1, Math.min(0.8, s)), keystroke_score: Math.max(0.1, s - .1), cursor_score: Math.max(0.1, s - .15), device_score: i % 8 === 0 ? 0.4 : 0.05 });
  }
  return points;
}

function updateDashboard(risk, alerts, devices, history) {
  const score = Number(risk?.risk_score || 0);
  const percent = Math.round(score * 100);
  document.getElementById("riskPercent").textContent = `${percent}%`;
  document.getElementById("riskValueMono").textContent = score.toFixed(2);
  document.getElementById("riskLevel").textContent = (risk?.risk_level || "Low").toUpperCase();
  document.getElementById("riskSubtitle").textContent = score > 0.7 ? "Critical deviation detected in behavior patterns" : "No threats detected in last 30 min";
  document.getElementById("currentUser").textContent = risk?.username || "Yogesh";
  document.getElementById("deviceCount").textContent = `${(devices.connected || []).length} HID devices`;
  riskGauge.data.datasets[0].data = [percent, 100 - percent];
  riskGauge.data.datasets[0].backgroundColor = [levelColor(score), "#26375b"];
  riskGauge.update();

  const rows = (history && history.length) ? history : fallbackHistory();
  const labels = rows.map((r) => (r.ts || "").slice(11, 19) || r.ts);
  [[riskTrend, rows.map((r) => Number(r.risk_score || 0))], [keyTrend, rows.map((r) => Number(r.keystroke_score || 0))], [cursorTrend, rows.map((r) => Number(r.cursor_score || 0))], [deviceTrend, rows.map((r) => Number(r.device_score || 0))]].forEach(([chart, data]) => {
    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.update();
  });

  const deviceHTML = (devices.connected || []).map((d) => `<li>${d.product || "Unknown"} (${d.vid}:${d.pid}) <span class="badge ${d.trusted ? "sev-low" : "sev-high"}">${d.trusted ? "trusted" : "untrusted"}</span></li>`).join("") || "<li>No active HID device reported</li>";
  document.getElementById("deviceList").innerHTML = deviceHTML;
  renderEvents((alerts && alerts.length) ? alerts : [
    { ts: new Date().toISOString(), username: "Yogesh", risk_score: 0.22, risk_level: "Low", explanation: "Low keystroke variance", keystroke_score: 0.22, cursor_score: 0.15, device_score: 0 },
    { ts: new Date(Date.now() - 65000).toISOString(), username: "Yogesh", risk_score: 0.52, risk_level: "Medium", explanation: "Medium cursor anomaly", keystroke_score: 0.31, cursor_score: 0.57, device_score: 0 },
  ]);

  const top = alerts?.[0];
  if (top?.risk_level === "High") showToast(`High alert: ${top.explanation || "Behavior anomaly"}`);
}

async function refreshDashboard() {
  const [risk, alerts, devices, history] = await Promise.all([
    fetch("/risk/current").then((r) => r.json()).catch(() => ({})),
    fetch("/alerts/recent?limit=12").then((r) => r.json()).catch(() => []),
    fetch("/devices").then((r) => r.json()).catch(() => ({ connected: [] })),
    fetch("/risk/history?limit=30").then((r) => r.json()).catch(() => []),
  ]);
  updateDashboard(risk, alerts, devices, history);
}

async function simulateAttack() { await fetch("/simulate/robot", { method: "POST" }); }

function startCapture() {
  baselinedKeys = []; baselinedCursor = []; downTimes = {};
  document.getElementById("captureStatus").textContent = "Collecting keystroke baseline...";
  window.addEventListener("keydown", keyDownHandler);
  window.addEventListener("keyup", keyUpHandler);
  window.addEventListener("mousemove", mouseMoveHandler);
  window.addEventListener("click", mouseClickHandler);
  setTimeout(async () => {
    window.removeEventListener("keydown", keyDownHandler);
    window.removeEventListener("keyup", keyUpHandler);
    window.removeEventListener("mousemove", mouseMoveHandler);
    window.removeEventListener("click", mouseClickHandler);
    await submitRegistration();
  }, 15000);
}

function keyDownHandler(e) { downTimes[e.key] = performance.now() / 1000; }
function keyUpHandler(e) {
  const rel = performance.now() / 1000;
  baselinedKeys.push({ key: e.key, pressed_at: downTimes[e.key] || rel, released_at: rel });
}
function mouseMoveHandler(e) { baselinedCursor.push({ x: e.clientX, y: e.clientY, timestamp: performance.now() / 1000, event_type: "move" }); }
function mouseClickHandler(e) { baselinedCursor.push({ x: e.clientX, y: e.clientY, timestamp: performance.now() / 1000, event_type: "click" }); }

async function submitRegistration() {
  const username = document.getElementById("regUsername").value || "anonymous";
  const pass = document.getElementById("regPassword").value;
  const pass2 = document.getElementById("regPassword2").value;
  if (pass !== pass2) {
    document.getElementById("captureStatus").textContent = "Password and confirmation do not match.";
    return;
  }
  await fetch("/register", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, keystrokes: baselinedKeys, cursor_events: baselinedCursor }),
  });
  document.getElementById("captureStatus").textContent = "Complete! Profile saved.";
}

function setupRegistration() {
  const input = document.getElementById("typingInput");
  const accuracy = document.getElementById("typingAccuracy");
  const speed = document.getElementById("typingSpeed");
  const progress = document.getElementById("typingProgress");
  const captureBtn = document.getElementById("captureBtn");
  const mousePad = document.getElementById("mousePad");

  input.addEventListener("input", () => {
    if (!typingStart) typingStart = Date.now();
    const text = input.value;
    const correct = text.split("").filter((ch, i) => TARGET_SENTENCE[i] === ch).length;
    const acc = TARGET_SENTENCE.length ? Math.round((correct / Math.max(text.length, 1)) * 100) : 0;
    const elapsedMin = Math.max((Date.now() - typingStart) / 60000, 1 / 60);
    const wpm = Math.round((text.trim().split(/\s+/).filter(Boolean).length) / elapsedMin);
    accuracy.textContent = `${acc}%`;
    speed.textContent = `${wpm} WPM`;
    progress.style.width = `${Math.min((text.length / TARGET_SENTENCE.length) * 100, 100)}%`;
  });

  mousePad.addEventListener("click", () => {
    clickCounter += 1;
    document.getElementById("clickCount").textContent = Math.min(clickCounter, 5);
  });

  captureBtn.addEventListener("click", startCapture);
}

function setupSortableHeaders() {
  document.querySelectorAll("#eventsTable th[data-sort]").forEach((th) => {
    th.style.cursor = "pointer";
    th.addEventListener("click", () => {
      const key = th.getAttribute("data-sort");
      tableState.asc = tableState.key === key ? !tableState.asc : true;
      tableState.key = key;
      refreshDashboard();
    });
  });
}

window.addEventListener("DOMContentLoaded", () => {
  const page = document.body.dataset.page;
  if (page === "dashboard") {
    initDashboardCharts();
    setupSortableHeaders();
    refreshDashboard();
    setInterval(refreshDashboard, 5000);
  }
  if (page === "registration") setupRegistration();
});
