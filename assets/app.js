const $=id=>document.getElementById(id);
let statusBusy=false, commandBusy=false, commandPending=false, rollerBusy=false;
let rollerEnabled=false;
const motionRanges={
  walk:{backward:.2,strafe:.3,yaw:1,keyboard:[.2,.15,.5]},
  roller:{backward:.4,strafe:0,yaw:.25,keyboard:[.4,0,.25]}
};
for(let i=0;i<4;i++) $('head-controls').insertAdjacentHTML('beforeend',`<label>${t('head.joint',{n:i+1})}<input id="head${i}" type="range" min="-1" max="1" value="0" step="0.02"></label>`);
$('head-controls').insertAdjacentHTML('beforeend',`<label>${t('head.mouth')}<input id="mouth" type="range" min="0" max="30" value="0" step="1"></label>`);
async function post(path, body){const r=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const x=await r.json();if(!r.ok)throw new Error(x.detail||t('error.request'));return x;}
function showError(e){$('message').textContent=e.message;}
async function setMode(mode){try{await post('mode',{mode});$('message').textContent=t('msg.modeUpdated');}catch(e){showError(e);}}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));
function showRoller(enabled){
  const changed=rollerEnabled!==enabled;
  rollerEnabled=enabled;
  $('roller-mode').checked=enabled;$('roller-state').textContent=t(enabled?'common.on':'common.off');
  $('roller-warning').hidden=!enabled;
  $('action-profile').textContent=t(enabled?'action.roller':'action.walk');
  const limits=motionRanges[enabled?'roller':'walk'];
  $('motion-limits').textContent=t('motion.limits',{back:limits.backward,strafe:limits.strafe?'±'+limits.strafe:'0',yaw:limits.yaw});
  $('left-label').textContent=t(enabled?'motion.leftRoller':'motion.leftWalk');
  if(changed)zero(false);
}
function showBattery(b){
  const known=b&&b.voltage!=null, warn=$('battery-warning');
  $('battery').textContent=known?b.voltage.toFixed(1)+' V':'—';
  $('battery').className=known?b.level:'';
  $('battery-detail').textContent=known?t('battery.about',{p:b.percent}):t('battery.none');
  warn.hidden=!known||b.level==='ok';
  warn.classList.toggle('critical',known&&b.level==='critical');
  if(!warn.hidden)warn.innerHTML=t(b.level==='critical'?'battery.critical':'battery.low',{v:b.voltage.toFixed(1)});
}
$('roller-mode').onchange=async()=>{
  if(rollerBusy)return;
  const enabled=$('roller-mode').checked;
  showRoller(enabled);
  rollerBusy=true;$('roller-mode').disabled=true;
  try{const r=await post('roller',{enabled});showRoller(r.enabled);showActionSettings(r);$('message').textContent=t(r.enabled?'msg.rollerOn':'msg.rollerOff',{model:r.model});}
  catch(e){showRoller(!enabled);showError(e);}
  finally{rollerBusy=false;$('roller-mode').disabled=false;}
};
$('pick').onclick=async()=>{try{const r=await post('pick',{});$('message').textContent=t('msg.pick',{model:r.model});}catch(e){showError(e);}};
$('roulade').onclick=async()=>{try{const r=await post('roulade',{});$('message').textContent=t('msg.roulade',{model:r.model});}catch(e){showError(e);}};
$('stop').onclick=()=>{zero();setMode('off')};
const keys=new Set(), sticks={left:{x:0,y:0},right:{x:0,y:0}}, resetSticks=[];
let motion=[0,0,0], targetMotion=[0,0,0];
const deadzone=v=>Math.abs(v)<=.15?0:v;
function updateMotion(){
  const key=(a,b)=>keys.has(a)-keys.has(b);
  const limits=motionRanges[rollerEnabled?'roller':'walk'];
  const forward=deadzone(sticks.left.y);
  targetMotion=[keys.has('w')||keys.has('s')?key('w','s')*limits.keyboard[0]:forward*(forward<0?limits.backward:.4),
    keys.has('a')||keys.has('d')?key('a','d')*limits.keyboard[1]:deadzone(-sticks.left.x)*limits.strafe,
    keys.has('q')||keys.has('e')?key('q','e')*limits.keyboard[2]:deadzone(-sticks.right.x)*limits.yaw];
}
function showMotion(){
  ['vx','vy','wz'].forEach((id,i)=>$(id+'Value').textContent=motion[i].toFixed(2));
}
async function sendCommand(){
  if(commandBusy){commandPending=true;return;}
  commandBusy=true;commandPending=false;
  motion=motion.map((old,i)=>.3*old+.7*targetMotion[i]);
  showMotion();
  try{await post('command',{twist:[...motion],head:[0,1,2,3].map(i=>+$('head'+i).value),mouth:+$('mouth').value});}
  catch(e){showError(e);}
  finally{commandBusy=false;if(commandPending)sendCommand();}
}
function joystick(id,side){
  const zone=$(id),knob=zone.firstElementChild;
  let pointer=null;
  function reset(){
    const old=pointer;pointer=null;
    sticks[side]={x:0,y:0};knob.style.transform='translate(0px,0px)';
    if(old!==null&&zone.hasPointerCapture(old))zone.releasePointerCapture(old);
  }
  resetSticks.push(reset);
  function move(e){
    const b=zone.getBoundingClientRect(),radius=(zone.clientWidth-knob.offsetWidth)/2;
    let dx=e.clientX-b.left-b.width/2,dy=e.clientY-b.top-b.height/2;
    const distance=Math.hypot(dx,dy);
    if(distance>radius){dx*=radius/distance;dy*=radius/distance;}
    knob.style.transform=`translate(${dx}px,${dy}px)`;
    sticks[side]={x:dx/radius,y:-dy/radius};updateMotion();
  }
  zone.onpointerdown=e=>{if(pointer!==null||e.button!==0)return;e.preventDefault();pointer=e.pointerId;zone.setPointerCapture(pointer);move(e);sendCommand();};
  zone.onpointermove=e=>{if(e.pointerId===pointer)move(e);};
  const release=e=>{if(e.pointerId!==pointer)return;reset();updateMotion();sendCommand();};
  zone.onpointerup=zone.onpointercancel=zone.onlostpointercapture=release;
}
joystick('joy-left','left');joystick('joy-right','right');
function zero(send=true){keys.clear();resetSticks.forEach(reset=>reset());motion=[0,0,0];updateMotion();showMotion();if(send)sendCommand();}
$('zero').onclick=()=>zero();
['leg-alpha','head-alpha'].forEach(id=>$(id).onchange=()=>post('filter',{leg:+$('leg-alpha').value,head:+$('head-alpha').value}).catch(showError));
const actionInputs=[['action-scale','action_scale'],['leg-alpha','action_alpha'],['head-alpha','action_alpha_head']];
actionInputs.forEach(([id])=>$(id).oninput=()=>$(id+'-value').textContent=(+$(id).value).toFixed(2));
function showActionSettings(settings){
  actionInputs.forEach(([id,key])=>{if(document.activeElement!==$(id)){$(id).value=settings[key];$(id+'-value').textContent=(+$(id).value).toFixed(2);}});
}
$('action-scale').onchange=()=>post('action-scale',{scale:+$('action-scale').value}).catch(showError);
$('restore-defaults').onclick=async()=>{
  if(!confirm(t('action.confirmRestore')))return;
  try{await post('settings/reset',{});$('message').textContent=t('action.restored');}catch(e){showError(e);}
};
const imuFilters=[['gyro-alpha','gyro_alpha'],['gravity-tau','gravity_tau_s']];
imuFilters.forEach(([id,key])=>{
  const input=$(id),output=$(id+'-value');
  input.oninput=()=>output.textContent=(+input.value).toFixed(2);
  input.onchange=()=>post('imu-filter',{[key]:+input.value}).catch(showError);
});
function keyCommand(){updateMotion();sendCommand();}
window.addEventListener('keydown',e=>{if(e.code==='Space'){e.preventDefault();$('stop').click();return;}const k=e.key.toLowerCase();if('wasdqe'.includes(k)&&k.length===1){keys.add(k);keyCommand();}});
window.addEventListener('keyup',e=>{const k=e.key.toLowerCase();if(keys.delete(k))keyCommand();});
window.addEventListener('blur',()=>zero());
document.addEventListener('visibilitychange',()=>{if(document.hidden)zero();});
window.addEventListener('pagehide',()=>{
  zero(false);
  xgoBeacon('/api/command',{twist:[0,0,0]});
});
setInterval(()=>{if(!document.hidden&&!commandBusy)sendCommand();},50);
setInterval(async()=>{if(statusBusy||document.hidden)return;statusBusy=true;try{const r=await fetch('/api/status');if(!r.ok)throw new Error(t('error.status'));const s=await r.json();$('rx').textContent=s.feedback_hz.toFixed(1)+' Hz';$('rl').textContent=s.inference_hz.toFixed(1)+' Hz';$('servos').textContent=(s.servo_ids?.length||0)+'/15';$('imu').textContent=t(s.imu_ok?'status.online':'status.offline');$('mode').textContent=t('modeLabel.'+s.mode,null,s.mode)+t(s.enabled?'status.enabled':'status.torqueOff');$('message').textContent=s.last_error||s.settings_error||t('status.bridge',{mbps:(s.bridge_baud/1e6).toFixed(0),age:(s.feedback_age_ms||0).toFixed(1)});
showBattery(s.battery);
$('pairing-warning').hidden=!(s.access&&s.access.require_pairing&&!s.access.paired);
document.querySelectorAll('[data-mode="hold"],[data-mode="policy"]').forEach(b=>b.disabled=!s.control_ready);
if(s.roller&&!rollerBusy)showRoller(s.roller.enabled);
if(!rollerBusy)showActionSettings(s.deployment);
imuFilters.forEach(([id,key])=>{if(document.activeElement!==$(id)){$(id).value=s.deployment[key];$(id+'-value').textContent=(+$(id).value).toFixed(2);}});
const recovery=s.recovery, pick=s.pick, roulade=s.roulade;
const upright=(s.mode==='shadow'||s.mode==='policy')&&recovery&&recovery.active&&recovery.phase==='walk';
$('pick').disabled=!upright||(pick&&pick.active)||(roulade&&roulade.active);
$('roulade').disabled=$('pick').disabled;
if(recovery){const phaseLabel=roulade&&roulade.active?t('phase.roulade'):pick&&pick.active?t('phase.pick'):t('phase.'+recovery.phase,null,recovery.phase);
$('recovery-phase').textContent=recovery.active?phaseLabel:t('phase.idle');$('active-model').textContent=s.active_model||'—';$('tilt-angle').textContent=recovery.angle_deg==null?'—':recovery.angle_deg.toFixed(1)+'°';
$('recovery-timer').textContent=!recovery.active?'—':roulade&&roulade.active?t('timer.roulade',{left:roulade.remaining_s.toFixed(2),total:roulade.seconds.toFixed(2)}):pick&&pick.active?t('timer.pick',{phi:pick.phi.toFixed(2)}):recovery.phase==='default_pose'?t('timer.hold',{left:recovery.hold_remaining_s.toFixed(2)}):recovery.phase==='getup'?t('timer.upright',{t:recovery.stand_elapsed_s.toFixed(2)}):t('timer.fallen',{t:recovery.fall_elapsed_s.toFixed(2)});
if(pick&&pick.active)$('mouth').value=Math.round(s.mouth||0);}
for(const [id,values]of [['acc-values',s.acc],['gyro-values',s.gyro],['gravity-values',s.gravity]])$(id).textContent=values?values.map(x=>x.toFixed(3)).join(' / '):'—';
$('command-health').textContent=t('telemetry.health',{sent:s.sent,echo:s.mcu_command_seq??'—',age:s.mcu_command_age_us<1e9?(s.mcu_command_age_us/1000).toFixed(1)+' ms':'—',gaps:s.sequence_gaps,rejected:s.mcu_invalid_commands??0});
if(s.angles)$('joints').innerHTML=s.motors.map((id,i)=>`<tr class="${s.servo_ids.includes(id)?'':'missing'}"><td>${id}</td><td>${s.angles[i].toFixed(1)}</td><td>${s.targets[i].toFixed(1)}</td></tr>`).join('');
}catch(e){showError(e);}finally{statusBusy=false;}},250);
