"""Zemin çalışması (2026-10-12): aynı sahne, oyunun kamerası, üç farklı zemin yüzeyi.

Yalnızca zemin yüzeyi değişir; makine, bant, insan, derzler ve sarı yol çizgileri her
varyantta aynıdır. Dokular Poly Haven (CC0), output/zemin_calismasi_20261012/tex altında.
Blender MCP execute_code ile ya da `blender -b -P` ile çalışır; render() üç PNG yazar.
"""
import math
import os

import bpy

ROOT = "C:/Users/tvural.REPKON/Desktop/ProjelerY"
OUT = ROOT + "/blender/output/zemin_calismasi_20261012"
TEX = OUT + "/tex"
GAME = ROOT + "/prosedürel/assets/models"

# Tur 2. dict: doku, gerçek boyu (m), düz renk + karışım oranı (0 = saf doku), ton aralığı
# (büyük ölçekli kir), pürüzlülük çarpanı, normal gücü, leke (yağ/lastik) gücü.
VARIANTS = [
    dict(name="1_acik_gri_epoksi", asset="painted_concrete_02", size=4.0,
         flat=(0.50, 0.53, 0.55), mix=0.72, tone=(0.92, 1.03), rough=0.32, normal=0.35, stain=0.25),
    dict(name="2_eskimis_beton", asset="concrete_floor_worn_001", size=3.0,
         flat=(0.42, 0.42, 0.41), mix=0.15, tone=(0.70, 1.12), rough=1.0, normal=1.4, stain=0.75,
         tile=dict(period=4, dark=0.80, light=1.10, joint=0.012, joint_tone=0.55,
                   block_joint=0.035, block_tone=0.25)),
    dict(name="3_yesil_epoksi", asset="painted_concrete", size=2.0,
         flat=(0.07, 0.17, 0.11), mix=0.85, tone=(0.90, 1.05), rough=0.42, normal=0.3, stain=0.3),
]
FLOOR_W, FLOOR_D = 90.0, 60.0
JOINT = 2.0


def clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.lights, bpy.data.cameras):
        for item in list(coll):
            if item.users == 0:
                coll.remove(item)


