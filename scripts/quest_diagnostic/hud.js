/* Display-only settings; never change control coordinates or camera observations. */
const HUD_REVISION='cast-fixed-14';
// Single source for the fixed starting preset; actual Meta casting is unverified.
const CAST_FIT_DEFAULTS=Object.freeze({mode:'cast_fit',scale:.46,margin:.02,centerX:.22,centerY:.04,diagnostic:false});
function hudSettings(input={}) {
  const number=(v,fallback,lo,hi)=>Number.isFinite(Number(v))?Math.max(lo,Math.min(hi,Number(v))):fallback;
  const mode=['normal','casting','cast_fit'].includes(input.mode)?input.mode:'normal';
  const casting=mode!=='normal';
  return {mode,scale:number(input.scale,mode==='cast_fit'?CAST_FIT_DEFAULTS.scale:.65,.20,.85),
    margin:number(input.margin,.02,0,.18),
    centerX:casting?number(input.centerX,mode==='cast_fit'?CAST_FIT_DEFAULTS.centerX:0,-.45,.45):0,
    centerY:casting?number(input.centerY,mode==='cast_fit'?CAST_FIT_DEFAULTS.centerY:0,-.45,.45):0,diagnostic:!!input.diagnostic};
}
// Cast fit is an adjustable right/up estimate, not a measured Meta crop calibration.
// Keep the former off-axis casting profile available separately.
const HUD_STORAGE_KEY='cyclo.quest.display.v5';
const HUD_MODES=['normal','casting','cast_fit'];
function hudDefaults(mode='cast_fit') {
  if(mode==='normal')return hudSettings({mode,scale:.65,margin:.02,diagnostic:false});
  if(mode==='casting')return hudSettings({mode,scale:.50,margin:.02,centerX:.24,centerY:.10,diagnostic:true});
  return hudSettings(CAST_FIT_DEFAULTS);
}
function defaultHUDPreferences(){return {schema:5,mode:'cast_fit',profiles:Object.fromEntries(HUD_MODES.map(m=>[m,hudDefaults(m)]))};}
function loadHUDPreferences(storage){
  const fallback=defaultHUDPreferences();
  const valid=v=>v&&['scale','margin','centerX','centerY'].every(k=>typeof v[k]==='number'&&Number.isFinite(v[k]))&&typeof v.diagnostic==='boolean';
  try{
    if(storage===undefined)storage=globalThis.localStorage;
    const raw=storage.getItem(HUD_STORAGE_KEY);
    if(!raw){
      // Preserve previous profiles, but never let an old active mode suppress the new preset.
      // Apply Cast fit once; the v5 key thereafter restores the user's mode and edits.
      try{
        const old=JSON.parse(storage.getItem('cyclo.quest.display.v4')||storage.getItem('cyclo.quest.display.v3')||storage.getItem('cyclo.quest.display.v2')||'null');
        if([2,3,4].includes(old?.schema))for(const mode of ['normal','casting'])
          if(valid(old.profiles?.[mode]))fallback.profiles[mode]=hudSettings({...old.profiles[mode],mode});
      }catch(error){/* Invalid legacy settings cannot prevent selecting Cast fit. */}
      return {state:fallback,status:'Cast fit selected once; previous profiles retained — '+saveHUDPreferences(fallback,storage)};
    }
    const data=JSON.parse(raw);
    if(data.schema!==5||!HUD_MODES.includes(data.mode)||!data.profiles)throw Error('invalid saved settings');
    for(const mode of HUD_MODES){
      const v=data.profiles[mode];
      if(!valid(v))throw Error('invalid saved profile');
      fallback.profiles[mode]=hudSettings({...v,mode});
    }
    fallback.mode=data.mode;
    return {state:fallback,status:'Saved display settings restored'};
  }catch(error){return {state:fallback,status:'Failed to load saved settings; using defaults: '+String(error)};}
}
function saveHUDPreferences(state,storage){
  try{
    if(storage===undefined)storage=globalThis.localStorage;
    storage.setItem(HUD_STORAGE_KEY,JSON.stringify(state));
    return 'Display settings saved — retained across reloads/VR sessions at this address';
  }catch(error){return 'Failed to save display settings (usable in the current VR session): '+String(error);}
}
function hudTransform(viewport,settings) {
  const {width:w,height:h}=viewport;
  if(!(w>0&&h>0))throw Error('Invalid XR viewport');
  const aspect=settings.mode==='cast_fit'?832/992:1;
  const sx=settings.scale*Math.min(1,h/w)*aspect,sy=settings.scale*Math.min(1,w/h);
  // Keep the complete panel within each eye. Meta's downstream crop is unknown.
  const clamp=(v,s)=>Math.max(-.98+s,Math.min(.98-s,v));
  // Clip-space center: +Y moves up; a delta of 0.02 is 1% of viewport height.
  const x=clamp(settings.centerX,sx),y=clamp(settings.centerY,sy);
  return {scale:[sx,sy],center:[x,y],bounds:[x-sx,y-sy,x+sx,y+sy]};
}
// Pure presentation of the simulator's verdict; button state never implies control activation.
function teleopStatusLines(status,fresh){
  if(!fresh)return ['Status unavailable — stale/interrupted video', 'Previous arm-active indication is invalid', 'After input/video recovery, release squeeze → press again'];
  if(!status||status.version!==1)return ['No control status received — check teleop launcher/server versions', 'Valid input or a pressed button alone does not establish active arm control'];
  const reasons={ready:'Ready',active:'Arm active',anchored:'Anchored',waiting:'Waiting',episode_waiting:'Waiting',
    release_then_squeeze:'Release squeeze, then press again',input_not_live:'Input lost',preview_not_live:'Video unconfirmed',
    loop_gap:'Control loop delayed',new_reference_release_buttons:'New reference: release squeeze',
    look_forward_release_both_squeezes:'Look forward; release both squeezes',controller_jump_release:'Input jump: release squeeze'};
  const rows=[`${status.episode_state} ${status.preview_only?'Preview only':''} | X start / A stop·wait | Control verdict`];
  const number=v=>Number.isFinite(v)?v.toFixed(2):'--';
  for(const side of ['left','right']){
    const h=status.hands[side];
    const control=!status.live?'Input lost':!h.valid?'Invalid input':status.preview_only?'Control disabled':status.episode_state==='WAITING'?'Waiting':
      h.active?'Arm active':(reasons[h.control_reason]||h.control_reason);
    const sq=h.raw_squeeze||{pressed:h.squeeze_pressed,value:h.squeeze},tr=h.raw_trigger||{value:h.trigger};
    rows.push(`${side==='left'?'L':'R'} Input ${h.valid?'Valid':'Invalid'} | ${control} | SQ ${sq.pressed?'ON':'OFF'} ${number(sq.value)} / TR ${number(tr.value)}`);
  }
  const age=v=>Number.isFinite(v)?Math.round(v)+'ms':'--';
  rows.push(`Input ${age(status.input_age_ms)} | focus ${status.visibility||'--'} | Video ${age(status.preview?.frame_age_ms)} | ACK ${status.preview_ok?'OK':status.compatibility==='reload_required'?'Version mismatch':'Unconfirmed'}`);
  if(status.preview_only){
    rows.push('Preview only: robot control disabled / X can start');
  }else if(status.episode_state==='WAITING'){
    const labels={input_stale:'Stale/missing input',quest_not_visible:'Quest not focused',input_not_live:'Invalid connection',
      preview_unconfirmed:'Fresh video display unconfirmed (stale/not displayed)',invalid:'Invalid input',not_touch_plus:'Not Touch Plus',
      buttons_invalid:'Invalid buttons/mapping',squeeze_held:'Release squeeze'};
    const blocks=status.start_blockers.map(code=>{const parts=code.split(':');return parts.length===2?
      (parts[0]==='left'?'L ':'R ')+(labels[parts[1]]||parts[1]):(labels[code]||code);});
    const message=blocks.length?(status.start_blocked?'START_BLOCKED: ':'Start conditions: ')+blocks.join(' · '):'Ready to start — press X again';
    // Wrap, never truncate a blocking condition. The common two-hand case fits two lines.
    for(let i=0;i<message.length;i+=56)rows.push(message.slice(i,i+56));
  }else rows.push('SQ: squeeze state/value / TR: trigger value — button ON ≠ active arm control');
  return rows;
}
// Compact view has at most two lines; full reasons remain in the page's details view.
function compactStatusLines(status,fresh){
  if(!fresh)return ['Status unavailable — stale video', 'After input/video recovery, release squeeze → press again'];
  if(!status||status.version!==1)return ['No control status received', 'Check launcher/server connection / see details'];
  const names={ready:'Ready',active:'Active',anchored:'Anchored',waiting:'Waiting',episode_waiting:'Waiting',
    release_then_squeeze:'Release again',input_not_live:'Input lost',preview_not_live:'Waiting for video',
    loop_gap:'Loop delayed',new_reference_release_buttons:'Release again',
    look_forward_release_both_squeezes:'Awaiting reference',controller_jump_release:'Input jump'};
  const value=v=>Number.isFinite(v)?v.toFixed(1):'--';
  const sides=['left','right'].map(side=>{
    const h=status.hands[side];
    const state=!status.live?'Input lost':!h.valid?'Invalid input':status.preview_only?'Disabled':
      status.episode_state==='WAITING'?'Waiting':h.active?'Active':names[h.control_reason]||'Blocked';
    return `${side==='left'?'L':'R'} ${state} SQ${value(h.raw_squeeze?.value??h.squeeze)}/TR${value(h.raw_trigger?.value??h.trigger)}`;
  });
  const rows=[`${status.episode_state} | ${sides.join(' | ')}`];
  if(status.episode_state==='WAITING'&&!status.preview_only&&status.start_blockers?.length){
    const blocks=status.start_blockers;
    let reason;
    if(status.compatibility==='reload_required')reason='Reload page';
    else if(blocks.includes('input_stale'))reason='Stale input';
    else if(blocks.includes('quest_not_visible'))reason='Quest not focused';
    else if(blocks.includes('preview_unconfirmed'))reason='Confirm fresh video';
    else if(blocks.some(b=>b.endsWith(':squeeze_held')))reason='Release squeeze: '+['left','right'].filter(s=>blocks.includes(s+':squeeze_held')).map(s=>s==='left'?'Left hand':'Right hand').join('·');
    else reason='Check both Touch Plus inputs';
    rows.push('Start blocked: '+reason+' · See page for details');
  }
  return rows;
}
// Display-only extraction of COMPLETE square camera tiles from compose_live's 960x936 mosaic.
// No camera pixels are cropped: the overview, labels and old footer simply are not drawn.
function cameraTiles(native=false,compact=false){
  // Source rectangles stay fixed; only display destinations change.
  // Labels use empty space / the 24px inter-row gap, never the camera area.
  const tiles=[
    {name:'HEAD',source:native?[6,6,244,244]:[10,612,300,300],destination:[272,144,480,480],label:[80,168]},
    {name:'LEFT WRIST',source:native?[262,6,244,244]:[330,612,300,300],destination:[108,648,328,328],label:[108,643]},
    {name:'RIGHT WRIST',source:native?[518,6,244,244]:[650,612,300,300],destination:[588,648,328,328],label:[588,643]}
  ];
  if(compact){
    const destinations=[[176,76,480,480],[12,580,400,400],[420,580,400,400]];
    const labels=[[12,96],[12,575],[420,575]];
    tiles.forEach((tile,i)=>{tile.destination=destinations[i];tile.label=labels[i];});
  }
  return tiles;
}
function controllerConnected(hand,received,network){
  const touch=h=>!!h&&!!h.source_id&&h.profiles?.includes('meta-quest-touch-plus')&&
    !h.profiles.some(p=>/hand/i.test(p))&&h.reason!=='hand_input_excluded'&&h.mapping==='xr-standard';
  // A pose can temporarily be invalid while the physical controller is still connected.
  // SQ/TR, WAITING and video freshness intentionally do not participate in connectivity.
  return network==='ACK OK'&&touch(hand)&&touch(received)&&hand.source_id===received.source_id;
}
function recordingBadge(status,fresh){
  if(!fresh||typeof status?.recording!=='boolean')return {text:'Checking',color:'#a3aab3'};
  return status.recording?{text:'● REC',color:'#ff6565'}:{text:'NO REC',color:'#a3aab3'};
}
function episodeResultBadge(status){
  // A completed result is historical, not a connectivity/recording verdict.
  const result=status?.episode_result;
  if(!result)return {text:'',color:'#a3aab3'};
  return {text:result.label||result.reason||'',color:result.success?'#61e993':'#ffc477'};
}
function statusPanelLayout(compact=false){
  // Preserve the original layout; compact mode translates the same fixed slots.
  const layout={panel:{x:108,y:80,w:808,h:56},
    connections:[{x:120,y:82,w:176,h:26},{x:428,y:82,w:176,h:26}],
    controls:[{x:308,y:82,w:112,h:26},{x:616,y:82,w:112,h:26}],
    phase:{x:740,y:82,w:164,h:26},
    recording:{x:120,y:108,w:124,h:28},result:{x:260,y:108,w:424,h:28},
    detail:{x:704,y:108,w:200,h:28},firstBaseline:101,secondBaseline:129};
  if(compact){
    for(const box of [layout.panel,...layout.connections,...layout.controls,layout.phase,layout.recording,layout.result,layout.detail]){box.x-=96;box.y-=68;}
    layout.firstBaseline-=68;layout.secondBaseline-=68;
  }
  return layout;
}
function drawStatusText(c,text,box,baseline,font,color){
  c.font=font;c.fillStyle=color;c.textAlign='left';c.textBaseline='alphabetic';
  // Do not use fillText's maxWidth: it can squeeze glyphs/letter spacing.
  // Known status/result labels fit in full. Only unexpected long details elide.
  let shown=String(text);
  if(c.measureText(shown).width>box.w){
    while(shown.length&&c.measureText(shown+'…').width>box.w)shown=shown.slice(0,-1);
    shown+='…';
  }
  c.fillText(shown,box.x,baseline);
}
function handControlLabel(status,fresh,side){
  const hand=status?.hands?.[side];
  if(!fresh||!hand)return 'Checking';
  if(status.preview_only)return 'Disabled';
  if(status.episode_state==='WAITING')return 'Waiting';
  // Present the simulator's verdict, never infer activation from SQ/TR or REC.
  return status.live&&hand.valid&&hand.active?'Active':'Inactive';
}
function drawEpisodeBadges(c,status,fresh,layout){
  const recording=recordingBadge(status,fresh),result=episodeResultBadge(status);
  drawStatusText(c,recording.text,layout.recording,layout.secondBaseline,'21px sans-serif',recording.color);
  drawStatusText(c,result.text,layout.result,layout.secondBaseline,'bold 26px sans-serif',result.color);
  // Keep recording details inside the reserved row, including on video errors.
  // The full path/error is still available in the page's control details JSON.
  const detail=fresh?(status?.video_error?'VIDEO ERROR':status?.record_episode_id||''):'';
  drawStatusText(c,detail,layout.detail,layout.secondBaseline,'16px sans-serif','#d3dce6');
  return {recording:recording.text,result:result.text,resultColor:result.color,
    resultBox:layout.result};
}
function drawStatusPanel(c,status,fresh,connections=null,compact=false){
  const layout=statusPanelLayout(compact),panel=layout.panel;
  c.fillStyle='#06121f';c.fillRect(panel.x,panel.y,panel.w,panel.h);
  ['left','right'].forEach((side,i)=>{
    const connected=connections?.[side],prefix=i===0?'L':'R';
    // The PC preview has simulator input validity, not browser controller ACKs.
    const valid=fresh&&status?.live&&status?.hands?.[side]?.valid;
    const input=connections?`${prefix}: ${connected==null?'Checking':connected?'Connected':'Disconnected'}`:
      `${prefix} input: ${!fresh||!status?.hands?.[side]?'--':valid?'Valid':'Invalid'}`;
    drawStatusText(c,input,layout.connections[i],layout.firstBaseline,'21px sans-serif',
      (connections?connected:valid)?'#61e993':'#a3aab3');
    drawStatusText(c,handControlLabel(status,fresh,side),layout.controls[i],layout.firstBaseline,'21px sans-serif','#d3dce6');
  });
  drawStatusText(c,fresh?status?.episode_state||'Checking':'Checking',layout.phase,
    layout.firstBaseline,'21px sans-serif','#d3dce6');
  return {...panel,placement:'above-head',rendered:true,lines:2,connections,
    ...drawEpisodeBadges(c,status,fresh,layout)};
}
function drawPCPreview(canvas,image,status,fresh){
  const c=canvas.getContext('2d');
  c.fillStyle='#101c2b';c.fillRect(0,0,1024,1024);
  const native=image?.width===768&&image?.height===256;
  const supported=native||(image?.width===960&&image?.height===936);
  c.font='18px sans-serif';c.fillStyle='white';
  for(const tile of cameraTiles(native)){
    c.fillText(tile.name,...tile.label);
    if(image&&fresh&&supported)c.drawImage(image,...tile.source,...tile.destination);
  }
  return drawStatusPanel(c,status,fresh);
}
/* A small, head-fixed diagnostic panel, not immersive simulation streaming. */
function makeHUD(gl, options={}) {
  options=hudSettings(options);
  const compact=options.mode==='cast_fit';
  const canvas=document.createElement('canvas');canvas.width=compact?832:1024;canvas.height=compact?992:1024;
  const c=canvas.getContext('2d');
  function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
  const program=gl.createProgram();
  gl.attachShader(program,shader(gl.VERTEX_SHADER,'attribute vec2 p; uniform vec2 panelScale; uniform vec2 panelCenter; varying vec2 uv; void main(){uv=vec2((p.x+1.0)/2.0,(1.0-p.y)/2.0);gl_Position=vec4(p.x*panelScale.x+panelCenter.x,p.y*panelScale.y+panelCenter.y,0.,1.);}'));
  gl.attachShader(program,shader(gl.FRAGMENT_SHADER,'precision mediump float; varying vec2 uv; uniform sampler2D tex; void main(){gl_FragColor=texture2D(tex,uv);}'));
  gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
  const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
  const texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
  let last=-Infinity,lastImage=null,lastPanel=null;
  const draw=(views,layer,hands,network,image,previewFresh,t,previewStatus,build,teleop=null,receivedHands=null)=>{
    const eyeViews=views.map(view=>{
      const v=layer.getViewport(view);
      return {eye:view.eye,viewport:{x:v.x,y:v.y,width:v.width,height:v.height},
        transform:hudTransform(v,options),projectionMatrix:Array.from(view.projectionMatrix||[])};
    });
    draw.info={revision:HUD_REVISION,build,settings:options,status_panel:lastPanel,
      canvas:{width:canvas.width,height:canvas.height},
      camera_tiles:cameraTiles(image?.width===768&&image?.height===256,compact),
      framebuffer:{width:layer.framebufferWidth,height:layer.framebufferHeight},
      projection:'screen-fixed clip-space HUD; XR projection not applied',eyes:eyeViews};
    gl.useProgram(program);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    const location=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(location);gl.vertexAttribPointer(location,2,gl.FLOAT,false,0,0);
    gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texture);gl.uniform1i(gl.getUniformLocation(program,'tex'),0);
    if(t-last>100||image!==lastImage){last=t;lastImage=image;
      c.fillStyle='#101c2b';c.fillRect(0,0,canvas.width,canvas.height);c.font='20px sans-serif';
      const native=image?.width===768&&image?.height===256;
      const supported=native||(image?.width===960&&image?.height===936);
      const tiles=cameraTiles(native,compact);
      c.font='18px sans-serif';c.fillStyle='white';
      for(const tile of tiles){
        c.fillText(tile.name,...tile.label);
        if(image&&previewFresh&&supported)
          c.drawImage(image,...tile.source,...tile.destination);
      }
      if(!image||!previewFresh||!supported){
        c.fillStyle='#adbecd';c.fillText('Waiting for video',300,360);
      }
      const connections={left:receivedHands===null?null:controllerConnected(hands.left,receivedHands.left,network),
                         right:receivedHands===null?null:controllerConnected(hands.right,receivedHands.right,network)};
      draw.info.status_panel=lastPanel=drawStatusPanel(c,teleop,previewFresh,connections,compact);
      if(options.diagnostic){
        c.save();c.strokeStyle='#00ffff';c.lineWidth=6;c.strokeRect(4,4,canvas.width-8,canvas.height-8);
        c.font='bold 24px sans-serif';
        for(const [label,x,y,color] of [['TL',8,8,'#00ffff'],['TR',canvas.width-80,8,'#ffe45c'],['BL',8,canvas.height-46,'#65ff85'],['BR',canvas.width-80,canvas.height-46,'#ff85e5']]){
          c.fillStyle='#000';c.fillRect(x,y,72,38);c.fillStyle=color;c.fillText(label,x+12,y+28);
        }
        c.restore();
      }
      gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,canvas);
    }
    if(gl.isContextLost())throw Error('WebGL context lost');
    for(const eye of eyeViews){const v=eye.viewport,transform=eye.transform;
      gl.viewport(v.x,v.y,v.width,v.height);
      gl.uniform2f(gl.getUniformLocation(program,'panelScale'),...transform.scale);
      gl.uniform2f(gl.getUniformLocation(program,'panelCenter'),...transform.center);
      gl.drawArrays(gl.TRIANGLE_STRIP,0,4);}
    const error=gl.getError();if(error!==gl.NO_ERROR)throw Error('WebGL draw/upload error '+error);
    return !!image&&previewFresh&&((image.width===960&&image.height===936)||(image.width===768&&image.height===256))&&views.length>0;
  };
  draw.info=null;
  return draw;
}
