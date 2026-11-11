/* CPU mocks only; no claim about actual WebGL optics or Meta casting. Run after hud.js. */
// Geometry tests use a deterministic metric. Raster checks must also use real fonts.
function hudMockMeasureText(text){return {width:String(text).length*Number(this.font.match(/(\d+)px/)[1])*.5};}
function runHUDTests(){
 let count=0;
 const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
 const near=(a,b)=>Math.abs(a-b)<1e-8;
 const normal=hudSettings({});
 assert(normal.scale===.65&&normal.centerX===0&&normal.centerY===0&&!normal.diagnostic,'normal defaults changed');count++;
 assert(hudSettings({mode:'normal',centerX:.4,centerY:.4}).centerX===0,'casting offset leaked into normal');count++;
 const cast=hudSettings({mode:'casting',scale:.6,centerX:.1,centerY:-.1,diagnostic:true});
 const a=hudTransform({width:1200,height:1400},cast);
 assert(near(a.scale[0]*1200,a.scale[1]*1400),'per-eye aspect');count++;
 assert(near(a.center[0],.1)&&near(a.center[1],-.1),'center sign/application');count++;
 for(const [w,h] of [[1200,1400],[1400,1200],[1920,1080]])for(const x of [-.45,.45]){
   const r=hudTransform({width:w,height:h},hudSettings({mode:'casting',scale:.85,centerX:x,centerY:x}));
   assert(r.bounds.every(n=>n>=-.980000001&&n<=.980000001),'panel clipped inside eye');
 }count++;
 let failed=false;try{hudTransform({width:0,height:100},cast);}catch(e){failed=true;}
 assert(failed,'bad viewport accepted');count++;
 const bad=hudSettings({scale:NaN,margin:NaN,mode:'casting',centerX:Infinity});
 assert(bad.scale===.65&&bad.margin===.02&&bad.centerX===0,'invalid settings fallback');count++;
 return count;
}
function runHUDRenderTests(){
 const events=[],texts=[],images=[],uniforms=[],viewports=[];
 let error=0,lost=false;
 const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
 const context={measureText:hudMockMeasureText,fillRect(){},fillText:(...a)=>texts.push(a),drawImage:(...a)=>images.push(a),
   save(){},restore(){},strokeRect:(...a)=>events.push(['border',...a])};
 const gl=new Proxy({NO_ERROR:0,getError:()=>error,isContextLost:()=>lost,
   getShaderParameter:()=>true,getProgramParameter:()=>true,getUniformLocation:(_,n)=>n,
   uniform2f:(...a)=>uniforms.push(a),viewport:(...a)=>viewports.push(a)},
   {get:(o,k)=>k in o?o[k]:()=>({})});
 const draw=makeHUD(gl,{mode:'casting',scale:.65,centerX:.1,centerY:.1,diagnostic:true});
 const views=[{eye:'left',projectionMatrix:[1]},{eye:'right',projectionMatrix:[2]}];
 const layer={framebufferWidth:3000,framebufferHeight:1700,
   getViewport:v=>v.eye==='left'?{x:0,y:0,width:1400,height:1600}:{x:1500,y:40,width:1450,height:1550}};
 const hands={left:{valid:true,reason:'ok',buttons:[]},right:{valid:true,reason:'ok',buttons:[]}};
 const image={width:960,height:936};
 // The runner installs this document mock before calling makeHUD.
 globalThis.hudTestContext=context;
 // Context is requested at makeHUD time, so runner's getContext returns a forwarding proxy.
 const ack=draw(views,layer,hands,'ACK OK',image,true,200,{stage:'decoded'},'test-build');
 assert(ack,'fresh draw not acknowledged');
 assert(draw.info.status_panel.rendered&&draw.info.status_panel.placement==='above-head','panel was not drawn');
 const panel=draw.info.status_panel;
 const iy=images[0][6];
 assert(panel.y>=0&&panel.y+panel.h<iy&&panel.x>=0&&panel.x+panel.w<=1024,'status overlaps image or leaves panel');
 assert(draw.info.status_panel.lines<=2,'compact status grew beyond two lines');
 assert(texts.some(t=>t[0]==='L: Checking'),'missing connectivity hides bar');
 draw(views,layer,hands,'ACK OK',image,true,210,{stage:'decoded'},'test-build');
 assert(draw.info.status_panel?.rendered,'panel diagnostics lost between canvas updates');
 assert(viewports[0].join()==='0,0,1400,1600'&&viewports[1].join()==='1500,40,1450,1550','framebuffer/eye mix-up');
 assert(draw.info.framebuffer.width===3000&&draw.info.eyes.length===2,'missing render diagnostics');
 assert(uniforms.filter(a=>a[0]==='panelCenter').every(a=>a[1]===.1&&a[2]===.1),'center uniform missing');
 assert(images.length===3&&images.every(a=>a.length===9&&a[3]===300&&a[4]===300&&a[7]===a[8]),'camera tile cropped or stretched');
 assert(images.map(a=>a[1]).join(',')==='10,330,650'&&images.every(a=>a[2]===612),'wrong camera source');
 assert(images[1][7]===images[2][7]&&images[0][7]>images[1][7],'HEAD not large or wrists unequal');
 assert(['TL','TR','BL','BR'].every(n=>texts.some(t=>t[0]===n))&&events.some(e=>e[0]==='border'),'missing calibration marks');
 assert(!draw(views,layer,hands,'ACK OK',image,false,400,{stage:'stale'},'test-build'),'stale preview acknowledged');
 assert(texts.some(t=>t[0].includes('Waiting for video')),'stale video hidden');
 const nativeStart=images.length;
 assert(draw(views,layer,hands,'ACK OK',{width:768,height:256},true,500,{stage:'decoded'},'test-build',{recording:true,episode_result:{label:'SUCCESS',success:true}},{}),'native preview not acknowledged');
 assert(images.slice(nativeStart).length===3&&images.slice(nativeStart).every(a=>a[3]===244&&a[4]===244),'native draw used legacy crop');
 assert(texts.some(t=>t[0]==='● REC')&&texts.some(t=>t[0]==='SUCCESS'),'record/result not both drawn');
 assert(draw.info.status_panel.resultBox.y+draw.info.status_panel.resultBox.h<144,'result overlaps camera');
 error=1282;let threw=false;try{draw(views,layer,hands,'ACK OK',image,true,600,{stage:'decoded'},'test-build');}catch(e){threw=true;}
 assert(threw,'WebGL error suppressed');
 error=0;lost=true;threw=false;try{draw(views,layer,hands,'ACK OK',image,true,800,{stage:'decoded'},'test-build');}catch(e){threw=true;}
 assert(threw,'context loss suppressed');
 return 19;
}

