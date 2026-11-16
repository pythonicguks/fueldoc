/* Modèle 1D radial d'un crayon combustible — miroir de fuelmodel.py (test croisé: reference.json) */
(function () {
  const F = window.FUEL_PARAMS;            // généré depuis fueldoc.model (source unique)
  const P = F.params;
  const CLIM = F.clim;
  const Q = F.q;                           // kW/m
  const R = F.r;                           // mm

  function temps(q, rf) {
    const rci = rf + P.gap, rco = rci + P.t_clad;
    const d_film = q / (2 * Math.PI * rco * P.h_cool);
    const d_clad = q / (2 * Math.PI * P.k_clad) * Math.log(rco / rci);
    const d_gap = q / (2 * Math.PI * rf * P.h_gap);
    const d_fuel = q / (4 * Math.PI * P.k_fuel);
    const T_co = P.T_cool + d_film, T_ci = T_co + d_clad, T_fs = T_ci + d_gap;
    return { rci, rco, d_film, d_clad, d_gap, d_fuel,
             T_clad_out: T_co, T_clad_in: T_ci, T_fuel_surf: T_fs, T_center: T_fs + d_fuel };
  }
  window.FuelModel = { temps, P, Q, R, CLIM };

  const css = (v) => getComputedStyle(document.body).getPropertyValue(v).trim();
  function theme() {
    const dark = document.body.getAttribute('data-md-color-scheme') === 'slate';
    const fg = dark ? '#e6e6e6' : '#222';
    return { fg, grid: dark ? 'rgba(255,255,255,.12)' : 'rgba(0,0,0,.10)',
             accent: '#e8590c', cool: '#1c7ed6', ok: '#2f9e44', bad: '#e03131' };
  }
  function base(extra) {
    const t = theme();
    return Object.assign({
      paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      font: { color: t.fg, family: 'Roboto, sans-serif', size: 13 },
      margin: { l: 64, r: 20, t: 36, b: 52 },
      xaxis: { gridcolor: t.grid, zerolinecolor: t.grid },
      yaxis: { gridcolor: t.grid, zerolinecolor: t.grid },
      legend: { orientation: 'h', y: -0.22 },
    }, extra);
  }
  const cfg = { responsive: true, displaylogo: false };

  /* ---------- Page « étude paramétrique » : curseurs -> scène 3D + profil radial ---------- */
  function initStudy() {
    const frame = document.getElementById('vtk-view');
    if (!frame) return;
    const sq = document.getElementById('sl-q'), sr = document.getElementById('sl-r');
    const base_url = frame.dataset.base;
    const lq = document.getElementById('val-q'), lr = document.getElementById('val-r');
    const out = document.getElementById('kpis');
    const bar = document.getElementById('cbar');
    bar.style.background = 'linear-gradient(to top,#000004,#420a68,#932667,#dd513a,#fca50a,#fcffa4)';
    document.getElementById('cb-max').textContent = CLIM[1] + ' °C';
    document.getElementById('cb-min').textContent = CLIM[0] + ' °C';

    let timer;
    function update() {
      const q = Q[+sq.value], r = R[+sr.value];
      lq.textContent = q + ' kW/m'; lr.textContent = r.toFixed(1) + ' mm';
      clearTimeout(timer);
      timer = setTimeout(() => {
        frame.src = `${base_url}viewer.html?s=scenes/q${q}_r${r.toFixed(1)}.json`;
      }, 120);
      const p = temps(q * 1e3, r * 1e-3);
      const margin = P.T_melt - p.T_center;
      out.innerHTML =
        `<div><b>${p.T_center.toFixed(0)} °C</b><span>température au centre</span></div>` +
        `<div><b>${p.T_fuel_surf.toFixed(0)} °C</b><span>surface pastille</span></div>` +
        `<div><b>${p.T_clad_out.toFixed(0)} °C</b><span>surface gaine</span></div>` +
        `<div class="${margin > 400 ? 'ok' : 'bad'}"><b>${margin.toFixed(0)} K</b><span>marge à la fusion (${P.T_melt} °C)</span></div>`;
      drawProfile(q, r, p);
    }
    function drawProfile(q, r, p) {
      const t = theme(), qq = q * 1e3, rf = r * 1e-3;
      const rs = [], Ts = [];
      for (let i = 0; i <= 60; i++) {                       // pastille
        const x = rf * i / 60; rs.push(x * 1e3);
        Ts.push(p.T_fuel_surf + qq / (4 * Math.PI * P.k_fuel) * (1 - (x / rf) ** 2));
      }
      rs.push(p.rci * 1e3); Ts.push(p.T_clad_in);            // jeu (segment)
      for (let i = 0; i <= 20; i++) {                       // gaine
        const x = p.rci + (p.rco - p.rci) * i / 20; rs.push(x * 1e3);
        Ts.push(p.T_clad_in - qq / (2 * Math.PI * P.k_clad) * Math.log(x / p.rci));
      }
      const shapes = [
        { type: 'rect', xref: 'x', yref: 'paper', x0: 0, x1: r, y0: 0, y1: 1, fillcolor: 'rgba(232,89,12,.08)', line: { width: 0 } },
        { type: 'rect', xref: 'x', yref: 'paper', x0: p.rci * 1e3, x1: p.rco * 1e3, y0: 0, y1: 1, fillcolor: 'rgba(28,126,214,.18)', line: { width: 0 } },
        { type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: P.T_melt, y1: P.T_melt, line: { color: t.bad, dash: 'dash', width: 1.5 } },
      ];
      Plotly.react('plot-profile', [{
        x: rs, y: Ts, mode: 'lines', line: { color: t.accent, width: 3 }, name: 'T(r)',
        hovertemplate: 'r = %{x:.2f} mm<br>T = %{y:.0f} °C<extra></extra>' }], base({
        title: { text: 'Profil radial de température', font: { size: 14 } },
        xaxis: { title: 'rayon r (mm)', gridcolor: t.grid, range: [0, p.rco * 1e3 + 0.1] },
        yaxis: { title: 'T (°C)', gridcolor: t.grid, range: [250, 3000] },
        shapes, showlegend: false,
        annotations: [
          { x: r / 2, y: 300, text: 'UO₂', showarrow: false, font: { size: 11 } },
          { x: p.rco * 1e3, y: 300, text: 'gaine', showarrow: false, xanchor: 'right', yanchor: 'bottom', font: { size: 11 } },
          { xref: 'paper', x: 0.02, xanchor: 'left', y: P.T_melt, yanchor: 'bottom', showarrow: false,
            text: 'fusion UO₂', font: { color: t.bad, size: 11 } }],
      }), cfg);
    }
    sq.addEventListener('input', update); sr.addEventListener('input', update);
    window.__studyRedraw = update;
    update();
  }

  /* ---------- Page « résultats » : trois figures Plotly ---------- */
  function initResults() {
    if (!document.getElementById('plot-tc')) return;
    const t = theme();
    const colors = ['#1c7ed6', '#e8590c', '#7048e8'];
    const qs = []; for (let q = 5; q <= 70; q += 1) qs.push(q);
    const traces = R.map((r, i) => ({
      x: qs, y: qs.map(q => temps(q * 1e3, r * 1e-3).T_center), mode: 'lines',
      name: `R = ${r.toFixed(1)} mm`, line: { color: colors[i], width: 3 },
      hovertemplate: "q' = %{x} kW/m<br>T = %{y:.0f} °C<extra></extra>" }));
    Plotly.react('plot-tc', traces, base({
      title: { text: "Température centrale selon la puissance linéique", font: { size: 14 } },
      xaxis: { title: "puissance linéique q' (kW/m)", gridcolor: t.grid },
      yaxis: { title: 'T centre (°C)', gridcolor: t.grid },
      shapes: [{ type: 'rect', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: P.T_melt, y1: 4200, fillcolor: 'rgba(224,49,49,.12)', line: { width: 0 } },
               { type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: P.T_melt, y1: P.T_melt, line: { color: t.bad, dash: 'dash' } }],
      annotations: [{ xref: 'paper', x: 0.01, y: P.T_melt, yanchor: 'bottom', text: 'fusion UO₂ (2840 °C)', showarrow: false, font: { color: t.bad, size: 11 } }],
    }), cfg);

    const R0 = 4.1e-3;
    const comp = [['d_fuel', 'Pastille UO₂', '#e8590c'], ['d_gap', 'Jeu', '#f59f00'],
                  ['d_clad', 'Gaine', '#1c7ed6'], ['d_film', 'Film caloporteur', '#74c0fc']];
    const qb = [10, 20, 30, 40, 50];
    Plotly.react('plot-contrib', comp.map(([k, name, c]) => ({
      type: 'bar', name, x: qb.map(q => q + ' kW/m'), y: qb.map(q => temps(q * 1e3, R0)[k]),
      marker: { color: c }, hovertemplate: name + ': %{y:.0f} K<extra></extra>' })), base({
      barmode: 'stack', title: { text: 'Contributions à l’écart T(centre) − T(fluide), R = 4,1 mm', font: { size: 14 } },
      yaxis: { title: 'ΔT (K)', gridcolor: t.grid }, xaxis: { gridcolor: t.grid },
    }), cfg);

    const qz = [], rz = [], zz = [];
    for (let r = 3.8; r <= 4.4001; r += 0.05) { rz.push(+r.toFixed(2)); }
    for (let q = 10; q <= 60; q += 2.5) { qz.push(q); }
    rz.forEach(r => zz.push(qz.map(q => temps(q * 1e3, r * 1e-3).T_center)));
    Plotly.react('plot-surf', [{ type: 'surface', x: qz, y: rz, z: zz, colorscale: 'Inferno', cmin: 300, cmax: 2800,
      colorbar: { title: { text: '°C' }, len: .7 },
      hovertemplate: "q' = %{x} kW/m<br>R = %{y} mm<br>T = %{z:.0f} °C<extra></extra>" }], {
      paper_bgcolor: 'rgba(0,0,0,0)', font: { color: t.fg }, margin: { l: 0, r: 0, t: 30, b: 0 },
      title: { text: 'Surface de réponse T_centre(q′, R)', font: { size: 14 } },
      scene: { xaxis: { title: "q' (kW/m)" }, yaxis: { title: 'R (mm)' }, zaxis: { title: 'T (°C)' },
               camera: { eye: { x: 1.6, y: -1.6, z: 0.9 } } },
    }, cfg);
  }

  function init() { initStudy(); initResults(); }
  if (window.document$) window.document$.subscribe(init);
  else document.addEventListener('DOMContentLoaded', init);

  /* redessine si l'utilisateur bascule clair/sombre */
  new MutationObserver(() => { if (window.__studyRedraw) window.__studyRedraw(); initResults(); })
    .observe(document.body, { attributes: true, attributeFilter: ['data-md-color-scheme'] });
})();
