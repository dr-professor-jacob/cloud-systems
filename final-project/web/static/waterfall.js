/**
 * RF Survey Dashboard — Waterfall + Controls
 * Polls /api/waterfall every 5s, renders spectrum on Canvas.
 */

const POLL_INTERVAL = 3000;
const WATERFALL_ROWS = 120;   // history depth (rows)
const DB_MIN = -10;
const DB_MAX = 40;

// Band annotations — must match worker.py BANDS table
const BANDS = [
  { start: 87.5,   end: 108,    label: "FM",      color: "#4af" },
  { start: 108,    end: 137,    label: "AVIA",    color: "#a8f" },
  { start: 137,    end: 138,    label: "SAT",     color: "#5d5" },
  { start: 144,    end: 148,    label: "HAM",     color: "#fa5" },
  { start: 156,    end: 174,    label: "VHF",     color: "#5af" },
  { start: 162.4,  end: 162.55, label: "WX",      color: "#5d5" },
  { start: 433.05, end: 434.79, label: "ISM433",  color: "#ff5" },
  { start: 462,    end: 467,    label: "FRS",     color: "#fa5" },
  { start: 575,    end: 590,    label: "LTE41",   color: "#f55" },
  { start: 614,    end: 652,    label: "LTE71",   color: "#f55" },
  { start: 699,    end: 768,    label: "LTE12",   color: "#f55" },
  { start: 850,    end: 900,    label: "CELL",    color: "#f55" },
  { start: 902,    end: 928,    label: "ISM915",  color: "#ff5" },
  { start: 1089,   end: 1091,   label: "ADSB",   color: "#5ff" },
  { start: 1575,   end: 1576,   label: "GPS",     color: "#aff" },
  // Athens, OH ground-truth
  { start: 91.3,   end: 91.3,   label: "WOUB",    color: "#4af" },
  { start: 105.5,  end: 105.5,  label: "WXTQ",    color: "#4af" },
  { start: 146.625,end: 146.73, label: "W8UKE",   color: "#fa5" },
  { start: 162.425,end: 162.425,label: "KZZ46",   color: "#5d5" },
];

const DISPLAY_MAX_MHZ = 1150;  // crop display here — right side is empty above 1090 MHz

let freqStart    = 24;    // MHz
let freqEnd      = 1150;  // MHz — display end (capped at DISPLAY_MAX_MHZ)
let freqEndData  = 1700;  // MHz — full data range from Pi
let nBins        = 0;
let history      = [];    // circular buffer of Float32Arrays
let currentPeak    = null;
let currentMinHold = null;
let currentAvg     = null;
let currentRaw     = null;

const canvas      = document.getElementById("waterfall");
const ctx         = canvas.getContext("2d");
const bandCanvas  = document.getElementById("band-overlay");
const bandCtx     = bandCanvas.getContext("2d");
const statusEl    = document.getElementById("status");
const peakEl      = document.getElementById("peak-signal");

// ─── Color mapping ────────────────────────────────────────────────────────────
function dbmToColor(dbm) {
  const t = Math.max(0, Math.min(1, (dbm - DB_MIN) / (DB_MAX - DB_MIN)));
  // Viridis-inspired: dark purple → blue → green → yellow → white
  if (t < 0.2) {
    const s = t / 0.2;
    return [Math.floor(s * 60), 0, Math.floor(60 + s * 60)];
  } else if (t < 0.4) {
    const s = (t - 0.2) / 0.2;
    return [0, Math.floor(s * 120), Math.floor(120 + s * 80)];
  } else if (t < 0.6) {
    const s = (t - 0.4) / 0.2;
    return [0, Math.floor(120 + s * 80), Math.floor(200 - s * 100)];
  } else if (t < 0.8) {
    const s = (t - 0.6) / 0.2;
    return [Math.floor(s * 200), Math.floor(200 + s * 55), 0];
  } else {
    const s = (t - 0.8) / 0.2;
    return [200 + Math.floor(s * 55), 255, Math.floor(s * 255)];
  }
}

// ─── Frequency ↔ Canvas X mapping ────────────────────────────────────────────
function freqToX(freqMhz) {
  return ((freqMhz - freqStart) / (freqEnd - freqStart)) * canvas.width;
}

