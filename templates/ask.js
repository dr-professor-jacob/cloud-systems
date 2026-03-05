(function () {
  var form      = document.getElementById("ask-form");
  var input     = document.getElementById("ask-input");
  var btn       = document.getElementById("ask-btn");
  var counter   = document.getElementById("ask-counter");
  var remaining = document.getElementById("ask-remaining");
  var answerBox = document.getElementById("ask-answer");
  var answerTxt = document.getElementById("ask-answer-text");
  var errorBox  = document.getElementById("ask-error");

  var MAX = 300;

  document.querySelectorAll("button.chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      input.value = chip.dataset.q;
      form.dispatchEvent(new Event("submit"));
    });
  });

  var wildcard = document.getElementById("chip-wildcard");
  if (wildcard) {
    wildcard.addEventListener("click", function () {
      window.open("https://youtu.be/dQw4w9WgXcQ", "_blank");
    });
  }

  input.addEventListener("input", function () {
    var left = MAX - input.value.length;
    counter.textContent = left + " characters remaining";
    counter.style.color = left < 30 ? "#c0392b" : "#888";
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) return;

    btn.disabled    = true;
    btn.textContent = "Asking Claude…";
    errorBox.style.display  = "none";
    answerBox.style.display = "none";

    fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    })
      .then(function (r) {
        return r.json().then(function (data) {
          return { ok: r.ok, status: r.status, data: data };
        });
      })
      .then(function (res) {
        if (!res.ok) {
          errorBox.textContent    = res.data.detail || "Something went wrong.";
          errorBox.style.display  = "";
        } else {
          answerTxt.textContent   = res.data.answer;
          answerBox.style.display = "";
          if (res.data.remaining !== undefined) {
            remaining.textContent = res.data.remaining + " question" + (res.data.remaining === 1 ? "" : "s") + " remaining today";
            remaining.style.display = "";
          }
          input.value = "";
          counter.textContent = MAX + " characters remaining";
          counter.style.color = "#888";
        }
      })
      .catch(function () {
        errorBox.textContent   = "Could not reach the server. Try again shortly.";
        errorBox.style.display = "";
      })
      .finally(function () {
        btn.disabled    = false;
        btn.textContent = "Ask";
      });
  });
})();
