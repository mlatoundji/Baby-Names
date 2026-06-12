# Baby Names in France (1900–2020) — Design Sketches: Strengths & Weaknesses

For each set of questions we explore several designs. The guiding principle is *overview + detail
on demand*: a single interactive visualization must answer **all** of the sub-questions. All shares
are normalized (% of births) rather than raw counts, so that years and departments can be compared
fairly.

## Visualization 1 — Evolution over time

*(consistently popular/unpopular, sudden or brief popularity, trends)*


| Design                                                                                                                                                         | Strengths                                                                                                                                                                                                                                                                                                                                                    | Weaknesses                                                                                                                                                                |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Diagonal heatmap** (names × years, sorted by peak year)                                                                                                      | The diagonal instantly shows that each name has its era; reads consistency (long band: Jean), brief fads (spots), and accelerating turnover.                                                                                                                                                                                                                 | Static; hard to read one specific name; Top-N must be chosen.                                                                                                             |
| **Animated longevity bubble cloud** (X = peak year, Y = longevity in Top 100, area = births that year) + year slider on the X-axis + “Follow a name” sparkline | Consistent vs brief popularity is read on the vertical axisScrubbing the year makes turnover tangible; a dashed ghost ring recalls the previous year's size. **Top n** (1–100) thins the cloud; **Follow a name** highlights one bubble, fades the rest, and draws its 1900–2020 births curve Longevity is explicit: years spent in the national Top 100 | Bubble overplotting at high Top nLabels need greedy layout / small bubbles stay unlabeled. Raw birth counts, not shares (year-to-year sizes also reflect total births). |
| **Bump chart / "metro"** (Top 10 rank)                                                                                                                         | Ideal for crossings and rank reversals.                                                                                                                                                                                                                                                                                                                      | Limited to ~10 names (misses obscure fads); rank hides actual magnitude.                                                                                                  |
| **Generic motion chart** (sex + volume, unconstrained positions)                                                                                               | Attractive                                                                                                                                                                                                                                                                                                                                                   | Animation prevents comparing trajectories (memory load); cluttered, illegible. *Dropped — animation kept inside the bubble cloud instead.*                                |


**Chosen:** Animated longevity bubble cloud (sexes pooled, no sex encoding) with Top n filter and “Follow a name” sparkline (overview + detail on demand). Diagonal heatmap as a strong static alternative.

## Visualization 2 — Regional effect

*(are some names more popular in some regions? are popular names popular everywhere?)*


| Design                                                                       | Strengths                                                                                                                            | Weaknesses                                                                             |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| **Single-name choropleth** (location quotient) + name selector + year slider | Direct, geographic answer; the LQ (local share ÷ national share) isolates the regional effect; the slider shows diffusion over time. | One metric/name at a time; depends on the user's choice.                               |
| **Small multiples: regional vs national**                                    | Contrasts at a glance a name that "lights up" locally with a uniform one: answers both sub-questions together.                       | Static; limited number of maps.                                                        |
| **"Signature name" per department map**                                      | Reveals regional identities (Breton, Basque, Catalan, Corsican).                                                                     | 96 labels are crowded; color scale sensitive to outliers.                              |
| **"#1 name" per department map**                                             | Shows that top names are national (nearly uniform).                                                                                  | Little variety (one name dominates); mostly confirmatory.                              |
| **Treemap / sunburst** (region→department)                                   | Readable hierarchical composition.                                                                                                   | **No geographic dimension** nor any "local vs national" notion. *Secondary view only.* |


**Chosen:** Interactive LQ choropleth (selector + slider) as the centerpiece; small multiples for the contrast.

## Visualization 3 — Gender effect

*(unisex names: does their popularity evolve consistently across sexes?)*


| Design                                                      | Strengths                                                             | Weaknesses                                                                        |
| ----------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Female-share heatmap per decade** (diverging blue↔orange) | Immediate reading of gender flips (Camille, Alix…); compact overview. | Decade aggregation smooths out fine-grained variation.                            |
| **Female-share line chart** (interactive, click to isolate) | Precise temporal detail per name.                                     | Illegible spaghetti without default filtering.                                    |
| **Split M/F violins per name**                              | Shows each name's active periods.                                     | Answers "when" more than "gender"; hard to read.                                  |
| **Top-15 stability (RBO) by sex**                           | Rigorous on turnover.                                                 | Different question (turnover): a complement to Viz 1 rather than a gender answer. |


**Chosen:** Female-share heatmap (overview) + click-filtered line chart (detail).

---

**Cross-cutting consistency:** reuse of the "diagonal heatmap" visual language across Viz 1 and 3; M/F blue↔orange color encoding in Viz 3 only (Viz 1 deliberately omits sex); cleaned data (rare names, `dpt=XX`, `annais=XXXX` excluded).