function xToFreq(x) {
  return freqStart + (x / canvas.width) * (freqEnd - freqStart);
}

function binToFreq(binIdx) {
  if (!nBins) return 0;
  return freqStart + (binIdx / nBins) * (freqEndData - freqStart);
}

// ─── Render one sweep row ──────────────────────────────────────────────────────
function renderRow(bins, y, imgData) {
  const w = canvas.width;
  const maxBin = freqEndData > freqStart
    ? Math.floor((freqEnd - freqStart) / (freqEndData - freqStart) * bins.length)
    : bins.length;
  for (let px = 0; px < w; px++) {
    const binIdx = Math.floor((px / w) * maxBin);
    const dbm    = bins[Math.min(binIdx, bins.length - 1)];
    const [r, g, b] = dbmToColor(dbm);
    const i = (y * w + px) * 4;
    imgData.data[i]     = r;
    imgData.data[i + 1] = g;
    imgData.data[i + 2] = b;
    imgData.data[i + 3] = 255;
  }
}

// ─── No-data placeholder ─────────────────────────────────────────────────────
function drawNoData() {
  const w = canvas.width, h = canvas.height;
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = "#333";
  ctx.font = "14px monospace";
  ctx.textAlign = "center";
  ctx.fillText("Waiting for Pi sweep data…", w / 2, h / 2);
  ctx.textAlign = "left";
  bandCtx.clearRect(0, 0, bandCanvas.width, bandCanvas.height);
}

// ─── Full waterfall redraw ────────────────────────────────────────────────────
function redrawWaterfall() {
  if (history.length === 0) { drawNoData(); return; }
  const h   = canvas.height;
  const w   = canvas.width;
  const img = ctx.createImageData(w, h);

  // Respect display mode: avg (history), peak hold, or min hold
  const mode = window.getDisplayMode ? window.getDisplayMode() : "avg";

  if (mode === "peak" && currentPeak) {
    for (let row = 0; row < h; row++) renderRow(currentPeak, row, img);
  } else if (mode === "min_hold" && currentMinHold) {
    for (let row = 0; row < h; row++) renderRow(currentMinHold, row, img);
  } else {
    // Rolling waterfall — newest row at top, tile to fill if not enough history yet
    for (let row = 0; row < h; row++) {
      const histIdx = history.length - 1 - (row % history.length);
      renderRow(history[histIdx], row, img);
    }
  }
  ctx.putImageData(img, 0, 0);
  drawBandLabels();  // overlay labels directly on waterfall canvas
}

// ─── Band annotation overlay ──────────────────────────────────────────────────
function drawBands() {
  bandCtx.clearRect(0, 0, bandCanvas.width, bandCanvas.height);
}

// ─── Band labels — drawn directly on the waterfall canvas ────────────────────
function drawBandLabels() {
  const BAR_H    = 22;
  const minWidthPx = 18;
  ctx.font = "bold 11px monospace";

  for (const b of BANDS) {
    const x1 = freqToX(b.start);
    const x2 = freqToX(b.end < b.start + 0.5 ? b.start + 0.5 : b.end);
    const w  = x2 - x1;

    // Tinted band stripe
    ctx.globalAlpha = 0.30;
    ctx.fillStyle = b.color;
    ctx.fillRect(x1, 0, Math.max(w, 2), BAR_H);
    ctx.globalAlpha = 1.0;

    // Label with dark pill background
    if (w >= minWidthPx) {
      ctx.save();
      ctx.beginPath();
      ctx.rect(x1, 0, w, BAR_H);
      ctx.clip();
      const tw = ctx.measureText(b.label).width;
      ctx.fillStyle = "rgba(0,0,0,0.82)";
      ctx.fillRect(x1 + 2, 4, tw + 6, 15);
      ctx.fillStyle = b.color;
      ctx.fillText(b.label, x1 + 5, 15);
      ctx.restore();
    } else {
      ctx.globalAlpha = 0.8;
      ctx.fillStyle = b.color;
      ctx.fillRect(x1, 0, Math.max(w, 1), BAR_H);
      ctx.globalAlpha = 1.0;
    }
  }
}

