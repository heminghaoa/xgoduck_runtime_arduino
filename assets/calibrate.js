const $=id=>document.getElementById(id);
const MOTORS=[10,11,12,13,14,20,21,22,23,24,30,31,32,33,34];
let statusBusy=false, active=false, centering=null, presentMask=0;
let held=Array(15).fill(false);

async function post(path, body={}){
  const r=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const x=await r.json().catch(()=>({}));
  if(!r.ok) throw new Error(x.detail||t('error.request'));
  return x;
}
function showError(e){$('message').textContent=e.message||String(e);}

// Zero-pose pictures come from tools/render-zero-refs.py; joint.<id> and ref.<id> in i18n.js
// name and describe each one. The mouth is not in the training model.
MOTORS.forEach((id,i)=>{
  const pic=id===34?t('cal.beakClosed'):`<img src="zero/joint-${id}.webp" alt="">`;
  $('joints').insertAdjacentHTML('beforeend',`<div class="cal-row" id="row${i}">
    <button class="cal-ref" data-ref="${id}" aria-label="${t('cal.refLabel',{id})}">${pic}</button>
    <div class="cal-meta"><b>ID ${id}</b><em>${t('joint.'+id)}</em><span id="raw${i}">${t('cal.waiting')}</span></div>
    <div class="cal-actions"><span id="state${i}">${t('cal.unloaded')}</span><button data-center="${i}" disabled>${t('cal.center').replace('&','&amp;')}</button></div>
  </div>`);
});

document.querySelectorAll('[data-ref]').forEach(btn=>{
  btn.onclick=()=>{
    const id=+btn.dataset.ref, img=$('ref-img');
    img.hidden=id===34;
    if(id!==34)img.src=`zero/joint-${id}.webp`;
    $('ref-title').textContent=`ID ${id} · ${t('joint.'+id)}`;
    $('ref-text').textContent=t('ref.'+id);
    $('ref').showModal();
  };
});
$('ref').onclick=e=>{if(e.target===$('ref'))$('ref').close();};

function refreshRows(){
  document.querySelectorAll('[data-center]').forEach(btn=>{
    const i=+btn.dataset.center;
    btn.disabled=!active||centering!==null||held[i]||!(presentMask&(1<<i));
    $(`row${i}`).classList.toggle('done',held[i]);
    $(`state${i}`).textContent=t(centering===i?'cal.centering':held[i]?'cal.holding':'cal.unloaded');
  });
}

document.querySelectorAll('[data-center]').forEach(btn=>{
  btn.onclick=async()=>{
    const i=+btn.dataset.center;
    centering=i;
    refreshRows();
    $('message').textContent=t('cal.setting',{id:MOTORS[i]});
    try{
      await post('cal/center',{index:i});
      $('message').textContent=t('cal.sent',{id:MOTORS[i]});
    }catch(e){showError(e);}
    finally{centering=null;refreshRows();}
  };
});

async function enter(){
  try{
    await post('cal/enter');
    active=true;
    held.fill(false);
    $('message').textContent=t('cal.ready');
  }catch(e){showError(e);}
  refreshRows();
}
async function exit(){
  active=false;
  refreshRows();
  try{
    await post('cal/exit');
    held.fill(false);
    $('message').textContent=t('cal.closedMessage');
  }catch(e){showError(e);}
  refreshRows();
}
$('start').onclick=enter;
$('exit').onclick=exit;
$('exit2').onclick=exit;
window.addEventListener('pagehide',()=>xgoBeacon('/api/cal/exit',{}));
document.addEventListener('visibilitychange',()=>{if(document.hidden&&active)exit();});

setInterval(async()=>{
  if(statusBusy||document.hidden)return;
  statusBusy=true;
  try{
    if(active)await post('cal/heartbeat').catch(()=>{});
    const r=await fetch('/api/status');
    if(!r.ok)throw new Error(t('error.status'));
    const s=await r.json();
    active=s.mode==='calibrate';
    presentMask=s.raw_mask||0;
    held=s.cal_done||Array(15).fill(false);
    $('mode').textContent=t(active?'cal.active':'cal.closed');
    if(s.last_error)$('message').textContent=s.last_error;
    if(s.raw_pos)s.raw_pos.forEach((v,i)=>{
      $(`raw${i}`).textContent=presentMask&(1<<i)?t('cal.encoder',{v}):t('cal.noFeedback');
    });
    refreshRows();
  }catch(e){showError(e);}
  finally{statusBusy=false;}
},250);

enter();
