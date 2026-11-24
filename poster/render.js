const {chromium}=require('playwright');
(async()=>{const dir=process.argv[2];const name=process.argv[3]||'poster';const fmt=process.argv[4]||'A1';const S={A0:['841mm','1189mm',3179,4494],A1:['594mm','841mm',2245,3179]}[fmt];const b=await chromium.launch();const p=await b.newPage({viewport:{width:S[2],height:S[3]}});
await p.goto('file://'+dir+'/'+name+'.html');await p.waitForTimeout(1500);
await p.pdf({path:dir+'/'+name+'.pdf',width:S[0],height:S[1],printBackground:true});
const r=await p.evaluate(()=>{const m=document.querySelector('main')||document.querySelector('.poster');return {main:[m.scrollHeight,m.clientHeight], rows:[...document.querySelectorAll('.row')].map(x=>x.getBoundingClientRect().height|0), over:[...document.querySelectorAll('.box')].map(x=>x.scrollHeight-x.clientHeight)}});
console.log(JSON.stringify(r));
const p2=await b.newPage({viewport:{width:S[2],height:S[3]},deviceScaleFactor:0.55});
await p2.goto('file://'+dir+'/'+name+'.html');await p2.waitForTimeout(1500);await p2.screenshot({path:dir+'/'+(name==='poster'?'preview':'preview_'+name.replace('poster_',''))+'.png'});
await b.close();})();
