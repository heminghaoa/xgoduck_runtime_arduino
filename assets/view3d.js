// Live 3D view of the duck. The model comes from tools/export-3d-model.py; MuJoCo is z-up,
// quaternions are (w, x, y, z), and status angles in degrees map straight onto joint radians.
import * as THREE from 'three';
import {OrbitControls} from './libs/three/OrbitControls.js';

const $=id=>document.getElementById(id);
const show=text=>{$('message').textContent=text;};
const quat=q=>new THREE.Quaternion(q[1],q[2],q[3],q[0]);
const DOWN=new THREE.Vector3(0,0,-1);
const HOME_VIEW={position:[0.34,0.25,0.27],target:[0,0,0.155]};

const holder=$('view3d');
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
holder.append(renderer.domElement);
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x0e1924);
const camera=new THREE.PerspectiveCamera(38,1,0.01,10);
camera.up.set(0,0,1);
const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;
function resetView(){camera.position.fromArray(HOME_VIEW.position);controls.target.fromArray(HOME_VIEW.target);controls.update();}
resetView();
scene.add(new THREE.HemisphereLight(0xffffff,0x2a3a4a,1.4));
const sun=new THREE.DirectionalLight(0xffffff,1.6);
sun.position.set(0.6,0.4,1);
scene.add(sun);
const grid=new THREE.GridHelper(0.6,12,0x3c5b78,0x26384b);
grid.rotation.x=Math.PI/2;
scene.add(grid);

const bodyMat=new THREE.MeshStandardMaterial({color:0xd6dde5,roughness:0.6,metalness:0.05,flatShading:true});
const headMat=bodyMat.clone();
const joints={};
let root=null, rootQuat=null, gravity=null, live=false;

async function load(){
  const [model,bin]=await Promise.all([
    fetch('model/model.json').then(r=>{if(!r.ok)throw new Error('model.json missing');return r.json();}),
    fetch('model/model.bin').then(r=>{if(!r.ok)throw new Error('model.bin missing');return r.arrayBuffer();}),
  ]);
  const geoms=model.meshes.map(m=>{
    const q=new Int16Array(bin,m.offset,m.vertices*3), pos=new Float32Array(m.vertices*3);
    for(let i=0;i<pos.length;i++){const k=i%3;pos[i]=m.min[k]+(q[i]+32768)/65535*(m.max[k]-m.min[k]);}
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.BufferAttribute(pos,3));
    g.setIndex(new THREE.BufferAttribute(new Uint16Array(bin,m.offset+m.vertices*6,m.triangles*3),1));
    g.computeVertexNormals();
    return g;
  });
  const contents=[];
  model.bodies.forEach(b=>{
    const frame=new THREE.Group();
    if(b.parent<0){
      // The floating base: MuJoCo places it with the STAND keyframe, not body_pos.
      frame.position.fromArray(model.root.pos);rootQuat=quat(model.root.quat);frame.quaternion.copy(rootQuat);
      scene.add(frame);root=frame;
    }else{
      frame.position.fromArray(b.pos);frame.quaternion.copy(quat(b.quat));
      contents[b.parent].add(frame);
    }
    let content=frame;
    if(b.joint){
      // Hinge through joint.pos: rotate a pivot there and shift the body back under it.
      const pivot=new THREE.Group();
      pivot.position.fromArray(b.joint.pos);
      content=new THREE.Group();
      content.position.fromArray(b.joint.pos).negate();
      pivot.add(content);frame.add(pivot);
      const j={pivot,axis:new THREE.Vector3().fromArray(b.joint.axis).normalize(),stand:b.joint.stand,q:b.joint.stand,target:b.joint.stand};
      if(b.joint.motor)joints[b.joint.motor]=j;
      pivot.quaternion.setFromAxisAngle(j.axis,j.q);
    }
    const mat=b.name==='jaw_soft'?headMat:bodyMat;
    for(const g of b.geoms){
      const mesh=new THREE.Mesh(geoms[g.mesh],mat);
      mesh.position.fromArray(g.pos);mesh.quaternion.copy(quat(g.quat));
      content.add(mesh);
    }
    contents.push(content);
  });
  const parts=[], legend=[];
  for(const p of model.parts){
    const mat=new THREE.MeshStandardMaterial({color:p.color,roughness:0.5,flatShading:true});
    let geo;
    if(p.shape==='cylinder-x'){geo=new THREE.CylinderGeometry(p.size[1]/2,p.size[1]/2,p.size[0],24);geo.rotateZ(-Math.PI/2);}
    else geo=new THREE.BoxGeometry(...p.size);
    const mesh=new THREE.Mesh(geo,mat);
    mesh.position.fromArray(p.pos);mesh.quaternion.copy(quat(p.quat));
    contents[p.body].add(mesh);parts.push(mesh);
    if(p.label)legend.push(p);
  }
  $('legend').replaceChildren(...legend.map(p=>{
    const li=document.createElement('li'),dot=document.createElement('i'),b=document.createElement('b');
    dot.style.background=p.color;b.textContent=p.label;
    li.append(dot,b,document.createTextNode(' '+p.note));
    return li;
  }));
  const showParts=()=>{
    const on=$('parts').checked;
    parts.forEach(m=>{m.visible=on;});
    $('legend').hidden=!on;
    headMat.transparent=on;headMat.opacity=on?0.3:1;headMat.depthWrite=!on;headMat.needsUpdate=true;
  };
  $('parts').onchange=showParts;
  showParts();
}

