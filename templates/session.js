function detectBrowser(ua) {
  if (/Edg\//.test(ua))       return "Microsoft Edge";
  if (/OPR\/|Opera/.test(ua)) return "Opera";
  if (/Firefox\//.test(ua))   return "Firefox";
  if (/Chrome\//.test(ua))    return "Chrome";
  if (/Safari\//.test(ua))    return "Safari";
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

try {
  var ua = navigator.userAgent || "";
  var set = function(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val || "blocked";
  };
  set("v-browser", detectBrowser(ua));
  set("v-os",      detectOS(ua));
  set("v-lang",    navigator.language);
  set("v-screen",  screen.width && screen.height ? screen.width + " \xd7 " + screen.height : null);
  set("v-ua",      ua);
} catch(e) {}
