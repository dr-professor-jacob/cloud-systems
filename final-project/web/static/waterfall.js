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
let viewRows         = 120;   // how many history rows to display (zoom control)
let locationReset    = false; // true after New Location — don't restore old peak/min from history
let lastSweepSig = null;  // fingerprint of last avg array (detects real Pi data change)
let sweepFrozen      = false; // true when fingerprint unchanged (controls row pushing)
let piOnline         = false; // true when last_pi_sweep_ts < 120s (drives overlay)
let lastLiveSweepTime = "";   // human-readable time of last real Pi sweep
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

  // All modes: only fill as many rows as we have history for
  const pxPerRow   = Math.max(1, Math.floor(h / viewRows));
  const rowsToShow = Math.min(history.length, viewRows);
  const fillHeight = rowsToShow * pxPerRow;

  if (mode === "peak" && currentPeak) {
    for (let row = 0; row < fillHeight; row++) renderRow(currentPeak, row, img);
  } else if (mode === "min_hold" && currentMinHold) {
    for (let row = 0; row < fillHeight; row++) renderRow(currentMinHold, row, img);
  } else {
    // Rolling waterfall — newest at top
    for (let row = 0; row < fillHeight; row++) {
      const histSlot = Math.floor(row / pxPerRow);
      const histIdx  = history.length - 1 - histSlot;
      if (histIdx >= 0) renderRow(history[histIdx], row, img);
    }
  }
  ctx.putImageData(img, 0, 0);
  drawBandLabels();  // tinted band stripes on waterfall

  // Frozen overlay — dim the waterfall when Pi is offline (driven by pipeline data, not fingerprint)
  if (!piOnline && isLiveMode) {
    ctx.globalAlpha = 0.55;
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, w, h);
    ctx.globalAlpha = 1.0;
    ctx.fillStyle = "#f55";
    ctx.font = "bold 13px monospace";
    ctx.textAlign = "center";
    ctx.fillText("PI OFFLINE — WATERFALL FROZEN", w / 2, h / 2 - 8);
    ctx.fillStyle = "#555";
    ctx.font = "11px monospace";
    ctx.fillText("last live sweep: " + (lastLiveSweepTime || "unknown"), w / 2, h / 2 + 12);
    ctx.textAlign = "left";
  }
}

// ─── Band annotation overlay ──────────────────────────────────────────────────
function drawBands() {
  bandCtx.clearRect(0, 0, bandCanvas.width, bandCanvas.height);
}

// ─── Band stripes — none on waterfall, labels handled by strip below ─────────
function drawBandLabels() { /* no-op — see drawBandLabelStrip */ }

// ─── Band label strip — removed; hover tooltip handles band identification ────
function drawBandLabelStrip() { /* no-op */ }

// ─── Hover tooltip — freq + band name ────────────────────────────────────────
function xToFreqMhz(x, canvasWidth) {
  return freqStart + (x / canvasWidth) * (freqEnd - freqStart);
}

function bandAtFreq(mhz) {
  // prefer longer label (specific over general) when overlapping
  let best = null;
  for (const b of BANDS) {
    const lo = b.start;
    const hi = b.end < b.start + 0.5 ? b.start + 1.0 : b.end;
    if (mhz >= lo && mhz <= hi) {
      if (!best || (hi - lo) < (best.hi - best.lo)) best = { ...b, hi };
    }
  }
  return best;
}

(function setupHoverTooltip() {
  // Create tooltip element once
  const tip = document.createElement("div");
  tip.id = "freq-tooltip";
  tip.style.cssText = [
    "position:fixed",
    "padding:4px 8px",
    "background:#111",
    "border:1px solid #333",
    "border-radius:3px",
    "color:#d0d0d0",
    "font:11px 'Courier New',monospace",
    "pointer-events:none",
    "display:none",
    "z-index:999",
    "white-space:nowrap",
  ].join(";");
  document.body.appendChild(tip);

  function onMove(e) {
    const rect = e.currentTarget.getBoundingClientRect();
    const x    = e.clientX - rect.left;
    const mhz  = xToFreqMhz(x, rect.width);
    const band = bandAtFreq(mhz);

    tip.textContent = band
      ? `${mhz.toFixed(1)} MHz — ${band.label}`
      : `${mhz.toFixed(1)} MHz`;
    tip.style.display = "block";
    // keep tooltip from clipping off right edge
    const tx = Math.min(e.clientX + 12, window.innerWidth - tip.offsetWidth - 8);
    tip.style.left = tx + "px";
    tip.style.top  = (e.clientY - 28) + "px";
  }

  function onLeave() { tip.style.display = "none"; }

  // Attach to waterfall, spectrum chart, freq axes, and band strip
  const targets = ["waterfall","spectrum-chart","freq-axis","freq-axis-top"];
  targets.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("mousemove", onMove);
      el.addEventListener("mouseleave", onLeave);
    }
  });
})();

