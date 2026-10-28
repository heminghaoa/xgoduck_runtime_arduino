const $=id=>document.getElementById(id);
let stickerUri='', youId=null;
function show(text){$('message').textContent=text;}
function showError(e){show(e.message||String(e));}
async function getJson(path,options){
  const r=await fetch('/api/'+path,options);
  const x=await r.json().catch(()=>({}));
  if(!r.ok){const e=new Error(x.detail||'request failed');e.status=r.status;throw e;}
  return x;
}
const postJson=(path,body)=>getJson(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});

async function loadSticker(){
  const s=await getJson('identity');
  if(s.error)throw new Error(s.error);
  $('duck-id').textContent=s.id;
  $('unclaimed').hidden=s.claimed;
  $('claimed').hidden=!s.claimed;
  stickerUri='';
  if(s.claimed){show('Pairing sticker saved');return;}
  try{
    const sticker=await getJson('identity/sticker');
    $('qr').innerHTML=sticker.svg;
    $('sticker-id').textContent=sticker.id;
    stickerUri=sticker.uri;
    show('Print this sticker, then press I have saved the sticker.');
  }catch(e){
    if(e.status!==401)throw e;
    $('unclaimed').hidden=true;
  }
}

function renderAccess(a){
  youId=a.you?a.you.id:null;
  $('access-state').textContent=a.require_pairing?'· pairing required':'· open on this network';
  $('require').checked=a.require_pairing;
  $('require').disabled=!a.you;
  $('you').textContent=a.you?`· paired as ${a.you.name}`:'· not paired';
  $('pair-form').hidden=!!a.you;
  $('unpair').hidden=!a.you;
  const items=a.paired.map(p=>{
    const li=document.createElement('li'),label=document.createElement('span'),remove=document.createElement('button');
    label.textContent=`${p.name} · ${p.created.slice(0,10)}${p.id===youId?' · this browser':''}`;
    remove.textContent='Remove';
    remove.onclick=async()=>{
      if(!confirm(`Remove ${p.name}? It will need to pair again.`))return;
      try{await postJson('access/revoke',{id:p.id});if(p.id===youId)xgoSetToken('');await loadAccess();show(`${p.name} removed`);}
      catch(e){showError(e);}
    };
    li.append(label,remove);
    return li;
  });
  if(!items.length){const li=document.createElement('li');li.textContent='None yet';items.push(li);}
  $('paired').replaceChildren(...items);
  if(a.error)show(a.error);
}

async function loadAccess(){
  try{renderAccess(await getJson('access'));}
  catch(e){
    if(e.status!==401)throw e;
    // Pairing is required and this browser has no valid token.
    youId=null;
    $('access-state').textContent='· pairing required';
    $('require').checked=true;$('require').disabled=true;
    $('you').textContent='· not paired';
    $('pair-form').hidden=false;$('unpair').hidden=true;
    $('paired').replaceChildren();
  }
}

async function load(){
  try{await loadSticker();await loadAccess();}catch(e){showError(e);}
}

$('print').onclick=()=>window.print();
$('claim').onclick=async()=>{
  if(!confirm('Have you printed or saved the sticker? After this the duck never shows its pairing key over the network again.'))return;
  try{await postJson('identity/claim',{});$('qr').innerHTML='';await load();}catch(e){showError(e);}
};
$('pair').onclick=async()=>{
  const secret=$('secret').value.trim()||stickerUri;
  try{
    if(!secret)throw new Error('Scan the sticker with the phone camera and paste the link it shows.');
    await xgoPair(secret,$('client-name').value.trim()||'Browser');
    $('secret').value='';
    await load();
    show('This browser is paired');
  }catch(e){showError(e);}
};
$('unpair').onclick=async()=>{
  if(!confirm('Unpair this browser? If pairing is required, it will no longer be able to move the duck.'))return;
  try{if(youId)await postJson('access/revoke',{id:youId});}catch(e){if(e.status!==401)return showError(e);}
  xgoSetToken('');
  await load();
  show('This browser is unpaired');
};
$('require').onchange=async()=>{
  const on=$('require').checked;
  if(on&&!confirm('Only paired phones and browsers will be able to move the duck or change its settings. Turn this on?')){$('require').checked=false;return;}
  try{renderAccess(await postJson('access',{require_pairing:on}));show(on?'Pairing is now required':'The duck is open on this network again');}
  catch(e){$('require').checked=!on;showError(e);}
};
load();