// ─── Frequency axis ───────────────────────────────────────────────────────────
function drawFreqAxis() {
  const axisCanvas = document.getElementById("freq-axis");
  if (!axisCanvas) return;
  const actx = axisCanvas.getContext("2d");
  actx.clearRect(0, 0, axisCanvas.width, axisCanvas.height);
  actx.fillStyle = "#888";
  actx.font = "10px monospace";

  const ticks = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700];
  for (const mhz of ticks) {
    const x = freqToX(mhz);
    actx.fillStyle = "#666";
    actx.fillRect(x, 0, 1, 4);
    actx.fillStyle = "#aaa";
    actx.fillText(`${mhz}`, x - 12, 14);
  }
}

// ─── Update peak signal display ───────────────────────────────────────────────
function updatePeakDisplay(peak) {
  if (!peak || peak.length === 0) return;
  let maxDbm = -999, maxIdx = 0;
  for (let i = 0; i < peak.length; i++) {
    if (peak[i] > maxDbm) { maxDbm = peak[i]; maxIdx = i; }
  }
  const freqMhz = binToFreq(maxIdx);

  // Find band
  let bandLabel = "unknown band";
  for (const band of BANDS) {
    if (freqMhz >= band.start && freqMhz <= band.end) { bandLabel = band.label; break; }
  }
  peakEl.textContent = `Peak: ${freqMhz.toFixed(2)} MHz  ${maxDbm.toFixed(1)} dBm  [${bandLabel}]`;
}

// ─── Fetch and update ─────────────────────────────────────────────────────────
async function fetchSweep() {
  try {
    const res  = await fetch("/api/waterfall");
    if (!res.ok) {
      statusEl.textContent = "Waiting for Pi sweep data...";
      return;
    }
    const data = await res.json();

    freqStart   = data.freq_start / 1e6;
    freqEndData = (data.freq_start + data.n_bins * data.freq_step) / 1e6;
    freqEnd     = Math.min(freqEndData, DISPLAY_MAX_MHZ);
    nBins       = data.n_bins;
    currentAvg     = data.avg;
    currentPeak    = data.peak;
    currentMinHold = data.min_hold;
    currentRaw     = data.raw && data.raw.length ? data.raw : null;

    // Push new row to history
    history.push(new Float32Array(data.avg));
    if (history.length > WATERFALL_ROWS) history.shift();

    redrawWaterfall();
    drawBands();
    drawBandLabels();
    drawFreqAxis();
    updatePeakDisplay(data.peak);
    drawSpectrumChart();
    autoLogActivity();

    const ts = new Date(data.ts).toLocaleTimeString();
    statusEl.textContent = `Live — last update ${ts} — ${nBins} bins`;

  } catch (e) {
    statusEl.textContent = `Error: ${e.message}`;
  }
}

// ─── Spectrum line chart ─────────────────────────────────────────────────────
function drawSpectrumChart() {
  const c = document.getElementById("spectrum-chart");
  if (!c) return;
  c.width = c.offsetWidth || c.parentElement.clientWidth;
  const w = c.width, h = c.height;
  const sctx = c.getContext("2d");
  sctx.fillStyle = "#000";
  sctx.fillRect(0, 0, w, h);

  if (!currentAvg || !nBins) return;

  const dbLo = DB_MIN, dbHi = DB_MAX;

  function drawLine(bins, color, alpha) {
    sctx.beginPath();
    sctx.strokeStyle = color;
    sctx.globalAlpha = alpha;
    sctx.lineWidth = 1;
    for (let px = 0; px < w; px++) {
      const binIdx = Math.min(Math.floor((px / w) * bins.length), bins.length - 1);
      const dbm = bins[binIdx];
      const y = h - ((dbm - dbLo) / (dbHi - dbLo)) * h;
      if (px === 0) sctx.moveTo(px, y);
      else sctx.lineTo(px, y);
    }
    sctx.stroke();
    sctx.globalAlpha = 1;
  }

  // Draw raw first (behind), then avg on top
  if (currentRaw) drawLine(currentRaw, "#666", 0.75);
  drawLine(currentAvg, "#4af", 1.0);

  // Y axis labels
  sctx.fillStyle = "#444";
  sctx.font = "9px monospace";
  sctx.fillText(`${dbHi}`, 2, 9);
  sctx.fillText(`${dbLo}`, 2, h - 2);
}