def flat_mat(name, rgb, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def tile_tone(n, l, tc, col, t):
    """1 m karolar; her karonun koyuluğu rastgele ama desen `period` karoda bir tekrar eder
    (yakında rastgele 1×1, uzakta period×period büyük karo gibi okunur). İnce derz de buradan."""
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Object"], sep.inputs["Vector"])
    cells = []
    for axis in ("X", "Y"):
        fl = n.new("ShaderNodeMath")
        fl.operation = "FLOOR"
        l.new(sep.outputs[axis], fl.inputs[0])
        md = n.new("ShaderNodeMath")
        md.operation = "FLOORED_MODULO"
        md.inputs[1].default_value = t["period"]
        l.new(fl.outputs[0], md.inputs[0])
        cells.append(md.outputs[0])
    vec = n.new("ShaderNodeCombineXYZ")
    l.new(cells[0], vec.inputs["X"])
    l.new(cells[1], vec.inputs["Y"])
    vec.inputs["Z"].default_value = t.get("seed", 7.0)
    wn = n.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    l.new(vec.outputs["Vector"], wn.inputs["Vector"])
    rng = n.new("ShaderNodeMapRange")
    rng.inputs["To Min"].default_value = t["dark"]
    rng.inputs["To Max"].default_value = t["light"]
    l.new(wn.outputs["Value"], rng.inputs["Value"])
    def joint(period, width, tone):
        # PINGPONG(x, period/2) = en yakın derz çizgisine uzaklık; `width` içinde `tone` kadar koyu.
        dist = []
        for axis in ("X", "Y"):
            fr = n.new("ShaderNodeMath")
            fr.operation = "PINGPONG"
            fr.inputs[1].default_value = period * 0.5
            l.new(sep.outputs[axis], fr.inputs[0])
            dist.append(fr.outputs[0])
        mn = n.new("ShaderNodeMath")
        mn.operation = "MINIMUM"
        l.new(dist[0], mn.inputs[0])
        l.new(dist[1], mn.inputs[1])
        jt = n.new("ShaderNodeMapRange")
        jt.inputs["From Min"].default_value = width * 0.5
        jt.inputs["From Max"].default_value = width * 0.5 + 0.004
        jt.inputs["To Min"].default_value = tone
        jt.inputs["To Max"].default_value = 1.0
        l.new(mn.outputs[0], jt.inputs["Value"])
        return jt.outputs["Result"]

    f = n.new("ShaderNodeMath")
    f.operation = "MULTIPLY"
    l.new(rng.outputs["Result"], f.inputs[0])
    l.new(joint(1.0, t["joint"], t["joint_tone"]), f.inputs[1])
    if t.get("block_joint"):
        f2 = n.new("ShaderNodeMath")
        f2.operation = "MULTIPLY"
        l.new(f.outputs[0], f2.inputs[0])
        l.new(joint(t["period"], t["block_joint"], t["block_tone"]), f2.inputs[1])
        f = f2
    cc = n.new("ShaderNodeCombineColor")
    for ch in ("Red", "Green", "Blue"):
        l.new(f.outputs[0], cc.inputs[ch])
    x = n.new("ShaderNodeMix")
    x.data_type = "RGBA"
    x.blend_type = "MULTIPLY"
    x.inputs["Factor"].default_value = 1.0
    l.new(col, x.inputs["A"])
    l.new(cc.outputs["Color"], x.inputs["B"])
    return x.outputs["Result"]


def floor_mat(v):
    m = bpy.data.materials.new("Floor_" + v["name"])
    m.use_nodes = True
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / v["size"], 1 / v["size"], 1)
    l.new(tc.outputs["Object"], mp.inputs["Vector"])

    def img(kind, non_color):
        t = n.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(f"{TEX}/{v['asset']}_{kind}_2k.jpg", check_existing=True)
        if non_color:
            t.image.colorspace_settings.name = "Non-Color"
        l.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t

    def mix(fac, a, b_, mode="MIX"):
        x = n.new("ShaderNodeMix")
        x.data_type = "RGBA"
        x.blend_type = mode
        if isinstance(fac, float):
            x.inputs["Factor"].default_value = fac
        else:
            l.new(fac, x.inputs["Factor"])
        for sock, val in ((x.inputs["A"], a), (x.inputs["B"], b_)):
            if isinstance(val, tuple):
                sock.default_value = (*val, 1)
            else:
                l.new(val, sock)
        return x.outputs["Result"]

    def noise(scale, detail, lo, hi, lo_out, hi_out):
        t = n.new("ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = scale
        t.inputs["Detail"].default_value = detail
        l.new(tc.outputs["Object"], t.inputs["Vector"])
        r = n.new("ShaderNodeMapRange")
        r.inputs["From Min"].default_value = lo
        r.inputs["From Max"].default_value = hi
        r.inputs["To Min"].default_value = lo_out
        r.inputs["To Max"].default_value = hi_out
        l.new(t.outputs["Fac"], r.inputs["Value"])
        return r.outputs["Result"]

    diff, rough, nor = img("diff", False), img("rough", True), img("nor_gl", True)
    base = mix(v["mix"], diff.outputs["Color"], v["flat"])
    # Büyük ölçekli ton farkı: tekrar eden desen kırılsın, zemin "kullanılmış" görünsün.
    tone = noise(0.08, 4, 0.3, 0.7, *v["tone"])
    toned = mix(1.0, base, (1, 1, 1), "MULTIPLY")
    comb = n.new("ShaderNodeCombineColor")
    for ch in ("Red", "Green", "Blue"):
        l.new(tone, comb.inputs[ch])
    l.new(comb.outputs["Color"], toned.node.inputs["B"])
    # Lekeler: yağ ve lastik izi gibi koyu, daha parlak bölgeler.
    stain = noise(0.35, 6, 0.58, 0.72, 0.0, v["stain"])
    col = mix(stain, toned, (0.08, 0.08, 0.075))
    if v.get("tile"):
        col = tile_tone(n, l, tc, col, v["tile"])
    l.new(col, b.inputs["Base Color"])
    rm = n.new("ShaderNodeMath")
    rm.operation = "MULTIPLY"
    rm.inputs[1].default_value = v["rough"]
    l.new(rough.outputs["Color"], rm.inputs[0])
    rs = n.new("ShaderNodeMath")
    rs.operation = "SUBTRACT"
    l.new(rm.outputs["Value"], rs.inputs[0])
    sm = n.new("ShaderNodeMath")
    sm.operation = "MULTIPLY"
    sm.inputs[1].default_value = 0.4
    l.new(stain, sm.inputs[0])
    l.new(sm.outputs["Value"], rs.inputs[1])
    rs.use_clamp = True
    l.new(rs.outputs["Value"], b.inputs["Roughness"])
    nm = n.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = v["normal"]
    l.new(nor.outputs["Color"], nm.inputs["Color"])
    l.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def strip(name, x, y, w, d, mat, z=0.002):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (w, d, 1)
    ob.data.materials.append(mat)
    return ob


def box(name, x, y, z, sx, sy, sz, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (sx, sy, sz)
    ob.data.materials.append(mat)
    return ob


def person(x, y):
    body = flat_mat("Person_body", (0.18, 0.24, 0.36), 0.8)
    skin = flat_mat("Person_skin", (0.62, 0.45, 0.35), 0.7)
    helmet = flat_mat("Person_helmet", (0.85, 0.65, 0.05), 0.5)
    for i, dx in enumerate((-0.1, 0.1)):
        box(f"Leg{i}", x + dx, y, 0.42, 0.14, 0.18, 0.84, body)
    box("Torso", x, y, 1.15, 0.42, 0.24, 0.62, body)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(x, y, 1.6))
    bpy.context.active_object.data.materials.append(skin)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.125, location=(x, y, 1.67))
    h = bpy.context.active_object
    h.scale.z = 0.6
    h.data.materials.append(helmet)