function runHUDPersistenceTests(){
 let raw=null,count=0;
 const assert=(v,msg)=>{if(!v)throw Error(msg);};
 const storage={getItem:()=>raw,setItem:(_,v)=>{raw=v;}};
 let loaded=loadHUDPreferences(storage),state=loaded.state;
 assert(state.mode==='cast_fit'&&state.profiles.cast_fit.scale===.46&&state.profiles.casting.scale===.50&&state.profiles.casting.centerX===.24&&state.profiles.casting.centerY===.10,'estimated preset');count++;
 assert(state.profiles.normal.scale===.65&&state.profiles.normal.centerX===0,'normal changed');count++;
 state.profiles.casting.scale=.62;state.profiles.casting.centerX=.14;state.profiles.casting.centerY=.08;
 saveHUDPreferences(state,storage);loaded=loadHUDPreferences(storage);
 assert(loaded.state.profiles.casting.scale===.62&&loaded.state.profiles.casting.centerX===.14&&loaded.state.profiles.casting.centerY===.08,'refresh persistence');count++;
 state.mode='normal';saveHUDPreferences(state,storage);loaded=loadHUDPreferences(storage);
 assert(loaded.state.mode==='normal'&&loaded.state.profiles.casting.scale===.62,'mode/profile retention');count++;
 state.profiles.casting=hudDefaults('casting');state.mode='casting';saveHUDPreferences(state,storage);
 assert(loadHUDPreferences(storage).state.profiles.casting.scale===.50,'persisted reset');count++;
 raw='{broken';assert(loadHUDPreferences(storage).state.mode==='cast_fit','bad JSON fallback');count++;
 raw=JSON.stringify({schema:99});assert(loadHUDPreferences(storage).state.profiles.casting.centerX===.24,'schema fallback');count++;
 const denied={getItem(){throw Error('blocked');},setItem(){throw Error('quota');}};
 assert(loadHUDPreferences(denied).status.includes('Failed')&&saveHUDPreferences(state,denied).includes('Failed'),'storage denial hidden');count++;
 return count;
}