// ─── Activity Ledger ─────────────────────────────────────────────────────────
const activityLog = [];        // [{ts, freq, band, dbm}]
const seenFreqs   = new Map(); // freqMhz → last logged timestamp

function logActivity(freqMhz, dbm) {
  const el = document.getElementById("ledger");
  if (!el) return;
  let band = "—";
  for (const b of BANDS) if (freqMhz >= b.start && freqMhz <= b.end) { band = b.label; break; }
  const ts = new Date().toLocaleTimeString();
  activityLog.unshift({ ts, freqMhz: freqMhz.toFixed(2), band, dbm: dbm ? dbm.toFixed(1) : "—" });
  if (activityLog.length > 50) activityLog.pop();
  el.innerHTML = activityLog.map(e =>
    `<div style="display:flex;gap:8px;border-bottom:1px solid #111;padding:2px 0;">
      <span style="color:#444;flex:0 0 60px;">${e.ts}</span>
      <span style="color:#4af;flex:0 0 80px;">${e.freqMhz} MHz</span>
      <span style="color:#888;flex:1">${e.band}</span>
      <span style="color:#fa5;">${e.dbm} dBm</span>
    </div>`
  ).join("");
}

// Log strong peaks — deduplicated, only re-log after 5 minutes
function autoLogActivity() {
  if (!currentPeak || !nBins) return;
  const threshold  = 10;
  const dedupMs    = 5 * 60 * 1000;
  const now        = Date.now();
  let lastFreq = -999;
  for (let i = 1; i < nBins - 1; i++) {
    if (currentPeak[i] > threshold && currentPeak[i] > currentPeak[i-1] && currentPeak[i] > currentPeak[i+1]) {
      const freq = freqStart + (i / nBins) * (freqEndData - freqStart);
      if (freq - lastFreq > 1.0) {
        const key = freq.toFixed(0);
        if (!seenFreqs.has(key) || now - seenFreqs.get(key) > dedupMs) {
          seenFreqs.set(key, now);
          logActivity(freq, currentPeak[i]);
        }
        lastFreq = freq;
      }
    }
  }
}

// ─── Aircraft Radar ───────────────────────────────────────────────────────────
let acMap = null;
let acMarkers = [];

function initAircraftMap() {
  if (acMap || !document.getElementById("aircraft-map")) return;
  acMap = L.map("aircraft-map", {
    zoomControl: false,
    attributionControl: false,
    dragging: false,
    touchZoom: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    boxZoom: false,
    keyboard: false,
  }).setView([39.3292, -82.1013], 8);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 13,
    attribution: '© OpenStreetMap © CARTO'
  }).addTo(acMap);
  // Center on user's location if available
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(pos => {
      acMap.setView([pos.coords.latitude, pos.coords.longitude], 8);
    });
  }
}

function renderAircraftData(data) {
  initAircraftMap();
  const statusEl = document.getElementById("aircraft-status");
  const aircraft = data.aircraft || [];
  if (statusEl) statusEl.textContent = data.count
    ? `${data.count} aircraft tracked — ${aircraft.filter(a => a.lat).length} with position`
    : (data.message || "No aircraft");

  acMarkers.forEach(m => acMap.removeLayer(m));
  acMarkers = [];

  const planeIcon = L.divIcon({
    html: `<div style="color:#4af;font-size:18px;transform-origin:center;line-height:1">✈</div>`,
    className: "", iconSize: [20, 20], iconAnchor: [10, 10],
  });

  aircraft.forEach(ac => {
    if (!ac.lat || !ac.lon) return;
    const label = ac.flight || ac.hex || "???";
    const popup = `<b>${label}</b><br>
      ${ac.altitude ? `Alt: ${ac.altitude} ft<br>` : ""}
      ${ac.speed ? `Speed: ${ac.speed} kt<br>` : ""}
      ${ac.track ? `Track: ${ac.track}°` : ""}`;
    const icon = ac.track
      ? L.divIcon({ html: `<div style="color:#4af;font-size:18px;transform:rotate(${ac.track}deg);line-height:1">✈</div>`, className: "", iconSize: [20,20], iconAnchor: [10,10] })
      : planeIcon;
    const m = L.marker([ac.lat, ac.lon], { icon }).bindPopup(popup).addTo(acMap);
    acMarkers.push(m);
  });

  if (acMarkers.length > 0) {
    const group = L.featureGroup(acMarkers);
    acMap.fitBounds(group.getBounds().pad(0.2));
  }
}

