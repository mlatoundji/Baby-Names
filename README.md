# Prénoms en France (1900–2020) — Visualisations interactives

Mini-projet de visualisation de données sur les prénoms attribués en France de 1900 à 2020
(source : fichiers Insee, niveau départemental). Trois visualisations interactives répondent
chacune à un jeu de questions.

## Arborescence

```
.
├── data/        # données sources + tables agrégées (dpt2020.csv non versionné)
├── scripts/     # préparation des données et génération des visualisations
├── output/      # visualisations interactives (HTML autonomes)
├── sketches/    # esquisses de design + aperçus PNG
└── report/      # rapports (design sketches, post final)
```

## Visualisations (HTML autonomes, à ouvrir dans un navigateur)

| Fichier | Question | Description |
|---|---|---|
| [`output/viz1_bulles.html`](output/viz1_bulles.html) | **Évolution dans le temps** | Nuage de bulles animé : longévité (Top 100) vs année du pic, taille = naissances, couleur = sexe. Slider « Année ». |
| [`output/viz2_radial_prenom.html`](output/viz2_radial_prenom.html) | **Effet régional** | Graphe radial par prénom : secteurs d'égale largeur en ordre pseudo-géographique, longueur = popularité locale rapportée au national (×national), cercle de référence ×1. Sélecteur de prénom + slider décennie. |
| [`output/viz2_sunburst_interactif.html`](output/viz2_sunburst_interactif.html) | **Effet régional (contexte)** | Vue complémentaire : sunburst région → département des naissances (poids démographique). Slider « Décennie », survol pour isoler une région. |
| [`output/viz3_genre.html`](output/viz3_genre.html) | **Effet de genre** | Heatmap part féminine des prénoms mixtes par décennie + courbe année par année liée au clic. |

Les `.html` embarquent leurs données agrégées : aucun serveur ni dépendance, double-cliquez pour ouvrir.

## Reproduire (depuis la racine du projet)

```bash
pip install altair pandas vl-convert-python python-docx
python scripts/prep_data.py            # agrège data/dpt2020.csv -> data/data_*.csv
python scripts/build_viz1.py           # -> output/viz1_bulles.html
python scripts/build_viz2_radial.py    # -> output/viz2_radial_prenom.html  (radial par prénom)
python scripts/build_viz2_sunburst.py  # -> output/viz2_sunburst_interactif.html  (contexte)
python scripts/build_viz3.py           # -> output/viz3_genre.html
```

## Données

- `data/dpt2020.csv` (78 Mo, **non versionné**) : fichier source Insee « Fichier des prénoms par
  département ». À placer dans `data/` pour relancer la préparation.
- `data/departements.geojson` : contours des départements métropolitains.
- `data/data_*.csv` : tables agrégées légères produites par `scripts/prep_data.py`.

## Conception & rapports

- `report/discussion_designs.md` — esquisses et analyse forces/faiblesses.
- `report/Baby_Names_Designs_Report.docx` — rapport des designs (forces/faiblesses).
- `report/Final_Visualizations_Report.docx` — post final : présentation et justification des 3 viz.