function runHUDMigrationTests(){
 const values=new Map([['cyclo.quest.display.v1',JSON.stringify({schema:1,mode:'normal',profiles:{casting:{scale:.7}}})]]);
 const storage={getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v)};
 const old=values.get('cyclo.quest.display.v1');
 const assert=(v,m)=>{if(!v)throw Error(m);};
 let result=loadHUDPreferences(storage);
 assert(HUD_STORAGE_KEY==='cyclo.quest.display.v5'&&result.state.schema===5,'version not advanced');
 assert(result.state.mode==='cast_fit'&&result.state.profiles.cast_fit.scale===.46&&result.state.profiles.casting.scale===.5&&result.state.profiles.casting.centerX===.24&&result.state.profiles.casting.centerY===.1&&result.state.profiles.casting.diagnostic,'old values overrode new preset');
 assert(values.has(HUD_STORAGE_KEY)&&values.get('cyclo.quest.display.v1')===old,'first load not saved or old data modified');
 result.state.profiles.casting.centerX=.31;result.state.profiles.casting.scale=.53;saveHUDPreferences(result.state,storage);
 result=loadHUDPreferences(storage);
 assert(result.state.profiles.casting.centerX===.31&&result.state.profiles.casting.scale===.53,'preset reapplied over user edits');
 const transform=hudTransform({width:1680,height:1760},hudDefaults('casting'));
 assert(transform.center[0]===.24&&transform.center[1]===.1&&transform.scale[0]===.5,'measured viewport clamps preset');
 assert(Math.abs((transform.center[0]-.12)*1680/2-100.8)<1e-8,'horizontal displacement');
 return 6;
}

function runControlStatusTests(){
 const assert=(v,m)=>{if(!v)throw Error(m);};
 const h={valid:true,active:false,control_reason:'ready',squeeze_pressed:true,squeeze:1,trigger:.4};
 const status={version:1,episode_state:'WAITING',live:true,hands:{left:h,right:{...h}},start_blocked:true,
   start_blockers:['input_stale','preview_unconfirmed','left:squeeze_held','right:squeeze_held']};
 let lines=teleopStatusLines(status,true).join('');
 assert(lines.includes('WAITING')&&lines.includes('SQ ON 1.00')&&!lines.includes('Arm active'),'button misrepresented as control');
 assert(['START_BLOCKED','Stale/missing input','Fresh video display unconfirmed','L Release squeeze','R Release squeeze'].every(s=>lines.includes(s)),'lost blocking condition');
 status.episode_state='RUNNING';h.active=true;h.control_reason='active';
 assert(teleopStatusLines(status,true).join('').includes('L Input Valid | Arm active'),'actual verdict missing');
 assert(!teleopStatusLines(status,false).join('').includes('L Input Valid | Arm active'),'stale active verdict');
 assert(teleopStatusLines(null,true)[0].includes('received'),'old producer invents state');
 status.live=false;
 assert(teleopStatusLines(status,true)[1].includes('Input lost'),'input loss hidden by button');
 return 6;
}

function runCompactStatusTests(){
 const assert=(v,m)=>{if(!v)throw Error(m);};
 const h={valid:true,active:false,control_reason:'ready',squeeze:1,trigger:.7};
 const s={version:1,episode_state:'WAITING',live:true,hands:{left:h,right:{...h}},
   start_blockers:['left:squeeze_held','right:squeeze_held','left:invalid']};
 let rows=compactStatusLines(s,true);
 assert(rows.length===2&&rows[0].includes('L Waiting SQ1.0/TR0.7')&&!rows[0].includes('Active'),'buttons imply movement');
 assert(rows[1].includes('Left hand·Right hand')&&!rows[1].includes('invalid'),'blocking summary');
 s.episode_state='RUNNING';h.active=true;
 rows=compactStatusLines(s,true);
 assert(rows.length===1&&rows[0].includes('L Active')&&rows[0].includes('R Ready'),'actual control not shown');
 assert(compactStatusLines(s,false).length<=2&&!compactStatusLines(s,false).join('').includes('L Active'),'stale active status');
 assert(compactStatusLines(null,true).length<=2,'missing status too long');
 assert(!rows.join('').match(/build|revision|ms|focus/),'detail leaked into compact view');
 return 6;
}

