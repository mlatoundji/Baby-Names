# -*- coding: utf-8 -*-
"""Viz 3 — Effet de genre : violons split garçons/filles par prénom mixte.

Pour chaque prénom donné aux deux sexes, un violon partagé montre la distribution
des naissances dans le temps : moitié gauche = garçons, moitié droite = filles.
Un décalage vertical entre les deux moitiés = bascule de genre au fil du temps.
"""
import pandas as pd
import altair as alt

alt.data_transformers.disable_max_rows()

raw = pd.read_csv("data/dpt2020.csv", sep=";", dtype=str)
raw = raw[(raw.preusuel != "_PRENOMS_RARES") & (raw.annais != "XXXX")]
raw["nombre"] = raw["nombre"].astype(int)
raw["annais"] = raw["annais"].astype(int)
raw["sexe"] = raw["sexe"].map({"1": "M", "2": "F"})
nat = raw.groupby(["sexe", "preusuel", "annais"], as_index=False).nombre.sum()

# --- sélection des prénoms mixtes ---
tot = nat.groupby("preusuel").nombre.sum()
fem = nat[nat.sexe == "F"].groupby("preusuel").nombre.sum()
fshare = (fem / tot).fillna(0)
cand = tot[(fshare.between(0.12, 0.88)) & (tot >= 3000)].index
mixed = list(tot[cand].sort_values(ascending=False).head(20).index)

# --- densité lissée des naissances par année, par sexe ---
YEARS = list(range(1900, 2021))
rows = []
for name in mixed:
    sub = nat[nat.preusuel == name]
    series, maxw = {}, 0.0
    for sx in ["M", "F"]:
        s = (sub[sub.sexe == sx].set_index("annais").nombre
             .reindex(YEARS, fill_value=0)
             .rolling(7, center=True, min_periods=1).mean())
        series[sx] = s
        maxw = max(maxw, s.max())
    for sx in ["M", "F"]:
        w = series[sx] / maxw if maxw else series[sx]
        sign = -1 if sx == "M" else 1
        for y in YEARS:
            rows.append(dict(preusuel=name, sexe=sx, annais=y,
                             x=round(sign * float(w[y]), 4),
                             births=int(series[sx][y])))
df = pd.DataFrame(rows)
order = list(fshare[mixed].sort_values().index)  # du plus masculin au plus féminin

sexscale = alt.Scale(domain=["M", "F"], range=["#3b6fb6", "#e0792b"])
hover = alt.selection_point(on="mouseover", fields=["preusuel"], empty=True)

violins = alt.Chart(df).mark_area(orient="horizontal").encode(
    y=alt.Y("annais:Q", title="Année", scale=alt.Scale(domain=[1900, 2020]),
            axis=alt.Axis(format="d", values=list(range(1900, 2021, 20)))),
    x=alt.X("x:Q", title=None, axis=None, scale=alt.Scale(domain=[-1, 1])),
    color=alt.Color("sexe:N", title="Sexe", scale=sexscale,
                    legend=alt.Legend(orient="top")),
    detail="sexe:N",
    opacity=alt.condition(hover, alt.value(0.95), alt.value(0.6)),
    tooltip=[alt.Tooltip("preusuel:N", title="Prénom"),
             alt.Tooltip("sexe:N", title="Sexe"),
             alt.Tooltip("annais:Q", title="Année", format="d"),
             alt.Tooltip("births:Q", title="Naissances (lissé/an)", format=",")],
).add_params(hover).properties(width=42, height=430)

chart = violins.facet(
    column=alt.Column("preusuel:N", title=None, sort=order,
                      header=alt.Header(labelAngle=-90, labelAlign="right",
                                        labelFontSize=10, labelFontWeight="bold")),
    spacing=3,
).properties(
    title=alt.TitleParams(
        "Prénoms mixtes : distribution des naissances dans le temps, par sexe",
        subtitle=["Un violon par prénom — moitié gauche (bleu) = garçons, moitié droite (orange) = filles. "
                  "Largeur = naissances cette année-là.",
                  "Deux moitiés décalées verticalement = le prénom a changé de sexe au fil du temps "
                  "(prénoms triés du plus masculin au plus féminin)."],
        anchor="start", fontSize=15),
).configure_view(stroke=None)

chart.save("output/viz3_violon.html")
print("OK output/viz3_violon.html | prénoms mixtes:", len(mixed))
chart.save("sketches/viz3_violon_preview.png", scale_factor=1.8)
print("OK sketches/viz3_violon_preview.png")
