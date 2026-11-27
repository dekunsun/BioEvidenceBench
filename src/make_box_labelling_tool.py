"""Build the gold-box labelling tool for Level 3 (image) grounding (exploratory, DEVIATIONS.md).

    python src/make_box_labelling_tool.py            -> results/level3_anchor/box_labelling_test.html

One self-contained HTML file (scans embedded) that the author opens locally in a browser. For every
primary-field gold mention on the 16 test pages (taxon, person, locality, institution, date: 350 rows),
it shows the mention in its context from the expert transcription and a BLANK scan. The author drags
a tight box around the printed value. A value broken across lines gets one box per line segment.

Nothing is pre-filled: no OCR box, no model box, no hOCR box is ever drawn or loaded, so the gold
boxes cannot be anchored on any route under test. The only text shown is the author's own gold.
Progress is kept in the browser (localStorage); "Export CSV" downloads
  page_id, start, end, field, text, box_index, x0, y0, x1, y1, flag, seconds
in scan pixel coordinates. The delivered CSV is archived unchanged in gold/received/ before use.

Scans: bhl-impact-gt page images (CC BY 3.0, IMPACT / BHL). The HTML is not committed (it embeds
the images); this script rebuilds it.
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pandas as pd
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from common import DATA, ROOT  # noqa: E402
from score import load_gold, page_text  # noqa: E402

PRIMARY = ["taxon", "person", "locality", "institution", "date"]
OUT = ROOT / "results" / "level3_anchor" / "box_labelling_test.html"
CTX = 60


def build() -> Path:
    split = pd.read_csv(DATA / "sample_split.csv")
    test = split[split.split == "test"]
    gold = load_gold(ROOT / "gold" / "gold_mentions_gloria_test.csv")
    gold = gold[gold.field.isin(PRIMARY)]
    pages = []
    for r in test.itertuples():
        pid = int(r.PageID)
        img_path = DATA / "cache" / "images" / f"{pid}.webp"
        with Image.open(img_path) as im:
            w, h = im.size
        text = page_text("expert", pid)
        ms = []
        for g in gold[gold.page_id == pid].sort_values("start").itertuples():
            ms.append({"start": int(g.start), "end": int(g.end), "field": g.field, "text": g.text,
                       "before": text[max(0, g.start - CTX):g.start], "after": text[g.end:g.end + CTX]})
        pages.append({"page_id": pid, "book": r.book, "w": w, "h": h,
                      "img": "data:image/webp;base64," + base64.b64encode(img_path.read_bytes()).decode(),
                      "mentions": ms})
    n = sum(len(p["mentions"]) for p in pages)
    html = TEMPLATE.replace("__DATA__", json.dumps(pages, ensure_ascii=False)).replace("__N__", str(n))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"{OUT} ({n} mentions on {len(pages)} pages, {OUT.stat().st_size / 1e6:.1f} MB)")
    return OUT


TEMPLATE = r"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gold boxes · test pages</title>
<style>
:root{--ink:#1d2433;--soft:#5b6475;--line:#d9dde5;--bg:#f6f7f9;--acc:#c0392b;--ok:#1e7d4f}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
header{display:flex;gap:12px;align-items:center;padding:8px 12px;background:#fff;border-bottom:1px solid var(--line);flex-wrap:wrap}
header b{font-size:15px}button,select{font:inherit;padding:4px 10px;border:1px solid var(--line);border-radius:6px;background:#fff;cursor:pointer}
button.primary{background:var(--ink);color:#fff;border-color:var(--ink)}
main{display:flex;height:calc(100vh - 50px)}
#side{width:360px;min-width:300px;overflow:auto;background:#fff;border-right:1px solid var(--line);padding:10px}
#help{font-size:12.5px;color:var(--soft);background:var(--bg);border-radius:6px;padding:8px;margin-bottom:10px}
.m{padding:7px 8px;border:1px solid var(--line);border-radius:6px;margin-bottom:6px;cursor:pointer}
.m.cur{border-color:var(--acc);box-shadow:0 0 0 2px #f4d4d0}
.m .f{font-size:11px;color:var(--soft);text-transform:uppercase;letter-spacing:.04em}
.m .c{font-family:Georgia,serif;white-space:pre-wrap;word-break:break-word}
.m mark{background:#ffe08a;padding:0 1px}
.m .st{font-size:11.5px;margin-top:3px}.done{color:var(--ok)}.flag{color:var(--acc)}
#wrap{flex:1;position:relative;overflow:hidden;background:#3b3f47;cursor:crosshair}
canvas{position:absolute;left:0;top:0}
#bar{display:flex;gap:6px;margin:8px 0;flex-wrap:wrap}
</style></head><body>
<header><b>Gold boxes · 16 test pages</b>
<select id="pg"></select><span id="prog"></span>
<button id="exp" class="primary">Export CSV</button><span id="saved" style="color:var(--soft);font-size:12px"></span></header>
<main><div id="side">
<div id="help">在<b>空白扫描图</b>上为高亮的值拖出一个<b>紧贴墨迹</b>的框。跨行的值每行画一个框。
滚轮缩放，按住空格（或右键）拖动平移。<br>Enter 下一个 · Backspace 删最后一个框 · 找不到用「找不到」。
不预填任何框；只按扫描图判断。进度自动保存在本浏览器。</div>
<div id="bar"><button id="prev">← 上一个</button><button id="next" class="primary">下一个 →</button>
<button id="undo">删最后一个框</button><button id="nf">找不到</button><button id="uns">不确定</button></div>
<div id="list"></div></div>
<div id="wrap"><canvas id="cv"></canvas></div></main>
<script>
const PAGES=__DATA__, N=__N__, KEY='gold_boxes_test_v1';
let st={};try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){st={}}
const id=(p,m)=>p.page_id+':'+m.start+':'+m.end+':'+m.field;
let pi=0,mi=0,img=new Image(),z=1,ox=0,oy=0,drag=null,pan=null,space=false,t0=Date.now();
const cv=document.getElementById('cv'),cx=cv.getContext('2d'),wrap=document.getElementById('wrap');
function rec(){const p=PAGES[pi],m=p.mentions[mi];if(!m)return null;const k=id(p,m);st[k]=st[k]||{boxes:[],flag:'',sec:0};return st[k]}
function save(){try{localStorage.setItem(KEY,JSON.stringify(st));document.getElementById('saved').textContent='已保存 '+new Date().toLocaleTimeString()}catch(e){document.getElementById('saved').textContent='未能自动保存，请及时导出'}}
function tick(){const r=rec();if(r){r.sec+=Math.round((Date.now()-t0)/1000)}t0=Date.now()}
function done(r){return r&&(r.boxes.length>0||r.flag==='not_found')}
function prog(){let d=0;for(const p of PAGES)for(const m of p.mentions)if(done(st[id(p,m)]))d++;document.getElementById('prog').textContent=d+' / '+N+' 已完成'}
function fillSel(){const s=document.getElementById('pg');s.innerHTML='';PAGES.forEach((p,i)=>{const o=document.createElement('option');o.value=i;o.textContent=p.book+' '+p.page_id+' ('+p.mentions.length+')';s.appendChild(o)});s.value=pi;s.onchange=()=>{tick();pi=+s.value;mi=0;load()}}
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function list(){const L=document.getElementById('list');L.innerHTML='';const p=PAGES[pi];p.mentions.forEach((m,i)=>{const r=st[id(p,m)];const d=document.createElement('div');d.className='m'+(i===mi?' cur':'');
d.innerHTML='<div class="f">'+m.field+'</div><div class="c">…'+esc(m.before)+'<mark>'+esc(m.text)+'</mark>'+esc(m.after)+'…</div><div class="st">'+(r&&r.flag==='not_found'?'<span class="flag">找不到</span>':r&&r.boxes.length?'<span class="done">'+r.boxes.length+' 个框'+(r.flag==='unsure'?' · 不确定':'')+'</span>':'')+'</div>';
d.onclick=()=>{tick();mi=i;list();draw()};L.appendChild(d);if(i===mi)setTimeout(()=>d.scrollIntoView({block:'nearest'}),0)})}
function fit(){const W=wrap.clientWidth,H=wrap.clientHeight,p=PAGES[pi];z=Math.min(W/p.w,H/p.h);ox=(W-p.w*z)/2;oy=(H-p.h*z)/2}
function load(){img=new Image();img.onload=()=>{fit();draw()};img.src=PAGES[pi].img;list();prog()}
function draw(){cv.width=wrap.clientWidth;cv.height=wrap.clientHeight;cx.setTransform(1,0,0,1,0,0);cx.clearRect(0,0,cv.width,cv.height);cx.setTransform(z,0,0,z,ox,oy);cx.drawImage(img,0,0);
const p=PAGES[pi];p.mentions.forEach((m,i)=>{const r=st[id(p,m)];if(!r)return;for(const b of r.boxes){cx.lineWidth=(i===mi?2.5:1.5)/z;cx.strokeStyle=i===mi?'#e74c3c':'rgba(80,160,255,.8)';cx.strokeRect(b[0],b[1],b[2]-b[0],b[3]-b[1])}});
if(drag){cx.lineWidth=2/z;cx.strokeStyle='#e74c3c';cx.setLineDash([6/z,4/z]);cx.strokeRect(drag.x0,drag.y0,drag.x1-drag.x0,drag.y1-drag.y0);cx.setLineDash([])}}
function pt(e){const r=cv.getBoundingClientRect();return{x:(e.clientX-r.left-ox)/z,y:(e.clientY-r.top-oy)/z}}
cv.addEventListener('contextmenu',e=>e.preventDefault());
cv.addEventListener('mousedown',e=>{if(e.button===2||space){pan={x:e.clientX,y:e.clientY,ox,oy};return}const q=pt(e);drag={x0:q.x,y0:q.y,x1:q.x,y1:q.y}});
window.addEventListener('mousemove',e=>{if(pan){ox=pan.ox+e.clientX-pan.x;oy=pan.oy+e.clientY-pan.y;draw()}else if(drag){const q=pt(e);drag.x1=q.x;drag.y1=q.y;draw()}});
window.addEventListener('mouseup',()=>{if(pan){pan=null;return}if(drag){const p=PAGES[pi];const b=[Math.max(0,Math.min(drag.x0,drag.x1)),Math.max(0,Math.min(drag.y0,drag.y1)),Math.min(p.w,Math.max(drag.x0,drag.x1)),Math.min(p.h,Math.max(drag.y0,drag.y1))].map(Math.round);
drag=null;if(b[2]-b[0]>=3&&b[3]-b[1]>=3){const r=rec();if(r){r.boxes.push(b);if(r.flag==='not_found')r.flag='';save();list();prog()}}draw()}});
cv.addEventListener('wheel',e=>{e.preventDefault();const r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,f=Math.exp(-e.deltaY*0.0015),nz=Math.min(8,Math.max(0.1,z*f));ox=mx-(mx-ox)*nz/z;oy=my-(my-oy)*nz/z;z=nz;draw()},{passive:false});
function go(d){tick();save();const p=PAGES[pi];mi+=d;if(mi>=p.mentions.length){if(pi<PAGES.length-1){pi++;mi=0;document.getElementById('pg').value=pi;load();return}mi=p.mentions.length-1}if(mi<0){if(pi>0){pi--;mi=PAGES[pi].mentions.length-1;document.getElementById('pg').value=pi;load();return}mi=0}list();draw()}
document.getElementById('next').onclick=()=>go(1);document.getElementById('prev').onclick=()=>go(-1);
document.getElementById('undo').onclick=()=>{const r=rec();if(r&&r.boxes.length){r.boxes.pop();save();list();draw();prog()}};
document.getElementById('nf').onclick=()=>{const r=rec();if(r){r.boxes=[];r.flag='not_found';save();go(1)}};
document.getElementById('uns').onclick=()=>{const r=rec();if(r){r.flag=r.flag==='unsure'?'':'unsure';save();list()}};
window.addEventListener('keydown',e=>{if(e.target.tagName==='SELECT')return;if(e.code==='Space'){space=true;e.preventDefault()}else if(e.key==='Enter'){go(1)}else if(e.key==='Backspace'){e.preventDefault();document.getElementById('undo').click()}});
window.addEventListener('keyup',e=>{if(e.code==='Space')space=false});
window.addEventListener('resize',()=>{fit();draw()});
document.getElementById('exp').onclick=()=>{tick();save();const rows=[['page_id','start','end','field','text','box_index','x0','y0','x1','y1','flag','seconds']];
for(const p of PAGES)for(const m of p.mentions){const r=st[id(p,m)]||{boxes:[],flag:'',sec:0};const base=[p.page_id,m.start,m.end,m.field,m.text];
if(r.boxes.length)r.boxes.forEach((b,i)=>rows.push([...base,i,...b,r.flag,r.sec]));else rows.push([...base,'','','','','',r.flag||'not_done',r.sec])}
const csv=rows.map(r=>r.map(v=>{v=String(v);return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v}).join(',')).join('\n');
const a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['﻿'+csv],{type:'text/csv'}));a.download='gold_boxes_test_gloria_'+new Date().toISOString().slice(0,10)+'.csv';a.click()};
fillSel();load();
</script></body></html>
"""

if __name__ == "__main__":
    build()
