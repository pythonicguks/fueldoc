---
icon: lucide/box
---

# Étude paramétrique 3D

Déplacez les curseurs : la coupe 3D (PyVista, rendu vtk.js) et le profil radial (Plotly) se mettent à jour. La vue 3D est interactive (rotation, zoom, déplacement).

{{ fuel_study }}

!!! info "Lecture"
    La coupe montre un tronçon de 20 mm au plan médian, quart de section retiré. L'échelle de couleur est la même pour toutes les scènes (300 à 2 400 °C), ce qui permet de comparer les configurations. Le jeu pastille-gaine est visible en sombre entre la pastille et la gaine.

!!! note "Comment c'est fait"
    Les 27 combinaisons de paramètres sont calculées **en amont** par PyVista et exportées en scènes vtk.js. Le curseur ne fait que charger la scène voulue : aucun serveur n'est nécessaire. Voir [Reproductibilité](reproductibilite.md).