function runCameraConnectionTests(){
 const assert=(v,m)=>{if(!v)throw Error(m);};
 const h={source_id:'2',profiles:['meta-quest-touch-plus'],mapping:'xr-standard',valid:false,reason:'no_grip_pose'};
 assert(controllerConnected(h,{...h},'ACK OK'),'temporary pose loss incorrectly disconnects controller');
 assert(!controllerConnected(h,h,'stale'),'stale reception allowed');
 assert(!controllerConnected(h,{...h,source_id:'3'},'ACK OK'),'old source ACK accepted');
 assert(!controllerConnected({...h,profiles:['meta-fixed-hand']},h,'ACK OK'),'hand tracking connected');
 assert(!controllerConnected({...h,reason:'hand_input_excluded'},h,'ACK OK'),'disguised hand connected');
 assert(!controllerConnected(h,{},'ACK OK'),'missing received input connected');
 for(const margin of [0,.02,.18]){
   const box={x:24+margin*1024,y:84+margin*1024,w:976-2*margin*1024,h:842-2*margin*1024};
   const r=Math.min(box.w/960,box.h/936);
   const rect={x:box.x+(box.w-960*r)/2,y:box.y+(box.h-936*r)/2,w:960*r,h:936*r};
   const tiles=cameraTiles(rect);
   for(const tile of tiles){const [x,y,w,h]=tile.destination;
     assert(x>=0&&y>=0&&x+w<=1024&&y+h<=1024&&w===h,'tile outside canvas / distorted');}
   assert(tiles[0].destination[1]+tiles[0].destination[3]<tiles[1].destination[1],'camera overlap');
 }
 return 8;
}

function runDenseLayoutTests(){
 const tiles=cameraTiles();const assert=(v,m)=>{if(!v)throw Error(m);};
 assert(tiles[0].destination[2]===480&&tiles[1].destination[2]===328,'unexpected sizes');
 assert(tiles[1].destination[2]===tiles[2].destination[2],'unequal wrists');
 assert(136<tiles[0].destination[1],'bar overlaps head');
 assert(tiles.every(t=>t.destination[0]>=48&&t.destination[1]>=144&&t.destination[0]+t.destination[2]<=976&&t.destination[1]+t.destination[3]<=976),'safe area overflow');
 assert(tiles.every(t=>t.source[2]===300&&t.source[3]===300&&t.destination[2]===t.destination[3]),'crop/stretch');
 return 5;
}

function runNativeRecordingTests(){
 const assert=(v,m)=>{if(!v)throw Error(m);};
 const old=cameraTiles(false),native=cameraTiles(true);
 assert(native.every((t,i)=>t.destination.join()===old[i].destination.join()),'layout changed');
 assert(native.every(t=>t.source[2]===244&&t.source[3]===244)&&native[2].source[0]===518,'native ROI cropped');
 assert(recordingBadge({episode_state:'RUNNING'},true).text==='Checking','RUNNING inferred recording');
 assert(recordingBadge({episode_state:'RUNNING',recording:false},true).text==='NO REC','disabled recorder shows REC');
 assert(recordingBadge({episode_state:'WAITING',recording:true},true).text==='● REC','recorder verdict overridden');
 assert(recordingBadge({recording:true},false).text==='Checking','stale REC retained');
 assert(recordingBadge(null,true).text==='Checking','missing status not explicit');
 return 7;
}

function runEpisodeResultTests(){
 const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
 const status={episode_state:'WAITING',recording:false,live:false,
   episode_result:{reason:'success',label:'SUCCESS',success:true}};
 assert(episodeResultBadge(status).color==='#61e993','success must be green');
 const calls=[],rects=[],images=[];
 const c={measureText:hudMockMeasureText,fillRect:(...x)=>rects.push(x),fillText:function(text,x,y,maxWidth){calls.push({text,x,y,maxWidth,color:this.fillStyle,font:this.font});},
   drawImage:(...x)=>images.push(x)};
 const canvas={getContext:()=>c};
 const panel=drawPCPreview(canvas,{width:768,height:256},status,true);
 assert(panel.recording==='NO REC'&&panel.result==='SUCCESS','practice result hidden by recorder state');
 const result=calls.find(x=>x.text==='SUCCESS');
 assert(result.color==='#61e993'&&result.font==='bold 26px sans-serif','success styling');
 assert(result.maxWidth===undefined&&result.x===panel.resultBox.x&&panel.resultBox.x+panel.resultBox.w<=916&&result.y<144,'result compressed, clips or overlaps camera');
 assert(images.every(x=>x[6]>=144),'camera overlaps status');
 assert(drawPCPreview(canvas,null,status,false).result==='SUCCESS','historical result erased by stale input');
 for(const label of ['STOPPED','TRACKING STALL','TIMEOUT','BREAD DROPPED']){
   status.episode_result={label,success:false};
   assert(drawPCPreview(canvas,null,status,true).result===label,'wrong stop reason');
 }
 status.episode_result=null;assert(drawPCPreview(canvas,null,status,true).result==='','approved start did not clear');
 return 10;
}