function standPose(){for(const j of Object.values(joints))j.target=j.stand;gravity=null;}

let polling=false;
async function poll(){
  if(polling||document.hidden)return;
  if(!$('live').checked){live=false;standPose();show('Showing the default pose');return;}
  polling=true;
  try{
    const r=await fetch('/api/status');
    if(!r.ok)throw new Error('status read failed');
    const s=await r.json();
    live=!!(s.angles&&s.feedback_age_ms!=null&&s.feedback_age_ms<500);
    if(live){
      s.motors.forEach((id,i)=>{if(joints[id])joints[id].target=s.angles[i]*Math.PI/180;});
      gravity=s.gravity?new THREE.Vector3(...s.gravity):null;
      show(`Live · ${s.feedback_hz.toFixed(0)} Hz feedback · ${s.servo_ids.length}/15 servos`);
    }else{standPose();show('No servo feedback: showing the default pose');}
  }catch(e){live=false;standPose();show(e.message);}
  finally{polling=false;}
}

const tilt=new THREE.Quaternion(), clock=new THREE.Clock();
function frame(){
  const k=Math.min(1,clock.getDelta()*15);
  for(const j of Object.values(joints)){
    j.q+=(j.target-j.q)*k;
    j.pivot.quaternion.setFromAxisAngle(j.axis,j.q);
  }
  if(root){
    tilt.identity();
    if(live&&$('tilt').checked&&gravity&&gravity.lengthSq()>0.25)tilt.setFromUnitVectors(gravity.clone().normalize(),DOWN);
    root.quaternion.slerp(tilt.multiply(rootQuat),k);
  }
  controls.update();
  renderer.render(scene,camera);
  requestAnimationFrame(frame);
}
function resize(){
  const w=holder.clientWidth,h=holder.clientHeight;
  renderer.setSize(w,h,false);camera.aspect=w/h;
  // On a tall phone screen keep the same width in view instead of cropping the duck.
  camera.fov=camera.aspect<1?2*Math.atan(Math.tan(THREE.MathUtils.degToRad(19))/camera.aspect)*180/Math.PI:38;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(holder);
$('reset-view').onclick=resetView;
$('live').onchange=poll;

load().then(()=>{
  resize();frame();poll();setInterval(poll,100);
}).catch(e=>show(`3D model not loaded: ${e.message}`));
