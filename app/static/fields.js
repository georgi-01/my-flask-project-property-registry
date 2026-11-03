(function () {
  document.addEventListener("input", function (event) {
    var input = event.target;
    if (!input.matches) return;
    if (input.matches("[data-digits]")) {
      input.value = input.value.replace(/\D/g, "");
    }
    if (input.matches("[data-decimal]")) {
      var cleaned = input.value.replace(",", ".").replace(/[^\d.]/g, "");
      var parts = cleaned.split(".");
      input.value = parts.length > 1 ? parts[0] + "." + parts.slice(1).join("") : parts[0];
    }
    if (input.matches("[data-date]")) {
      var digits = input.value.replace(/\D/g, "").slice(0, 8);
      var text = digits;
      if (digits.length > 4) text = digits.slice(0, 2) + "." + digits.slice(2, 4) + "." + digits.slice(4);
      else if (digits.length > 2) text = digits.slice(0, 2) + "." + digits.slice(2);
      input.value = text;
    }
  });
})();