// ─── Frequency axis ───────────────────────────────────────────────────────────
function _drawAxisOn(c, ticksUp) {
  if (!c) return;
  const actx = c.getContext("2d");
  const h = c.height;
  actx.clearRect(0, 0, c.width, h);
  actx.font = "10px monospace";
  const ticks = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100];
  for (const mhz of ticks) {
    const x = freqToX(mhz);
    actx.fillStyle = "#555";
    actx.fillRect(x, ticksUp ? h - 4 : 0, 1, 4);
    actx.fillStyle = "#aaa";
    actx.fillText(`${mhz}`, x - 12, ticksUp ? h - 6 : 14);
  }
}

function drawFreqAxis() {
  _drawAxisOn(document.getElementById("freq-axis"),     false);
  _drawAxisOn(document.getElementById("freq-axis-top"), true);
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
  // Don't overwrite historical playback
  if (!isLiveMode) return;

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
    // After New Location, keep peak/min null until fresh Pi data arrives
    currentPeak    = locationReset ? null : data.peak;
    currentMinHold = locationReset ? null : data.min_hold;
    currentRaw     = data.raw && data.raw.length ? data.raw : null;

    // Fingerprint the avg array using a few spread samples
    // Worker writes identical data every 30s when Pi is off — detect that
    const avg = data.avg || [];
    const sig = avg.length
      ? [avg[0], avg[Math.floor(avg.length * 0.25)],
         avg[Math.floor(avg.length * 0.5)],
         avg[Math.floor(avg.length * 0.75)], avg[avg.length - 1]].join(',')
      : '';

    const isNewSweep = sig !== lastSweepSig;
    sweepFrozen = !isNewSweep;
    if (isNewSweep && locationReset) locationReset = false; // fresh data arrived
    if (isNewSweep) {
      lastSweepSig = sig;
      lastLiveSweepTime = new Date(data.ts).toLocaleTimeString();
      history.push(new Float32Array(data.avg));
      if (history.length > WATERFALL_ROWS) history.shift();
    }

    redrawWaterfall();
    drawBands();
    drawBandLabels();
    drawBandLabelStrip();
    drawFreqAxis();
    updatePeakDisplay(data.peak);
    drawSpectrumChart();
    if (isNewSweep) autoLogActivity();

    const ts = new Date(data.ts).toLocaleTimeString();
    statusEl.textContent = piOnline
      ? `Live — last update ${ts} — ${nBins} bins`
      : `Frozen — Pi offline — last sweep ${ts} — ${nBins} bins`;

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
    const data = await res.json();
    if (!res.ok) {
      if (statusEl) statusEl.textContent = data.message || "No ISM scan yet — waiting for Pi scanner";
      return;
    }
    if (statusEl) {
      const age = data.ts ? (Date.now() - new Date(data.ts).getTime()) / 1000 : null;
      statusEl.textContent = data.message + (age != null ? ` — ${humanAge(age)} ago` : "");
    }
    renderIsmPackets(data.packets || []);
  } catch(e) { if (statusEl) statusEl.textContent = "ISM data unavailable"; }
}

async function fetchAdsb() {
  const statusEl = document.getElementById("aircraft-status");
  try {
    const res = await fetch("/api/adsb");
    const data = await res.json();
    if (!res.ok) {
      if (statusEl) statusEl.textContent = data.message || "No ADS-B scan yet — waiting for Pi scanner";
      return;
    }
    if (statusEl) {
      const age = data.ts ? (Date.now() - new Date(data.ts).getTime()) / 1000 : null;
      statusEl.textContent = data.message + (age != null ? ` — ${humanAge(age)} ago` : "");
    }
    renderAircraftData(data);
  } catch(e) { if (statusEl) statusEl.textContent = "ADS-B data unavailable"; }
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
  const freqTop = document.getElementById("freq-axis-top");
  if (freqTop) freqTop.width = w;
  drawBands();
  drawBandLabels();
  drawBandLabelStrip();
  drawFreqAxis();
  redrawWaterfall();
  drawSpectrumChart();
}

window.addEventListener("resize", resizeCanvases);
resizeCanvases();
drawNoData();