function hudLayoutCases(){
 const cases=[];
 for(const phase of ['WAITING','RUNNING'])for(const recording of [false,true])
  for(const result of ['', 'SUCCESS','STOPPED','TRACKING STALL']){
   const hand={valid:true,active:phase==='RUNNING',control_reason:phase==='RUNNING'?'active':'episode_waiting'};
   cases.push({name:`${phase} / ${recording?'REC':'NO REC'} / ${result||'no result'}`,fresh:true,
    status:{version:1,episode_state:phase,live:true,hands:{left:{...hand},right:{...hand}},recording,
     record_episode_id:recording?'episode_000001':null,record_path:recording?'/example/session/episode_000001':null,
     episode_result:result?{label:result,success:result==='SUCCESS'}:null},
    connections:{left:true,right:true}});
  }
 const running=cases.find(c=>c.status.episode_state==='RUNNING'&&c.status.recording&&!c.status.episode_result);
 for(const [name,modify] of [
  ['Disconnected controllers',c=>{c.connections={left:false,right:false};c.status.live=false;}],
  ['Connected, inactive arms',c=>{for(const h of Object.values(c.status.hands)){h.active=false;h.control_reason='release_then_squeeze';h.squeeze=1;}}],
  ['Invalid input pose',c=>{for(const h of Object.values(c.status.hands))h.valid=false;}],
  ['Preview only',c=>{c.status.preview_only=true;}],
  ['Video error',c=>{c.status.video_error='Example error retained in full in the details view';}],
  ['Long recording detail',c=>{c.status.record_episode_id='episode_'+'0123456789'.repeat(15);}]
 ]){const c=JSON.parse(JSON.stringify(running));c.name=name;modify(c);cases.push(c);}
 const stale=JSON.parse(JSON.stringify(cases.find(c=>c.status.episode_result?.success)));
 stale.name='Stale preview, retained SUCCESS';stale.fresh=false;cases.push(stale);
 cases.push({name:'No status yet',status:null,fresh:false,connections:{left:null,right:null}});
 return cases;
}

