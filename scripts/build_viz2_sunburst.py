# -*- coding: utf-8 -*-
"""Viz 2 — Sunburst région → département (naissances), par décennie."""
import pandas as pd
import altair as alt

alt.data_transformers.disable_max_rows()
sun = pd.read_csv("data/data_viz2_sunburst.csv")

dec = alt.param(
    name="decennie", value=2010,
    bind=alt.binding_range(min=1900, max=2020, step=10, name="Décennie  "),
)
hover = alt.selection_point(on="mouseover", fields=["region"], empty=False)

base = alt.Chart(sun).add_params(dec, hover).transform_filter("datum.decade == decennie")

arcs = base.mark_arc(stroke="white", strokeWidth=1).encode(
    theta=alt.Theta("theta:Q", scale=None),
    theta2=alt.Theta2("theta2:Q"),
    radius=alt.Radius("radius:Q", scale=None),
    radius2=alt.Radius2("radius2:Q"),
    color=alt.Color("region:N", title="Région", scale=alt.Scale(scheme="tableau20")),
    opacity=alt.condition(
        hover, alt.value(1.0),
        alt.Opacity("ring:N", scale=alt.Scale(domain=["region", "dpt"], range=[1.0, 0.5]),
                    legend=None)),
    tooltip=[alt.Tooltip("region:N", title="Région"),
             alt.Tooltip("nom:N", title="Département"),
             alt.Tooltip("births:Q", title="Naissances", format=",")],
)

# étiquettes des régions (anneau interne)
labels = base.transform_filter("datum.ring == 'region' && (datum.theta2 - datum.theta) > 0.12") \
    .mark_text(fontSize=9, fontWeight="bold", color="white", radiusOffset=0).encode(
        theta=alt.Theta("tmid:Q", scale=None),
        radius=alt.Radius("rmid:Q", scale=None),
        text="label:N",
    )

chart = (arcs + labels).properties(
    width=560, height=560,
    title=alt.TitleParams(
        "Répartition des naissances par région et département",
        subtitle=["Anneau interne = région, anneau externe = départements. "
                  "Glissez « Décennie » ; survolez pour mettre une région en avant."],
        anchor="start", fontSize=18),
).configure_view(stroke=None)

chart.save("output/viz2_sunburst_interactif.html")
print("OK viz2_sunburst_interactif.html")
chart.save("sketches/viz2_sunburst_preview.png", scale_factor=1.5)
print("OK viz2_sunburst_preview.png")
