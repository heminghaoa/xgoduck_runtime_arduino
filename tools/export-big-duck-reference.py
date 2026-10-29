"""Export the Microduck model, scaled up, as reference parts for drawing the big duck in CAD.

Writes one binary STL per visual part, already placed where it sits in the model's zero pose
(every joint at 0, trunk_base origin at 0,0,0; x forward, y left, z up; millimetres), and
joints.csv with each joint's pivot, axis and range at the same scale. Imported together into one
CAD part studio, the STLs line up as the assembly. Redraw the parts that hold servos around the
ST3215 and keep every pivot where joints.csv puts it, so the training model still matches.

The meshes are Pollen Robotics' Microduck parts (CC BY-NC-SA 4.0). Keep the output for personal
use and out of this repository.

Usage: python export-big-duck-reference.py <xgoduck_rl>/src/mjlab_microduck/robot/microduck/scene_walk.xml out_dir [scale]
Scale defaults to 1.4. Needs mujoco and numpy on a desktop machine (the xgoduck_rl environment
has both).
"""
import csv
import math
import sys
from pathlib import Path

import mujoco
import numpy as np

STL_TRI = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('attr', '<u2')])


def write_stl(path, verts, faces):
    tri = verts[faces]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(faces), STL_TRI)
    rec['n'], rec['v'] = n, tri
    with open(path, 'wb') as fh:
        fh.write(b'big duck reference'.ljust(80, b' '))
        fh.write(np.uint32(len(faces)).tobytes())
        fh.write(rec.tobytes())


def main(scene, out_dir, scale='1.4'):
    scale = float(scale)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    m = mujoco.MjModel.from_xml_path(scene)
    d = mujoco.MjData(m)
    mujoco.mj_resetData(m, d)
    d.qpos[:7] = [0, 0, 0, 1, 0, 0, 0]    # trunk_base at the origin, upright
    mujoco.mj_kinematics(m, d)
    k = 1000.0 * scale

    count = {}
    for g in range(m.ngeom):
        if m.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH or m.geom_group[g] != 2:
            continue
        mid = m.geom_dataid[g]
        name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, mid)
        body = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, m.geom_bodyid[g])
        va, vn = m.mesh_vertadr[mid], m.mesh_vertnum[mid]
        fa, fn = m.mesh_faceadr[mid], m.mesh_facenum[mid]
        verts = (m.mesh_vert[va:va + vn] @ d.geom_xmat[g].reshape(3, 3).T + d.geom_xpos[g]) * k
        key = f'{body}_{name}'
        count[key] = count.get(key, 0) + 1
        suffix = f'_{count[key]}' if count[key] > 1 else ''
        write_stl(out / f'{key}{suffix}.stl', verts, m.mesh_face[fa:fa + fn])

    with open(out / 'joints.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['joint', 'pivot_x_mm', 'pivot_y_mm', 'pivot_z_mm', 'axis_x', 'axis_y', 'axis_z', 'min_deg', 'max_deg'])
        for j in range(m.njnt):
            if m.jnt_type[j] != mujoco.mjtJoint.mjJNT_HINGE:
                continue
            p, a = d.xanchor[j] * k, d.xaxis[j]
            lo, hi = (math.degrees(v) for v in m.jnt_range[j])
            w.writerow([mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j)] + [f'{v:.1f}' for v in p]
                       + [f'{v:+.3f}' for v in a] + [f'{lo:.0f}', f'{hi:.0f}'])
    print(f'{sum(count.values())} parts and joints.csv written to {out} at {scale:g}x')


if __name__ == '__main__':
    main(*sys.argv[1:4])