function renderAircraft(jsonStr) {
  initAircraftMap();
  const statusEl = document.getElementById("aircraft-status");
  let data;
  try { data = JSON.parse(jsonStr); } catch(e) {
    if (statusEl) statusEl.textContent = jsonStr.slice(0, 120);
    return;
  }
  const aircraft = data.aircraft || [];
  if (statusEl) statusEl.textContent = data.count
    ? `${data.count} aircraft tracked — ${aircraft.filter(a => a.lat).length} with position`
    : (data.message || "No aircraft");

  // Clear old markers
  acMarkers.forEach(m => acMap.removeLayer(m));
  acMarkers = [];

  const planeIcon = L.divIcon({
    html: `<div style="color:#4af;font-size:18px;transform-origin:center;line-height:1">✈</div>`,
    className: "", iconSize: [20, 20], iconAnchor: [10, 10],
  });

  aircraft.forEach(ac => {
    if (!ac.lat || !ac.lon) return;
    const label = ac.flight || ac.hex || "???";
    const popup = `<b>${label}</b><br>
      ${ac.alt ? `Alt: ${ac.alt} ft<br>` : ""}
      ${ac.speed ? `Speed: ${ac.speed} kt<br>` : ""}
      ${ac.track ? `Track: ${ac.track}°` : ""}`;
    const icon = ac.track
      ? L.divIcon({ html: `<div style="color:#4af;font-size:18px;transform:rotate(${ac.track}deg);line-height:1">✈</div>`, className: "", iconSize: [20,20], iconAnchor: [10,10] })
      : planeIcon;
    const m = L.marker([ac.lat, ac.lon], { icon })
      .bindPopup(popup)
      .addTo(acMap);
    acMarkers.push(m);
  });

  if (acMarkers.length > 0) {
    const group = L.featureGroup(acMarkers);
    acMap.fitBounds(group.getBounds().pad(0.2));
  }
}

async function scanAdsb() {
  const statusEl = document.getElementById("aircraft-status");
  const btn = document.getElementById("btn-adsb");
  if (btn) { btn.disabled = true; btn.textContent = "Scanning…"; }
  if (statusEl) statusEl.textContent = "Running dump1090 for 30s — counting transponders…";
  initAircraftMap();

  try {
    const res = await fetch("/api/decode", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ freq_hz: 1090000000, tool: "dump1090", duration: 30 }),
    });
    const { job_id } = await res.json();
    let attempts = 0;
    const poller = setInterval(async () => {
      attempts++;
      const r = await fetch(`/api/results/${job_id}`);
      if (r.status === 200) {
        clearInterval(poller);
        const data = await r.json();
        renderAircraft(data.output);
        if (btn) { btn.disabled = false; btn.textContent = "▶ Scan 30s"; }
      } else if (attempts > 25) {
        clearInterval(poller);
        if (statusEl) statusEl.textContent = "Scan timed out.";
        if (btn) { btn.disabled = false; btn.textContent = "▶ Scan 30s"; }
      }
    }, 3000);
  } catch(e) {
    if (statusEl) statusEl.textContent = `Error: ${e.message}`;
    if (btn) { btn.disabled = false; btn.textContent = "▶ Scan 30s"; }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initAircraftMap();
  fetchIsm();
  fetchAdsb();
  fetchAnomalies();
  initHistory();
  setInterval(fetchIsm,       3 * 60 * 1000);
  setInterval(fetchAdsb,      3 * 60 * 1000);
  setInterval(fetchAnomalies, 30 * 1000);      // check for new anomalies every 30s
});

async function fetchIsm() {
  const statusEl = document.getElementById("ism-status");
  try {
    const res = await fetch("/api/ism");
    if (!res.ok) return;
    const data = await res.json();
    if (statusEl) {
      const age = data.ts ? Math.round((Date.now() - new Date(data.ts).getTime()) / 1000) : null;
      statusEl.textContent = data.message + (age != null ? ` — ${age}s ago` : "");
    }
    renderIsmPackets(data.packets || []);
  } catch(e) { /* silent */ }
}

