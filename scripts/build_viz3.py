# -*- coding: utf-8 -*-
"""Viz 3 — Effet de genre : heatmap part féminine par décennie + courbe liée au clic."""
import pandas as pd
import altair as alt

alt.data_transformers.disable_max_rows()

raw = pd.read_csv("data/dpt2020.csv", sep=";", dtype=str)
raw = raw[(raw.preusuel != "_PRENOMS_RARES") & (raw.annais != "XXXX")]
raw["nombre"] = raw["nombre"].astype(int)
raw["annais"] = raw["annais"].astype(int)
raw["sexe"] = raw["sexe"].map({"1": "M", "2": "F"})
nat = raw.groupby(["sexe", "preusuel", "annais"], as_index=False).nombre.sum()

# --- sélection des prénoms mixtes (donnés aux deux sexes, volume suffisant) ---
tot = nat.groupby("preusuel").nombre.sum()
fem = nat[nat.sexe == "F"].groupby("preusuel").nombre.sum()
fshare = (fem / tot).fillna(0)
mixed = tot[(fshare.between(0.12, 0.88)) & (tot >= 2500)].index
order = fshare[mixed].sort_values().index.tolist()  # tri par part féminine globale

m = nat[nat.preusuel.isin(mixed)].copy()
m["decade"] = (m.annais // 10) * 10


def fshare_table(keys):
    g = m.groupby(keys + ["sexe"]).nombre.sum().unstack("sexe").fillna(0)
    g["tot"] = g.sum(axis=1)
    g["fshare"] = g.get("F", 0) / g["tot"]
    return g.reset_index()[keys + ["fshare", "tot"]]


heat = fshare_table(["preusuel", "decade"])
line = fshare_table(["preusuel", "annais"])

# --- échelle de couleur divergente : bleu = garçons, orange = filles ---
fscale = alt.Scale(domain=[0, 0.5, 1], range=["#3b6fb6", "#f2f2f2", "#e0792b"])
sel = alt.selection_point(fields=["preusuel"], value=[{"preusuel": "CAMILLE"}], empty=False)

heatmap = alt.Chart(heat).mark_rect(stroke="white", strokeWidth=0.5).encode(
    x=alt.X("decade:O", title="Décennie",
            axis=alt.Axis(labelAngle=0, format="d")),
    y=alt.Y("preusuel:N", title=None, sort=order),
    color=alt.Color("fshare:Q", title="Part féminine", scale=fscale,
                    legend=alt.Legend(format="%")),
    opacity=alt.condition(sel, alt.value(1), alt.value(0.85)),
    stroke=alt.condition(sel, alt.value("#111"), alt.value("white")),
    strokeWidth=alt.condition(sel, alt.value(2), alt.value(0.5)),
    tooltip=[alt.Tooltip("preusuel:N", title="Prénom"),
             alt.Tooltip("decade:O", title="Décennie"),
             alt.Tooltip("fshare:Q", title="Part féminine", format=".0%"),
             alt.Tooltip("tot:Q", title="Naissances", format=",")],
).add_params(sel).properties(
    width=430, height=560,
    title=alt.TitleParams("Part féminine des prénoms mixtes, par décennie",
                          subtitle="Bleu = surtout garçons · Orange = surtout filles · "
                                   "Cliquez un prénom pour le détail →",
                          anchor="start"))

detail = alt.Chart(line).transform_filter(sel)
ref = alt.Chart(pd.DataFrame({"y": [0.5]})).mark_rule(
    color="#999", strokeDash=[4, 4]).encode(y="y:Q")
curve = detail.mark_line(point=True, color="#7a4fb0").encode(
    x=alt.X("annais:Q", title="Année", scale=alt.Scale(domain=[1900, 2020]),
            axis=alt.Axis(format="d")),
    y=alt.Y("fshare:Q", title="Part féminine", scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(format="%")),
    tooltip=[alt.Tooltip("annais:Q", title="Année", format="d"),
             alt.Tooltip("fshare:Q", title="Part féminine", format=".0%"),
             alt.Tooltip("tot:Q", title="Naissances", format=",")],
)
title_txt = detail.mark_text(align="left", fontSize=15, fontWeight="bold",
                             color="#7a4fb0", dx=5, dy=-8).encode(
    x=alt.value(0), y=alt.value(12), text="preusuel:N")
right = (ref + curve + title_txt).properties(
    width=430, height=560,
    title=alt.TitleParams("Évolution année par année (prénom sélectionné)", anchor="start"))

chart = alt.hconcat(heatmap, right).resolve_scale(color="independent").configure_view(
    stroke=None).configure_axis(grid=True, gridOpacity=0.25)

chart.save("output/viz3_genre.html")
print("OK viz3_genre.html")
chart.save("sketches/viz3_genre_preview.png", scale_factor=1.5)
print("OK viz3_genre_preview.png  | prénoms mixtes:", len(mixed))
