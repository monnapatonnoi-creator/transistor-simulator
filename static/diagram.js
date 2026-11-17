(function () {
  "use strict";

  const UNITS = { ohm: "Ω", kohm: "kΩ", mohm: "MΩ" };
  const MODES = {
    voltage_divider: {
      title: "Voltage Divider Bias",
      show: ["r1", "r2", "re"],
    },
    fixed_bias: {
      title: "Fixed Bias",
      show: ["rb", "emitter-direct"],
    },
    emitter_bias: {
      title: "Emitter Bias",
      show: ["rb", "re"],
    },
  };
  const GROUPS = ["r1", "r2", "rb", "re", "emitter-direct"];
  const RESISTORS = ["r1", "r2", "rb", "rc", "re"];

  function visibleInput(name) {
    return Array.from(document.querySelectorAll('input[name="' + name + '"]'))
      .find(function (element) { return element.type !== "hidden"; });
  }

  function carriedInput(name) {
    return document.querySelector('input[name="carry_' + name + '"]');
  }

  function bind(name, text) {
    const element = document.querySelector('[data-bind="' + name + '"]');
    if (element) element.textContent = text;
  }

  function resistorLabel(name) {
    const input = visibleInput(name) || carriedInput(name);
    const raw = input ? input.value : "—";
    const select = document.querySelector('select[name="' + name + '_unit"]');
    const carriedUnit = carriedInput(name + "_unit");
    const unit = select ? select.value : (carriedUnit ? carriedUnit.value : "kohm");
    return raw + " " + (UNITS[unit] || "Ω");
  }

  function update() {
    const modeSelect = document.querySelector('select[name="bias_type"]');
    const key = modeSelect && MODES[modeSelect.value] ? modeSelect.value : "voltage_divider";
    const mode = MODES[key];

    GROUPS.forEach(function (name) {
      const group = document.querySelector('[data-group="' + name + '"]');
      if (group) {
        group.classList.toggle("is-hidden", mode.show.indexOf(name) === -1);
      }
    });
    bind("mode-title", mode.title);

    RESISTORS.forEach(function (name) {
      bind(name, resistorLabel(name));
    });
    ["vcc", "beta", "vbe"].forEach(function (name) {
      const input = visibleInput(name);
      if (input) bind(name, input.value + (name === "vcc" || name === "vbe" ? " V" : ""));
    });

    bind("ic", "— (กด Calculate)");
    bind("vce", "— (กด Calculate)");
  }

  document.addEventListener("input", update);
  document.addEventListener("change", update);
})();
