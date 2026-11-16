"""Génère les ressources 3D du site : scènes PyVista (vtk.js), viewer, paramètres JS, Plotly.

Usage : python -m fueldoc.scenes <dossier_de_sortie>
Sortie : params.js, plotly.min.js, vtk/viewer.html, vtk/scenes/q{q}_r{r}.json, vtk/reference.json
"""
from __future__ import annotations

import base64
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

from .model import PARAMS, Q_GRID, R_GRID, T_CLIM, T_of_r, temps

L_MM = 20.0                     # longueur du tronçon représenté (plan médian)
THETA = np.linspace(0, 1.5 * np.pi, 61)   # secteur 0..270° (quart retiré)

VIEWER_LOADER = """function loadDataSet() {
  const container = document.querySelector('.content') || document.querySelector('body');
  const u = new URLSearchParams(location.search).get('s');
  fetch(u).then(r => r.json()).then(b64 => {
    OfflineLocalView.load(container, { base64Str: b64 });
  });
}
</script>
  </body>
</html>
"""


def _setup_pyvista():
    import pyvista as pv

    pv.OFF_SCREEN = True  # rendu hors écran : aucun serveur X nécessaire pour cet export
    return pv


def _ring(pv, r_in, r_out, n_r, temp_fn):
    r = np.linspace(r_in, r_out, n_r)
    rr, tt, zz = np.meshgrid(r, THETA, np.array([0.0, L_MM]), indexing="ij")
    grid = pv.StructuredGrid(rr * np.cos(tt), rr * np.sin(tt), zz)
    grid["T"] = temp_fn(grid.points[:, :2]).astype(float)
    return grid.extract_surface(algorithm=None)


def _export(pv, q_kw: float, rf_mm: float, path: Path) -> None:
    p = temps(q_kw * 1e3, rf_mm * 1e-3)

    def temp_fn(xy):
        r = np.hypot(xy[:, 0], xy[:, 1])
        return np.array([T_of_r(q_kw * 1e3, rf_mm * 1e-3, x * 1e-3) for x in r])

    fuel = _ring(pv, 0.0, rf_mm, 28, temp_fn)
    clad = _ring(pv, p["rci"] * 1e3, p["rco"] * 1e3, 8, temp_fn)
    pl = pv.Plotter(notebook=False, window_size=(900, 700))
    for m in (fuel, clad):
        pl.add_mesh(m, scalars="T", cmap="inferno", clim=T_CLIM, show_scalar_bar=False, smooth_shading=True)
    pl.set_background("#1b1b1f")
    pl.view_vector((1.0, -1.15, 0.75))
    pl.camera.zoom(1.05)
    pl.export_html(str(path))
    pl.close()


def generate(out: Path) -> None:
    out = Path(out)
    vtk = out / "vtk"
    (vtk / "scenes").mkdir(parents=True, exist_ok=True)
    pv = _setup_pyvista()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_html = Path(tmp) / "scene.html"
        first = True
        for q in Q_GRID:
            for r in R_GRID:
                _export(pv, q, r, tmp_html)
                html = tmp_html.read_text()
                b64 = re.search(r'base64Str = "([A-Za-z0-9+/=]+)"', html).group(1)
                (vtk / "scenes" / f"q{q}_r{r:.1f}.json").write_text(json.dumps(b64))
                if first:  # le viewer vtk.js est identique pour toutes les scènes
                    i = html.index("function loadDataSet()")
                    (vtk / "viewer.html").write_text(html[:i] + VIEWER_LOADER)
                    first = False

    # source unique des paramètres pour le JavaScript
    params = {"q": Q_GRID, "r": R_GRID, "clim": T_CLIM, "params": PARAMS}
    (out / "params.js").write_text("window.FUEL_PARAMS = " + json.dumps(params) + ";\n")

    # valeurs de référence pour le test croisé Python / JavaScript
    ref = [{"q": q, "r": r, **{k: temps(q * 1e3, r * 1e-3)[k] for k in
            ("T_center", "T_fuel_surf", "T_clad_in", "T_clad_out")}}
           for q in (10, 30, 50) for r in (3.9, 4.3)]
    (vtk / "reference.json").write_text(json.dumps(ref, indent=1))

    # Plotly embarqué (aucun CDN) : copié depuis le paquet Python
    import plotly

    shutil.copy(Path(plotly.__file__).parent / "package_data" / "plotly.min.js", out / "plotly.min.js")


if __name__ == "__main__":
    generate(Path(sys.argv[1]))
