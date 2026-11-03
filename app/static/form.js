(function () {
  var form = document.getElementById("listing-form");
  if (!form) return;
  var kindInput = form.querySelector("[name=kind]");
  var price = form.querySelector("#price_eur");
  var area = form.querySelector("#area_sqm");
  var out = document.getElementById("ppm");

  function syncKind() {
    var kind = kindInput ? kindInput.value : "apartment";
    form.querySelectorAll("[data-kind]").forEach(function (node) {
      var active = node.getAttribute("data-kind") === kind;
      node.hidden = !active;
      node.querySelectorAll("input, select, textarea").forEach(function (field) {
        field.disabled = !active;
      });
    });
  }

  function syncPrice() {
    var amount = parseFloat(String(price.value).replace(",", "."));
    var meters = parseFloat(String(area.value).replace(",", "."));
    if (amount > 0 && meters > 0) {
      var value = amount / meters;
      out.textContent = value.toLocaleString("bg-BG", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €/m²";
    } else {
      out.textContent = "—";
    }
  }

  if (kindInput) kindInput.addEventListener("change", syncKind);
  price.addEventListener("input", syncPrice);
  area.addEventListener("input", syncPrice);
  syncKind();
  syncPrice();
})();
