function loadMetrics() {
  fetch('/metrics.json?t=' + Date.now())
    .then(function(r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function(d) {
      document.getElementById('m-load').textContent     = d.load ? d.load.split(' ')[0] : '—';
      document.getElementById('m-mem').textContent      = d.mem_used || '—';
      document.getElementById('m-disk').textContent     = d.disk_pct ? d.disk_pct.replace(/%/g,'') + '%' : '—';
      document.getElementById('m-uptime').textContent   = d.uptime || '—';
      document.getElementById('m-loadfull').textContent = d.load || '—';
      document.getElementById('m-memfull').textContent  = (d.mem_used && d.mem_total) ? d.mem_used + ' / ' + d.mem_total : '—';
      document.getElementById('m-diskfull').textContent = (d.disk_used && d.disk_total) ? d.disk_used + ' / ' + d.disk_total + ' (' + d.disk_pct.replace(/%/g,'') + '%)' : '—';
      document.getElementById('m-nginx').textContent    = d.nginx_connections || '—';
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
      note.textContent = 'Metrics not yet available. Claude Code will populate this on next run.';
    });
}
loadMetrics();
setInterval(loadMetrics, 30000);

function loadActivity() {
  fetch('/activity.json?t=' + Date.now())
    .then(function(r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function(d) {
      if (d.updated) {
        var dt = new Date(d.updated);
        document.getElementById('a-updated').textContent = dt.toUTCString();
        var age = Math.round((Date.now() - dt.getTime()) / 1000);
        document.getElementById('activity-age').textContent = age < 120 ? age + 's ago' : Math.round(age / 60) + 'm ago';
      }
      document.getElementById('a-calls').textContent = d.calls ? d.calls.join(', ') : '—';
      document.getElementById('a-summary').textContent = d.summary || '—';
      document.getElementById('activity-note').style.display = 'none';
    })
    .catch(function() {
      var note = document.getElementById('activity-note');
      note.style.display = '';
      note.textContent = 'No session logged yet.';
    });
}
loadActivity();
setInterval(loadActivity, 30000);
