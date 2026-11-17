# SPDX-License-Identifier: GPL-3.0-or-later
#
# Mini Bezier Shaper
# Shape a row of vertices, or a whole strand (e.g. a hair lock), with a live Bezier curve.

bl_info = {
    "name": "Mini Bezier Shaper",
    "author": "KC",
    "version": (1, 5, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar (N) > Edit > Mini Bezier Shaper",
    "description": "Shape a row of vertices or a whole hair strand with a live Bezier curve",
    "category": "Mesh",
}

import bisect
import math
import bpy
import bmesh
from bpy.app.handlers import persistent
from bpy.app.translations import pgettext_tip as tip_
from mathutils import Vector, Matrix

_busy = False


# ---------------------------------------------------------------- geometry

def ordered_chain(sel_verts):
    s = set(sel_verts)
    nb = {v: [e.other_vert(v) for e in v.link_edges
              if e.select and e.other_vert(v) in s] for v in sel_verts}
    ends = [v for v in sel_verts if len(nb[v]) == 1]
    if len(ends) != 2:
        return None
    chain, prev, cur = [ends[0]], None, ends[0]
    while True:
        nxt = [n for n in nb[cur] if n is not prev]
        if not nxt:
            break
        prev, cur = cur, nxt[0]
        chain.append(cur)
    return chain if len(chain) == len(sel_verts) else None


def cumulative(pts):
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    return L


def locate(L, t):
    target = t * L[-1]
    i = bisect.bisect_left(L, target)
    i = max(1, min(i, len(L) - 1))
    seg = L[i] - L[i - 1]
    f = 0.0 if seg == 0 else (target - L[i - 1]) / seg
    return i - 1, f


def sample(pts, L, t):
    i, f = locate(L, t)
    return pts[i].lerp(pts[i + 1], f)


def any_perp(v):
    a = Vector((1, 0, 0)) if abs(v.x) < 0.9 else Vector((0, 1, 0))
    return v.cross(a).normalized()


def frames(pts, n0):
    """Rotation-minimizing frame (T, N, B) for each polyline segment."""
    res, n, prev_t = [], n0.copy(), None
    for i in range(len(pts) - 1):
        T = (pts[i + 1] - pts[i]).normalized()
        if prev_t is not None:
            n = prev_t.rotation_difference(T) @ n
        n = n - T * n.dot(T)
        if n.length < 1e-8:
            n = any_perp(T)
        n.normalize()
        res.append((T, n, T.cross(n)))
        prev_t = T
    return res


def project(p, pts):
    best = None
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        l2 = ab.length_squared
        f = 0.0 if l2 == 0 else max(0.0, min(1.0, (p - a).dot(ab) / l2))
        q = a + ab * f
        d = (p - q).length_squared
        if best is None or d < best[0]:
            best = (d, i, f, q)
    return best[1], best[2], best[3]


def centerline(pts, bins=12):
    """Rough spine through a strand: principal axis, binned averages."""
    c = sum(pts, Vector()) / len(pts)
    cov = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
    for p in pts:
        d = p - c
        for r in range(3):
            for s in range(3):
                cov[r][s] += d[r] * d[s]
    axis = Vector((0.577, 0.577, 0.577))
    for _ in range(60):
        w = cov @ axis
        if w.length == 0:
            break
        axis = w.normalized()
    proj = [(p - c).dot(axis) for p in pts]
    lo, hi = min(proj), max(proj)
    if hi - lo < 1e-9:
        return None
    sums = [Vector() for _ in range(bins)]
    cnt = [0] * bins
    for p, s in zip(pts, proj):
        b = min(bins - 1, int((s - lo) / (hi - lo) * bins))
        sums[b] += p
        cnt[b] += 1
    line = [sums[b] / cnt[b] for b in range(bins) if cnt[b]]
    if len(line) < 2:
        return None
    line[0] = line[0] + axis * (lo - (line[0] - c).dot(axis))
    line[-1] = line[-1] + axis * (hi - (line[-1] - c).dot(axis))
    return line


def eval_curve_points(cobj, depsgraph):
    ev = cobj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    raw = [cobj.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    out = []
    for p in raw:
        if not out or (p - out[-1]).length > 1e-7:
            out.append(p)
    return out


# ---------------------------------------------------------------- live update

def apply_shape(cobj, depsgraph):
    target = bpy.data.objects.get(cobj.get("mbs_target", ""))
    if not target or target.type != 'MESH' or target.mode != 'OBJECT':
        return
    pts = eval_curve_points(cobj, depsgraph)
    if len(pts) < 2:
        return
    L = cumulative(pts)
    if L[-1] == 0:
        return
    inv = target.matrix_world.inverted()
    verts = target.data.vertices
    idx = list(cobj["mbs_idx"])
    ts = list(cobj["mbs_t"])

    if cobj.get("mbs_mode") == 'ROW':
        for k, t in zip(idx, ts):
            if k < len(verts):
                verts[k].co = inv @ sample(pts, L, t)
    else:
        off = list(cobj["mbs_off"])
        t0_rest = Vector(cobj["mbs_T0"])
        n0_rest = Vector(cobj["mbs_N0"])
        t0 = (pts[1] - pts[0]).normalized()
        fr = frames(pts, t0_rest.rotation_difference(t0) @ n0_rest)
        for j, (k, t) in enumerate(zip(idx, ts)):
            if k >= len(verts):
                continue
            i, f = locate(L, t)
            T, N, B = fr[i]
            base = pts[i].lerp(pts[i + 1], f)
            o = off[3 * j:3 * j + 3]
            verts[k].co = inv @ (base + T * o[0] + N * o[1] + B * o[2])
    target.data.update()


@persistent
def mbs_handler(scene, depsgraph):
    global _busy
    if _busy:
        return
    _busy = True
    try:
        for upd in depsgraph.updates:
            ob = getattr(upd.id, "original", upd.id)
            if isinstance(ob, bpy.types.Object) and "mbs_target" in ob:
                apply_shape(ob, depsgraph)
    finally:
        _busy = False


# ---------------------------------------------------------------- operators

class MESH_OT_mbs_create(bpy.types.Operator):
    bl_idname = "mesh.mbs_create"
    bl_label = "Create Shaper Curve"
    bl_description = "Create a Bezier curve on the selection; editing the curve reshapes the mesh live"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        obj = context.edit_object
        mode = context.scene.mbs_mode
        n_ctrl = context.scene.mbs_points
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.index_update()
        sel = [v for v in bm.verts if v.select]
        if len(sel) < 2:
            self.report({'ERROR'}, tip_("Select at least 2 vertices"))
            return {'CANCELLED'}

        if mode == 'ROW':
            sel = ordered_chain(sel)
            if not sel:
                self.report({'ERROR'}, tip_("Single Row mode needs one connected, open row of vertices"))
                return {'CANCELLED'}

        mw = obj.matrix_world
        world = [mw @ v.co for v in sel]
        idx = [v.index for v in sel]
        orig = [c for v in sel for c in v.co]
        guide = None
        if mode == 'ROW':
            guide = world
        else:
            if context.scene.mbs_follow_rings:
                guide = ring_spine(sel, mw)
                if not guide:
                    self.report({'WARNING'}, tip_("Could not follow the rings; used the simple direction instead"))
            if not guide:
                guide = centerline(world)
        if not guide:
            self.report({'ERROR'}, tip_("Could not find the strand direction"))
            return {'CANCELLED'}
        GL = cumulative(guide)

        bpy.ops.object.mode_set(mode='OBJECT')

        cd = bpy.data.curves.new("ShaperCurve", 'CURVE')
        cd.dimensions = '3D'
        cd.resolution_u = 32
        sp = cd.splines.new('BEZIER')
        sp.bezier_points.add(n_ctrl - 1)
        for i, bp in enumerate(sp.bezier_points):
            bp.co = sample(guide, GL, i / (n_ctrl - 1))
            bp.handle_left_type = bp.handle_right_type = 'AUTO'
        cobj = bpy.data.objects.new("ShaperCurve", cd)
        context.collection.objects.link(cobj)
        context.view_layer.update()

        if mode == 'ROW':
            ts = [d / GL[-1] if GL[-1] else 0.0 for d in GL]
        else:
            pts = eval_curve_points(cobj, context.evaluated_depsgraph_get())
            L = cumulative(pts)
            t0 = (pts[1] - pts[0]).normalized()
            n0 = any_perp(t0)
            fr = frames(pts, n0)
            ts, off = [], []
            for p in world:
                i, f, q = project(p, pts)
                ts.append((L[i] + f * (L[i + 1] - L[i])) / L[-1])
                T, N, B = fr[i]
                d = p - q
                off += [d.dot(T), d.dot(N), d.dot(B)]
            cobj["mbs_off"] = off
            cobj["mbs_T0"] = list(t0)
            cobj["mbs_N0"] = list(n0)

        cobj["mbs_target"] = obj.name
        cobj["mbs_mode"] = mode
        cobj["mbs_idx"] = idx
        cobj["mbs_t"] = ts
        cobj["mbs_orig"] = orig

        for o in context.selected_objects:
            o.select_set(False)
        cobj.select_set(True)
        context.view_layer.objects.active = cobj
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


def _back_to_mesh(context, cobj):
    target = bpy.data.objects.get(cobj["mbs_target"])
    bpy.data.objects.remove(cobj, do_unlink=True)
    if target:
        target.select_set(True)
        context.view_layer.objects.active = target
        bpy.ops.object.mode_set(mode='EDIT')


class MESH_OT_mbs_finish(bpy.types.Operator):
    bl_idname = "mesh.mbs_finish"
    bl_label = "Finish Shaping"
    bl_description = "Keep the new shape, delete the shaper curve and return to the mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and "mbs_target" in ob

    def execute(self, context):
        cobj = context.active_object
        if cobj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        apply_shape(cobj, context.evaluated_depsgraph_get())
        _back_to_mesh(context, cobj)
        return {'FINISHED'}


class MESH_OT_mbs_cancel(bpy.types.Operator):
    bl_idname = "mesh.mbs_cancel"
    bl_label = "Cancel Shaping"
    bl_description = "Restore the original shape and delete the shaper curve"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob is not None and "mbs_target" in ob

    def execute(self, context):
        cobj = context.active_object
        if cobj.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        target = bpy.data.objects.get(cobj["mbs_target"])
        if target:
            verts = target.data.vertices
            orig = list(cobj["mbs_orig"])
            for j, k in enumerate(cobj["mbs_idx"]):
                if k < len(verts):
                    verts[k].co = Vector(orig[3 * j:3 * j + 3])
            target.data.update()
        _back_to_mesh(context, cobj)
        return {'FINISHED'}


# ---------------------------------------------------------------- strand rings

def strand_rings(sel):
    """Split a selected strand into cross-section rings, counted from its root.

    The root is the open end of the strand, or where it touches unselected geometry.
    Returns (neighbours, layer per vertex, rings, ring index per vertex) or None.
    """
    S = set(sel)
    nb = {v: [e.other_vert(v) for e in v.link_edges if e.other_vert(v) in S] for v in sel}
    seeds = [v for v in sel if v.is_boundary
             or any(e.other_vert(v) not in S for e in v.link_edges)]
    if not seeds:
        return None

    layer = {v: 0 for v in seeds}
    frontier = seeds
    while frontier:
        nxt = []
        for v in frontier:
            for n in nb[v]:
                if n not in layer:
                    layer[n] = layer[v] + 1
                    nxt.append(n)
        frontier = nxt

    ring_of, rings = {}, []
    for v in sel:
        if v not in layer or v in ring_of:
            continue
        ri = len(rings)
        comp, stack = [v], [v]
        ring_of[v] = ri
        while stack:
            a = stack.pop()
            for n in nb[a]:
                if n not in ring_of and layer.get(n) == layer[v]:
                    ring_of[n] = ri
                    comp.append(n)
                    stack.append(n)
        rings.append(comp)
    return nb, layer, rings, ring_of


def ring_spine(sel, mw):
    """Centre line through the ring centres, root to tip, in world space."""
    found = strand_rings(sel)
    if not found:
        return None
    _, layer, rings, _ = found
    by_layer = {}
    for r in rings:
        by_layer.setdefault(layer[r[0]], []).append(r)
    if any(len(rs) != 1 for rs in by_layer.values()):
        return None
    pts = []
    for k in sorted(by_layer):
        r = by_layer[k][0]
        pts.append(mw @ (sum((v.co for v in r), Vector()) / len(r)))
    return pts if len(pts) >= 2 else None


# ---------------------------------------------------------------- tidy strand

def _cycle_order(ring, nb):
    if len(ring) < 3:
        return None
    rs = set(ring)
    rn = {v: [n for n in nb[v] if n in rs] for v in ring}
    if any(len(x) != 2 for x in rn.values()):
        return None
    start = ring[0]
    order, prev, cur = [start], None, start
    while True:
        a, b = rn[cur]
        nxt = b if a is prev else a
        if nxt is start:
            break
        order.append(nxt)
        prev, cur = cur, nxt
        if len(order) > len(ring):
            return None
    return order if len(order) == len(ring) else None


class MESH_OT_mbs_tidy(bpy.types.Operator):
    bl_idname = "mesh.mbs_tidy_strand"
    bl_label = "Tidy Strand"
    bl_description = ("Make every cross-section of the selected strand round and evenly spaced, "
                      "and smooth the strand along its length")
    bl_options = {'REGISTER', 'UNDO'}

    roundness: bpy.props.FloatProperty(
        name="Roundness", default=1.0, min=0.0, max=1.0, subtype='FACTOR')
    smooth: bpy.props.IntProperty(name="Smooth", default=3, min=0, max=30)
    untwist: bpy.props.BoolProperty(name="Untwist", default=True)

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        obj = context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)
        sel = [v for v in bm.verts if v.select]
        if len(sel) < 3:
            self.report({'ERROR'}, tip_("Select at least 3 vertices"))
            return {'CANCELLED'}
        found = strand_rings(sel)
        if not found:
            self.report({'ERROR'}, tip_("Leave the root open, or leave the root ring unselected as an anchor"))
            return {'CANCELLED'}
        nb, layer, rings, ring_of = found

        R = len(rings)
        adj = [set() for _ in range(R)]
        for v, ri in ring_of.items():
            for n in nb[v]:
                rj = ring_of.get(n)
                if rj is not None and rj != ri:
                    adj[ri].add(rj)
        adj = [list(a) for a in adj]
        anchor = [layer[r[0]] == 0 for r in rings]
        movable = [not anchor[i] and len(adj[i]) == 2 for i in range(R)]

        rlayer = [layer[r[0]] for r in rings]
        center = [sum((v.co for v in r), Vector()) / len(r) for r in rings]

        def prev_next(i):
            lo = [j for j in adj[i] if rlayer[j] < rlayer[i]]
            hi = [j for j in adj[i] if rlayer[j] > rlayer[i]]
            return (lo[0] if lo else None), (hi[0] if hi else None)

        # smooth the spine
        c = [x.copy() for x in center]
        for _ in range(self.smooth):
            c = [c[i].lerp((c[adj[i][0]] + c[adj[i][1]]) / 2, 0.5) if movable[i] else c[i]
                 for i in range(R)]

        # direction of the strand at each ring, always pointing root -> tip
        normal = []
        for i in range(R):
            p, q = prev_next(i)
            if p is not None and q is not None:
                d = c[q] - c[p]
            elif q is not None:
                d = c[q] - c[i]
            elif p is not None:
                d = c[i] - c[p]
            else:
                d = Vector((0, 0, 1))
            normal.append(d.normalized() if d.length > 1e-9 else Vector((0, 0, 1)))

        by_layer = sorted(range(R), key=lambda k: rlayer[k])

        # twist-free reference direction carried from the root to the tip
        uref = [None] * R
        for i in by_layer:
            n = normal[i]
            p, _ = prev_next(i)
            if p is not None and uref[p] is not None:
                u = normal[p].rotation_difference(n) @ uref[p]
            else:
                u = any_perp(n)
            u = u - n * u.dot(n)
            uref[i] = u.normalized() if u.length > 1e-9 else any_perp(n)

        # radius per ring, then smooth it so the taper stays clean
        rad = []
        for i, r in enumerate(rings):
            n = normal[i]
            ds = []
            for v in r:
                d = v.co - center[i]
                ds.append((d - n * d.dot(n)).length)
            rad.append(sum(ds) / len(ds))
        for _ in range(self.smooth):
            rad = [(rad[i] + (rad[adj[i][0]] + rad[adj[i][1]]) / 2) / 2 if movable[i] else rad[i]
                   for i in range(R)]

        targets, final_ang, skipped, done = {}, {}, 0, 0
        for i in by_layer:
            ring = rings[i]
            n = normal[i]
            u = uref[i]
            w = n.cross(u)
            if anchor[i]:
                for v in ring:
                    d = v.co - center[i]
                    final_ang[v] = math.atan2(d.dot(w), d.dot(u))
                continue
            shift = c[i] - center[i]
            order = _cycle_order(ring, nb)
            if not order:
                if len(ring) >= 3:
                    skipped += 1
                for v in ring:
                    targets[v] = v.co + shift
                continue
            angs = []
            for v in order:
                d = v.co - center[i]
                angs.append(math.atan2(d.dot(w), d.dot(u)))
            m = len(order)
            turn = sum(((angs[(k + 1) % m] - angs[k] + math.pi) % (2 * math.pi)) - math.pi
                       for k in range(m))
            if turn < 0:
                order.reverse()
                angs.reverse()
            step = 2 * math.pi / m

            # untwist: line each vertex up with the one it connects to in the previous ring
            ref = []
            if self.untwist:
                p, _ = prev_next(i)
                if p is not None:
                    pr = set(rings[p])
                    for k, v in enumerate(order):
                        cs = [x for x in nb[v] if x in pr and x in final_ang]
                        if cs:
                            ref.append((k, final_ang[cs[0]]))
            if not ref:
                ref = list(enumerate(angs))
            sx = sum(math.cos(a - k * step) for k, a in ref)
            sy = sum(math.sin(a - k * step) for k, a in ref)
            phase = math.atan2(sy, sx)

            for k, v in enumerate(order):
                a = phase + k * step
                ideal = c[i] + (u * math.cos(a) + w * math.sin(a)) * rad[i]
                targets[v] = (v.co + shift).lerp(ideal, self.roundness)
                final_ang[v] = a
            done += 1

        for v, p in targets.items():
            v.co = p
        bmesh.update_edit_mesh(obj.data)

        if done == 0:
            self.report({'WARNING'}, tip_("No clean cross-section loops found; only smoothed the path"))
        elif skipped:
            self.report({'WARNING'}, tip_("Some cross-sections are not clean loops; they were only smoothed"))
        return {'FINISHED'}


# ---------------------------------------------------------------- smooth twist

def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


class MESH_OT_mbs_smooth_twist(bpy.types.Operator):
    bl_idname = "mesh.mbs_smooth_twist"
    bl_label = "Smooth Twist"
    bl_description = ("Spread the twist of the selected strand evenly from root to tip. "
                      "Each cross-section keeps its shape and position and is only turned "
                      "around the strand")
    bl_options = {'REGISTER', 'UNDO'}

    strength: bpy.props.FloatProperty(
        name="Strength", default=1.0, min=0.0, max=1.0, subtype='FACTOR')

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        obj = context.edit_object
        bm = bmesh.from_edit_mesh(obj.data)
        sel = [v for v in bm.verts if v.select]
        if len(sel) < 3:
            self.report({'ERROR'}, tip_("Select at least 3 vertices"))
            return {'CANCELLED'}
        found = strand_rings(sel)
        if not found:
            self.report({'ERROR'}, tip_("Leave the root open, or leave the root ring unselected as an anchor"))
            return {'CANCELLED'}
        nb, layer, rings, ring_of = found

        per_layer = {}
        for i, r in enumerate(rings):
            per_layer.setdefault(layer[r[0]], []).append(i)
        if any(len(x) != 1 for x in per_layer.values()):
            self.report({'ERROR'}, tip_("Select one strand at a time, with clean cross-section rings"))
            return {'CANCELLED'}
        order = [per_layer[k][0] for k in sorted(per_layer)]
        R = len(order)
        if R < 3:
            self.report({'ERROR'}, tip_("The strand needs at least 3 cross-sections"))
            return {'CANCELLED'}

        center = [sum((v.co for v in rings[i]), Vector()) / len(rings[i]) for i in order]

        # strand direction at each ring, root -> tip
        normal = []
        for k in range(R):
            a = center[max(k - 1, 0)]
            b = center[min(k + 1, R - 1)]
            d = b - a
            normal.append(d.normalized() if d.length > 1e-9 else Vector((0, 0, 1)))

        # twist-free reference carried from root to tip
        uref = []
        for k in range(R):
            n = normal[k]
            u = any_perp(n) if k == 0 else normal[k - 1].rotation_difference(n) @ uref[k - 1]
            u = u - n * u.dot(n)
            uref.append(u.normalized() if u.length > 1e-9 else any_perp(n))

        # angle of each vertex around the strand, in that twist-free frame
        ang = {}
        for k, i in enumerate(order):
            n, u = normal[k], uref[k]
            w = n.cross(u)
            for v in rings[i]:
                d = v.co - center[k]
                d = d - n * d.dot(n)
                if d.length > 1e-7:
                    ang[v] = math.atan2(d.dot(w), d.dot(u))

        # how far each ring is turned compared with the root, following the edges
        theta = [0.0] + [None] * (R - 1)
        for k in range(1, R):
            if theta[k - 1] is None:
                break
            prev = set(rings[order[k - 1]])
            sx = sy = 0.0
            for v in rings[order[k]]:
                if v not in ang:
                    continue
                for x in nb[v]:
                    if x in prev and x in ang:
                        dlt = _wrap(ang[v] - ang[x])
                        sx += math.cos(dlt)
                        sy += math.sin(dlt)
            if sx == 0.0 and sy == 0.0:
                break
            theta[k] = theta[k - 1] + math.atan2(sy, sx)

        last = max(k for k in range(R) if theta[k] is not None
                   and len(rings[order[k]]) >= 3)
        if last < 2:
            self.report({'ERROR'}, tip_("The strand needs at least 3 cross-sections"))
            return {'CANCELLED'}

        # distance along the strand, so the twist is spread by length
        s = [0.0]
        for k in range(1, last + 1):
            s.append(s[-1] + (center[k] - center[k - 1]).length)
        total = s[last] or 1.0

        moved = 0
        for k in range(1, last):
            target = theta[last] * s[k] / total
            delta = (target - theta[k]) * self.strength
            if abs(delta) < 1e-6:
                continue
            rot = Matrix.Rotation(delta, 3, normal[k])
            c = center[k]
            for v in rings[order[k]]:
                v.co = c + rot @ (v.co - c)
            moved += 1

        bmesh.update_edit_mesh(obj.data)
        if moved == 0:
            self.report({'INFO'}, tip_("The twist is already even"))
        return {'FINISHED'}


# ---------------------------------------------------------------- UI

class VIEW3D_PT_mbs(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Edit"
    bl_label = "Mini Bezier Shaper"

    def draw(self, context):
        layout = self.layout
        ob = context.active_object
        if ob is not None and "mbs_target" in ob:
            col = layout.column(align=True)
            col.operator(MESH_OT_mbs_finish.bl_idname, icon='CHECKMARK')
            col.operator(MESH_OT_mbs_cancel.bl_idname, icon='X')
            return
        sc = context.scene
        layout.prop(sc, "mbs_mode", expand=True)
        layout.prop(sc, "mbs_points")
        if sc.mbs_mode == 'STRAND':
            layout.prop(sc, "mbs_follow_rings")
        layout.operator(MESH_OT_mbs_create.bl_idname, icon='CURVE_BEZCURVE')
        if context.mode == 'EDIT_MESH':
            layout.separator()
            col = layout.column(align=True)
            col.operator(MESH_OT_mbs_tidy.bl_idname, icon='MESH_CIRCLE')
            col.operator(MESH_OT_mbs_smooth_twist.bl_idname, icon='FORCE_VORTEX')


# ---------------------------------------------------------------- translations

_zh = {
    ("*", "Mini Bezier Shaper"): "迷你貝茲塑形",
    ("Operator", "Create Shaper Curve"): "建立塑形曲線",
    ("Operator", "Finish Shaping"): "完成塑形",
    ("Operator", "Cancel Shaping"): "取消塑形",
    ("*", "Create Shaper Curve"): "建立塑形曲線",
    ("*", "Finish Shaping"): "完成塑形",
    ("*", "Cancel Shaping"): "取消塑形",
    ("*", "Mode"): "模式",
    ("*", "Whole Strand"): "整撮髮束",
    ("*", "Single Row"): "單排點",
    ("*", "Control Points"): "控制點數",
    ("*", "Select at least 2 vertices"): "請至少選 2 個點",
    ("*", "Single Row mode needs one connected, open row of vertices"): "單排點模式需要選一排相連、不封閉的點",
    ("*", "Could not find the strand direction"): "找不到髮束的方向",
    ("*", "Bend everything selected (a hair strand, a tube, a ribbon) along the curve"): "沿曲線彎曲所有選取的部分（髮束、管子、髮片）",
    ("*", "Snap one connected row of vertices onto the curve"): "把一排相連的點貼到曲線上",
    ("Operator", "Tidy Strand"): "整理髮束",
    ("*", "Tidy Strand"): "整理髮束",
    ("*", "Roundness"): "圓度",
    ("*", "Smooth"): "平順",
    ("*", "Untwist"): "解開扭轉",
    ("*", "Follow Rings"): "沿截面找中心線",
    ("*", "Find the strand's centre line through its cross-section rings, "
          "so strands that are already bent work too"): "沿著每一圈截面找髮束中心線，已經彎過的髮束也能用",
    ("*", "Could not follow the rings; used the simple direction instead"): "沒辦法沿截面找中心線，改用簡單方向",
    ("Operator", "Smooth Twist"): "平順扭轉",
    ("*", "Smooth Twist"): "平順扭轉",
    ("*", "Strength"): "強度",
    ("*", "Select one strand at a time, with clean cross-section rings"): "一次選一撮，而且截面要是整齊的一圈",
    ("*", "The strand needs at least 3 cross-sections"): "髮束至少要有 3 圈截面",
    ("*", "The twist is already even"): "扭轉已經很平均了",
    ("*", "Select at least 3 vertices"): "請至少選 3 個點",
    ("*", "Leave the root open, or leave the root ring unselected as an anchor"): "請讓根部保持開口，或根部那圈不要選，當作固定基準",
    ("*", "No clean cross-section loops found; only smoothed the path"): "找不到整齊的截面環，只做了走向平順",
    ("*", "Some cross-sections are not clean loops; they were only smoothed"): "部分截面不是整齊的環，那幾圈只做了平順",
}
translations = {"zh_HANT": _zh, "zh_TW": _zh}


# ---------------------------------------------------------------- register

classes = (MESH_OT_mbs_create, MESH_OT_mbs_finish, MESH_OT_mbs_cancel,
           MESH_OT_mbs_tidy, MESH_OT_mbs_smooth_twist, VIEW3D_PT_mbs)


def register():
    bpy.types.Scene.mbs_mode = bpy.props.EnumProperty(
        name="Mode",
        items=[
            ('STRAND', "Whole Strand", "Bend everything selected (a hair strand, a tube, a ribbon) along the curve"),
            ('ROW', "Single Row", "Snap one connected row of vertices onto the curve"),
        ],
        default='STRAND',
    )
    bpy.types.Scene.mbs_points = bpy.props.IntProperty(
        name="Control Points", default=3, min=2, max=12)
    bpy.types.Scene.mbs_follow_rings = bpy.props.BoolProperty(
        name="Follow Rings",
        description="Find the strand's centre line through its cross-section rings, "
                    "so strands that are already bent work too",
        default=False,
    )
    for c in classes:
        bpy.utils.register_class(c)
    if mbs_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(mbs_handler)
    try:
        bpy.app.translations.register(__name__, translations)
    except ValueError:
        pass


def unregister():
    try:
        bpy.app.translations.unregister(__name__)
    except Exception:
        pass
    if mbs_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(mbs_handler)
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.mbs_follow_rings
    del bpy.types.Scene.mbs_points
    del bpy.types.Scene.mbs_mode


if __name__ == "__main__":
    register()
