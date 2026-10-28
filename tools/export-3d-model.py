"""Export the xgoduck_rl MuJoCo model for the web page's 3D view.

Writes model.json (bodies, joints, geoms, add-on parts) and model.bin (meshes:
int16 positions quantised to each mesh's bounds, uint16 triangle indices).
Joint angles in degrees from /api/status map one to one onto the model's joints
in radians: the runtime's default pose is the model's STAND keyframe.

Usage: python export-3d-model.py <xgoduck_rl>/src/mjlab_microduck/robot/xgoduck/scene_walk.xml assets/model
Needs mujoco and numpy on a desktop machine, not on the Uno Q.
"""
import json
import sys
from pathlib import Path
import numpy as np
import mujoco

# Servo ID -> MuJoCo joint. The mouth (34) is not modelled.
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


def main(scene, out):
    m = mujoco.MjModel.from_xml_path(scene)
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, m.key('STAND').id)
    mujoco.mj_forward(m, d)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    motor = {name: mid for mid, name in JOINTS.items()}

    blob, meshes, index = bytearray(), [], {}
    def mesh(mid):
        if mid in index:
            return index[mid]
        v = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
        f = m.mesh_face[m.mesh_faceadr[mid]:m.mesh_faceadr[mid] + m.mesh_facenum[mid]]
        assert len(v) < 65536
        lo, hi = v.min(0), v.max(0)
        q = np.round((v - lo) / np.maximum(hi - lo, 1e-9) * 65535 - 32768).astype('<i2')
        while len(blob) % 4:
            blob.append(0)
        start = len(blob)
        blob.extend(q.tobytes())
        blob.extend(f.astype('<u2').tobytes())
        meshes.append(dict(name=mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, mid), offset=start,
                           vertices=len(v), triangles=len(f), min=lo.tolist(), max=hi.tolist()))
        index[mid] = len(meshes) - 1
        return index[mid]

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
        geoms = [dict(mesh=mesh(m.geom_dataid[g]), pos=m.geom_pos[g].tolist(), quat=m.geom_quat[g].tolist())
                 for g in range(m.ngeom)
                 if m.geom_bodyid[g] == b and m.geom_group[g] == 2 and m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH]
        bodies.append(dict(name=name, parent=int(m.body_parentid[b]) - 1, pos=m.body_pos[b].tolist(),
                           quat=m.body_quat[b].tolist(), joint=joint, geoms=geoms))

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
    main(*sys.argv[1:3])