function runFixedStatusLayoutTests(){
 let count=0;
 const assert=(ok,msg)=>{if(!ok)throw Error(msg);count++;};
 const layout=statusPanelLayout(),p=layout.panel;
 const boxes=[...layout.connections,...layout.controls,layout.phase,layout.recording,layout.result,layout.detail];
 assert(p.y>=80&&p.y+p.h===136,'status not lowered within the existing camera gap');
 for(const b of boxes)assert(b.x>=p.x&&b.x+b.w<=p.x+p.w&&b.y>=p.y&&b.y+b.h<=p.y+p.h,'slot leaves fixed panel');
 for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){
  const a=boxes[i],b=boxes[j];
  assert(a.x+a.w<=b.x||b.x+b.w<=a.x||a.y+a.h<=b.y||b.y+b.h<=a.y,'reserved slots overlap');
 }
 const gl=new Proxy({NO_ERROR:0,getError:()=>0,isContextLost:()=>false,getShaderParameter:()=>true,getProgramParameter:()=>true},
  {get:(o,k)=>k in o?o[k]:()=>({})});
 const views=[{eye:'left'},{eye:'right'}];
 const layer={framebufferWidth:3360,framebufferHeight:1760,
  getViewport:v=>({x:v.eye==='left'?0:1680,y:0,width:1680,height:1760})};
 const draw=makeHUD(gl,hudDefaults('casting'));
 const h={source_id:'source',profiles:['meta-quest-touch-plus'],mapping:'xr-standard'};
 const hands={left:h,right:h};
 let time=100;
 for(const entry of hudLayoutCases()){
  const snapshot=JSON.stringify(entry.status),calls=[],images=[];
  const c={measureText:hudMockMeasureText,fillRect(){},strokeRect(){},save(){},restore(){},
   fillText:function(text,x,y,...extra){calls.push({text,x,y,extra,font:this.font,color:this.fillStyle,width:this.measureText(text).width});},
   drawImage:(...a)=>images.push(a)};
  globalThis.hudTestContext=c;
  for(const mode of ['PC','XR']){
   calls.length=0;images.length=0;
   const image={width:768,height:256};
   let panel;
   if(mode==='PC')panel=drawPCPreview({getContext:()=>c},image,entry.status,entry.fresh);
   else{
    const received=entry.connections.left===null?null:{left:entry.connections.left?h:{},right:entry.connections.right?h:{}};
    draw(views,layer,hands,'ACK OK',image,entry.fresh,time+=110,{},'test',entry.status,received);
    panel=draw.info.status_panel;
   }
   assert(['x','y','w','h'].every(k=>panel[k]===p[k])&&panel.lines===2,'panel moved/resized for '+entry.name);
   const texts=calls.filter(t=>t.y>=p.y&&t.y<=p.y+p.h);
   assert(texts.length===8&&texts.every(t=>[layout.firstBaseline,layout.secondBaseline].includes(t.y)),'unexpected line/wrap');
   for(const t of texts){
    const box=boxes.find(b=>b.x===t.x&&t.y>=b.y&&t.y<=b.y+b.h);
    assert(box&&t.width<=box.w&&t.extra.length===0,'text overflow or glyph compression: '+t.text);
   }
   assert(calls.every(t=>t.y>=p.y||['TL','TR'].includes(t.text)),'floating status/path above the panel');
   const result=entry.status?.episode_result?.label||'';
   assert(panel.result===result&&texts.some(t=>t.text===result&&t.x===layout.result.x),'result truncated or hidden');
   assert(texts.some(t=>t.x===layout.recording.x&&t.text===recordingBadge(entry.status,entry.fresh).text),'recording hidden by result');
   if(entry.fresh&&entry.status)assert(texts.some(t=>t.text===entry.status.episode_state),'episode phase missing');
   if(result==='SUCCESS')assert(texts.some(t=>t.text===result&&t.color==='#61e993'&&t.font==='bold 26px sans-serif'),'success styling changed');
   if(entry.name==='Long recording detail')assert(texts.some(t=>t.x===layout.detail.x&&t.text.endsWith('…')),'long detail not bounded');
   if(entry.name==='Video error')assert(texts.some(t=>t.text==='VIDEO ERROR'&&t.y===layout.secondBaseline),'error adds an upper row');
   if(entry.name==='Connected, inactive arms'||entry.name==='Invalid input pose')
    assert(texts.filter(t=>t.text==='Inactive').length===2&&!texts.some(t=>t.text==='Active'),'connection/buttons imply active control');
   assert(images.every((a,i)=>a.slice(5).join()===cameraTiles(true)[i].destination.join()),'camera destination changed');
  }
  assert(JSON.stringify(entry.status)===snapshot,'presentation mutated simulator status');
 }
 return count;
}

function runStatusViewportTests(){
 let count=0;
 const assert=(ok,msg)=>{if(!ok)throw Error(msg);count++;};
 const p=statusPanelLayout().panel;
 const viewports=[{x:0,y:0,width:1680,height:1760},{x:1680,y:0,width:1680,height:1760},
  {x:0,y:0,width:1400,height:1600},{x:1500,y:40,width:1450,height:1550},
  {x:0,y:0,width:1920,height:1080},{x:0,y:0,width:1080,height:1920}];
 const profiles=[hudDefaults('normal'),hudDefaults('casting')];
 for(const scale of [.35,.85])for(const center of [-.45,.45])
  profiles.push(hudSettings({mode:'casting',scale,centerX:center,centerY:center}));
 for(const v of viewports)for(const settings of profiles){
  const t=hudTransform(v,settings);
  const rect=b=>({x:v.x+(1+t.center[0]+(b.x/512-1)*t.scale[0])*v.width/2,
   y:v.y+(1-t.center[1]-(1-b.y/512)*t.scale[1])*v.height/2,
   w:b.w/1024*t.scale[0]*v.width,h:b.h/1024*t.scale[1]*v.height});
  const status=rect(p),head=rect({x:272,y:144,w:480,h:480});
  assert(status.x>=v.x&&status.y>=v.y&&status.x+status.w<=v.x+v.width&&status.y+status.h<=v.y+v.height,'status clipped in eye viewport');
  assert(status.y+status.h<head.y,'status overlaps head in eye viewport');
 }
 // PC canvas is a square with intrinsic 1024x1024 and CSS width min(100%,850px).
 for(const width of [360,768,850,1024]){
  const scale=width/1024;
  assert(p.x*scale>=0&&p.y*scale>=0&&(p.x+p.w)*scale<=width&&(p.y+p.h)*scale<144*scale,'PC canvas clipping/overlap');
 }
 return count;
}

