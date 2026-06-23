# -*- coding: utf-8 -*-
"""Viz 1 — Nuage de bulles « longévité des prénoms » (maquette v2 + filtres).

Génère output/viz1_bulles.html : page autonome D3.js fidèle à
sketches/viz1-nuage_de_bulles_v2.png :
  - fond crème, bulles monochromes bleu ardoise, prénom + naissances
    écrits en blanc dans les bulles assez grandes ;
  - millésime géant en haut à droite, « Longévité » en titre d'axe ;
  - slider intégré DIRECTEMENT sur l'axe des abscisses (même échelle
    que l'année du pic) : glisser la poignée change l'année ;
  - bouton « Lecture année par année » (animation), flèches ← → au clavier ;
  - cercle pointillé = taille de la bulle l'année précédente.

Anti-chevauchement : un layout de forces écarte légèrement les bulles
(collision) tout en les ancrant sur leur vraie position (X = année du pic,
Y = longévité, plus ferme pour rester lisible) ; les bulles sont aussi
légèrement transparentes pour deviner celles qui sont enfouies.

Couleur : part de filles parmi les naissances de l'ANNÉE AFFICHÉE, sur une
échelle divergente garçons (bleu) ↔ mixte (neutre) ↔ filles (rose). La teinte
évolue donc avec le curseur — un prénom qui change de genre au fil du temps
(Camille…) vire visiblement du bleu au rose.

Filtres (barre au-dessus du graphique) :
  - mini-slider « TOP n » : ne garder que les n prénoms les plus donnés
    de l'année (1 à 100) ;
  - champ « Suivre un prénom… » (liste déroulante avec recherche) : met le
    prénom en évidence (terracotta), estompe le reste, affiche sa courbe de
    naissances 1900-2020 et le garde visible même hors du Top n.
    Cliquer une bulle suit aussi son prénom ; Échap ou ✕ pour quitter.

Vue partageable par l'ancre d'URL : viz1_bulles.html#annee=1964&top=50&nom=Brigitte

Usage : python scripts/build_viz1.py   (après scripts/prep_data.py)
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
YEAR0 = 1985   # année affichée à l'ouverture, comme sur la maquette
TOP0 = 30      # filtre Top n par défaut (densité de la maquette)

# ------------------------------------------------------------------ données
df = pd.read_csv(ROOT / "DATA" / "data_viz1_anim.csv")

# prénoms ordonnés par popularité cumulée (ordre des suggestions du dropdown)
totals = df.groupby("preusuel", as_index=False).nombre.sum()
meta = df.drop_duplicates(subset="preusuel")[["preusuel", "longevity", "peak_year"]]
uniq = (totals.sort_values("nombre", ascending=False)
        .merge(meta, on="preusuel").reset_index(drop=True))
idx = {r.preusuel: i for i, r in enumerate(uniq.itertuples(index=False))}

# payload compact : 1 entrée par prénom (x, y fixes) ; la couleur (part de filles)
# est portée PAR ANNÉE -> chaque ligne annuelle = [id, naissances, % filles cette année]
payload = {
    "names": [
        {"n": str(r.preusuel).title(), "l": int(r.longevity), "p": int(r.peak_year)}
        for r in uniq.itertuples(index=False)
    ],
    "years": {
        int(y): [[idx[r.preusuel], int(r.nombre), int(r.fy)]
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
  --masc:#88A9D2; --mid:#B49EAC; --fem:#CB7E9B; --ghost:#B3AC9B; --soft:#6F6A5E;
  --accent:#D9714E; --accent-d:#A04A2B;
}
html,body{margin:0;background:var(--bg);}
body{font-family:"Segoe UI",-apple-system,"Helvetica Neue",Arial,sans-serif;color:var(--ink);}
#wrap{position:relative;max-width:1500px;margin:0 auto;padding:6px 18px 24px;}
#bar{display:flex;justify-content:flex-end;align-items:center;gap:30px;
     flex-wrap:wrap;padding:12px 6px 2px;font-size:13px;color:var(--soft);}
#legend{display:flex;align-items:center;gap:8px;margin-right:auto;font-size:12.5px;}
#legend .grad{width:104px;height:11px;border-radius:6px;
       background:linear-gradient(90deg,var(--masc),var(--mid),var(--fem));}
#bar .lab{letter-spacing:.2em;font-weight:600;font-size:11.5px;color:var(--muted);}
#bar .ctl{display:flex;align-items:center;gap:10px;}
#topn{width:150px;accent-color:var(--ink);}
#topnv{font-weight:700;color:var(--ink);min-width:2.2em;}
#who{background:transparent;border:none;border-bottom:1px solid #C9C3B2;
     padding:4px 2px;font:inherit;font-size:13px;color:var(--ink);width:210px;outline:none;}
#who:focus{border-bottom-color:var(--ink);}
#who::placeholder{color:var(--muted);}
#clear{background:none;border:none;color:var(--muted);cursor:pointer;
       font-size:15px;padding:2px 5px;visibility:hidden;}
#clear:hover{color:var(--ink);}
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
  <div id="bar">
    <div id="legend" title="Couleur = part de filles parmi les naissances de l'année affichée">
      <span>Garçons</span><span class="grad"></span><span>Filles</span>
    </div>
    <div class="ctl" title="Ne garder que les n prénoms les plus donnés de l'année">
      <span class="lab">TOP</span>
      <input type="range" id="topn" min="1" max="100" step="1" value="__TOP0__"
             aria-label="Nombre de prénoms affichés (top n de l'année)">
      <span id="topnv">__TOP0__</span>
    </div>
    <div class="ctl">
      <input id="who" list="dl" placeholder="Suivre un prénom…" autocomplete="off"
             aria-label="Mettre un prénom en évidence">
      <datalist id="dl"></datalist>
      <button id="clear" title="Ne plus suivre (Échap)">✕</button>
    </div>
  </div>
  <svg id="viz" role="img" aria-label="Nuage de bulles : longévité des prénoms en France, année par année"></svg>
  <div id="tt"></div>
</div>
<script>
const DATA=__DATA__;

/* ---- géométrie (viewBox fixe, page fluide) ---- */
const W=1500,H=880,ML=110,MR=40,MT=170,PB=690,SY=780,FY=852;
const X0=ML,X1=W-MR;
const x=d3.scaleLinear().domain([DATA.yearMin,DATA.yearMax]).range([X0,X1]);
const y=d3.scaleLinear().domain([0,122]).range([PB,MT]);
const r=d3.scaleSqrt().domain([0,DATA.maxN]).range([0,95]);   // aire ∝ naissances, comparable d'une année à l'autre
const fmt=new Intl.NumberFormat("fr-FR");

/* couleur = part de filles PARMI les naissances de l'année affichée, sur une
   échelle divergente garçons↔mixte↔filles. La teinte évolue donc avec le
   curseur : un prénom qui bascule de genre (Camille…) change de couleur.
   Le focus n'écrase pas la couleur : anneau sombre (strokeOf/strokeW) + estompage. */
const C_MASC="#88A9D2",C_MID="#B49EAC",C_FEM="#CB7E9B";
const sexScale=d3.scaleLinear().domain([0,50,100]).range([C_MASC,C_MID,C_FEM])
                .interpolate(d3.interpolateLab).clamp(true);
const sexColor=fy=>sexScale(fy);
const sexLabel=fy=>fy>=85?"Prénom féminin":fy<=15?"Prénom masculin":`Mixte — ${fy}% de filles`;
const strokeOf=d=>d.i===focusI?"var(--ink)":"var(--bg)";
const strokeW=d=>d.i===focusI?2.6:1.2;

/* ---- état + ancre d'URL partageable ---- */
const label=i=>DATA.names[i].n;
const byName=new Map(DATA.names.map((d,i)=>[d.n.toLowerCase(),i]));
function resolveName(s){
  s=(s||"").trim().toLowerCase();
  return s&&byName.has(s)?byName.get(s):null;
}
let year=__YEAR0__,topN=__TOP0__,focusI=null,timer=null;
(()=>{ // #1950 (forme courte) ou #annee=1950&top=50&nom=Marie
  const h=location.hash.slice(1);
  if(/^\d{4}$/.test(h)){const v=+h;if(v>=DATA.yearMin&&v<=DATA.yearMax)year=v;return;}
  const p=new URLSearchParams(h);
  const a=+p.get("annee");if(a>=DATA.yearMin&&a<=DATA.yearMax)year=a;
  const t=+p.get("top");if(t>=1&&t<=100)topN=t;
  focusI=resolveName(p.get("nom"));
})();
function writeHash(){
  const s=`annee=${year}&top=${topN}`+(focusI!=null?`&nom=${encodeURIComponent(label(focusI))}`:"");
  history.replaceState(null,"","#"+s);
}

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
   .attr("fill","var(--ink)").text(year);

/* ---- calques (bulles sous les pointillés, étiquettes au-dessus) ---- */
const layerB=svg.append("g"),layerG=svg.append("g"),layerL=svg.append("g");

/* titre d'axe par-dessus les bulles : Marie déborde en haut à gauche vers 1900-1915 */
svg.append("text").attr("x",26).attr("y",84).attr("font-size",22)
   .attr("font-weight",700).text("Longévité");

/* ---- courbe du prénom suivi (mode focus) ---- */
const SX0=360,SW=400,SH=88,SB=SH-20;
const spark=svg.append("g").attr("transform",`translate(${SX0},28)`).attr("opacity",0)
   .style("pointer-events","none");
const sparkX=d3.scaleLinear().domain([DATA.yearMin,DATA.yearMax]).range([0,SW]);
spark.append("line").attr("x1",0).attr("x2",SW).attr("y1",SB).attr("y2",SB)
   .attr("stroke","var(--muted)").attr("stroke-width",1);
spark.append("text").attr("x",0).attr("y",SB+15).attr("font-size",10.5)
   .attr("fill","var(--muted)").text(DATA.yearMin);
spark.append("text").attr("x",SW).attr("y",SB+15).attr("text-anchor","end")
   .attr("font-size",10.5).attr("fill","var(--muted)").text(DATA.yearMax);
const sparkTitle=spark.append("text").attr("x",0).attr("y",6).attr("font-size",12.5)
   .attr("font-weight",700).attr("letter-spacing",".08em").attr("fill","var(--accent-d)");
const sparkInfo=spark.append("text").attr("x",SW).attr("y",6).attr("text-anchor","end")
   .attr("font-size",11.5).attr("fill","var(--soft)");
const sparkArea=spark.append("path").attr("fill","var(--accent)").attr("opacity",.14);
const sparkLine=spark.append("path").attr("fill","none")
   .attr("stroke","var(--accent)").attr("stroke-width",1.7);
const sparkDot=spark.append("circle").attr("r",3.6).attr("fill","var(--accent-d)");
let sparkFor=null,sparkSeries=null,sparkY=null;
function drawSpark(){
  if(focusI==null){spark.attr("opacity",0);sparkFor=null;return;}
  if(sparkFor!==focusI){
    sparkSeries=d3.range(DATA.yearMin,DATA.yearMax+1).map(yy=>{
      const e=(DATA.years[yy]||[]).find(a=>a[0]===focusI);
      return e?e[1]:null;
    });
    sparkY=d3.scaleLinear().domain([0,d3.max(sparkSeries)]).range([SB,16]);
    const ix=i=>sparkX(DATA.yearMin+i),ok=v=>v!=null;
    sparkArea.attr("d",d3.area().defined(ok).x((v,i)=>ix(i)).y0(SB).y1(v=>sparkY(v))(sparkSeries));
    sparkLine.attr("d",d3.line().defined(ok).x((v,i)=>ix(i)).y(v=>sparkY(v))(sparkSeries));
    sparkTitle.text(DATA.names[focusI].n.toUpperCase());
    sparkFor=focusI;
  }
  const v=sparkSeries[year-DATA.yearMin];
  sparkDot.attr("opacity",v!=null?1:0);
  if(v!=null)sparkDot.attr("cx",sparkX(year)).attr("cy",sparkY(v));
  sparkInfo.text(v!=null?`${year} : ${fmt.format(v)} naissances`:`${year} : hors top 100`);
  spark.attr("opacity",1);
}

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
const handle=slider.append("circle").attr("cx",x(year)).attr("cy",SY).attr("r",10.5)
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
   .attr("fill","none").attr("stroke","var(--soft)").attr("stroke-width",1.8);
svg.append("circle").attr("cx",1108).attr("cy",FY-5).attr("r",10)
   .attr("fill","none").attr("stroke","var(--soft)").attr("stroke-width",1.8);
svg.append("text").attr("x",1128).attr("y",FY).attr("font-size",15)
   .attr("fill","var(--soft)").text("Naissances dans l'année");
svg.append("circle").attr("cx",1326).attr("cy",FY-5).attr("r",9)
   .attr("fill","none").attr("stroke","var(--ghost)").attr("stroke-width",1.6)
   .attr("stroke-dasharray","4 4");
svg.append("text").attr("x",1342).attr("y",FY).attr("font-size",15)
   .attr("fill","var(--soft)").text("Année précédente");

/* ---- rendu d'une année ---- */
/* gf = part de filles cette année-là. NB : ne pas nommer ce champ « fy »,
   réservé par d3-force (position Y figée) — cela écraserait le placement. */
const rowsFor=yy=>(DATA.years[yy]||[]).map(([i,v,gf],k)=>({i,v,gf,rank:k+1,...DATA.names[i]}));
function visibleRows(yy){              // filtre Top n + prénom suivi toujours visible
  const all=rowsFor(yy);
  const rows=all.slice(0,topN);
  if(focusI!=null&&!rows.some(d=>d.i===focusI)){
    const f=all.find(d=>d.i===focusI);
    if(f)rows.push(f);
  }
  return rows;
}
const valFS=d=>Math.min(18,Math.max(9,r(d.v)*0.27));
const showVal=d=>r(d.v)>=24;

/* anti-chevauchement : on écarte les bulles d'un cran tout en les gardant
   ancrées sur leur vraie position (X = année du pic, Y = longévité). Les
   positions résolues sont mémorisées pour des transitions continues d'une
   année à l'autre. Y plus ferme que X : la longévité doit rester lisible. */
const pos=new Map();
function resolveLayout(rows){
  rows.forEach(d=>{
    d.ax=x(d.p);d.ay=y(d.l);
    const p=pos.get(d.i);
    d.x=p?p.x:d.ax+(Math.random()-0.5);
    d.y=p?p.y:d.ay+(Math.random()-0.5);
  });
  d3.forceSimulation(rows).alpha(0.9).alphaDecay(0.09).velocityDecay(0.4)
    .force("x",d3.forceX(d=>d.ax).strength(0.3))
    .force("y",d3.forceY(d=>d.ay).strength(0.6))
    .force("collide",d3.forceCollide(d=>r(d.v)+0.6).strength(0.85).iterations(2))
    .stop().tick(140);
  rows.forEach(d=>pos.set(d.i,{x:d.x,y:d.y}));
  return rows;
}

/* étiquettes : police réduite pour tenir dans la bulle, puis élagage
   glouton des chevauchements (prénom suivi d'abord, puis grosses bulles) */
function layoutLabels(rows){
  const out=[];
  const ordered=focusI==null?rows:
    [...rows].sort((a,b)=>(b.i===focusI)-(a.i===focusI)||b.v-a.v);
  for(const d of ordered){
    const rr=r(d.v),foc=d.i===focusI;
    if(!foc&&rr<14)continue;
    const fs=Math.min(34,Math.max(foc?11:9.5,Math.min(rr*0.46,2.05*rr/(0.58*d.n.length))));
    if(fs*0.58*d.n.length>2.3*rr){
      if(!foc)continue;                // ne tient pas, même réduit
      const w=13*0.58*d.n.length;      // prénom suivi : étiquette sombre au-dessus
      out.push({...d,fs:13,oa:true,
        b:{x0:d.x-w/2,y0:d.y-rr-22,x1:d.x+w/2,y1:d.y-rr-4}});
      continue;
    }
    const h=fs+(showVal(d)?valFS(d)*1.5:0);
    const w=Math.max(fs*0.6*d.n.length,showVal(d)?valFS(d)*0.62*String(d.v).length+4:0);
    const b={x0:d.x-w/2,y0:d.y-h/2,x1:d.x+w/2,y1:d.y+h/2};
    if(out.some(o=>b.x0<o.b.x1+4&&b.x1>o.b.x0-4&&b.y0<o.b.y1+2&&b.y1>o.b.y0-2))continue;
    out.push({...d,fs,b});
  }
  return out;
}

function render(dur){
  const rows=resolveLayout(visibleRows(year).sort((a,b)=>b.v-a.v));
  const cur=new Map(rows.map(d=>[d.i,d.v]));
  const ghosts=[];                     // année précédente : sortie du top n, ou taille nettement différente
  for(const d of visibleRows(year-1)){
    if(r(d.v)<10)continue;
    const c=cur.get(d.i);
    if(c===undefined||Math.abs(r(c)-r(d.v))>=3){
      const p=pos.get(d.i);
      ghosts.push({...d,gx:p?p.x:x(d.p),gy:p?p.y:y(d.l)});
    }
  }
  const t=svg.transition().duration(dur).ease(d3.easeCubicOut);
  const quick=dur<200;                  // scrubbing rapide : retirer les sortants sans transition (anti-fuite de nœuds)
  const dimmed=i=>focusI!=null&&i!==focusI;
  const bubOp=d=>focusI==null?0.84:(d.i===focusI?1:0.13);   // légère transparence : on devine les bulles enfouies

  layerB.selectAll("circle").data(rows,d=>d.i)
    .join(e=>e.append("circle")
        .attr("cx",d=>d.x).attr("cy",d=>d.y).attr("r",0)
        .attr("fill",d=>sexColor(d.gf))
        .attr("stroke",strokeOf).attr("stroke-width",strokeW).attr("opacity",bubOp)
        .style("cursor","pointer")
        .on("click",(ev,d)=>setFocus(d.i===focusI?null:d.i))
        .on("mouseenter",(ev,d)=>{d3.select(ev.currentTarget).attr("stroke","var(--ink)").attr("stroke-width",1.8).attr("opacity",1).raise();showTT(ev,d);})
        .on("mousemove",moveTT)
        .on("mouseleave",(ev,d)=>{d3.select(ev.currentTarget).attr("stroke",strokeOf(d)).attr("stroke-width",strokeW(d)).attr("opacity",bubOp(d));tt.style.opacity=0;}),
      u=>u,
      ex=>quick?ex.remove():ex.transition(t).attr("r",0).remove())
    .sort((a,b)=>b.v-a.v)              // grosses bulles derrière
    .transition(t).attr("cx",d=>d.x).attr("cy",d=>d.y).attr("r",d=>r(d.v))
    .attr("fill",d=>sexColor(d.gf))
    .attr("stroke",strokeOf).attr("stroke-width",strokeW)
    .attr("opacity",bubOp);

  layerG.selectAll("circle").data(ghosts,d=>d.i)
    .join(e=>e.append("circle")
        .attr("cx",d=>d.gx).attr("cy",d=>d.gy).attr("fill","none")
        .attr("stroke","var(--ghost)").attr("stroke-width",1.6)
        .attr("stroke-dasharray","5 5").attr("opacity",0),
      u=>u,
      ex=>quick?ex.remove():ex.transition(t).attr("opacity",0).remove())
    .attr("r",d=>r(d.v))
    .transition(t).attr("cx",d=>d.gx).attr("cy",d=>d.gy)
    .attr("opacity",d=>dimmed(d.i)?.1:.85);

  const lab=layerL.selectAll("g.lbl").data(layoutLabels(rows),d=>d.i)
    .join(e=>{const g=e.append("g").attr("class","lbl")
        .attr("transform",d=>`translate(${d.x},${d.y})`).attr("opacity",0);
        g.append("text").attr("class","nm").attr("text-anchor","middle");
        g.append("text").attr("class","vl").attr("text-anchor","middle");
        return g;},
      u=>u,
      ex=>quick?ex.remove():ex.transition(t).attr("opacity",0).remove())
    .order();
  lab.transition(t).attr("opacity",d=>dimmed(d.i)?.15:1)
     .attr("transform",d=>`translate(${d.x},${d.y})`);
  lab.select(".nm").text(d=>d.n)
     .attr("fill",d=>d.oa?"var(--accent-d)":"#fff")
     .transition(t).attr("font-size",d=>d.fs)
     .attr("y",d=>d.oa?-(r(d.v)+9):(showVal(d)?-d.fs*0.18:d.fs*0.35));
  lab.select(".vl").text(d=>!d.oa&&showVal(d)?fmt.format(d.v):"")
     .transition(t).attr("font-size",valFS)
     .attr("y",d=>valFS(d)*1.25+3);

  bigYear.text(year);
  handle.transition(t).attr("cx",x(year));
  drawSpark();
}

/* ---- interactions ---- */
function setYear(v,fast){
  v=Math.round(Math.max(DATA.yearMin,Math.min(DATA.yearMax,v)));
  if(v===year)return;
  year=v;render(fast?90:430);writeHash();
}
const topn=document.getElementById("topn"),topnv=document.getElementById("topnv");
const who=document.getElementById("who"),clearBtn=document.getElementById("clear");
document.getElementById("dl").innerHTML=
  DATA.names.map((d,i)=>`<option value="${label(i)}"></option>`).join("");
topn.value=topN;topnv.textContent=topN;
topn.addEventListener("input",()=>{
  topN=+topn.value;topnv.textContent=topN;render(140);writeHash();
});
function setFocus(i){
  focusI=i;
  who.value=i!=null?label(i):"";
  clearBtn.style.visibility=i!=null?"visible":"hidden";
  render(280);writeHash();
}
who.addEventListener("change",()=>setFocus(resolveName(who.value)));
clearBtn.addEventListener("click",()=>setFocus(null));
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
  tt.innerHTML=`<b>${d.n}</b> <span class="dim">· ${sexLabel(d.gf)}</span><br>`+
    `${fmt.format(d.v)} naissances en ${year} <span class="dim">· n° ${d.rank} de l'année</span><br>`+
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
  if(ev.target===who)return;
  if(ev.key==="ArrowRight"){stopPlay();setYear(year+1,true);}
  else if(ev.key==="ArrowLeft"){stopPlay();setYear(year-1,true);}
  else if(ev.key==="Escape"){setFocus(null);}
});
window.viz={
  setYear:v=>{stopPlay();setYear(v,false);},
  setTop:v=>{topN=Math.max(1,Math.min(100,Math.round(v)));topn.value=topN;topnv.textContent=topN;render(140);writeHash();},
  setFocus:s=>setFocus(typeof s==="number"?s:resolveName(s)),
  get state(){return {year,topN,focus:focusI!=null?label(focusI):null};}
};

if(focusI!=null){who.value=label(focusI);clearBtn.style.visibility="visible";}
render(0);
</script>
</body>
</html>
"""

# ----------------------------------------------------------------- écriture
html = (TEMPLATE
        .replace("__DATA__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        .replace("__YEAR0__", str(YEAR0))
        .replace("__TOP0__", str(TOP0)))

out = ROOT / "output" / "viz1_bulles.html"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(html, encoding="utf-8")
print(f"OK {out.relative_to(ROOT)} ({out.stat().st_size/1024:.0f} Ko, "
      f"{len(payload['names'])} prénoms, {len(payload['years'])} années)")
