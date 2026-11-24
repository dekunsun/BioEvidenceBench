const {chromium}=require('playwright');
(async()=>{const dir=process.argv[2];const b=await chromium.launch();const p=await b.newPage({viewport:{width:3179,height:4494}});
await p.goto('file://'+dir+'/poster.html');await p.waitForTimeout(1500);
await p.pdf({path:dir+'/poster.pdf',width:'841mm',height:'1189mm',printBackground:true});
const r=await p.evaluate(()=>{const m=document.querySelector('main');return {main:[m.scrollHeight,m.clientHeight], rows:[...document.querySelectorAll('.row')].map(x=>x.getBoundingClientRect().height|0), over:[...document.querySelectorAll('.box')].map(x=>x.scrollHeight-x.clientHeight)}});
console.log(JSON.stringify(r));
const p2=await b.newPage({viewport:{width:3179,height:4494},deviceScaleFactor:0.4});
await p2.goto('file://'+dir+'/poster.html');await p2.waitForTimeout(1500);await p2.screenshot({path:dir+'/preview.png'});
await b.close();})();