function runCastFitTests(){
 let count=0;const assert=(ok,msg)=>{if(!ok)throw Error(msg);count++;};
 const fit=hudDefaults('cast_fit');
 assert(fit.scale===.46&&fit.centerX===.22&&fit.centerY===.04,'Cast fit defaults');
 assert(hudSettings({...fit,scale:.1}).scale===.20,'small scale adjustment');
 const old={schema:2,mode:'casting',profiles:{normal:hudDefaults('normal'),casting:{...hudDefaults('casting'),scale:.73,centerY:.23}}};
 const values=new Map([['cyclo.quest.display.v2',JSON.stringify(old)]]);
 const storage={getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v)};
 let state=loadHUDPreferences(storage).state;
 assert(state.mode==='cast_fit'&&state.profiles.cast_fit.scale===.46,'old active mode overrides new preset');
 assert(state.profiles.casting.scale===.73&&state.profiles.casting.centerY===.23,'legacy edits lost');
 assert(values.get('cyclo.quest.display.v2')===JSON.stringify(old),'legacy storage modified');
 state.profiles.cast_fit.scale=.31;state.profiles.cast_fit.centerY=-.08;saveHUDPreferences(state,storage);
 state=loadHUDPreferences(storage).state;
 assert(state.mode==='cast_fit'&&state.profiles.cast_fit.scale===.31&&state.profiles.cast_fit.centerY===-.08,'Cast fit edits lost on reconnect');
 state.mode='normal';saveHUDPreferences(state,storage);
 assert(loadHUDPreferences(storage).state.mode==='normal','default view cannot persist');
 // Simulated central crops of each eye, never a claim about Meta's actual output.
 for(const [width,height] of [[1680,1760],[1920,1080],[1200,1400],[1024,1024]]){
  const t=hudTransform({width,height},fit);
  assert(Math.abs(t.scale[0]*width-t.scale[1]*height*832/992)<1e-8,'square aspect distorted');
  for(const crop of [.85,.75])
   assert(t.bounds[0]>=-crop&&t.bounds[1]>=-crop&&t.bounds[2]<=crop&&t.bounds[3]<=crop,'entire canvas clips in simulated central crop');
 }
 const layout=statusPanelLayout();
 for(const test of hudLayoutCases()){
  const b=episodeResultBadge(test.status);
  assert(JSON.stringify(statusPanelLayout().result)===JSON.stringify(layout.result),'result changes geometry');
  if(test.status?.episode_result?.success)assert(b.color==='#61e993','SUCCESS not green');
 }
 for(const tile of cameraTiles(true,true)){
  assert(tile.source[2]===244&&tile.source[3]===244,'source camera cropped');
  assert(tile.destination[2]===tile.destination[3],'camera stretched');
 }
 return count;
}

function runCompactCastingTests(){
 let count=0;const assert=(ok,msg)=>{if(!ok)throw Error(msg);count++;};
 const fit=hudDefaults('cast_fit'),layout=statusPanelLayout(true),tiles=cameraTiles(true,true);
 const boxes=[...layout.connections,...layout.controls,layout.phase,layout.recording,layout.result,layout.detail];
 for(const b of [layout.panel,...boxes])assert(b.x>=12&&b.y>=12&&b.x+b.w<=820&&b.y+b.h<=68,'compact status bounds');
 assert(tiles[2].destination[0]-(tiles[1].destination[0]+tiles[1].destination[2])===8,'wrist gap');
 for(const tile of tiles){const [x,y,w,h]=tile.destination;
  assert(x>=12&&y>=76&&x+w<=820&&y+h<=980&&w===h,'full camera bounds/aspect');
 }
 const values=new Map([['cyclo.quest.display.v3',JSON.stringify({schema:3,mode:'cast_fit',profiles:{normal:hudDefaults('normal'),casting:hudDefaults('casting'),cast_fit:{...fit,scale:.21,centerX:-.4}}})]]);
 const storage={getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v)};
 const legacy=values.get('cyclo.quest.display.v3'),state=loadHUDPreferences(storage).state;
 assert(state.profiles.cast_fit.scale===.46&&state.profiles.cast_fit.centerX===.22,'v3 overrides new compact defaults');
 assert(values.get('cyclo.quest.display.v3')===legacy,'old settings overwritten');
 const gl=new Proxy({NO_ERROR:0,getError:()=>0,isContextLost:()=>false,getShaderParameter:()=>true,getProgramParameter:()=>true},{get:(o,k)=>k in o?o[k]:()=>({})});
 const draw=makeHUD(gl,fit),h={source_id:'source',profiles:['meta-quest-touch-plus'],mapping:'xr-standard'};
 const views=[{eye:'left'}],layer={framebufferWidth:1680,framebufferHeight:1760,getViewport:()=>({x:0,y:0,width:1680,height:1760})};
 let time=100;
 for(const entry of hudLayoutCases()){
  const texts=[],images=[];
  globalThis.hudTestContext={measureText:hudMockMeasureText,fillRect(){},strokeRect(){},save(){},restore(){},
   fillText(text,x,y){texts.push({text,x,y,font:this.font,color:this.fillStyle,width:this.measureText(text).width});},drawImage:(...args)=>images.push(args)};
  draw(views,layer,{left:h,right:h},'ACK OK',{width:768,height:256},entry.fresh,time+=110,{},'test',entry.status,{left:h,right:h});
  assert(draw.info.canvas.width===832&&draw.info.canvas.height===992,'compact canvas not applied');
  const rows=texts.filter(t=>t.y===33||t.y===61);
  assert(rows.length===8,'status rows missing');
  for(const t of rows){const b=boxes.find(b=>b.x===t.x&&t.y>=b.y&&t.y<=b.y+b.h);assert(b&&t.width<=b.w,'compact text overflow '+t.text);}
  assert(draw.info.status_panel.result===(entry.status?.episode_result?.label||''),'outcome lost');
  if(entry.status?.episode_result?.success)assert(rows.some(t=>t.text==='SUCCESS'&&t.color==='#61e993'),'success missing');
  if(entry.fresh)assert(images.length===3,'camera missing');
 }
 // Explicitly distinguish viewport containment from unknown casting containment.
 const t=hudTransform({width:1680,height:1760},fit);
 assert(t.bounds.every(v=>Math.abs(v)<=.98),'eye clipping');
 assert(t.bounds[2]>.50||t.bounds[3]>.50,'test must not imply all central crops fit');
 return count;
}

