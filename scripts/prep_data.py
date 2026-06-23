# -*- coding: utf-8 -*-
"""Précalcule les tables pour : (1) nuage de bulles longévité, (2) sunburst région→dpt."""
import json
import math
import pandas as pd

raw = pd.read_csv("data/dpt2020.csv", sep=";", dtype=str)
raw = raw[(raw.preusuel != "_PRENOMS_RARES") & (raw.annais != "XXXX")]
raw["nombre"] = raw["nombre"].astype(int)
raw["annais"] = raw["annais"].astype(int)
raw["sexe"] = raw["sexe"].map({"1": "M", "2": "F"})

# noms de départements (pour les tooltips)
DNAME = {f["properties"]["code"]: f["properties"]["nom"]
         for f in json.load(open("data/departements.geojson", encoding="utf-8"))["features"]}
DNAME["20"] = "Corse"

# ============================================================
# (1) NUAGE DE BULLES — niveau national, un prénom = une bulle
# ============================================================
# Le sexe ne sépare pas les bulles : les rares prénoms donnés aux deux sexes
# (Camille, Claude, Dominique, Marie) sont fusionnés. Il sert seulement à
# COLORER la bulle, via la part de filles de l'année affichée (couleur évolutive).
nat = raw.groupby(["preusuel", "annais"], as_index=False).nombre.sum()
# longévité = nb d'années passées dans le Top 100 national (tous prénoms confondus)
nat["rank"] = nat.groupby("annais").nombre.rank(ascending=False, method="min")
longevity = (nat[nat["rank"] <= 100].groupby("preusuel").annais.nunique()
             .rename("longevity").reset_index())
agg = nat.groupby("preusuel").nombre.sum().rename("total").reset_index()
peak = (nat.loc[nat.groupby("preusuel").nombre.idxmax(),
                ["preusuel", "annais"]].rename(columns={"annais": "peak_year"}))

# genre dominant + part de filles (%) de chaque prénom, calculés sur tout l'historique
sx = (raw.groupby(["preusuel", "sexe"]).nombre.sum()
         .unstack("sexe", fill_value=0))
for c in ("F", "M"):
    if c not in sx:
        sx[c] = 0
sx["fpct"] = (sx.F / (sx.F + sx.M) * 100).round().astype(int)
sx["sex"] = sx.apply(lambda r: "F" if r.F >= r.M else "M", axis=1)
sexinfo = sx[["sex", "fpct"]].reset_index()

names = (agg.merge(longevity, on="preusuel").merge(peak, on="preusuel")
            .merge(sexinfo, on="preusuel"))
names["id"] = names.preusuel
top = names.sort_values("total", ascending=False).head(250).copy()
top.to_csv("data/data_viz1_bubbles.csv", index=False)

# part de filles (%) PAR ANNÉE de chaque prénom -> couleur évolutive de la bulle
yr = (raw.groupby(["preusuel", "annais", "sexe"]).nombre.sum()
         .unstack("sexe", fill_value=0))
for c in ("F", "M"):
    if c not in yr:
        yr[c] = 0
yr_fem = ((yr.F / (yr.F + yr.M) * 100).round().astype(int)
          .rename("fy").reset_index())

# séries année par année : top 100 national de chaque année,
# pour le filtre « Top 1-100 » côté client (le rang = position dans l'année)
ts = nat.copy()
ts["yr_rank"] = ts.groupby("annais").nombre.rank(ascending=False, method="first")
ts = ts[ts.yr_rank <= 100]
ts = (ts.merge(longevity, on="preusuel").merge(peak, on="preusuel")
        .merge(yr_fem, on=["preusuel", "annais"]))
ts["id"] = ts.preusuel
ts = ts[["id", "preusuel", "annais", "nombre", "longevity", "peak_year", "fy"]]
ts.to_csv("data/data_viz1_anim.csv", index=False)
print("Viz1 bubbles:", len(top), "| anim rows:", len(ts), "| prénoms:", ts.id.nunique())

# ============================================================
# (2) SUNBURST région → département (par décennie)
# ============================================================
REGION = {}
for reg, deps in {
    "Alsace": "67 68", "Aquitaine": "24 33 40 47 64", "Auvergne": "03 15 43 63",
    "Basse-Normandie": "14 50 61", "Bourgogne": "21 58 71 89", "Bretagne": "22 29 35 56",
    "Centre": "18 28 36 37 41 45", "Champagne-Ardenne": "08 10 51 52", "Corse": "20",
    "Franche-Comté": "25 39 70 90", "Haute-Normandie": "27 76",
    "Île-de-France": "75 77 78 91 92 93 94 95",
    "Languedoc-Roussillon": "11 30 34 48 66", "Limousin": "19 23 87",
    "Lorraine": "54 55 57 88", "Midi-Pyrénées": "09 12 31 32 46 65 81 82",
    "Nord-Pas-de-Calais": "59 62", "Pays de la Loire": "44 49 53 72 85",
    "Picardie": "02 60 80", "Poitou-Charentes": "16 17 79 86",
    "Provence-Alpes-Côte d'Azur": "04 05 06 13 83 84",
    "Rhône-Alpes": "01 07 26 38 42 69 73 74",
}.items():
    for d in deps.split():
        REGION[d] = reg

geo = raw[(raw.dpt != "XX")].copy()
geo["region"] = geo.dpt.map(REGION)
geo = geo[geo.region.notna()]
geo["decade"] = (geo.annais // 10) * 10
sb = geo.groupby(["decade", "region", "dpt"]).nombre.sum().reset_index()

rows = []
TWO_PI = 2 * math.pi
for dec, grp in sb.groupby("decade"):
    total = grp.nombre.sum()
    rtot = grp.groupby("region").nombre.sum().sort_values(ascending=False)
    ang = 0.0
    for region in rtot.index:
        rg = grp[grp.region == region].sort_values("nombre", ascending=False)
        r_start = ang
        for _, r in rg.iterrows():
            t0 = ang
            t1 = ang + (r.nombre / total) * TWO_PI
            rows.append(dict(decade=int(dec), ring="dpt", region=region,
                             label=r.dpt, nom=DNAME.get(r.dpt, r.dpt),
                             births=int(r.nombre), theta=t0, theta2=t1,
                             tmid=(t0 + t1) / 2, radius=95, radius2=150, rmid=122))
            ang = t1
        rows.append(dict(decade=int(dec), ring="region", region=region,
                         label=region, nom=region, births=int(rg.nombre.sum()),
                         theta=r_start, theta2=ang, tmid=(r_start + ang) / 2,
                         radius=45, radius2=92, rmid=68))
sun = pd.DataFrame(rows).round({"theta": 5, "theta2": 5, "tmid": 5})
sun.to_csv("data/data_viz2_sunburst.csv", index=False)
print("Sunburst rows:", len(sun), "| décennies:", sun.decade.nunique())