// ─── Helpers ─────────────────────────────────────────────────────────────────
function humanAge(s) {
  if (s < 120)    return `${Math.round(s)}s`;
  if (s < 3600)   return `${Math.round(s / 60)}m`;
  return `${Math.round(s / 3600)}h`;
}

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

    // Pi connectivity — use last_pi_sweep_ts (only updated when Pi sends data)
    const piEl  = document.getElementById("pipe-pi");
    const piVal = document.getElementById("pipe-pi-val");
    const piAge = d.last_pi_sweep_ts
      ? (Date.now() - new Date(d.last_pi_sweep_ts).getTime()) / 1000
      : 9999;
    const piOffline = piAge > 240;  // scanner holds device ~55s + sweep ~70s = up to 125s gap
    piOnline = !piOffline;
    if (piEl)  piEl.className  = "pipe-node " + (piOffline ? "offline" : "active");
    if (piVal) piVal.textContent = piOffline
      ? `OFFLINE — ${humanAge(piAge)} ago`
      : "sweep every ~15s";

    if (workerVal) {
      const uptime = d.uptime_s < 3600
        ? `${Math.floor(d.uptime_s / 60)}m`
        : `${(d.uptime_s / 3600).toFixed(1)}h`;
      workerVal.textContent = `${d.sweep_count} sweeps · ${uptime} uptime`;
      if (workerEl) {
        const age = d.last_pi_sweep_ts
          ? (Date.now() - new Date(d.last_pi_sweep_ts).getTime()) / 1000
          : 999;
        workerEl.className = "pipe-node " + (age < 60 ? "active" : "idle");
      }
    }

    if (blobVal) {
      blobVal.textContent = piOffline
        ? `Pi offline — ${humanAge(piAge)} since last sweep`
        : d.last_pi_sweep_ts
          ? `last sweep ${humanAge(piAge)} ago`
          : "—";
    }

    if (noiseEl && d.noise_reduction_db != null) {
      noiseEl.textContent = `noise floor ↓${d.noise_reduction_db} dB`;
    }
  } catch(e) { /* silent */ }
}

fetchPipeline();
setInterval(fetchPipeline, 10000);

// fetchSweep started inside initHistory() after prefill completes

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
          <span style="color:#f55;font-size:11px;">${a.power_dbm} dBm</span>
          <span style="color:#888;font-size:11px;">baseline ${(a.power_dbm - a.excess_db).toFixed(1)} dBm</span>
          <span style="color:#fa5;font-size:11px;">+${a.excess_db} dB</span>
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

function snapIndexToLabel(idx) {
  // idx: 0=oldest … max=newest (slider value)
  // historySnapshots is sorted newest-first, so map idx → snapshots[length-1-idx]
  const snap = historySnapshots[historySnapshots.length - 1 - idx];
  if (!snap) return "—";
  const tsRaw = snap.split("/").pop().replace(".json", "");
  try {
    return new Date(tsRaw).toLocaleTimeString();
  } catch(e) { return tsRaw.slice(0, 19); }
}

async function refreshHistoryList() {
  try {
    const res = await fetch("/api/history");
    if (!res.ok) return;
    const data = await res.json();
    const prevCount  = historySnapshots.length;
    historySnapshots = data.snapshots || [];
    const slider  = document.getElementById("history-slider");
    const rangeEl = document.getElementById("history-range");
    if (rangeEl) rangeEl.textContent = historySnapshots.length
      ? `${historySnapshots.length} snapshots`
      : "No snapshots yet";
    if (slider) {
      slider.max = Math.max(0, historySnapshots.length - 1);
      slider.disabled = historySnapshots.length === 0;
      if (isLiveMode) slider.value = slider.max;
    }
    // Append only genuinely new snapshots — never wipe history
    if (isLiveMode && !locationReset && prevCount > 0 && historySnapshots.length > prevCount) {
      const newSnaps = historySnapshots.slice(0, historySnapshots.length - prevCount).reverse();
      for (const snap of newSnaps) {
        try {
          const r = await fetch(`/api/history/${snap}`);
          if (!r.ok) continue;
          const d = await r.json();
          history.push(new Float32Array(d.avg));
          if (history.length > WATERFALL_ROWS) history.shift();
        } catch(e) {}
      }
      if (newSnaps.length) { redrawWaterfall(); drawFreqAxis(); drawSpectrumChart(); }
    }
  } catch(e) {}
}