async function fetchAdsb() {
  const statusEl = document.getElementById("aircraft-status");
  try {
    const res = await fetch("/api/adsb");
    if (!res.ok) return;
    const data = await res.json();
    if (statusEl) {
      const age = data.ts ? Math.round((Date.now() - new Date(data.ts).getTime()) / 1000) : null;
      statusEl.textContent = data.message + (age != null ? ` — ${age}s ago` : "");
    }
    renderAircraftData(data);
  } catch(e) { /* silent */ }
}

function renderIsmPackets(packets) {
  const feedEl = document.getElementById("ism-feed");
  if (!feedEl) return;

  if (!Array.isArray(packets) || packets.length === 0) return;

  feedEl.innerHTML = "";  // clear old entries

  const ts = new Date().toLocaleTimeString();
  packets.forEach(p => {
    const div = document.createElement("div");
    div.style.cssText = "border:1px solid #1a1a1a;border-radius:3px;padding:6px 8px;background:#0d0d0d;font-size:11px;";

    const model  = p.model  || p.type  || "Unknown device";
    const temp   = p.temperature_C != null ? `🌡 ${p.temperature_C}°C` :
                   p.temperature_F != null ? `🌡 ${((p.temperature_F-32)*5/9).toFixed(1)}°C` : "";
    const humid  = p.humidity != null  ? `💧 ${p.humidity}%` : "";
    const batt   = p.battery_ok != null ? (p.battery_ok ? "🔋 OK" : "🪫 Low") : "";
    const chan    = p.channel  != null  ? `ch${p.channel}` : "";
    const id     = p.id != null ? `id:${p.id}` : "";

    div.innerHTML = `
      <div style="color:#4af;margin-bottom:3px;">${escapeHtml(model)} <span style="color:#444;">${chan} ${id}</span></div>
      <div style="color:#afa;display:flex;gap:10px;flex-wrap:wrap;">
        ${temp} ${humid} ${batt}
        ${Object.entries(p).filter(([k]) => !["model","type","time","id","channel","temperature_C","temperature_F","humidity","battery_ok","mic","protocol","freq"].includes(k))
          .slice(0,3).map(([k,v]) => `<span style="color:#888">${k}:${v}</span>`).join(" ")}
      </div>
      <div style="color:#333;font-size:10px;margin-top:2px;">${ts}</div>`;
    feedEl.prepend(div);
  });
}

// ─── Antenna Advisor ─────────────────────────────────────────────────────────
const ANT_MIN_CM = 5;    // stock dipole element fully collapsed
const ANT_MAX_CM = 67;   // stock dipole element fully extended

