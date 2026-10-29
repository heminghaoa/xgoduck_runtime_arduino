const $=id=>document.getElementById(id);
let stickerUri='', youId=null;
function show(text){$('message').textContent=text;}
function showError(e){show(e.message||String(e));}
async function getJson(path,options){
  const r=await fetch('/api/'+path,options);
  const x=await r.json().catch(()=>({}));
  if(!r.ok){const e=new Error(x.detail||t('error.request'));e.status=r.status;throw e;}
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
  if(s.claimed){show(t('pair.saved'));return;}
  try{
    const sticker=await getJson('identity/sticker');
    $('qr').innerHTML=sticker.svg;
    $('sticker-id').textContent=sticker.id;
    stickerUri=sticker.uri;
    show(t('pair.printPrompt'));
  }catch(e){
    if(e.status!==401)throw e;
    $('unclaimed').hidden=true;
  }
}

function renderAccess(a){
  youId=a.you?a.you.id:null;
  $('access-state').textContent=t(a.require_pairing?'pair.required':'pair.open');
  $('require').checked=a.require_pairing;
  $('require').disabled=!a.you;
  $('you').textContent=a.you?t('pair.pairedAs',{name:a.you.name}):t('pair.notPaired');
  $('pair-form').hidden=!!a.you;
  $('unpair').hidden=!a.you;
  const items=a.paired.map(p=>{
    const li=document.createElement('li'),label=document.createElement('span'),remove=document.createElement('button');
    label.textContent=`${p.name} · ${p.created.slice(0,10)}${p.id===youId?t('pair.you'):''}`;
    remove.textContent=t('pair.remove');
    remove.onclick=async()=>{
      if(!confirm(t('pair.confirmRemove',{name:p.name})))return;
      try{await postJson('access/revoke',{id:p.id});if(p.id===youId)xgoSetToken('');await loadAccess();show(t('pair.removed',{name:p.name}));}
      catch(e){showError(e);}
    };
    li.append(label,remove);
    return li;
  });
  if(!items.length){const li=document.createElement('li');li.textContent=t('pair.none');items.push(li);}
  $('paired').replaceChildren(...items);
  if(a.error)show(a.error);
}

async function loadAccess(){
  try{renderAccess(await getJson('access'));}
  catch(e){
    if(e.status!==401)throw e;
    // Pairing is required and this browser has no valid token.
    youId=null;
    $('access-state').textContent=t('pair.required');
    $('require').checked=true;$('require').disabled=true;
    $('you').textContent=t('pair.notPaired');
    $('pair-form').hidden=false;$('unpair').hidden=true;
    $('paired').replaceChildren();
  }
}

async function load(){
  try{await loadSticker();await loadAccess();}catch(e){showError(e);}
}

$('print').onclick=()=>window.print();
$('claim').onclick=async()=>{
  if(!confirm(t('pair.confirmClaim')))return;
  try{await postJson('identity/claim',{});$('qr').innerHTML='';await load();}catch(e){showError(e);}
};
$('pair').onclick=async()=>{
  const secret=$('secret').value.trim()||stickerUri;
  try{
    if(!secret)throw new Error(t('pair.scanPrompt'));
    await xgoPair(secret,$('client-name').value.trim()||t('pair.defaultName'));
    $('secret').value='';
    await load();
    show(t('pair.paired'));
  }catch(e){showError(e);}
};
$('unpair').onclick=async()=>{
  if(!confirm(t('pair.confirmUnpair')))return;
  try{if(youId)await postJson('access/revoke',{id:youId});}catch(e){if(e.status!==401)return showError(e);}
  xgoSetToken('');
  await load();
  show(t('pair.unpaired'));
};
$('require').onchange=async()=>{
  const on=$('require').checked;
  if(on&&!confirm(t('pair.confirmRequire'))){$('require').checked=false;return;}
  try{renderAccess(await postJson('access',{require_pairing:on}));show(t(on?'pair.nowRequired':'pair.nowOpen'));}
  catch(e){$('require').checked=!on;showError(e);}
};
load();
