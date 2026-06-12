# -*- coding: utf-8 -*-
"""Final submission post (English, Word): the 3 implemented visualizations + rationale."""
import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)
ACCENT = RGBColor(0x1F, 0x4E, 0x79)
ACCENT2 = RGBColor(0x2E, 0x75, 0xB6)


def h1(text):
    p = doc.add_paragraph(); p.space_before = Pt(14)
    r = p.add_run(text); r.bold = True; r.font.size = Pt(15); r.font.color.rgb = ACCENT


def sub(text):
    p = doc.add_paragraph(); p.space_before = Pt(6)
    r = p.add_run(text); r.bold = True; r.font.size = Pt(11.5); r.font.color.rgb = ACCENT2


def img(path, width=6.0):
    if os.path.exists(path):
        doc.add_picture(path, width=Inches(width))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run("Static snapshot — the live HTML adds the slider, hover and linked views.")
        r.italic = True; r.font.size = Pt(8.5); r.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    else:
        doc.add_paragraph(f"[missing image: {path}]")


def bullets(items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


# ---------------- Title ----------------
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("Baby Names in France (1900–2020)")
r.bold = True; r.font.size = Pt(20); r.font.color.rgb = ACCENT
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs = s.add_run("Final Visualizations — Presentation & Rationale")
rs.italic = True; rs.font.size = Pt(13)
doc.add_paragraph(
    "We implemented three interactive visualizations in Altair (Vega-Lite), one per set of "
    "questions. Each is a self-contained HTML file with a slider, tooltips and linked views. "
    "Popularity is measured as a share of births so that years, regions and sexes are comparable. "
    "Below, each visualization is presented with a snapshot and an explanation of why it is "
    "appropriate and effective for its target questions. (Screenshots here are static; the live "
    "files reveal the full interaction — we recommend a short screen-capture clip per "
    "visualization showing the slider being dragged.)"
)

# ============================================================
# VIZ 1
# ============================================================
h1("Visualization 1 — Evolution over time")
doc.add_paragraph(
    "Target questions: which names stay consistently (un)popular, which are suddenly or briefly "
    "popular, and are there temporal trends?"
)
sub("What it shows")
doc.add_paragraph(
    "An animated bubble cloud. Each bubble is a name in the selected year. The X-axis is the "
    "name's peak year, the Y-axis is its longevity (number of years it stayed in the national "
    "Top 100), bubble size is the number of births that year, and color encodes sex. The "
    "“Year” slider scrubs through 1900–2020; the giant year label and the moving, "
    "growing bubbles make the evolution tangible."
)
img("sketches/viz1_bulles_preview.png", 6.2)
sub("Why it is appropriate and effective")
bullets([
    "Consistent vs brief popularity is read directly off the vertical axis: long-lived classics "
    "sit high (e.g. Marie), short-lived fads sit low — answering the core question by position.",
    "Temporal trends emerge from scrubbing: the cloud drifts rightward over the century and names "
    "are replaced faster in recent decades, making accelerating turnover visible.",
    "Sudden popularity is shown by a bubble that appears and inflates rapidly as the slider "
    "advances, while its low longevity keeps it near the bottom.",
    "Bubble size preserves absolute magnitude (births), so rank and volume are not confused.",
    "Hover tooltips give the exact name, sex, births, peak year and longevity for detail on demand.",
])
sub("Key points to demonstrate (screenshots / video)")
bullets([
    "Snapshots at 1905, 1965 and 2015 to show how the set of names turns over.",
    "A long-lived name high on the axis (Marie/Jean) vs a brief fad low on the axis.",
    "A short clip dragging the slider to show the cloud shifting and bubbles growing.",
])

# ============================================================
# VIZ 2
# ============================================================
h1("Visualization 2 — Regional effect")
doc.add_paragraph(
    "Target questions: are some names more popular in some regions, and are popular names "
    "generally popular across the whole country?"
)
doc.add_paragraph(
    "We use two complementary views: a per-name radial chart (the main answer) and a sunburst "
    "(demographic context).", style=None)

sub("Main view — radial chart of a name's local popularity")
doc.add_paragraph(
    "Each department is a fixed-width angular sector, arranged in pseudo-geographic order "
    "(west on the left, east on the right, north on top), so the layout is always the same and "
    "recognizable. The radial length of a sector encodes the name's local popularity as a "
    "frequency — births per thousand in that department — normalized by the national rate, i.e. "
    "how many times more (or less) common the name is locally than nationally. A fixed dashed "
    "reference circle marks the national level (×1): a sector reaching beyond the circle means the "
    "name is over-represented there, inside means under-represented. A name selector (sorted by "
    "popularity) and a decade slider drive the chart; region codes label the ring and are repeated "
    "with full names in the legend."
)
img("sketches/viz2_radial_demo_ewen.png", 6.0)
sub("Why it is appropriate and effective")
bullets([
    "Frequency-normalized length removes the population-size bias: Paris (75) is no longer "
    "automatically ‘biggest’; we compare like with like.",
    "The fixed ×1 reference circle turns the regional question into a one-glance read: bars beyond "
    "the circle = locally more popular, bars inside = less.",
    "It answers both sub-questions directly — a regional name (Breton EWEN) makes the western "
    "sectors shoot past the circle while everywhere else stays inside; a top national name (EMMA) "
    "produces near-uniform bars hugging the circle everywhere (popular across the whole country).",
    "The stable geographic ordering lets the eye learn the layout once and then compare any name; "
    "the decade slider shows how a name's geography appears, spreads or fades over time.",
])

sub("Complementary view — sunburst of births by region and department")
doc.add_paragraph(
    "The sunburst (inner ring = region, outer ring = departments, angle = number of births, decade "
    "slider) gives the demographic context the radial chart abstracts away: how many births each "
    "region actually contributes, and how that weight shifts across decades. It is the "
    "‘how big is each region’ overview; the radial chart is the ‘where is this name "
    "over-represented’ detail."
)
img("sketches/viz2_sunburst_preview.png", 4.4)
sub("Key points to demonstrate (screenshots / video)")
bullets([
    "Radial chart with a regional name (EWEN/JORDI/MAYLIS) — western/southern sectors past the circle.",
    "Radial chart with a national name (EMMA/LUCAS) — uniform bars on the reference circle.",
    "A short clip changing the name in the selector to show the pattern reshaping.",
])

# ============================================================
# VIZ 3
# ============================================================
h1("Visualization 3 — Gender effect")
doc.add_paragraph(
    "Target questions: are there gender effects, and does the popularity of names given to both "
    "sexes evolve consistently across sexes?"
)
sub("What it shows")
doc.add_paragraph(
    "A heatmap of unisex names (rows) by decade (columns), colored by the female share on a "
    "diverging scale (blue = mostly boys, orange = mostly girls, pale = balanced). Clicking a name "
    "opens, on the right, its year-by-year female-share curve with a dashed 50% reference line."
)
img("sketches/viz3_genre_preview.png", 6.2)
sub("Why it is appropriate and effective")
bullets([
    "It focuses on unisex names — the only names for which a gender question is meaningful — "
    "so the view is on-topic by construction.",
    "Whether a name evolves consistently is read along each row: a row that stays one color is "
    "stable, a row that changes from blue to orange has flipped sex over time (e.g. Camille).",
    "The diverging palette centered at 50% makes ‘mostly boys’, ‘balanced’ and "
    "‘mostly girls’ instantly distinguishable across many names at once.",
    "The linked line chart gives the precise trajectory: when it crosses 50% and whether the shift "
    "is gradual or abrupt — the exact ‘consistent evolution?’ answer.",
])
sub("Key points to demonstrate (screenshots / video)")
bullets([
    "The heatmap overview showing several names that flip color over the decades.",
    "Clicking Camille (or Dominique) to reveal the curve crossing the 50% line mid-century.",
    "A name that stays one color throughout as a stable counter-example.",
])

# ---- closing ----
h1("Summary")
doc.add_paragraph(
    "Each visualization is matched to its question through a deliberate encoding: longevity on an "
    "axis for time, a frequency-normalized radial chart with a national reference circle (plus a "
    "sunburst for demographic context) for region, and a diverging female-share heatmap for "
    "gender. All three follow the same overview + detail-on-demand pattern (slider / hover / "
    "linked view) and share a consistent, accessible color language."
)

out = "report/Final_Visualizations_Report.docx"
doc.save(out)
print("Saved", out)