function updateAntennaAdvisor(freqMhz) {
  const freqEl   = document.getElementById("antenna-freq");
  const recEl    = document.getElementById("antenna-rec");
  const warnEl   = document.getElementById("antenna-warn");
  const barEl    = document.getElementById("antenna-bar");
  const inchEl   = document.getElementById("antenna-inches");
  if (!freqEl) return;

  const lambda4_cm = 7500 / freqMhz;
  const lambda4_in = lambda4_cm / 2.54;
  const lambda2_cm = lambda4_cm * 2;

  freqEl.textContent = `${freqMhz.toFixed(2)} MHz  —  λ/4 = ${lambda4_cm.toFixed(1)} cm  (${lambda4_in.toFixed(1)}")`;

  let rec = "", warn = "", barPct = 0, color = "#4af";

  if (lambda4_cm <= ANT_MIN_CM) {
    // Fully collapse — still too long
    barPct = 0;
    color  = "#f55";
    rec    = `Collapse fully (${ANT_MIN_CM} cm / ${(ANT_MIN_CM/2.54).toFixed(1)}")`;
    warn   = `⚠ Stock antenna too long for ${freqMhz.toFixed(0)} MHz — even collapsed it's ${(ANT_MIN_CM/lambda4_cm).toFixed(1)}× too long`;
  } else if (lambda4_cm > ANT_MAX_CM) {
    // Extend fully — still too short
    barPct = 100;
    color  = "#fa5";
    rec    = `Extend fully (${ANT_MAX_CM} cm / ${(ANT_MAX_CM/2.54).toFixed(1)}")`;
    warn   = `⚠ Stock antenna too short for ${freqMhz.toFixed(0)} MHz — even at max it's ${(lambda4_cm/ANT_MAX_CM).toFixed(1)}× too short`;
  } else {
    barPct = ((lambda4_cm - ANT_MIN_CM) / (ANT_MAX_CM - ANT_MIN_CM)) * 100;
    color  = "#4af";
    rec    = `Set each element to  ${lambda4_cm.toFixed(1)} cm  (${lambda4_in.toFixed(1)}")`;
    warn   = "";
  }

  recEl.innerHTML   = `<b>Each element:</b> ${rec}<br><span style="color:#666">Half-wave total: ${lambda2_cm.toFixed(1)} cm (${(lambda2_cm/2.54).toFixed(1)}")</span>`;
  warnEl.textContent = warn;
  barEl.style.width  = `${barPct}%`;
  barEl.style.background = color;
  inchEl.textContent = lambda4_cm >= ANT_MIN_CM && lambda4_cm <= ANT_MAX_CM
    ? `✓ Within stock range`
    : `✗ Outside stock range`;
  inchEl.style.color = lambda4_cm >= ANT_MIN_CM && lambda4_cm <= ANT_MAX_CM ? "#4a4" : "#a44";
}

function escapeHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// ─── Resize canvases to container width ───────────────────────────────────────
function resizeCanvases() {
  const container = document.getElementById("waterfall-container");
  const w = container.clientWidth;
  canvas.width      = w;
  bandCanvas.width  = w;
  const axisCanvas  = document.getElementById("freq-axis");
  if (axisCanvas) axisCanvas.width = w;
  const specChart   = document.getElementById("spectrum-chart");
  if (specChart) specChart.width = w;
  const labelsCanvas = document.getElementById("band-labels");
  if (labelsCanvas) labelsCanvas.width = w;
  drawBands();
  drawBandLabels();
  drawFreqAxis();
  redrawWaterfall();
  drawSpectrumChart();
}

window.addEventListener("resize", resizeCanvases);
resizeCanvases();
drawNoData();

// ─── Cloud Pipeline panel ────────────────────────────────────────────────────
async function fetchPipeline() {
  try {
    const res = await fetch("/api/pipeline");
    if (!res.ok) return;
    const d = await res.json();

    const workerEl  = document.getElementById("pipe-worker");
    const workerVal = document.getElementById("pipe-worker-val");
    const blobVal   = document.getElementById("pipe-blob-val");
    const noiseEl   = document.getElementById("pipeline-noise");

    if (workerVal) {
      workerVal.textContent = `${d.sweep_count} sweeps · ${Math.floor(d.uptime_s / 60)}m uptime`;
      if (workerEl) {
        const age = d.last_sweep_ts
          ? (Date.now() - new Date(d.last_sweep_ts).getTime()) / 1000
          : 999;
        workerEl.className = "pipe-node " + (age < 60 ? "active" : "idle");
      }
    }

    if (blobVal) {
      const age = d.last_sweep_ts
        ? Math.round((Date.now() - new Date(d.last_sweep_ts).getTime()) / 1000)
        : null;
      blobVal.textContent = age != null ? `last write ${age}s ago` : "—";
    }

    if (noiseEl && d.noise_reduction_db != null) {
      noiseEl.textContent = `noise floor ↓${d.noise_reduction_db} dB`;
    }
  } catch(e) { /* silent */ }
}

fetchPipeline();
setInterval(fetchPipeline, 10000);

// ─── Start polling ────────────────────────────────────────────────────────────
fetchSweep();
setInterval(fetchSweep, POLL_INTERVAL);

