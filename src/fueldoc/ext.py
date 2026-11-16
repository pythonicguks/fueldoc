"""Extension Python-Markdown : point d'accroche de la génération dans `zensical build`.

Zensical (0.1.x) n'expose pas encore d'API de hooks. Les extensions Markdown, elles, s'exécutent
pendant la construction du site, et les fichiers écrits dans `docs/` pendant ce temps sont copiés
dans `site/` au même build. L'extension :

  1. génère (une fois par processus, avec cache par empreinte du code) les ressources PyVista,
     params.js et plotly.min.js dans `docs/generated/` ;
  2. remplace le marqueur `{{ fuel_study }}` d'une page par le bloc HTML interactif.

Après modification du modèle : `uv run zensical build --clean` (le cache différentiel de Zensical
ne reconstruit pas une page Markdown inchangée).
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

from markdown import Extension
from markdown.preprocessors import Preprocessor

MARKER = "{{ fuel_study }}"
_done: set[Path] = set()

STUDY_HTML = """
<div class="controls">
  <label for="sl-q">Puissance linéique q′</label>
  <input id="sl-q" type="range" min="0" max="{nq}" step="1" value="{iq}">
  <output id="val-q"></output>
  <label for="sl-r">Rayon de pastille R<sub>f</sub></label>
  <input id="sl-r" type="range" min="0" max="{nr}" step="1" value="{ir}">
  <output id="val-r"></output>
</div>

<div id="kpis"></div>

<div class="study">
  <div class="viewer">
    <iframe id="vtk-view" data-base="generated/vtk/" title="Coupe 3D du crayon" loading="lazy"></iframe>
    <div class="cbar-wrap"><div id="cbar"></div><div class="labels"><span id="cb-max"></span><span id="cb-min"></span></div></div>
  </div>
  <div id="plot-profile" class="plot"></div>
</div>
"""


def _fingerprint() -> str:
    h = hashlib.sha256()
    for name in ("model.py", "scenes.py"):
        h.update((Path(__file__).parent / name).read_bytes())
    return h.hexdigest()[:16]


def is_current(out: Path) -> bool:
    stamp = out / ".fingerprint"
    return ((out / "vtk" / "viewer.html").exists() and (out / "params.js").exists()
            and stamp.exists() and stamp.read_text() == _fingerprint())


def ensure_generated(out: Path, force: bool = False) -> bool:
    """Lance la génération si l'empreinte du code a changé ou si des fichiers manquent.

    Retourne True si une génération a eu lieu."""
    out = out.resolve()
    if not force and (out in _done or is_current(out)):
        _done.add(out)
        return False
    print(f"[fueldoc] génération des scènes PyVista -> {out}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, "-m", "fueldoc.scenes", str(out)], capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[-3000:])
        raise RuntimeError("fueldoc : échec de la génération des scènes PyVista")
    (out / ".fingerprint").write_text(_fingerprint())
    _done.add(out)
    return True


class FuelPreprocessor(Preprocessor):
    def __init__(self, md, out: Path):
        super().__init__(md)
        self.out = out

    def run(self, lines: list[str]) -> list[str]:
        if ensure_generated(self.out):
            # Zensical a déjà collecté les fichiers statiques de docs/ : ils ne sont servis qu'au build suivant.
            print("[fueldoc] ATTENTION : ressources générées pendant le build ; relancer le build pour les "
                  "inclure (ou utiliser `uv run fueldoc build`).", flush=True)
        if MARKER not in lines:
            return lines
        from .model import Q_GRID, R_GRID

        html = STUDY_HTML.format(nq=len(Q_GRID) - 1, iq=Q_GRID.index(30), nr=len(R_GRID) - 1, ir=R_GRID.index(4.1))
        i = lines.index(MARKER)
        return lines[:i] + html.splitlines() + lines[i + 1:]


class FuelDocExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {"out_dir": ["docs/generated", "Dossier des ressources générées"]}
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        out = Path(self.getConfig("out_dir"))
        md.preprocessors.register(FuelPreprocessor(md, out), "fueldoc", 30)


def makeExtension(**kwargs):
    return FuelDocExtension(**kwargs)
