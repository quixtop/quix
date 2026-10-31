/* (c) Shrix — author: shrix — ste100 sheet: theme switch and findings filter */
(function () {
  var root = document.documentElement, btn = document.getElementById("theme");
  var modes = ["auto", "light", "dark"], key = "ste100-theme", cur = "auto";
  try { cur = localStorage.getItem(key) || "auto"; } catch (e) {}
  function apply(m) {
    cur = m;
    if (m === "auto") root.removeAttribute("data-theme"); else root.setAttribute("data-theme", m);
    if (btn) btn.textContent = "Theme: " + m;
    try { localStorage.setItem(key, m); } catch (e) {}
  }
  apply(modes.indexOf(cur) < 0 ? "auto" : cur);
  if (btn) btn.addEventListener("click", function () { apply(modes[(modes.indexOf(cur) + 1) % modes.length]); });

  var sev = "all", rule = "", sel = document.getElementById("rulef");
  var buttons = document.querySelectorAll(".filters button[data-f]");
  function filter() {
    var rows = document.querySelectorAll("table.flist tbody tr");
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      var show = (sev === "all" || r.getAttribute("data-sev") === sev) && (!rule || r.getAttribute("data-rule") === rule);
      r.classList.toggle("hide", !show);
    }
  }
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].addEventListener("click", function () {
      sev = this.getAttribute("data-f");
      for (var j = 0; j < buttons.length; j++) buttons[j].setAttribute("aria-pressed", String(buttons[j] === this));
      filter();
    });
  }
  if (sel) sel.addEventListener("change", function () { rule = sel.value; filter(); });
})();