// ─── Signal Anomalies ─────────────────────────────────────────────────────────
async function fetchAnomalies() {
  const statusEl = document.getElementById("anomaly-status");
  const feedEl   = document.getElementById("anomaly-feed");
  try {
    const res = await fetch("/api/anomalies");
    if (!res.ok) { if (statusEl) statusEl.textContent = "Building baseline…"; return; }
    const items = await res.json();
    if (!items || items.length === 0) {
      if (statusEl) statusEl.textContent = "No anomalies detected yet — baseline accumulating";
      return;
    }
    if (statusEl) statusEl.textContent = `${items.length} anomal${items.length === 1 ? "y" : "ies"} detected`;
    if (!feedEl) return;
    feedEl.innerHTML = items.slice(0, 8).map(a => {
      const ts  = a.ts ? new Date(a.ts).toLocaleTimeString() : "";
      const cls = a.classification ? `<div style="color:#afa;font-size:10px;margin-top:2px;">${escapeHtml(a.classification)}</div>` : "";
      return `<div style="border:1px solid #1a1a1a;border-radius:3px;padding:6px 10px;background:#0d0d0d;">
        <div style="display:flex;gap:10px;align-items:baseline;">
          <span style="color:#ff5;font-size:12px;font-weight:bold;">${a.freq_mhz} MHz</span>
          <span style="color:#fa5;font-size:11px;">+${a.excess_db} dB above baseline</span>
          <span style="color:#f55;font-size:11px;">${a.power_dbm} dBm</span>
          <span style="color:#555;font-size:10px;margin-left:auto;">${a.band}</span>
          <span style="color:#333;font-size:10px;">${ts}</span>
        </div>
        ${cls}
      </div>`;
    }).join("");
  } catch(e) { /* silent */ }
}

// ─── History Player ───────────────────────────────────────────────────────────
let historySnapshots = [];
let historyIndex     = -1;   // -1 = live
let isLiveMode       = true;

async function initHistory() {
  try {
    const res = await fetch("/api/history");
    if (!res.ok) return;
    const data = await res.json();
    historySnapshots = data.snapshots || [];
    const rangeEl = document.getElementById("history-range");
    if (rangeEl && historySnapshots.length > 0)
      rangeEl.textContent = `${historySnapshots.length} snapshots today`;
  } catch(e) {}

  document.getElementById("btn-live")?.addEventListener("click", () => {
    isLiveMode   = true;
    historyIndex = -1;
    document.getElementById("history-ts").textContent = "● Live";
    document.getElementById("btn-live").style.color = "#4af";
  });

  document.getElementById("btn-history-prev")?.addEventListener("click", () => stepHistory(1));
  document.getElementById("btn-history-next")?.addEventListener("click", () => stepHistory(-1));
}

async function stepHistory(dir) {
  // Refresh snapshot list first
  try {
    const res = await fetch("/api/history");
    if (res.ok) { const d = await res.json(); historySnapshots = d.snapshots || []; }
  } catch(e) {}

  if (historySnapshots.length === 0) return;

  if (isLiveMode) {
    historyIndex = 0;
    isLiveMode   = false;
  } else {
    historyIndex = Math.max(0, Math.min(historySnapshots.length - 1, historyIndex + dir));
  }

  const snap = historySnapshots[historyIndex];
  document.getElementById("btn-live").style.color = "#555";

  // Extract timestamp from path: "2026-04-20/2026-04-20T18:45:21.123456+00:00.json"
  const parts = snap.split("/");
  const tsRaw = parts[parts.length - 1].replace(".json", "");
  try {
    document.getElementById("history-ts").textContent =
      new Date(tsRaw).toLocaleTimeString() + " (archived)";
  } catch(e) {
    document.getElementById("history-ts").textContent = tsRaw;
  }

  try {
    const r = await fetch(`/api/history/${snap}`);
    if (!r.ok) return;
    const data = await r.json();
    // Load into waterfall without affecting live state
    freqStart   = data.freq_start / 1e6;
    freqEndData = (data.freq_start + data.n_bins * data.freq_step) / 1e6;
    freqEnd     = Math.min(freqEndData, DISPLAY_MAX_MHZ);
    nBins       = data.n_bins;
    currentAvg     = data.avg;
    currentPeak    = data.peak;
    currentMinHold = data.min_hold;
    currentRaw     = data.raw || null;
    history.length = 0;
    history.push(new Float32Array(data.avg));
    redrawWaterfall();
    drawFreqAxis();
    drawSpectrumChart();
    updatePeakDisplay(data.peak);
  } catch(e) { /* silent */ }
}
