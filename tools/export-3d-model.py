"""Export the xgoduck_rl MuJoCo model for the web page's 3D view.

Writes model.json (bodies, joints, geoms, add-on parts) and model.bin (meshes:
int16 positions quantised to each mesh's bounds, uint16 triangle indices).
Joint angles in degrees from /api/status map one to one onto the model's joints
in radians: the runtime's default pose is the model's STAND keyframe.

xgoduck_rl models the head as one rigid mesh. To let the mouth (servo 34) move,
the xgoduck_hardware head parts serve as a reference: they decide which of the
head mesh's triangles belong to the lower beak, and where its hinge is. Only
xgoduck_rl geometry is written out.

Usage: python export-3d-model.py <xgoduck_rl>/src/mjlab_microduck/robot/xgoduck/scene_walk.xml assets/model \
           <xgoduck_hardware>/structure
Needs mujoco, numpy and scipy on a desktop machine, not on the Uno Q.
"""
import json
import sys
from pathlib import Path
import numpy as np
import mujoco
from scipy.spatial import cKDTree

# Servo ID -> MuJoCo joint. The mouth (34) has no joint in xgoduck_rl; see MOUTH below.
JOINTS = {
    10: 'left_hip_yaw', 11: 'left_hip_roll', 12: 'left_hip_pitch', 13: 'left_knee', 14: 'left_ankle',
    20: 'right_hip_yaw', 21: 'right_hip_roll', 22: 'right_hip_pitch', 23: 'right_knee', 24: 'right_ankle',
    30: 'neck_pitch', 31: 'head_pitch', 32: 'head_yaw', 33: 'head_roll',
}
# Planned USB add-ons (docs/fork-roadmap.md), in mm in the STAND pose. World: x forward, y left, z up.
PARTS = [
    dict(id='camera', label='USB camera', body='jaw_soft', centre=(73, 0, 244), size=(4, 32, 32), color='#1acca6',
         note='Inside the head; the lens looks out through the eye.'),
    dict(id='lens', label=None, body='jaw_soft', centre=(82, 0, 244), size=(14, 14, 14), color='#1acca6',
         shape='cylinder-x'),
    dict(id='hub', label='USB hub', body='trunk_base', centre=(-44, 4, 156), size=(21, 65, 12), color='#fa8c26',
         note="On the Uno Q's USB-C, folded flat along the board's top edge."),
    dict(id='sound', label='Sound card', body='trunk_base', centre=(14, -35.5, 136), size=(45, 6, 21), color='#9e66f2',
         note='Right side of the body, above the thigh.'),
    dict(id='speaker', label='Speaker', body='trunk_base', centre=(6, 36.8, 135), size=(40, 9.5, 28), color='#fad133',
         note='Left side of the body, above the thigh.'),
]
# The lower beak. xgoduck_hardware's head parts share one assembly frame in mm (x left, y forward,
# z down); R and T place it on the STAND head, fitted to head_roll.stl with a 0.45 mm median gap.
# The hinge runs along x through the centre of the jaw hub's servo horn. Positive angles open.
MOUTH = dict(motor=34, body='jaw_soft', R=((0, 1, 0), (1, 0, 0), (0, 0, -1)), T=(-27.70, 0.0, 106.055),
             hinge=(0, 51.562, -126.05), moving=('jaw', 'mouth_buttom_tpu'),
             fixed=('head', 'head_shell', 'mouth_up_tpu', 'head_servo_support', 'eye', 'eye_shell'))


def read_stl(path):
    """Triangles (n, 3, 3) from a binary or ASCII STL."""
    data = Path(path).read_bytes()
    if data[:5] == b'solid' and b'facet' in data[:300]:
        v = [line.split()[1:4] for line in data.decode(errors='ignore').splitlines() if line.strip().startswith('vertex')]
        return np.array(v, float).reshape(-1, 3, 3)
    n = int.from_bytes(data[80:84], 'little')
    rec = np.frombuffer(data[84:84 + n * 50], np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    return rec['v'].astype(float)


def split_mouth(tris, hardware):
    """Split world-frame head triangles (mm) into (head, beak). Triangles that straddle the seam are
    quartered until they fall on one side or are under 0.8 mm."""
    R, T = np.array(MOUTH['R'], float), np.array(MOUTH['T'])
    def surface(names, n):
        t = np.concatenate([read_stl(next(Path(hardware).glob(name + '.[sS][tT][lL]'))) for name in names])
        area = np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1)
        rng = np.random.default_rng(0)
        k = rng.choice(len(t), n, p=area / area.sum())
        s, r = np.sqrt(rng.random(n))[:, None], rng.random(n)[:, None]
        p = (1 - s) * t[k, 0] + s * (1 - r) * t[k, 1] + s * r * t[k, 2]
        return cKDTree(p @ R.T + T)
    moving, fixed = surface(MOUTH['moving'], 150000), surface(MOUTH['fixed'], 300000)
    head, beak, stack = [], [], [tris]
    while stack:
        t = stack.pop()
        probes = np.concatenate([t, t.mean(1, keepdims=True), (t + np.roll(t, -1, 1)) / 2], 1).reshape(-1, 3)
        on_beak = (moving.query(probes)[0] < fixed.query(probes)[0]).reshape(len(t), -1)
        all_beak, all_head = on_beak.all(1), ~on_beak.any(1)
        leaf = ~(all_beak | all_head) & (np.linalg.norm(t - np.roll(t, -1, 1), axis=2).max(1) < 0.8)
        beak.append(t[all_beak | leaf & on_beak[:, 3]])
        head.append(t[all_head | leaf & ~on_beak[:, 3]])
        a, b, c = (t[~(all_beak | all_head | leaf)][:, i] for i in range(3))
        if len(a):
            ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
            stack.append(np.concatenate([np.stack(x, 1) for x in ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca))]))
    return np.concatenate(head), np.concatenate(beak)


