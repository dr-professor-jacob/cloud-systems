// ── Browser / OS detection ──────────────────────────────────────────────────
function detectBrowser(ua) {
  if (/Edg\//.test(ua))        return "Microsoft Edge";
  if (/OPR\/|Opera/.test(ua))  return "Opera";
  if (/Firefox\//.test(ua))    return "Firefox";
  if (/Chrome\//.test(ua))     return "Chrome";
  if (/Safari\//.test(ua))     return "Safari";
  return "Unknown";
}
function detectOS(ua) {
  if (/Windows NT 10/.test(ua)) return "Windows 10/11";
  if (/Windows NT/.test(ua))    return "Windows";
  if (/Mac OS X/.test(ua))      return "macOS";
  if (/Android/.test(ua))       return "Android";
  if (/iPhone|iPad/.test(ua))   return "iOS";
  if (/Linux/.test(ua))         return "Linux";
  return "Unknown";
}

// ── Helper: set cell text or show "blocked" ─────────────────────────────────
function set(id, val, extraClass) {
  var el = document.getElementById(id);
  if (!el) return;
  if (val) {
    el.textContent = val;
    if (extraClass) el.className = extraClass;
  } else {
    el.innerHTML = "<span style=\"color:#bbb;font-style:italic;font-weight:400\">blocked</span>";
  }
}

// ── Live clock ──────────────────────────────────────────────────────────────
var pad = function(n) { return String(n).padStart(2, "0"); };
function updateClock() {
  var now = new Date();
  var utc = pad(now.getUTCHours()) + ":" + pad(now.getUTCMinutes()) + ":" + pad(now.getUTCSeconds());
  var loc = pad(now.getHours())    + ":" + pad(now.getMinutes())    + ":" + pad(now.getSeconds());
  var tz  = (Intl && Intl.DateTimeFormat) ? Intl.DateTimeFormat().resolvedOptions().timeZone : "local";
  var eu = document.getElementById("clock-utc");
  var el = document.getElementById("clock-local");
  if (eu) eu.textContent = "UTC " + utc;
  if (el) el.textContent = tz + " " + loc;
}
updateClock();
setInterval(updateClock, 1000);

// ── Visitor info ────────────────────────────────────────────────────────────
try {
  var ua = navigator.userAgent || "";
  set("v-browser", detectBrowser(ua));
  set("v-os",      detectOS(ua));
  set("v-lang",    navigator.language);
  set("v-screen",  (screen.width && screen.height) ? screen.width + " \xd7 " + screen.height : null);
  set("v-ua",      ua || null, "mono");

  var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  set("v-conn", conn
    ? ((conn.effectiveType ? conn.effectiveType.toUpperCase() : "") +
       (conn.downlink ? "  \u2022  " + conn.downlink + " Mbps" : ""))
    : "not reported");
} catch(e) {}

// ── Page load time (needs load event to be complete) ────────────────────────
window.addEventListener("load", function() {
  try {
    var t = performance && performance.timing;
    if (t && t.domContentLoadedEventEnd > t.navigationStart) {
      set("v-load", (t.domContentLoadedEventEnd - t.navigationStart) + " ms");
    }
  } catch(e) {}
});
