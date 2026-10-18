"""
Génère :
  - assets/demi_terrain.png : fond de terrain pour le nuage de points « Carte des tirs »
    de Power BI (axe X = map_x de 0 à 80, axe Y = map_y de 60 à 120, but en haut).
  - assets/apercu_carte_tirs_messi.png : aperçu de la carte des tirs de Messi 2018/19
    (image d'illustration pour le README / LinkedIn).
Usage : python make_pitch.py <dossier_data> <dossier_assets>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Rectangle
import pandas as pd

DATA = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "assets")
OUT.mkdir(parents=True, exist_ok=True)

LINE, GRASS = "#9AA5B1", "#FFFFFF"


def draw_half_pitch(ax):
    """Demi-terrain vertical, coordonnées StatsBomb : x (largeur) 0-80, y (longueur) 60-120."""
    ax.set_xlim(0, 80)
    ax.set_ylim(60, 120)
    ax.set_facecolor(GRASS)
    kw = dict(fill=False, edgecolor=LINE, linewidth=1.6)
    ax.add_patch(Rectangle((0, 60), 80, 60, **kw))           # contour
    ax.add_patch(Rectangle((18, 102), 44, 18, **kw))         # surface de réparation
    ax.add_patch(Rectangle((30, 114), 20, 6, **kw))          # surface de but
    ax.add_patch(Rectangle((36, 120), 8, 1.5, **kw))         # but
    ax.plot(40, 108, "o", color=LINE, markersize=3)         # point de penalty
    ax.add_patch(Arc((40, 108), 20, 20, theta1=217, theta2=323, color=LINE, linewidth=1.6))
    ax.add_patch(Arc((40, 60), 20, 20, theta1=0, theta2=180, color=LINE, linewidth=1.6))
    ax.set_aspect("equal")
    ax.axis("off")


# ---------- 1. fond pour Power BI (aucune marge : l'image doit coller aux axes) ----------
fig = plt.figure(figsize=(8, 6), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
draw_half_pitch(ax)
fig.savefig(OUT / "demi_terrain.png", facecolor=GRASS)
plt.close(fig)

# ---------- 2. aperçu : tirs de Messi, Liga 2018/19 ----------
shots = pd.read_csv(DATA / "FactShots.csv")
matches = pd.read_csv(DATA / "DimMatch.csv")
s = shots.merge(matches[["match_id", "season"]], on="match_id")
s = s[(s.player_id == 5503) & (s.season == "2018/19") & (s.is_penalty == 0)]

fig = plt.figure(figsize=(8, 7.4), dpi=200, facecolor="#FCFCFB")
ax = fig.add_axes([0.03, 0.03, 0.94, 0.78])
draw_half_pitch(ax)
miss, goal = s[s.is_goal == 0], s[s.is_goal == 1]
ax.scatter(miss.map_x, miss.map_y, s=miss.xg * 900 + 18, facecolor="#1F5FAD", alpha=0.35,
           edgecolor="#FCFCFB", linewidth=1.5, label="Tir non converti", zorder=3)
ax.scatter(goal.map_x, goal.map_y, s=goal.xg * 900 + 18, facecolor="#B0124F",
           edgecolor="#FCFCFB", linewidth=1.5, label="But", zorder=4)
fig.text(0.04, 0.94, "Lionel Messi — tirs en Liga 2018/19 (hors penalties)",
         fontsize=15, weight="bold", color="#1B1F24")
fig.text(0.04, 0.895,
         f"{len(s)} tirs · {int(goal.shape[0])} buts · {s.xg.sum():.1f} xG  —  taille du point = xG du tir",
         fontsize=10.5, color="#57606A")
fig.text(0.04, 0.86, "Source : StatsBomb Open Data", fontsize=8.5, color="#8C959F")
ax.legend(loc="lower left", frameon=False, fontsize=9.5, markerscale=0.6, labelcolor="#1B1F24")
fig.savefig(OUT / "apercu_carte_tirs_messi.png", facecolor="#FCFCFB")
print("ok", len(s), int(goal.shape[0]), round(s.xg.sum(), 2))
