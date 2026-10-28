// This browser's pairing token, sent with every /api/ request (see python/access.py).
// Plain-HTTP pages have no crypto.subtle, so SHA-256 and HMAC are implemented here.
const XGO_TOKEN='xgoduck-token';
function xgoToken(){try{return localStorage.getItem(XGO_TOKEN)||'';}catch(e){return '';}}
function xgoSetToken(t){try{t?localStorage.setItem(XGO_TOKEN,t):localStorage.removeItem(XGO_TOKEN);}catch(e){}}
const xgoFetch=window.fetch.bind(window);
window.fetch=(url,init={})=>{
  const t=xgoToken();
  if(t&&typeof url==='string'&&url.startsWith('/api/'))init={...init,headers:{...init.headers,Authorization:'Bearer '+t}};
  return xgoFetch(url,init);
};
// sendBeacon cannot carry the token; a keepalive fetch survives page unload just the same.
function xgoBeacon(url,body){fetch(url,{method:'POST',keepalive:true,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).catch(()=>{});}

const SHA256_K=new Uint32Array([
  0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
  0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
  0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
  0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
  0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
  0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
  0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
  0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]);
function sha256(bytes){
  const len=bytes.length,n=(len+72)&~63,m=new Uint8Array(n),dv=new DataView(m.buffer),w=new Uint32Array(64);
  m.set(bytes);m[len]=0x80;dv.setUint32(n-8,Math.floor(len/0x20000000));dv.setUint32(n-4,len<<3);
  const rotr=(x,r)=>x>>>r|x<<(32-r);
  let h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  for(let o=0;o<n;o+=64){
    for(let i=0;i<16;i++)w[i]=dv.getUint32(o+i*4);
    for(let i=16;i<64;i++){
      const a=w[i-15],b=w[i-2];
      w[i]=(rotr(a,7)^rotr(a,18)^a>>>3)+w[i-7]+(rotr(b,17)^rotr(b,19)^b>>>10)+w[i-16];
    }
    let [A,B,C,D,E,F,G,H]=h;
    for(let i=0;i<64;i++){
      const t1=(H+(rotr(E,6)^rotr(E,11)^rotr(E,25))+(E&F^~E&G)+SHA256_K[i]+w[i])|0;
      const t2=((rotr(A,2)^rotr(A,13)^rotr(A,22))+(A&B^A&C^B&C))|0;
      H=G;G=F;F=E;E=(D+t1)|0;D=C;C=B;B=A;A=(t1+t2)|0;
    }
    h=h.map((x,i)=>(x+[A,B,C,D,E,F,G,H][i])|0);
  }
  const out=new Uint8Array(32),odv=new DataView(out.buffer);
  h.forEach((x,i)=>odv.setUint32(i*4,x>>>0));
  return out;
}
function hmacSha256(key,msg){
  const k=new Uint8Array(64);k.set(key.length>64?sha256(key):key);
  const inner=new Uint8Array(64+msg.length),outer=new Uint8Array(96);
  inner.set(k.map(b=>b^0x36));inner.set(msg,64);
  outer.set(k.map(b=>b^0x5c));outer.set(sha256(inner),64);
  return sha256(outer);
}

// Pair this browser with the sticker's link (xgoduck://pair?id=…&k=…) or bare key.
async function xgoPair(secret,name){
  const key=(/[?&]k=([A-Za-z0-9_-]{22})/.exec(secret)||/^\s*([A-Za-z0-9_-]{22})\s*$/.exec(secret)||[])[1];
  if(!key)throw new Error('Paste the pairing link from the sticker, or its 22-character key.');
  const r=await xgoFetch('/api/pair/challenge'),c=await r.json();
  if(!r.ok)throw new Error(c.detail||'challenge failed');
  const id=(/[?&]id=([0-9A-F]{8})/.exec(secret)||[])[1];
  if(id&&id!==c.id)throw new Error(`This sticker belongs to duck ${id}, not ${c.id}.`);
  const enc=new TextEncoder(),mac=hmacSha256(enc.encode(key),enc.encode(`xgoduck-pair:${c.id}:${c.nonce}`));
  const proof=[...mac].map(b=>b.toString(16).padStart(2,'0')).join('');
  const p=await xgoFetch('/api/pair',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nonce:c.nonce,proof,name})});
  const x=await p.json();
  if(!p.ok)throw new Error(x.detail||'pairing failed');
  xgoSetToken(x.token);
  return x;
}
