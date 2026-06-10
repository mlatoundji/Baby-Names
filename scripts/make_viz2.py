# -*- coding: utf-8 -*-
"""Prototypes Viz 2 (effet régional) — cartes choroplèthes à partir de dpt2020.csv."""
import json
import pandas as pd
import altair as alt

alt.data_transformers.disable_max_rows()

# ---------- 1. Données ----------
df = pd.read_csv("data/dpt2020.csv", sep=";", dtype=str)
df = df[(df.preusuel != "_PRENOMS_RARES") & (df.dpt != "XX") & (df.annais != "XXXX")]
df["nombre"] = df["nombre"].astype(int)
df["annais"] = df["annais"].astype(int)
df = df[df.dpt.str.match(r"^(0[1-9]|[1-8][0-9]|9[0-5]|20)$")]  # métropole (Corse = 20)

# ---------- 2. Carte ----------
geo = json.load(open("data/departements.geojson", encoding="utf-8"))
features = geo["features"]
# noms de départements
DNAME = {f["properties"]["code"]: f["properties"]["nom"] for f in features}


def split_corsica(values: pd.DataFrame, key="dpt") -> pd.DataFrame:
    """Le CSV code la Corse '20' ; le GeoJSON utilise 2A/2B. On duplique."""
    cor = values[values[key] == "20"]
    if cor.empty:
        return values
    a = cor.copy(); a[key] = "2A"
    b = cor.copy(); b[key] = "2B"
    return pd.concat([values[values[key] != "20"], a, b], ignore_index=True)


def choropleth(values, color_enc, title, subtitle="", width=420, height=420):
    base = alt.Chart(
        alt.Data(values=geo, format=alt.DataFormat(property="features"))
    ).mark_geoshape(stroke="white", strokeWidth=0.4)
    return (
        base.transform_lookup(
            lookup="properties.code",
            from_=alt.LookupData(values, "dpt", list(values.columns)),
        )
        .encode(**color_enc)
        .project(type="mercator")
        .properties(width=width, height=height,
                    title=alt.TitleParams(title, subtitle=subtitle, anchor="start"))
    )


PERIOD = (1990, 2020)
d = df[df.annais.between(*PERIOD)]
tot_nat = d.nombre.sum()
nat = d.groupby("preusuel").nombre.sum()
dept_tot = d.groupby("dpt").nombre.sum()


def lq_table(name):
    """Quotient de localisation (LQ) par département pour un prénom."""
    s = d[d.preusuel == name].groupby("dpt").nombre.sum()
    out = pd.DataFrame({"dpt": dept_tot.index})
    out["births"] = out.dpt.map(s).fillna(0)
    out["dept_total"] = out.dpt.map(dept_tot)
    out["dept_share"] = out.births / out.dept_total
    out["nat_share"] = nat.get(name, 0) / tot_nat
    out["LQ"] = out.dept_share / out.nat_share
    out["nom"] = out.dpt.map(DNAME)
    out["prenom"] = name
    return split_corsica(out)


# =========================================================
# DESIGN A — choroplèthe d'un prénom régional (le cœur interactif)
# =========================================================
NAME_A = "EWEN"
tblA = lq_table(NAME_A)
colorA = alt.Color(
    "LQ:Q",
    scale=alt.Scale(scheme="redblue", reverse=True, domainMid=1, domain=[0, 6], clamp=True),
    legend=alt.Legend(title="Sur-représentation (LQ)"),
)
tipA = [alt.Tooltip("nom:N", title="Département"),
        alt.Tooltip("LQ:Q", title="LQ", format=".1f"),
        alt.Tooltip("births:Q", title="Naissances")]
A = choropleth(tblA, {"color": colorA, "tooltip": tipA},
               f"Design A · Concentration régionale du prénom « {NAME_A} » (1990–2020)",
               "Rouge = beaucoup plus donné qu'au niveau national (LQ>1). Sélecteur de prénom en version interactive.",
               width=520, height=520)
A.save("sketches/viz2_A_choropleth.png", scale_factor=2.0)
print("OK viz2_A_choropleth.png")

# =========================================================
# DESIGN B — petits multiples : régional vs national
# =========================================================
NAMES_B = ["EWEN", "GUILHEM", "MAYLIS", "EMMA"]
captions = {"EWEN": "breton (Bretagne)", "GUILHEM": "occitan (Hérault)",
            "MAYLIS": "Sud-Ouest (Landes)", "EMMA": "national (uniforme)"}