def import_glb(path, loc, rot_z=0.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    # GLB'lerde tek kök yok: her kök nesneyi kaydır, yerleşimi bozma.
    for r in roots:
        r.location = (r.location.x + loc[0], r.location.y + loc[1], r.location.z + loc[2])
    return new


def build():
    clear()
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.scale = (FLOOR_W, FLOOR_D, 1)
    bpy.ops.object.transform_apply(scale=True)

    joint = flat_mat("Joint", (0.02, 0.02, 0.02), 0.95)
    k = -1  # derzler artık zemin malzemesinde (tile_tone); geometri derzi yok
    for i in range(-k, k + 1):
        strip(f"JointX{i}", i * JOINT, 0, 0.03, FLOOR_D, joint, 0.001)
    for i in range(-k, k + 1):
        strip(f"JointY{i}", 0, i * JOINT, FLOOR_W, 0.03, joint, 0.001)

    paint = flat_mat("Paint_yellow", (0.85, 0.62, 0.02), 0.55)
    for x in (-6.0, 6.0):
        strip(f"Aisle{x}", x, 0, 0.1, FLOOR_D, paint, 0.003)
    strip("AisleTop", 0, 4.0, 12.0, 0.1, paint, 0.003)
    strip("AisleBot", 0, -4.0, 12.0, 0.1, paint, 0.003)

    import_glb(GAME + "/jm20_xl/jm20_xl_realistic.glb", (0.0, 0.0, 0.0))
    for i in range(4):
        for side in (-1, 1):
            import_glb(GAME + "/conveyors/conveyor_straight.glb", (side * (1.27 + i * 1.04), 0.0, 0.0))
    pallet = flat_mat("Pallet", (0.55, 0.42, 0.26), 0.85)
    crate = flat_mat("Crate", (0.42, 0.45, 0.48), 0.7)
    for j, (px, py) in enumerate(((-2.5, 2.2), (-1.2, 2.2), (2.5, -2.3))):
        box(f"Pallet{j}", px, py, 0.07, 1.2, 0.8, 0.14, pallet)
        box(f"Crate{j}", px, py, 0.14 + 0.3 * (j + 1) / 2, 1.1, 0.7, 0.3 * (j + 1), crate)
    person(1.6, 1.4)
    person(-3.4, -1.3)

    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun_data.energy = 2.8
    sun_data.angle = math.radians(6)
    sun = bpy.data.objects.new("Sun", sun_data)
    sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(42), 0, math.radians(-135 + 180))

    # Tavan lambaları (6 m arayla, 7 m yükseklikte): altı daha parlak, yansıma verir.
    for ix in range(-4, 5):
        for iy in range(-3, 4):
            ld = bpy.data.lights.new(f"Lamp{ix}_{iy}", "AREA")
            ld.shape = "RECTANGLE"
            ld.size, ld.size_y = 1.6, 0.4
            ld.energy = 70
            lo = bpy.data.objects.new(ld.name, ld)
            lo.location = (ix * 6.0 + 3.0, iy * 6.0 + 3.0, 7.0)
            sc.collection.objects.link(lo)

    world = sc.world or bpy.data.worlds.new("World")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.75, 0.78, 0.82, 1)
    bg.inputs["Strength"].default_value = 0.35

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 28.4  # oyunda camera.size 16 (dikey) → 16:9 yatay
    cam = bpy.data.objects.new("Cam", cam_data)
    sc.collection.objects.link(cam)
    cam.location = (-9.0, -14.0, 15.0)  # Godot CAMERA_OFFSET (-9, 15, 14) → Blender
    look = cam.constraints.new("TRACK_TO")
    target = bpy.data.objects.new("CamTarget", None)
    sc.collection.objects.link(target)
    look.target = target
    look.track_axis = "TRACK_NEGATIVE_Z"
    look.up_axis = "UP_Y"
    sc.camera = cam

    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast"
    sc.eevee.taa_render_samples = 48
    sc.eevee.use_raytracing = True
    sc.eevee.ray_tracing_options.resolution_scale = "1"
    return floor


def set_variant(floor, v):
    floor.data.materials.clear()
    floor.data.materials.append(floor_mat(v))


def render():
    floor = build()
    os.makedirs(OUT, exist_ok=True)
    for v in VARIANTS:
        set_variant(floor, v)
        bpy.context.scene.render.filepath = f"{OUT}/{v['name']}.png"
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    render()
