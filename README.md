# fueldoc — note de calcul interactive (PyVista + Plotly + Mermaid, publiée avec Zensical)

```bash
uv sync
uv run fueldoc build     # génère docs/generated (scènes PyVista, params.js, plotly.min.js) puis zensical build
uv run fueldoc serve     # prévisualisation locale
```

- `src/fueldoc/model.py` : modèle 1D radial (source unique des paramètres, exportés vers le JS)
- `src/fueldoc/scenes.py` : scènes PyVista → vtk.js (27 combinaisons q′ × R_f)
- `src/fueldoc/ext.py` : extension Markdown (marqueur `{{ fuel_study }}`, filet de sécurité)
- `src/fueldoc/cli.py` : `fueldoc build|serve|generate` (équivalent d'un hook pre-build)
- `docs/javascripts/fuel.js` : mêmes équations côté navigateur ; `node tests/crosscheck.js` vérifie l'accord avec Python
- `docs/javascripts/mermaid.min.js` : Mermaid embarqué (le thème le charge sinon depuis unpkg)

Après modification du modèle : `uv run fueldoc build --clean`.
Le site doit être servi en HTTP (les scènes 3D sont chargées par `fetch`).
