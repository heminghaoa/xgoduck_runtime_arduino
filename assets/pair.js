const $=id=>document.getElementById(id);
function showError(e){$('message').textContent=e.message||String(e);}
async function getJson(path,options){
  const r=await fetch('/api/'+path,options);
  const x=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(x.detail||'request failed');
  return x;
}

async function load(){
  try{
    const s=await getJson('identity');
    if(s.error)throw new Error(s.error);
    $('duck-id').textContent=s.id;
    $('unclaimed').hidden=s.claimed;
    $('claimed').hidden=!s.claimed;
    if(s.claimed){$('message').textContent='Pairing sticker saved';return;}
    const sticker=await getJson('identity/sticker');
    $('qr').innerHTML=sticker.svg;
    $('sticker-id').textContent=sticker.id;
    $('message').textContent='Print this sticker, then press I have saved the sticker.';
  }catch(e){showError(e);}
}

$('print').onclick=()=>window.print();
$('claim').onclick=async()=>{
  if(!confirm('Have you printed or saved the sticker? After this the duck never shows its pairing key over the network again.'))return;
  try{
    await getJson('identity/claim',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    $('qr').innerHTML='';
    await load();
  }catch(e){showError(e);}
};
load();
