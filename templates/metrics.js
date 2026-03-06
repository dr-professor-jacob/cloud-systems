function loadMetrics() {
  fetch('/metrics.json?t=' + Date.now())
    .then(function(r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function(d) {
      document.getElementById('m-load').textContent     = d.load ? d.load.split(' ')[0] : '--';
      document.getElementById('m-mem').textContent      = d.mem_used || '--';
      document.getElementById('m-disk').textContent     = d.disk_pct ? d.disk_pct.replace(/%/g,'') + '%' : '--';
      document.getElementById('m-uptime').textContent   = d.uptime || '--';
      document.getElementById('m-loadfull').textContent = d.load || '--';
      document.getElementById('m-memfull').textContent  = (d.mem_used && d.mem_total) ? d.mem_used + ' / ' + d.mem_total : '--';
      document.getElementById('m-diskfull').textContent = (d.disk_used && d.disk_total) ? d.disk_used + ' / ' + d.disk_total + ' (' + d.disk_pct.replace(/%/g,'') + '%)' : '--';
      document.getElementById('m-nginx').textContent    = d.nginx_connections || '--';
      if (d.updated) {
        var dt = new Date(d.updated);
        document.getElementById('m-updated').textContent = dt.toUTCString();
        var age = Math.round((Date.now() - dt.getTime()) / 1000);
        document.getElementById('metrics-age').textContent = age < 120 ? age + 's ago' : Math.round(age / 60) + 'm ago';
      }
      document.getElementById('metrics-note').style.display = 'none';
    })
    .catch(function() {
      var note = document.getElementById('metrics-note');
      note.style.display = '';
      note.textContent = 'Metrics not yet available.';
    });
}
loadMetrics();
setInterval(loadMetrics, 30000);

function timeAgo(iso) {
  var age = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (age < 60) return age + 's ago';
  if (age < 3600) return Math.round(age / 60) + 'm ago';
  return Math.round(age / 3600) + 'h ago';
}

function loadActivity() {
  fetch('/activity.json?t=' + Date.now())
    .then(function(r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function(d) {
      var feed = document.getElementById('activity-feed');
      var calls = d.calls;
      if (!calls || !calls.length || typeof calls[0] !== 'object') {
        feed.innerHTML = '<p style="font-size:.82rem;color:#888;font-style:italic;">No activity yet.</p>';
        return;
      }
      var html = '';
      calls.forEach(function(c) {
        var tools = c.tools && c.tools.length ? c.tools.join(', ') : 'none';
        html += '<div style="border-bottom:1px solid #f2f2f2;padding:.65rem 0;">' +
          '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:.5rem;margin-bottom:.25rem;">' +
          '<span style="font-size:.78rem;color:#333;font-weight:500;">' + escHtml(c.question) + '</span>' +
          '<span style="font-size:.68rem;color:#aaa;white-space:nowrap;">' + timeAgo(c.time) + '</span>' +
          '</div>' +
          '<div style="font-size:.72rem;color:#706e6c;margin-bottom:.2rem;">tools: <code>' + escHtml(tools) + '</code></div>' +
          '<div style="font-size:.8rem;color:#444;line-height:1.5;">' + renderAnswer(c.answer || c.synopsis || '') + '</div>' +
          '</div>';
      });
      feed.innerHTML = html.replace(/<div style="border-bottom[^>]+>/, '<div style="padding-bottom:.65rem;">').replace(/style="border-bottom[^"]*"/, 'style="padding:.65rem 0;"');
      feed.innerHTML = html;
    })
    .catch(function() {
      document.getElementById('activity-feed').innerHTML = '<p style="font-size:.82rem;color:#888;font-style:italic;">No activity yet.</p>';
    });
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderAnswer(s) {
  return escHtml(s)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n{2,}/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>').replace(/$/, '</p>');
}

loadActivity();
setInterval(loadActivity, 30000);

