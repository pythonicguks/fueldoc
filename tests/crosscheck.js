// Vérifie que les équations de fuel.js coïncident avec fueldoc.model (valeurs de référence)
const fs = require('fs');
global.window = {};
eval(fs.readFileSync('docs/generated/params.js', 'utf8'));
global.document = { getElementById: () => null, addEventListener() {}, body: { getAttribute() {} } };
global.getComputedStyle = () => ({}); global.MutationObserver = class { observe() {} };
eval(fs.readFileSync('docs/javascripts/fuel.js', 'utf8'));
let worst = 0;
for (const r of JSON.parse(fs.readFileSync('docs/generated/vtk/reference.json'))) {
  const t = window.FuelModel.temps(r.q * 1e3, r.r * 1e-3);
  for (const k of ['T_center', 'T_fuel_surf', 'T_clad_in', 'T_clad_out']) worst = Math.max(worst, Math.abs(t[k] - r[k]));
}
console.log('écart max JS/Python (K):', worst);
process.exit(worst < 1e-9 ? 0 : 1);
