/**
 * RF Survey Dashboard — Waterfall + Controls
 * Polls /api/waterfall every 5s, renders spectrum on Canvas.
 */

const POLL_INTERVAL = 5000;
const WATERFALL_ROWS = 120;   // history depth (rows)
const DB_MIN = -60;
const DB_MAX = 30;

// Band annotations — must match worker.py BANDS table
const BANDS = [
  { start: 87.5,   end: 108,    label: "FM",           color: "#4af" },
  { start: 108,    end: 137,    label: "Aviation",     color: "#a8f" },
  { start: 137,    end: 138,    label: "NOAA Sat",     color: "#5d5" },
  { start: 144,    end: 148,    label: "Ham 2m",       color: "#fa5" },
  { start: 156,    end: 174,    label: "Marine VHF",   color: "#5af" },
  { start: 162.4,  end: 162.55, label: "Wx Radio",     color: "#5d5" },
  { start: 433.05, end: 434.79, label: "ISM 433",      color: "#ff5" },
  { start: 462,    end: 467,    label: "FRS/GMRS",     color: "#fa5" },
  { start: 850,    end: 900,    label: "Cellular",     color: "#f55" },
  { start: 902,    end: 928,    label: "ISM 915",      color: "#ff5" },
  { start: 1089,   end: 1091,   label: "ADS-B",        color: "#5ff" },
  { start: 1575,   end: 1576,   label: "GPS L1",       color: "#aff" },
  // Athens, OH ground-truth
  { start: 91.3,   end: 91.3,   label: "WOUB-FM",      color: "#4af" },
  { start: 105.5,  end: 105.5,  label: "WXTQ",         color: "#4af" },
  { start: 146.625,end: 146.73, label: "W8UKE",        color: "#fa5" },
  { start: 162.425,end: 162.425,label: "NOAA KZZ46",   color: "#5d5" },
];

let freqStart    = 24;    // MHz
let freqEnd      = 1700;  // MHz
let nBins        = 0;
let history      = [];    // circular buffer of Float32Arrays
let currentPeak    = null;
let currentMinHold = null;
let currentAvg     = null;

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
  return freqStart + (binIdx / nBins) * (freqEnd - freqStart);
}

// ─── Render one sweep row ──────────────────────────────────────────────────────
function renderRow(bins, y, imgData) {
  const w = canvas.width;
  for (let px = 0; px < w; px++) {
    const binIdx = Math.floor((px / w) * bins.length);
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
}

// ─── Band annotation overlay ──────────────────────────────────────────────────
function drawBands() {
  const w = bandCanvas.width;
  const h = bandCanvas.height;
  bandCtx.clearRect(0, 0, w, h);
  bandCtx.font = "10px monospace";

  for (const band of BANDS) {
    const x1 = freqToX(band.start);
    const x2 = freqToX(band.end);
    const bw  = Math.max(x2 - x1, 2);

    // Colored bar at bottom
    bandCtx.fillStyle = band.color + "55";  // semi-transparent
    bandCtx.fillRect(x1, h - 18, bw, 18);
    bandCtx.fillStyle = band.color;
    bandCtx.fillRect(x1, h - 2, bw, 2);

    // Label if wide enough
    if (bw > 20) {
      bandCtx.fillStyle = "#fff";
      bandCtx.fillText(band.label, x1 + 2, h - 5);
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

    freqStart = data.freq_start / 1e6;
    freqEnd   = (data.freq_start + data.n_bins * data.freq_step) / 1e6;
    nBins     = data.n_bins;
    currentAvg     = data.avg;
    currentPeak    = data.peak;
    currentMinHold = data.min_hold;

    // Push new row to history
    history.push(new Float32Array(data.avg));
    if (history.length > WATERFALL_ROWS) history.shift();

    redrawWaterfall();
    drawBands();
    drawFreqAxis();
    updatePeakDisplay(data.peak);

    const ts = new Date(data.ts).toLocaleTimeString();
    statusEl.textContent = `Live — last update ${ts} — ${nBins} bins`;
  } catch (e) {
    statusEl.textContent = `Error: ${e.message}`;
  }
}

// ─── Click to decode ──────────────────────────────────────────────────────────
canvas.addEventListener("click", async (e) => {
  const rect    = canvas.getBoundingClientRect();
  const x       = e.clientX - rect.left;
  const freqMhz = xToFreq(x * canvas.width / rect.width);
  const freqHz  = Math.round(freqMhz * 1e6);

  // Auto-select best tool
  let tool = "rtl_power_scan";
  if (freqMhz >= 430 && freqMhz <= 436) tool = "rtl_433";
  if (freqMhz >= 910 && freqMhz <= 920) tool = "rtl_433";
  if (freqMhz >= 1088 && freqMhz <= 1092) tool = "dump1090";

  const resultsEl = document.getElementById("results");
  resultsEl.innerHTML = `<p class="pending">⏳ Dispatching ${tool} on ${freqMhz.toFixed(3)} MHz — waiting up to 35s for Pi…</p>`;
  document.getElementById("results-panel").scrollIntoView({ behavior: "smooth" });

  try {
    const res = await fetch("/api/decode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ freq_hz: freqHz, tool, duration: 30 }),
    });
    const { job_id } = await res.json();

    // Poll for result
    let attempts = 0;
    const poller = setInterval(async () => {
      attempts++;
      const r = await fetch(`/api/results/${job_id}`);
      if (r.status === 200) {
        clearInterval(poller);
        const data = await r.json();
        resultsEl.innerHTML = `
          <div class="result">
            <div class="result-meta">${tool} @ ${freqMhz.toFixed(3)} MHz — ${new Date(data.ts).toLocaleTimeString()}</div>
            <pre>${escapeHtml(data.output)}</pre>
          </div>`;
      } else if (attempts > 12) {
        clearInterval(poller);
        resultsEl.innerHTML = `<p class="error">Timed out waiting for Pi result.</p>`;
      }
    }, 3000);
  } catch (err) {
    resultsEl.innerHTML = `<p class="error">Dispatch error: ${err.message}</p>`;
  }
});

// ─── Ask Claude ───────────────────────────────────────────────────────────────
document.getElementById("ask-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input   = document.getElementById("ask-input");
  const output  = document.getElementById("ask-output");
  const question = input.value.trim();
  if (!question) return;

  output.textContent = "Thinking…";
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    if (res.ok) {
      output.textContent = data.answer;
      document.getElementById("ask-remaining").textContent = `${data.remaining} questions remaining today`;
    } else {
      output.textContent = data.detail || "Error";
    }
  } catch (err) {
    output.textContent = `Error: ${err.message}`;
  }
});

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
  drawBands();
  drawFreqAxis();
  redrawWaterfall();
}

window.addEventListener("resize", resizeCanvases);
resizeCanvases();
drawNoData();

// ─── Start polling ────────────────────────────────────────────────────────────
fetchSweep();
setInterval(fetchSweep, POLL_INTERVAL);
