const fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'preview.html'),'utf8');
const code=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const listeners={},els={family:{value:'sans'},weight:{value:'400'},italic:{checked:false},dark:{checked:false},contrast:{},proof:{},caption:{}};
for(const [id,e] of Object.entries(els)) e.addEventListener=(t,f)=>listeners[id+':'+t]=f;
const context={document:{getElementById:id=>els[id],body:{classList:{toggle:()=>{}}}}};
vm.runInNewContext(code,context);
let runs=0;
for(const f of ['sans','mono'])for(const w of [300,400,500,600,700,800,900])for(const i of [false,true])for(const d of [false,true]){
 els.family.value=f;els.weight.value=String(w);els.italic.checked=i;els.dark.checked=d;listeners['family:change']();
 if(!fs.existsSync(path.join(root,els.proof.src)))throw Error('Missing frame '+els.proof.src);
 if(!els.caption.textContent.includes(String(w)))throw Error('Incorrect weight caption');
 if(!els.proof.alt.includes('netfyr '+f))throw Error('Incorrect family alternative text');runs++;
}
els.weight.value='400';listeners['contrast:click']();if(els.weight.value!=='900')throw Error('400 ->900 switch failed');
listeners['contrast:click']();if(els.weight.value!=='400')throw Error('900 ->400 switch failed');
if(/data:font|base64,[A-Za-z0-9+/]{200}/.test(html))throw Error('Unexpected embedded payload');
const report={version:'0.506',frame_combinations_tested:runs,contrast_toggle_passed:true,all_referenced_frames_exist:true,embedded_fonts:false,scope:'JavaScript logic and local file existence; not an interactive browser rendering certification.'};
fs.writeFileSync(path.join(root,'validation/current/preview-interactions.json'),JSON.stringify(report,null,2)+'\n');console.log(report);