charts = []
for n in NAMES_B:
    t = lq_table(n)
    c = choropleth(
        t,
        {"color": alt.Color("LQ:Q",
                            scale=alt.Scale(scheme="redblue", reverse=True, domainMid=1,
                                            domain=[0, 6], clamp=True),
                            legend=alt.Legend(title="LQ") if n == NAMES_B[-1] else None),
         "tooltip": [alt.Tooltip("nom:N", title="Dép."), alt.Tooltip("LQ:Q", format=".1f")]},
        f"{n} — {captions[n]}", "", width=240, height=240)
    charts.append(c)
B = alt.concat(*charts, columns=2).properties(
    title=alt.TitleParams(
        "Design B · Régional vs national (LQ, 1990–2020)",
        subtitle="Un prénom régional « s'allume » localement ; un prénom national reste neutre partout.",
        anchor="start"))
B.save("sketches/viz2_B_smallmultiples.png", scale_factor=2.0)
print("OK viz2_B_smallmultiples.png")

# =========================================================
# DESIGN C — prénom « signature » de chaque département (LQ max)
# =========================================================
g = d.groupby(["dpt", "preusuel"]).nombre.sum().reset_index()
g["ds"] = g.nombre / g.dpt.map(dept_tot)
g["ns"] = g.preusuel.map(nat) / tot_nat
g["LQ"] = g.ds / g.ns
g = g[g.nombre >= 40]
sig = g.sort_values("LQ").groupby("dpt").tail(1).copy()
sig["nom"] = sig.dpt.map(DNAME)
sig = split_corsica(sig)

# centroïdes approximatifs pour placer les étiquettes
def centroid(coords):
    pts = []
    def walk(c):
        if isinstance(c[0], (float, int)):
            pts.append(c)
        else:
            for x in c:
                walk(x)
    walk(coords)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return sum(xs)/len(xs), sum(ys)/len(ys)

cent = {}
for f in features:
    cent[f["properties"]["code"]] = centroid(f["geometry"]["coordinates"])
sig["lon"] = sig.dpt.map(lambda c: cent[c][0])
sig["lat"] = sig.dpt.map(lambda c: cent[c][1])

shapeC = choropleth(
    sig,
    {"color": alt.Color("LQ:Q",
                        scale=alt.Scale(scheme="lightgreyteal", domain=[0, 80], clamp=True),
                        legend=alt.Legend(title="LQ du prénom signature")),
     "tooltip": [alt.Tooltip("nom:N", title="Dép."),
                 alt.Tooltip("preusuel:N", title="Prénom signature"),
                 alt.Tooltip("LQ:Q", format=".0f")]},
    "Design C · Le prénom « signature » de chaque département (LQ max, 1990–2020)",
    "Le prénom le plus sur-représenté localement révèle les identités régionales.",
    width=620, height=620)
labelsC = (alt.Chart(sig).mark_text(fontSize=7, fontWeight="bold")
           .encode(longitude="lon:Q", latitude="lat:Q", text="preusuel:N")
           .project(type="mercator"))
C = (shapeC + labelsC)
C.save("sketches/viz2_C_signature.png", scale_factor=2.0)
print("OK viz2_C_signature.png")

# =========================================================
# DESIGN D — prénom n°1 de chaque département (2000-2020)
# =========================================================
d2 = df[df.annais.between(2000, 2020)]
gg = d2.groupby(["dpt", "preusuel"]).nombre.sum().reset_index()
top1 = gg.sort_values("nombre").groupby("dpt").tail(1).copy()
top1["nom"] = top1.dpt.map(DNAME)
top1 = split_corsica(top1)
D = choropleth(
    top1,
    {"color": alt.Color("preusuel:N", scale=alt.Scale(scheme="tableau10"),
                        legend=alt.Legend(title="Prénom n°1")),
     "tooltip": [alt.Tooltip("nom:N", title="Dép."),
                 alt.Tooltip("preusuel:N", title="Prénom n°1"),
                 alt.Tooltip("nombre:Q", title="Naissances")]},
    "Design D · Le prénom n°1 de chaque département (2000–2020)",
    "Les têtes de classement sont quasi uniformes : les prénoms très populaires le sont partout.",
    width=560, height=560)
D.save("sketches/viz2_D_top1.png", scale_factor=2.0)
print("OK viz2_D_top1.png")
print("Terminé.")