async function loadHistorySnapshot(idx) {
  const snap  = historySnapshots[historySnapshots.length - 1 - idx];
  const tsEl  = document.getElementById("history-ts");
  if (!snap) return;
  tsEl.textContent = snapIndexToLabel(idx) + " — loading…";
  try {
    const r = await fetch(`/api/history/${snap}`);
    if (!r.ok) { tsEl.textContent = snapIndexToLabel(idx) + " (load failed)"; return; }
    const data = await r.json();
    freqStart      = data.freq_start / 1e6;
    freqEndData    = (data.freq_start + data.n_bins * data.freq_step) / 1e6;
    freqEnd        = Math.min(freqEndData, DISPLAY_MAX_MHZ);
    nBins          = data.n_bins;
    currentAvg     = data.avg;
    currentPeak    = data.peak;
    currentMinHold = data.min_hold;
    currentRaw     = data.raw || null;
    history.length = 0;
    history.push(new Float32Array(data.avg));
    redrawWaterfall();
    drawBandLabelStrip();
    drawFreqAxis();
    drawSpectrumChart();
    updatePeakDisplay(data.peak);
    tsEl.textContent = snapIndexToLabel(idx);
  } catch(e) { tsEl.textContent = snapIndexToLabel(idx) + " (error)"; }
}

async function prefillFromHistory() {
  if (historySnapshots.length === 0) return;
  // Fetch up to WATERFALL_ROWS snapshots — newest-first list, so reverse for oldest-first push
  const toFetch = historySnapshots.slice(0, WATERFALL_ROWS).reverse();
  try {
    const results = await Promise.all(
      toFetch.map(snap => fetch(`/api/history/${snap}`).then(r => r.ok ? r.json() : null))
    );
    history.length = 0;
    for (const data of results) {
      if (!data) continue;
      if (!nBins) {
        freqStart   = data.freq_start / 1e6;
        freqEndData = (data.freq_start + data.n_bins * data.freq_step) / 1e6;
        freqEnd     = Math.min(freqEndData, DISPLAY_MAX_MHZ);
        nBins       = data.n_bins;
      }
      history.push(new Float32Array(data.avg));
    }
    // Seed peak/min/avg from most recent snapshot — skip stale peak/min after reset
    const latest = results[results.length - 1];
    if (latest) {
      currentAvg     = latest.avg;
      currentPeak    = locationReset ? null : latest.peak;
      currentMinHold = locationReset ? null : latest.min_hold;
      currentRaw     = latest.raw || null;
      // Use same fingerprint as fetchSweep to prevent duplicate row on first poll
      const _a = latest.avg;
      lastSweepSig = _a.length ? [_a[0], _a[Math.floor(_a.length*0.25)],
        _a[Math.floor(_a.length*0.5)], _a[Math.floor(_a.length*0.75)], _a[_a.length-1]].join(',') : '';
      updatePeakDisplay(latest.peak);
    }
    redrawWaterfall();
    drawFreqAxis();
    drawSpectrumChart();
  } catch(e) { /* silent — live fetch will populate */ }
}

async function initHistory() {
  await refreshHistoryList();
  await prefillFromHistory();

  // Start live polling AFTER prefill — eliminates race condition
  fetchSweep();
  setInterval(fetchSweep, POLL_INTERVAL);

  const slider = document.getElementById("history-slider");
  const tsEl   = document.getElementById("history-ts");

  // Update label while dragging (no fetch)
  slider?.addEventListener("input", () => {
    const idx = parseInt(slider.value);
    tsEl.textContent = snapIndexToLabel(idx);
    isLiveMode = false;
    document.getElementById("btn-live").style.color = "#555";
  });

  // Load snapshot on release
  slider?.addEventListener("change", () => {
    const idx = parseInt(slider.value);
    isLiveMode = false;
    historyIndex = idx;
    loadHistorySnapshot(idx);
  });

  document.getElementById("btn-live")?.addEventListener("click", async () => {
    isLiveMode   = true;
    historyIndex = -1;
    if (slider) { slider.value = slider.max; }
    tsEl.textContent = "● Live";
    document.getElementById("btn-live").style.color = "#4af";
    await prefillFromHistory();   // restore full history buffer
    fetchSweep();
  });

  setInterval(refreshHistoryList, 30 * 1000);
}

// ─── Exposed helpers ──────────────────────────────────────────────────────────
window.clearWaterfallHistory = function() {
  history.length = 0;
  currentAvg = null; currentPeak = null; currentMinHold = null; currentRaw = null;
  lastSweepSig = null;
  locationReset = true;
  drawNoData();

  // Clear spectrum chart
  const sc = document.getElementById("spectrum-chart");
  if (sc) { const sctx = sc.getContext("2d"); sctx.clearRect(0, 0, sc.width, sc.height); }

  // Clear anomaly feed
  const af = document.getElementById("anomaly-feed");
  if (af) af.innerHTML = "";
  const as = document.getElementById("anomaly-status");
  if (as) as.textContent = "Waiting for baseline…";
};

window.setViewRows = function(n) {
  viewRows = n;
  redrawWaterfall();
};