def main(scene, out, hardware):
    m = mujoco.MjModel.from_xml_path(scene)
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, m.key('STAND').id)
    mujoco.mj_forward(m, d)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    motor = {name: mid for mid, name in JOINTS.items()}

    blob, meshes, index = bytearray(), [], {}
    def add_mesh(name, v, f):
        assert len(v) < 65536
        lo, hi = v.min(0), v.max(0)
        q = np.round((v - lo) / np.maximum(hi - lo, 1e-9) * 65535 - 32768).astype('<i2')
        while len(blob) % 4:
            blob.append(0)
        start = len(blob)
        blob.extend(q.tobytes())
        blob.extend(f.astype('<u2').tobytes())
        meshes.append(dict(name=name, offset=start, vertices=len(v), triangles=len(f), min=lo.tolist(), max=hi.tolist()))
        return len(meshes) - 1
    def mesh(mid):
        if mid not in index:
            index[mid] = add_mesh(mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, mid),
                                  m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]],
                                  m.mesh_face[m.mesh_faceadr[mid]:m.mesh_faceadr[mid] + m.mesh_facenum[mid]])
        return index[mid]

    # Split the head mesh into head and lower beak, both in the head body's frame.
    head = m.body(MOUTH['body']).id
    g, = [g for g in range(m.ngeom) if m.geom_bodyid[g] == head and m.geom_group[g] == 2]
    mid, rot, pos = m.geom_dataid[g], d.xmat[head].reshape(3, 3), d.xpos[head]
    v = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
    f = m.mesh_face[m.mesh_faceadr[mid]:m.mesh_faceadr[mid] + m.mesh_facenum[mid]]
    world = (v @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g]) * 1000
    pieces = []
    for name, tris in zip(('head', 'mouth'), split_mouth(world[f], hardware)):
        local = (tris.reshape(-1, 3) / 1000 - pos) @ rot  # world -> head body frame
        verts, faces = np.unique(local.round(7), axis=0, return_inverse=True)
        pieces.append([dict(mesh=add_mesh(name, verts, faces.reshape(-1, 3)), pos=[0, 0, 0], quat=[1, 0, 0, 0])])

    bodies = []
    for b in range(1, m.nbody):
        name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b)
        joint = None
        if m.body_jntnum[b]:
            j = m.body_jntadr[b]
            jname = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j)
            if m.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE:
                joint = dict(name=jname, motor=motor.get(jname), axis=m.jnt_axis[j].tolist(), pos=m.jnt_pos[j].tolist(),
                             stand=float(m.key('STAND').qpos[m.jnt_qposadr[j]]))
        geoms = pieces[0] if b == head else [
            dict(mesh=mesh(m.geom_dataid[g]), pos=m.geom_pos[g].tolist(), quat=m.geom_quat[g].tolist())
            for g in range(m.ngeom)
            if m.geom_bodyid[g] == b and m.geom_group[g] == 2 and m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH]
        bodies.append(dict(name=name, parent=int(m.body_parentid[b]) - 1, pos=m.body_pos[b].tolist(),
                           quat=m.body_quat[b].tolist(), joint=joint, geoms=geoms))

    # The lower beak hangs on its own body, hinged to the head.
    R, T = np.array(MOUTH['R'], float), np.array(MOUTH['T'])
    hinge = ((R @ MOUTH['hinge'] + T) / 1000 - pos) @ rot
    axis = R[:, 0] @ rot  # the hardware x axis; a positive turn about it drops the beak tip
    bodies.append(dict(name='mouth', parent=head - 1, pos=[0, 0, 0], quat=[1, 0, 0, 0],
                       joint=dict(name='mouth', motor=MOUTH['motor'], axis=axis.round(6).tolist(),
                                  pos=hinge.round(6).tolist(), stand=0.0),
                       geoms=pieces[1]))

    parts = []
    for p in PARTS:
        b = m.body(p['body']).id
        rot = d.xmat[b].reshape(3, 3).T  # world -> body, so parts stay square to the world in STAND
        local = rot @ (np.array(p['centre']) / 1000 - d.xpos[b])
        quat = np.zeros(4)
        mujoco.mju_mat2Quat(quat, rot.flatten())
        parts.append({**{k: v for k, v in p.items() if k != 'centre'}, 'body': b - 1, 'pos': local.round(5).tolist(),
                      'quat': quat.round(6).tolist(), 'size': (np.array(p['size']) / 1000).tolist()})

    root = m.key('STAND').qpos[:7]
    model = dict(version=1, source='xgoduck_rl scene_walk.xml', root=dict(pos=root[:3].tolist(), quat=root[3:].tolist()),
                 bodies=bodies, meshes=meshes, parts=parts)
    (out / 'model.json').write_text(json.dumps(model, separators=(',', ':')))
    (out / 'model.bin').write_bytes(bytes(blob))
    tris = sum(x['triangles'] for x in meshes)
    print(f'{len(bodies)} bodies, {len(meshes)} meshes, {tris} triangles, {len(blob) / 1e6:.2f} MB')


if __name__ == '__main__':
    main(*sys.argv[1:4])
