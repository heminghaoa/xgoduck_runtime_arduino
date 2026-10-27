"""Render zero-pose calibration references from the xgoduck_rl MuJoCo model.

All joints at 0 rad (keyframe INIT) is the pose every servo must hold when it is
centered: the runtime maps 0 deg to encoder 2047, and its default pose equals the
training model's STAND keyframe.

Usage: python render-zero-refs.py <xgoduck_rl>/src/mjlab_microduck/robot/xgoduck/scene_walk.xml assets/zero
Needs mujoco, numpy and pillow on a desktop machine, not on the Uno Q.
"""
import sys
from pathlib import Path
import numpy as np
import mujoco
from PIL import Image, ImageDraw

SCALE = 2  # Render at 2x and downsample for smooth edges.
MOVING = (0x6d, 0xe1, 0xc4)   # The link this servo turns (page accent).
PARENT = (0xc9, 0xd3, 0xde)   # The link the servo is mounted on.
OTHER = (0x4a, 0x5a, 0x6c)    # Everything else.
NEUTRAL = (0xaa, 0xb6, 0xc3)  # Whole-robot views.
MARK = (0xf1, 0xca, 0x86)     # Servo axis ring and line to the next axis.

# Servo ID -> MuJoCo joint, in runtime MOTOR_IDS order. The mouth (34) is not modelled.
JOINTS = {
    10: 'left_hip_yaw', 11: 'left_hip_roll', 12: 'left_hip_pitch', 13: 'left_knee', 14: 'left_ankle',
    20: 'right_hip_yaw', 21: 'right_hip_roll', 22: 'right_hip_pitch', 23: 'right_knee', 24: 'right_ankle',
    30: 'neck_pitch', 31: 'head_pitch', 32: 'head_yaw', 33: 'head_roll',
}
# Camera azimuth/elevation in degrees (MuJoCo free camera).
FRONT, LEFT, RIGHT = (180, 0), (-90, 0), (90, 0)
TOP, BELOW = (0, -89.9), (180, 89.9)  # Forward (+x) points up in both.
VIEWS = {
    10: BELOW, 20: BELOW, 11: FRONT, 21: FRONT,
    12: LEFT, 13: LEFT, 14: LEFT, 22: RIGHT, 23: RIGHT, 24: RIGHT,
    30: LEFT, 31: LEFT, 32: TOP, 33: FRONT,
}


def load(scene):
    m = mujoco.MjModel.from_xml_path(scene)
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, m.key('INIT').id)
    mujoco.mj_forward(m, d)
    m.vis.global_.orthographic = 1
    m.vis.global_.offwidth = m.vis.global_.offheight = 1024
    m.vis.headlight.ambient[:] = 0.2
    m.vis.headlight.diffuse[:] = 0.6
    m.vis.headlight.specular[:] = 0.15
    return m, d


def subtree(m, root):
    ids = set()
    for b in range(m.nbody):
        p = b
        while p > 0 and p != root:
            p = m.body_parentid[p]
        if p == root:
            ids.add(b)
    return ids


def basis(az, el):
    a, e = np.radians(az), np.radians(el)
    fwd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    up = np.array([-np.sin(e) * np.cos(a), -np.sin(e) * np.sin(a), np.cos(e)])
    return fwd, up, np.cross(fwd, up)


def render(m, d, colour, view, size, hidden=(), frame=None, marks=()):
    w, h = size
    for g in range(m.ngeom):
        b = m.geom_bodyid[g]
        shown = m.geom_group[g] == 2 and b not in hidden
        m.geom_rgba[g] = (*[c / 255 for c in colour(b)], 1) if shown else (0, 0, 0, 0)
    keep = [g for g in range(m.ngeom) if m.geom_rgba[g, 3] > 0 and (frame is None or m.geom_bodyid[g] in frame)]
    az, el = view
    fwd, up, right = basis(az, el)
    pts = np.array([d.geom_xpos[g] for g in keep])
    rad = np.array([m.geom_rbound[g] for g in keep])
    # Fit the framed geoms' bounding spheres on the image plane.
    u, r_ = pts @ up, pts @ right
    centre = ((u - rad).min() + (u + rad).max()) / 2 * up + ((r_ - rad).min() + (r_ + rad).max()) / 2 * right
    centre += (pts @ fwd).mean() * fwd
    extent = max((u + rad).max() - (u - rad).min(), ((r_ + rad).max() - (r_ - rad).min()) * h / w) * 1.12
    m.vis.global_.fovy = extent
    cam = mujoco.MjvCamera()
    cam.orthographic = 1
    cam.lookat[:] = centre
    cam.distance = 1.0
    cam.azimuth, cam.elevation = az, el
    r = mujoco.Renderer(m, h * SCALE, w * SCALE)
    opt = mujoco.MjvOption()
    opt.geomgroup[:] = 0
    opt.geomgroup[2] = 1
    r.update_scene(d, cam, opt)
    r.scene.flags[mujoco.mjtRndFlag.mjRND_SKYBOX] = 0
    rgb = r.render()
    r.enable_segmentation_rendering()
    r.update_scene(d, cam, opt)
    seg = r.render()[:, :, 0]
    r.close()
    alpha = np.where(seg >= 0, 255, 0).astype(np.uint8)
    img = Image.fromarray(np.dstack([rgb, alpha]), 'RGBA').resize((w, h), Image.LANCZOS)

    def px(p):
        v = np.asarray(p) - centre
        return (w / 2 + (v @ right) * h / extent, h / 2 - (v @ up) * h / extent)
    draw = ImageDraw.Draw(img)
    if len(marks) == 2:
        a, b = px(marks[0]), px(marks[1])
        n = max(1, int(np.hypot(b[0] - a[0], b[1] - a[1]) / 6))
        for i in range(0, n, 2):  # Dashed line to the next axis.
            t0, t1 = i / n, min(1, (i + 1) / n)
            draw.line([(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                       (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)], fill=MARK + (255,), width=2)
        draw.ellipse([b[0] - 3, b[1] - 3, b[0] + 3, b[1] + 3], fill=MARK + (255,))
    if marks:
        a = px(marks[0])
        draw.ellipse([a[0] - 8, a[1] - 8, a[0] + 8, a[1] + 8], outline=(11, 18, 26, 255), width=5)
        draw.ellipse([a[0] - 8, a[1] - 8, a[0] + 8, a[1] + 8], outline=MARK + (255,), width=2)
    return img


def main(scene, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    m, d = load(scene)
    above_hips = {m.body('trunk_base').id} | subtree(m, m.body('neck').id)

    for name, view in (('front', FRONT), ('side', LEFT), ('angle', (150, -25))):
        render(m, d, lambda b: NEUTRAL, view, (360, 420)).save(out / f'pose-{name}.webp', quality=88)

    for sid, jname in JOINTS.items():
        j = m.joint(jname).id
        body = m.jnt_bodyid[j]
        moving = subtree(m, body)
        parent = m.body_parentid[body]
        child = [k for k in range(m.njnt) if m.body_parentid[m.jnt_bodyid[k]] == body]
        marks = [d.xanchor[j].copy()] + ([d.xanchor[child[0]].copy()] if child else [])
        hidden = above_hips if VIEWS[sid] == BELOW else ()
        frame = (moving | {parent}) - set(hidden)

        def colour(b):
            return MOVING if b in moving else PARENT if b == parent else OTHER
        render(m, d, colour, VIEWS[sid], (360, 360), hidden, frame, marks).save(out / f'joint-{sid}.webp', quality=88)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
