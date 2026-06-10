# -*- coding: utf-8 -*-
"""Viz 1 — Nuage de bulles animé : longévité des prénoms, année par année."""
import pandas as pd
import altair as alt

alt.data_transformers.disable_max_rows()
anim = pd.read_csv("data/data_viz1_anim.csv")

YEARS = sorted(anim.annais.unique())
year = alt.param(
    name="annee", value=1985,
    bind=alt.binding_range(min=int(min(YEARS)), max=int(max(YEARS)), step=1, name="Année  "),
)
hover = alt.selection_point(on="mouseover", fields=["id"], empty=False)

base = alt.Chart(anim).add_params(year).transform_filter("datum.annais == annee")

bubbles = base.mark_circle(opacity=0.75, stroke="white", strokeWidth=0.6).encode(
    x=alt.X("peak_year:Q", title="Année du pic de popularité",
            scale=alt.Scale(domain=[1900, 2020])),
    y=alt.Y("longevity:Q", title="Longévité (nb d'années dans le Top 100 national)",
            scale=alt.Scale(domain=[0, 122])),
    size=alt.Size("nombre:Q", title="Naissances dans l'année",
                  scale=alt.Scale(range=[20, 3000])),
    color=alt.Color("sexe:N", title="Sexe",
                    scale=alt.Scale(domain=["F", "M"], range=["#e15a99", "#4a90d9"])),
    order=alt.Order("nombre:Q", sort="descending"),
    opacity=alt.condition(hover, alt.value(1), alt.value(0.7)),
    tooltip=[alt.Tooltip("preusuel:N", title="Prénom"),
             alt.Tooltip("sexe:N", title="Sexe"),
             alt.Tooltip("nombre:Q", title="Naissances (année)", format=","),
             alt.Tooltip("longevity:Q", title="Longévité (ans)"),
             alt.Tooltip("peak_year:Q", title="Année du pic")],
).add_params(hover)

# étiquettes des plus grosses bulles de l'année
labels = base.transform_window(
    r="rank()", sort=[alt.SortField("nombre", order="descending")],
).transform_filter("datum.r <= 12").mark_text(
    fontSize=10, fontWeight="bold", color="#222", dy=0,
).encode(x="peak_year:Q", y="longevity:Q", text="preusuel:N")

# grand millésime en filigrane
yeartxt = base.transform_aggregate(y="max(annais)").mark_text(
    align="right", baseline="top", fontSize=90, fontWeight="bold",
    color="#e8e8e8", dx=-10, dy=10,
).encode(x=alt.value(900), y=alt.value(20), text="y:Q")

chart = (yeartxt + bubbles + labels).properties(
    width=900, height=520,
    title=alt.TitleParams(
        "Longévité des prénoms — lecture année par année",
        subtitle=["Glissez le curseur « Année ». Haut = prénom durable ; bas = mode passagère. "
                  "Gauche/droite = ancien/récent. Taille = naissances cette année-là."],
        anchor="start", fontSize=18),
).configure_view(stroke=None).configure_axis(grid=True, gridOpacity=0.25)

chart.save("output/viz1_bulles.html")
print("OK viz1_bulles.html")
chart.save("sketches/viz1_bulles_preview.png", scale_factor=1.5)  # contrôle visuel (année=1985)
print("OK viz1_bulles_preview.png")
