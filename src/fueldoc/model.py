"""Modèle 1D radial, régime permanent, d'un crayon combustible REP (tronçon au plan médian).

Source unique : les paramètres sont exportés vers le JavaScript (params.js) à la génération.
Les équations sont réécrites dans docs/javascripts/fuel.js (test croisé : reference.json).
SI : q en W/m (puissance linéique), longueurs en m, températures en °C.
"""
import math

PARAMS = {
    "T_cool": 320.0,   # °C, température du fluide caloporteur
    "h_cool": 30000.0, # W/m²/K, coefficient d'échange paroi-fluide
    "h_gap": 5000.0,   # W/m²/K, conductance du jeu pastille-gaine
    "k_fuel": 3.0,     # W/m/K, UO2 (constante, simplification)
    "k_clad": 17.0,    # W/m/K, Zircaloy
    "gap": 0.08e-3,    # m, jeu radial
    "t_clad": 0.57e-3, # m, épaisseur de gaine
    "T_melt": 2840.0,  # °C, fusion UO2 neuf
}
Q_GRID = [10, 15, 20, 25, 30, 35, 40, 45, 50]  # kW/m
R_GRID = [3.9, 4.1, 4.3]           # mm, rayon de pastille
T_CLIM = [300.0, 2400.0]


def temps(q, rf, P=PARAMS):
    rci = rf + P["gap"]
    rco = rci + P["t_clad"]
    d_film = q / (2 * math.pi * rco * P["h_cool"])
    d_clad = q / (2 * math.pi * P["k_clad"]) * math.log(rco / rci)
    d_gap = q / (2 * math.pi * rf * P["h_gap"])
    d_fuel = q / (4 * math.pi * P["k_fuel"])
    T_co = P["T_cool"] + d_film
    T_ci = T_co + d_clad
    T_fs = T_ci + d_gap
    return dict(rci=rci, rco=rco, d_film=d_film, d_clad=d_clad, d_gap=d_gap, d_fuel=d_fuel,
                T_clad_out=T_co, T_clad_in=T_ci, T_fuel_surf=T_fs, T_center=T_fs + d_fuel)


def T_of_r(q, rf, r, P=PARAMS):
    """Température au rayon r (pastille ou gaine ; dans le jeu : interpolation linéaire)."""
    p = temps(q, rf, P)
    if r <= rf:
        return p["T_fuel_surf"] + q / (4 * math.pi * P["k_fuel"]) * (1 - (r / rf) ** 2)
    if r < p["rci"]:
        f = (r - rf) / (p["rci"] - rf)
        return p["T_fuel_surf"] + f * (p["T_clad_in"] - p["T_fuel_surf"])
    return p["T_clad_in"] - q / (2 * math.pi * P["k_clad"]) * math.log(r / p["rci"])
