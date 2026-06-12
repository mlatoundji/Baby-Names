# -*- coding: utf-8 -*-
"""Viz 2 (v2) — Graphe radial par prénom : fréquence locale (‰) par département,
secteurs d'égale largeur, ordre pseudo-géographique, cercle de référence national.

Reprend les remarques du groupe :
- secteurs angulaires fixes (même largeur par département)
- ordre pseudo-géographique stable (Bretagne à gauche, Alsace à droite…)
- longueur du segment = popularité locale du prénom
- popularité fréquentielle : naissances du prénom pour 1000 dans le département
- cercle = score national (repère sur/sous-représentation locale)
- code région sur le graphe + code & nom complet en légende
- sélecteur de prénom trié par popularité décroissante
"""
import json
import math
import pandas as pd
import altair as alt

alt.data_transformers.disable_max_rows()

# ---------------- données ----------------
raw = pd.read_csv("data/dpt2020.csv", sep=";", dtype=str)
raw = raw[(raw.preusuel != "_PRENOMS_RARES") & (raw.annais != "XXXX") & (raw.dpt != "XX")]
raw["nombre"] = raw["nombre"].astype(int)
raw["annais"] = raw["annais"].astype(int)
raw = raw[raw.dpt.str.match(r"^(0[1-9]|[1-8][0-9]|9[0-5]|20)$")].copy()
raw["decade"] = (raw.annais // 10) * 10

REGIONS = {
    "Alsace": ("ALS", "67 68"), "Aquitaine": ("AQU", "24 33 40 47 64"),
    "Auvergne": ("AUV", "03 15 43 63"), "Basse-Normandie": ("BNO", "14 50 61"),
    "Bourgogne": ("BOU", "21 58 71 89"), "Bretagne": ("BRE", "22 29 35 56"),
    "Centre": ("CEN", "18 28 36 37 41 45"), "Champagne-Ardenne": ("CHA", "08 10 51 52"),
    "Corse": ("COR", "20"), "Franche-Comté": ("FRC", "25 39 70 90"),
    "Haute-Normandie": ("HNO", "27 76"), "Île-de-France": ("IDF", "75 77 78 91 92 93 94 95"),
    "Languedoc-Roussillon": ("LRO", "11 30 34 48 66"), "Limousin": ("LIM", "19 23 87"),
    "Lorraine": ("LOR", "54 55 57 88"), "Midi-Pyrénées": ("MPY", "09 12 31 32 46 65 81 82"),
    "Nord-Pas-de-Calais": ("NPC", "59 62"), "Pays de la Loire": ("PDL", "44 49 53 72 85"),
    "Picardie": ("PIC", "02 60 80"), "Poitou-Charentes": ("PCH", "16 17 79 86"),
    "Provence-Alpes-Côte d'Azur": ("PAC", "04 05 06 13 83 84"),
    "Rhône-Alpes": ("RAL", "01 07 26 38 42 69 73 74"),
}
DEP2REG = {d: reg for reg, (_, deps) in REGIONS.items() for d in deps.split()}
DEP2CODE = {d: code for reg, (code, deps) in REGIONS.items() for d in deps.split()}
raw["region"] = raw.dpt.map(DEP2REG)
raw = raw[raw.region.notna()]

# ---------------- centroïdes & ordre pseudo-géographique ----------------
feats = json.load(open("data/departements.geojson", encoding="utf-8"))["features"]
DNAME = {f["properties"]["code"]: f["properties"]["nom"] for f in feats}


def centroid(coords):
    pts = []
    def walk(c):
        if isinstance(c[0], (int, float)):
            pts.append(c)
        else:
            for x in c:
                walk(x)
    walk(coords)
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


cent = {f["properties"]["code"]: centroid(f["geometry"]["coordinates"]) for f in feats}
cent["20"] = ((cent["2A"][0] + cent["2B"][0]) / 2, (cent["2A"][1] + cent["2B"][1]) / 2)

deps = sorted(DEP2REG)
cx = sum(cent[d][0] for d in deps) / len(deps)
cy = sum(cent[d][1] for d in deps) / len(deps)


def bearing(d):  # 0 = nord, sens horaire
    lon, lat = cent[d]
    return math.atan2(lon - cx, lat - cy) % (2 * math.pi)


reg_bear = {reg: sum(bearing(d) for d in REGIONS[reg][1].split())
            / len(REGIONS[reg][1].split()) for reg in REGIONS}
ordered = []
for reg in sorted(REGIONS, key=lambda r: reg_bear[r]):
    for d in sorted(REGIONS[reg][1].split(), key=bearing):
        ordered.append(d)

N = len(ordered)
W = 2 * math.pi / N
geo = {d: dict(theta=i * W, theta2=(i + 1) * W) for i, d in enumerate(ordered)}

reg_rows = []
for reg, (code, depstr) in REGIONS.items():
    idx = [ordered.index(d) for d in depstr.split()]
    reg_rows.append(dict(region=reg, code=code, tmid=(min(idx) + max(idx) + 1) / 2 * W))
reg_df = pd.DataFrame(reg_rows)

# ---------------- métrique fréquentielle (‰) ----------------
# top 8 de chaque décennie (couvre toutes les époques) + prénoms régionaux marquants
top_by_dec = set()
for d, grp in raw.groupby("decade"):
    top_by_dec |= set(grp.groupby("preusuel").nombre.sum().sort_values(ascending=False).head(8).index)
NAMES = sorted(top_by_dec
               | {"EWEN", "GWENDAL", "MAIWENN", "ERWAN", "YANN", "GUILHEM", "MAYLIS", "JORDI",
                  "JOAN", "IBAN", "ANGE", "MOUSSA", "MAMADOU", "FATOUMATA", "AUBIN"})
NAMES = [n for n in NAMES if n in set(raw.preusuel)]
g = raw[raw.preusuel.isin(NAMES)]

dept_tot = raw.groupby(["dpt", "decade"]).nombre.sum().rename("dtot")
nat_tot = raw.groupby("decade").nombre.sum().rename("gtot")
nd = g.groupby(["preusuel", "dpt", "decade"]).nombre.sum().rename("n").reset_index()
nd = nd.merge(dept_tot, on=["dpt", "decade"])
nd["permille"] = (nd.n / nd.dtot * 1000).round(2)

# table géo des départements (95 lignes) — jointe ensuite via transform_lookup
geo_df = pd.DataFrame([
    dict(dpt=d, theta=round(geo[d]["theta"], 5), theta2=round(geo[d]["theta2"], 5),
         region=DEP2REG[d], code=DEP2CODE[d],
         nom=DNAME.get(d, "Corse" if d == "20" else d),
         reglabel=DEP2CODE[d] + " · " + DEP2REG[d])
    for d in ordered])

name_nat = g.groupby(["preusuel", "decade"]).nombre.sum().rename("n").reset_index()
name_nat = name_nat.merge(nat_tot, on="decade")
name_nat["nat_permille"] = (name_nat.n / name_nat.gtot * 1000).round(2)
nd = nd.merge(name_nat[["preusuel", "decade", "nat_permille"]], on=["preusuel", "decade"])
# ratio local / national (quotient de localisation) : 1 = niveau national
nd["ratio"] = (nd.permille / nd.nat_permille).round(3)
# données embarquées slim (la géo est jointe via lookup pour alléger le HTML)
val_df = nd[["preusuel", "dpt", "decade", "ratio", "permille", "nat_permille"]]

# ---------------- paramètres interactifs ----------------
import sys
opts = list(raw.groupby("preusuel").nombre.sum().loc[NAMES].sort_values(ascending=False).index)
DEF_DEC = int(sys.argv[2]) if len(sys.argv) > 2 else 2010
DEF_NAME = (sys.argv[1] if len(sys.argv) > 1 else
            name_nat[name_nat.decade == DEF_DEC]
            .sort_values("nat_permille", ascending=False).preusuel.iloc[0])
prenom = alt.param(name="prenom", value=DEF_NAME,
                   bind=alt.binding_select(options=opts, name="Prénom  "))
dec = alt.param(name="decennie", value=DEF_DEC,
                bind=alt.binding_range(min=1900, max=2020, step=10, name="Décennie  "))

R0, R = 55, 175
# échelle sur le ratio (×national) : cercle fixe à ×1, pics régionaux vers l'extérieur
rscale = alt.Scale(type="sqrt", domain=[0, 9], range=[R0, R], clamp=True)

flt = "datum.preusuel == prenom && datum.decade == decennie"
hover = alt.selection_point(on="mouseover", fields=["dpt"], empty=False)
base = (alt.Chart(val_df).add_params(prenom, dec).transform_filter(flt)
        .transform_lookup(lookup="dpt", from_=alt.LookupData(
            geo_df, "dpt", ["theta", "theta2", "region", "code", "nom", "reglabel"])))

bars = base.mark_arc(stroke="white", strokeWidth=0.5).encode(
    theta=alt.Theta("theta:Q", scale=None), theta2=alt.Theta2("theta2:Q"),
    radius=alt.Radius("ratio:Q", scale=rscale), radius2=alt.value(R0),
    color=alt.Color("reglabel:N", title="Région (code · nom)",
                    scale=alt.Scale(scheme="tableau20"),
                    legend=alt.Legend(columns=1, symbolLimit=30, labelFontSize=9)),
    opacity=alt.condition(hover, alt.value(1), alt.value(0.85)),
    tooltip=[alt.Tooltip("nom:N", title="Département"),
             alt.Tooltip("region:N", title="Région"),
             alt.Tooltip("ratio:Q", title="× la moyenne nationale", format=".1f"),
             alt.Tooltip("permille:Q", title="Prénom ‰ local", format=".2f"),
             alt.Tooltip("nat_permille:Q", title="Niveau national ‰", format=".2f")],
).add_params(hover)

# cercle de référence FIXE à ×1 (= niveau national), identique pour tout prénom
ref_outline = alt.Chart(pd.DataFrame({"ratio": [1.0]})).mark_arc(
    theta=0, theta2=2 * math.pi, fill=None, stroke="#111",
    strokeWidth=2, strokeDash=[6, 4]).encode(radius=alt.Radius("ratio:Q", scale=rscale))

reglabels = alt.Chart(reg_df).mark_text(fontSize=9, fontWeight="bold", color="#333").encode(
    theta=alt.Theta("tmid:Q", scale=None), radius=alt.value(R + 14), text="code:N")

chart = (bars + ref_outline + reglabels).properties(
    width=560, height=560,
    title=alt.TitleParams(
        "Popularité locale d'un prénom par département (‰ des naissances)",
        subtitle=["Longueur = popularité locale du prénom rapportée à la moyenne nationale "
                  "(× national). Cercle pointillé = ×1 : au-delà = sur-représenté localement, en deçà = moins.",
                  "Secteurs d'égale largeur, ordonnés géographiquement (ouest à gauche, est à droite). "
                  "Choisissez le prénom (trié par popularité) et la décennie."],
        anchor="start", fontSize=16),
).configure_view(stroke=None)

chart.save("output/viz2_sunburst_2.html")
print("OK output/viz2_sunburst_2.html | prénoms:", len(opts), "| lignes:", len(nd))
chart.save("sketches/viz2_sunburst_2_preview.png", scale_factor=2.6)
print("OK sketches/viz2_sunburst_2_preview.png")