function runFixedPresetTests(){
 let count=0;const assert=(ok,msg)=>{if(!ok)throw Error(msg);count++;};
 const preset=hudDefaults('cast_fit');
 assert(preset.scale===.46&&preset.centerX===.22&&preset.centerY===.04,'fixed starting values');
 assert(JSON.stringify(hudSettings({mode:'cast_fit'}))===JSON.stringify(preset),'fallback/default mismatch');
 const old={schema:4,mode:'cast_fit',profiles:{normal:hudDefaults('normal'),casting:hudDefaults('casting'),cast_fit:{...preset,scale:.58,centerY:.12}}};
 const values=new Map([['cyclo.quest.display.v4',JSON.stringify(old)],['pair_fixture','unchanged-token']]);
 const writes=[],storage={getItem:k=>values.get(k)||null,setItem:(k,v)=>{writes.push(k);values.set(k,v);}};
 let loaded=loadHUDPreferences(storage).state;
 assert(loaded.schema===5&&JSON.stringify(loaded.profiles.cast_fit)===JSON.stringify(preset),'v4 did not migrate');
 const saved=values.get(HUD_STORAGE_KEY);
 for(let i=0;i<3;i++)assert(JSON.stringify(loadHUDPreferences(storage).state)===saved,'refresh/session reload changed fixed preset');
 assert(writes.length===1&&writes[0]===HUD_STORAGE_KEY,'migration repeated or touched unrelated storage');
 assert(values.get('cyclo.quest.display.v4')===JSON.stringify(old)&&values.get('pair_fixture')==='unchanged-token','old/Pair storage modified');
 loaded.profiles.cast_fit.scale=.45;saveHUDPreferences(loaded,storage);
 assert(loadHUDPreferences(storage).state.profiles.cast_fit.scale===.45,'field calibration overwritten on reload');
 assert(hudDefaults('cast_fit').scale===.46,'saved adjustment mutated fixed default');
 for(const v of [{width:1680,height:1760},{width:1920,height:1080},{width:1024,height:1024}]){
  const previous=hudTransform(v,{...preset,scale:.58,centerY:.12}),next=hudTransform(v,preset);
  assert(next.center[0]===previous.center[0],'horizontal alignment changed');
  assert(next.bounds[3]<previous.bounds[3]&&next.bounds[1]>previous.bounds[1],'top/bottom margins not improved');
  assert(Math.abs((previous.center[1]-next.center[1])*v.height/2-.04*v.height)<1e-8,'vertical shift not 4% down');
  assert(Math.abs(next.scale[0]*v.width/(next.scale[1]*v.height)-832/992)<1e-8,'panel aspect changed');
 }
 return count;
}
