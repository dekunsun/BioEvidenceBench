const {chromium}=require('playwright');
(async()=>{const dir=process.argv[2];const b=await chromium.launch();const p=await b.newPage({viewport:{width:2304,height:3456}});
await p.goto('file://'+dir+'/poster.html');await p.waitForTimeout(1500);
await p.pdf({path:dir+'/poster.pdf',width:'24in',height:'36in',printBackground:true});
const r=await p.evaluate(()=>{const m=document.querySelector('main');return {main:[m.scrollHeight,m.clientHeight], rows:[...document.querySelectorAll('.row')].map(x=>x.getBoundingClientRect().height|0), over:[...document.querySelectorAll('.box')].map(x=>x.scrollHeight-x.clientHeight)}});
console.log(JSON.stringify(r));
const p2=await b.newPage({viewport:{width:2304,height:3456},deviceScaleFactor:0.5});
await p2.goto('file://'+dir+'/poster.html');await p2.waitForTimeout(1500);await p2.screenshot({path:dir+'/preview.png'});
await b.close();})();
