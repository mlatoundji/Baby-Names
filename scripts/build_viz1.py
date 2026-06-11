# -*- coding: utf-8 -*-
"""Viz 1 — Nuage de bulles « longévité des prénoms » (maquette v2).

Génère output/viz1_bulles.html : page autonome D3.js fidèle à
sketches/viz1-nuage_de_bulles_v2.png :
  - fond crème, bulles monochromes bleu ardoise, prénom + naissances
    écrits en blanc dans les bulles assez grandes ;
  - millésime géant en haut à droite, « Longévité » en titre d'axe ;
  - slider intégré DIRECTEMENT sur l'axe des abscisses (même échelle
    que l'année du pic) : glisser la poignée change l'année ;
  - bouton « Lecture année par année » (animation), flèches ← → au clavier ;
  - cercle pointillé = taille de la bulle l'année précédente.

Usage : python scripts/build_viz1.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
YEAR0 = 1985  # année affichée à l'ouverture, comme sur la maquette

# ------------------------------------------------------------------ données
df = pd.read_csv(ROOT / "DATA" / "data_viz1_anim.csv")

# payload compact : 1 entrée par prénom (x, y fixes) + {année: [[id, naissances]]}
uniq = df.drop_duplicates(subset=["sexe", "preusuel"]).reset_index(drop=True)
idx = {(r.sexe, r.preusuel): i for i, r in enumerate(uniq.itertuples(index=False))}

payload = {
    "names": [
        {"n": str(r.preusuel).title(), "s": r.sexe,
         "l": int(r.longevity), "p": int(r.peak_year)}
        for r in uniq.itertuples(index=False)
    ],
    "years": {
        int(y): [[idx[(r.sexe, r.preusuel)], int(r.nombre)]
                 for r in g.sort_values("nombre", ascending=False).itertuples(index=False)]
        for y, g in df.groupby("annais")
    },
    "yearMin": int(df.annais.min()),
    "yearMax": int(df.annais.max()),
    "maxN": int(df.nombre.max()),
}

# ----------------------------------------------------------------- gabarit
TEMPLATE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Longévité des prénoms — nuage de bulles</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>
:root{
  --bg:#F6F3EB; --ink:#1E1D1A; --muted:#8F897C; --grid:#E8E4D7;
  --bubble:#92B0D3; --ghost:#B3AC9B; --soft:#6F6A5E;
}
html,body{margin:0;background:var(--bg);}
body{font-family:"Segoe UI",-apple-system,"Helvetica Neue",Arial,sans-serif;color:var(--ink);}
#wrap{position:relative;max-width:1500px;margin:0 auto;padding:10px 18px 24px;}
svg{display:block;width:100%;height:auto;user-select:none;}
text{font-family:inherit;}
.lbl{pointer-events:none;}
.lbl .nm{fill:#fff;font-weight:700;}
.lbl .vl{fill:#fff;opacity:.92;font-weight:600;}
#tt{position:absolute;pointer-events:none;opacity:0;transition:opacity .12s;
    background:rgba(30,29,26,.94);color:#fff;padding:9px 12px;border-radius:9px;
    font-size:13px;line-height:1.5;max-width:260px;box-shadow:0 6px 22px rgba(0,0,0,.18);}
#tt b{font-size:14px;}
#tt .dim{color:#C9C3B2;}
.clickable{cursor:pointer;}
.clickable:hover{opacity:.72;}
</style>
</head>
<body>
<div id="wrap">
  <svg id="viz" role="img" aria-label="Nuage de bulles : longévité des prénoms en France, année par année"></svg>
  <div id="tt"></div>
</div>
<script>
const DATA=__DATA__;
/* année d'ouverture : modifiable via l'ancre d'URL, p. ex. viz1_bulles.html#1950 */
const Y0=(h=>h>=DATA.yearMin&&h<=DATA.yearMax?h:__YEAR0__)(+location.hash.slice(1));

/* ---- géométrie (viewBox fixe, page fluide) ---- */
const W=1500,H=880,ML=110,MR=40,MT=170,PB=690,SY=780,FY=852;
const X0=ML,X1=W-MR;
const x=d3.scaleLinear().domain([DATA.yearMin,DATA.yearMax]).range([X0,X1]);
const y=d3.scaleLinear().domain([0,122]).range([PB,MT]);
const r=d3.scaleSqrt().domain([0,DATA.maxN]).range([0,95]);   // aire ∝ naissances, comparable d'une année à l'autre
const fmt=new Intl.NumberFormat("fr-FR");
let year=Y0,timer=null;

const svg=d3.select("#viz").attr("viewBox",`0 0 ${W} ${H}`);
const wrap=document.getElementById("wrap"),tt=document.getElementById("tt");

/* ---- décor : grille horizontale + axe Y ---- */
const grid=svg.append("g");
d3.range(0,121,20).forEach(t=>{
  grid.append("line").attr("x1",X0).attr("x2",X1).attr("y1",y(t)).attr("y2",y(t))
      .attr("stroke","var(--grid)").attr("stroke-width",t===0?1.4:1);
  grid.append("text").attr("x",X0-14).attr("y",y(t)+5).attr("text-anchor","end")
      .attr("font-size",14).attr("fill","var(--muted)").text(t+" ans");
});
svg.append("line").attr("x1",X0).attr("x2",X0).attr("y1",MT-26).attr("y2",PB+16)
   .attr("stroke","var(--ink)").attr("stroke-width",1.2);

/* ---- millésime géant ---- */
svg.append("text").attr("x",X1).attr("y",48).attr("text-anchor","end")
   .attr("font-size",15).attr("font-weight",600).attr("letter-spacing","0.38em")
   .attr("fill","var(--muted)").text("ANNÉE");
const bigYear=svg.append("text").attr("x",X1).attr("y",140).attr("text-anchor","end")
   .attr("font-size",104).attr("font-weight",800).attr("letter-spacing","-0.02em")
   .attr("fill","var(--ink)").text(Y0);

/* ---- calques (bulles sous les pointillés, étiquettes au-dessus) ---- */
const layerB=svg.append("g"),layerG=svg.append("g"),layerL=svg.append("g");

/* titre d'axe par-dessus les bulles : Marie déborde en haut à gauche vers 1900-1915 */
svg.append("text").attr("x",26).attr("y",84).attr("font-size",22)
   .attr("font-weight",700).text("Longévité");

/* ---- slider posé sur l'axe des abscisses ---- */
const slider=svg.append("g");
slider.append("line").attr("x1",X0).attr("x2",X1).attr("y1",SY).attr("y2",SY)
      .attr("stroke","var(--ink)").attr("stroke-width",2);
d3.range(DATA.yearMin,DATA.yearMax+1,40).forEach(t=>{
  slider.append("text").attr("x",x(t)).attr("y",SY+30).attr("text-anchor","middle")
        .attr("font-size",15).attr("fill","var(--muted)").text(t);
});
const overlay=slider.append("rect").attr("x",X0-16).attr("width",X1-X0+32)
      .attr("y",SY-24).attr("height",48).attr("fill","transparent").style("cursor","pointer");
const handle=slider.append("circle").attr("cx",x(Y0)).attr("cy",SY).attr("r",10.5)
      .attr("fill","#fff").attr("stroke","var(--ink)").attr("stroke-width",2.5)
      .style("cursor","grab");
const drag=d3.drag().on("start drag",ev=>{stopPlay();setYear(x.invert(ev.x),true);});
handle.call(drag);overlay.call(drag);

/* ---- pied de page : lecture + légendes ---- */
const ICON_PLAY="M0,-8 L13,0 L0,8 Z";
const ICON_PAUSE="M0,-8 H5 V8 H0 Z M8,-8 H13 V8 H8 Z";
const play=svg.append("g").attr("class","clickable")
   .attr("transform",`translate(${X0},${FY-5})`).on("click",togglePlay);
play.append("rect").attr("x",-10).attr("y",-16).attr("width",230).attr("height",32)
    .attr("fill","transparent");
const playIcon=play.append("path").attr("d",ICON_PLAY).attr("fill","var(--ink)");
const playTxt=play.append("text").attr("x",26).attr("y",5).attr("font-size",15)
    .attr("fill","var(--soft)").text("Lecture année par année");

svg.append("text").attr("x",700).attr("y",FY-8).attr("text-anchor","middle")
   .attr("font-size",12).attr("fill","var(--muted)")
   .text("Une bulle = un prénom, placée à l'année de son pic de popularité");
svg.append("text").attr("x",700).attr("y",FY+8).attr("text-anchor","middle")
   .attr("font-size",12).attr("fill","var(--muted)")
   .text("Hauteur = années passées dans le top 100 national · aire = naissances de l'année affichée");

svg.append("circle").attr("cx",1086).attr("cy",FY-5).attr("r",5)
   .attr("fill","none").attr("stroke","var(--bubble)").attr("stroke-width",1.8);
svg.append("circle").attr("cx",1108).attr("cy",FY-5).attr("r",10)
   .attr("fill","none").attr("stroke","var(--bubble)").attr("stroke-width",1.8);
svg.append("text").attr("x",1128).attr("y",FY).attr("font-size",15)
   .attr("fill","var(--soft)").text("Naissances dans l'année");
svg.append("circle").attr("cx",1326).attr("cy",FY-5).attr("r",9)
   .attr("fill","none").attr("stroke","var(--ghost)").attr("stroke-width",1.6)
   .attr("stroke-dasharray","4 4");
svg.append("text").attr("x",1342).attr("y",FY).attr("font-size",15)
   .attr("fill","var(--soft)").text("Année précédente");

/* ---- rendu d'une année ---- */
const rowsFor=yy=>(DATA.years[yy]||[]).map(([i,v])=>({i,v,...DATA.names[i]}));
const valFS=d=>Math.min(18,Math.max(9,r(d.v)*0.27));
const showVal=d=>r(d.v)>=24;

/* étiquettes : police réduite pour tenir dans la bulle, puis élagage
   glouton des chevauchements (les plus grosses bulles sont servies d'abord) */
function layoutLabels(rows){
  const out=[];
  for(const d of rows){
    const rr=r(d.v);
    if(rr<14)continue;
    const fs=Math.min(34,Math.max(9.5,Math.min(rr*0.46,2.05*rr/(0.58*d.n.length))));
    if(fs*0.58*d.n.length>2.3*rr)continue;          // ne tient pas, même réduit
    const h=fs+(showVal(d)?valFS(d)*1.5:0);
    const w=Math.max(fs*0.6*d.n.length,showVal(d)?valFS(d)*0.62*String(d.v).length+4:0);
    const b={x0:x(d.p)-w/2,y0:y(d.l)-h/2,x1:x(d.p)+w/2,y1:y(d.l)+h/2};
    if(out.some(o=>b.x0<o.b.x1+4&&b.x1>o.b.x0-4&&b.y0<o.b.y1+2&&b.y1>o.b.y0-2))continue;
    out.push({...d,fs,b});
  }
  return out;
}

function render(dur){
  const rows=rowsFor(year).sort((a,b)=>b.v-a.v);
  const cur=new Map(rows.map(d=>[d.i,d.v]));
  const ghosts=[];                       // année précédente : sortie du top, ou taille nettement différente
  (DATA.years[year-1]||[]).forEach(([i,v])=>{
    const c=cur.get(i);
    if(c===undefined||Math.abs(r(c)-r(v))>=3)ghosts.push({i,v,...DATA.names[i]});
  });
  const t=svg.transition().duration(dur).ease(d3.easeCubicOut);

  layerB.selectAll("circle").data(rows,d=>d.i)
    .join(e=>e.append("circle")
        .attr("cx",d=>x(d.p)).attr("cy",d=>y(d.l)).attr("r",0)
        .attr("fill","var(--bubble)").attr("stroke","var(--bg)").attr("stroke-width",1.4)
        .on("mouseenter",(ev,d)=>{d3.select(ev.currentTarget).attr("stroke","var(--ink)").attr("stroke-width",1.6);showTT(ev,d);})
        .on("mousemove",moveTT)
        .on("mouseleave",ev=>{d3.select(ev.currentTarget).attr("stroke","var(--bg)").attr("stroke-width",1.4);tt.style.opacity=0;}),
      u=>u,
      ex=>ex.transition(t).attr("r",0).remove())
    .sort((a,b)=>b.v-a.v)               // grosses bulles derrière
    .transition(t).attr("r",d=>r(d.v));

  layerG.selectAll("circle").data(ghosts,d=>d.i)
    .join(e=>e.append("circle")
        .attr("cx",d=>x(d.p)).attr("cy",d=>y(d.l)).attr("fill","none")
        .attr("stroke","var(--ghost)").attr("stroke-width",1.6)
        .attr("stroke-dasharray","5 5").attr("opacity",0),
      u=>u,
      ex=>ex.transition(t).attr("opacity",0).remove())
    .attr("r",d=>r(d.v))
    .transition(t).attr("opacity",.9);

  const lab=layerL.selectAll("g.lbl").data(layoutLabels(rows),d=>d.i)
    .join(e=>{const g=e.append("g").attr("class","lbl")
        .attr("transform",d=>`translate(${x(d.p)},${y(d.l)})`).attr("opacity",0);
        g.append("text").attr("class","nm").attr("text-anchor","middle");
        g.append("text").attr("class","vl").attr("text-anchor","middle");
        return g;},
      u=>u,
      ex=>ex.transition(t).attr("opacity",0).remove())
    .order();
  lab.transition(t).attr("opacity",1);
  lab.select(".nm").text(d=>d.n)
     .transition(t).attr("font-size",d=>d.fs)
     .attr("y",d=>showVal(d)?-d.fs*0.18:d.fs*0.35);
  lab.select(".vl").text(d=>showVal(d)?fmt.format(d.v):"")
     .transition(t).attr("font-size",valFS)
     .attr("y",d=>valFS(d)*1.25+3);

  bigYear.text(year);
  handle.transition(t).attr("cx",x(year));
}

/* ---- interactions ---- */
function setYear(v,fast){
  v=Math.round(Math.max(DATA.yearMin,Math.min(DATA.yearMax,v)));
  if(v===year)return;
  year=v;render(fast?90:430);
}
function togglePlay(){
  if(timer)return stopPlay();
  if(year>=DATA.yearMax){year=DATA.yearMin;render(0);}
  playIcon.attr("d",ICON_PAUSE);playTxt.text("Pause");
  timer=d3.interval(()=>{year<DATA.yearMax?setYear(year+1,false):stopPlay();},470);
}
function stopPlay(){
  if(!timer)return;
  timer.stop();timer=null;
  playIcon.attr("d",ICON_PLAY);playTxt.text("Lecture année par année");
}
function showTT(ev,d){
  tt.innerHTML=`<b>${d.n}</b> <span class="dim">· prénom ${d.s==="F"?"féminin":"masculin"}</span><br>`+
    `${fmt.format(d.v)} naissances en ${year}<br>`+
    `<span class="dim">Pic de popularité : ${d.p} — ${d.l} ans dans le top 100</span>`;
  tt.style.opacity=1;moveTT(ev);
}
function moveTT(ev){
  const b=wrap.getBoundingClientRect();
  let lx=ev.clientX-b.left+16,ly=ev.clientY-b.top-12;
  if(lx+280>b.width)lx-=310;
  tt.style.left=lx+"px";tt.style.top=ly+"px";
}
d3.select(window).on("keydown",ev=>{
  if(ev.key==="ArrowRight"){stopPlay();setYear(year+1,true);}
  else if(ev.key==="ArrowLeft"){stopPlay();setYear(year-1,true);}
});
window.viz={setYear:v=>{stopPlay();setYear(v,false);},get year(){return year;}};

render(0);
</script>
</body>
</html>
"""

# ----------------------------------------------------------------- écriture
html = (TEMPLATE
        .replace("__DATA__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        .replace("__YEAR0__", str(YEAR0)))

out = ROOT / "output" / "viz1_bulles.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")
print(f"OK {out.relative_to(ROOT)} ({out.stat().st_size/1024:.0f} Ko)")
