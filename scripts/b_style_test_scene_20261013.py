"""B tarzı deneme sahnesi (2026-10-13): "Modern stylized industrial" fabrika köşesi, 15×15 m.

Amaç: ChatGPT konseptindeki B görünümünü (temiz, ölçülü mavi, gerçek ekipmana benzeyen sade
formlar, yoğun çevre) kodla kurabiliyor muyuz, görmek. Oyunun parçası değil, provadır.
Zemin: bizim eskimiş beton (floor_study_20261012.py, 1 m karo, 4×4 tekrar eden ton).
İçerik: SMT makinesi, iki PC montaj istasyonu, L biçimli makaralı bant, mavi raflar, elektrik
panoları, tel çitli palet alanı, sarı zemin çizgileri, duvar ve lambalar.
Blender MCP execute_blender_code ile ya da `blender -b -P` ile çalışır.
"""
import math
import random

import bmesh
import bpy

ROOT = "C:/Users/tvural.REPKON/Desktop/ProjelerY"
OUT = ROOT + "/blender/output/b_tarzi_deneme_20261013"
FLOOR_SCRIPT = ROOT + "/blender/scripts/floor_study_20261012.py"
HALF = 7.5  # sahne 15×15 m, merkez (0, 0)
BELT_Z = 0.72

random.seed(4)


# --- Renkler ve malzemeler -------------------------------------------------------------

def srgb(hex_str):
    h = hex_str.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


_MATS = {}


def mat(name, hex_str, rough=0.55, metal=0.0, emit=0.0, alpha=1.0):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    col = srgb(hex_str)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
    _MATS[name] = m
    return m


def palette():
    return dict(
        white=mat("B_beyaz", "#E6EAEA", 0.45),
        light=mat("B_acik_gri", "#C5CBCE", 0.5),
        mid=mat("B_orta_gri", "#858D93", 0.5),
        dark=mat("B_antrasit", "#2C3238", 0.55),
        blue=mat("B_mavi", "#2F6DB5", 0.45),
        blue_dark=mat("B_koyu_mavi", "#1F4E86", 0.5),
        yellow=mat("B_sari", "#E3B11F", 0.5),
        orange=mat("B_turuncu", "#E2702A", 0.5),
        green=mat("B_yesil", "#3E9A55", 0.5),
        red=mat("B_kirmizi", "#C8322B", 0.45),
        card=mat("B_karton", "#B88954", 0.8),
        card_dark=mat("B_karton_koyu", "#9C7244", 0.8),
        wood=mat("B_ahsap", "#A47B4C", 0.85),
        rubber=mat("B_kaucuk", "#1D2125", 0.85),
        steel=mat("B_celik", "#B9BFC3", 0.35, 0.8),
        glass=mat("B_koyu_cam", "#1C2A33", 0.08),
        screen=mat("B_ekran", "#5FB3E0", 0.3, 0.0, 1.6),
        lamp=mat("B_lamba", "#FFF6E8", 0.3, 0.0, 6.0),
        lamp_red=mat("B_isik_kirmizi", "#E0392F", 0.3, 0.0, 2.5),
        lamp_yel=mat("B_isik_sari", "#F2B521", 0.3, 0.0, 1.2),
        lamp_grn=mat("B_isik_yesil", "#39C45A", 0.3, 0.0, 2.5),
        wall=mat("B_duvar", "#C9CED1", 0.7),
        wall_low=mat("B_duvar_alt", "#7E878D", 0.7),
        window=mat("B_pencere", "#9DB8C8", 0.1, 0.0, 0.4),
        mesh=mat("B_tel", "#3A4046", 0.5, 0.6),
        hatch_black=mat("B_tarama_siyah", "#22262A", 0.6),
    )


# --- Geometri yardımcıları -------------------------------------------------------------

COLL = None


def link(ob):
    COLL.objects.link(ob)
    return ob


_MESHES = {}


def box_mesh(sx, sy, sz, bevel):
    key = ("box", round(sx, 4), round(sy, 4), round(sz, 4), bevel)
    if key in _MESHES:
        return _MESHES[key]
    me = bpy.data.meshes.new("box")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    if bevel > 0:
        b = min(bevel, sx * 0.3, sy * 0.3, sz * 0.3)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, segments=2, affect="EDGES",
                        profile=0.5, clamp_overlap=True)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    _MESHES[key] = me
    return me


def box(name, x, y, z, sx, sy, sz, m, bevel=0.012, rz=0.0):
    """Kutu; (x, y) taban merkezi, z taban yüksekliği."""
    me = box_mesh(sx, sy, sz, bevel)
    ob = link(bpy.data.objects.new(name, me))
    ob.location = (x, y, z + sz / 2)
    ob.rotation_euler.z = rz
    if not me.materials:
        me.materials.append(m)
    elif me.materials[0] != m:
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = m
    return ob


def cyl(name, x, y, z, r, h, m, axis="Z", verts=16):
    key = ("cyl", round(r, 4), round(h, 4), verts)
    me = _MESHES.get(key)
    if me is None:
        me = bpy.data.meshes.new("cyl")
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=h)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = len(p.vertices) == 4
        _MESHES[key] = me
    ob = link(bpy.data.objects.new(name, me))
    ob.location = (x, y, z)
    if axis == "X":
        ob.rotation_euler.y = math.pi / 2
    elif axis == "Y":
        ob.rotation_euler.x = math.pi / 2
    if not me.materials:
        me.materials.append(m)
    elif me.materials[0] != m:
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = m
    return ob


def strip(name, x, y, sx, sy, m, z=0.003):
    return box(name, x, y, z - 0.002, sx, sy, 0.002, m, bevel=0)


# --- Ekipman ---------------------------------------------------------------------------

def light_tower(x, y, z, P):
    cyl("Kule_direk", x, y, z + 0.15, 0.012, 0.3, P["mid"])
    for i, k in enumerate(("lamp_grn", "lamp_yel", "lamp_red")):
        cyl("Kule_" + k, x, y, z + 0.32 + i * 0.065, 0.032, 0.06, P[k])
    cyl("Kule_kapak", x, y, z + 0.52, 0.03, 0.012, P["dark"])


def monitor(x, y, z, P, rz=0.0, w=0.42, h=0.28):
    cyl("Monitor_kol", x, y, z + 0.18, 0.015, 0.36, P["mid"])
    s = box("Monitor", x, y, z + 0.34, w, 0.04, h, P["dark"], 0.008, rz)
    e = box("Monitor_ekran", x, y, z + 0.36, w - 0.05, 0.005, h - 0.05, P["screen"], 0, rz)
    off = 0.024
    e.location.x += -math.sin(rz) * off
    e.location.y += -math.cos(rz) * off
    return s


def conveyor(x0, y0, x1, y1, P, items=True):
    """Makaralı bant: (x0, y0)→(x1, y1) eksene paralel; taşıma yüzü BELT_Z."""
    along_x = abs(x1 - x0) > abs(y1 - y0)
    length = abs(x1 - x0) if along_x else abs(y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w = 0.72
    for side in (-1, 1):
        ox, oy = (0, side * w / 2) if along_x else (side * w / 2, 0)
        sx, sy = (length, 0.05) if along_x else (0.05, length)
        box("Bant_ray", cx + ox, cy + oy, BELT_Z - 0.1, sx, sy, 0.13, P["dark"], 0.008)
    n = int(length / 0.11)
    for i in range(n):
        t = -length / 2 + (i + 0.5) * length / n
        rx, ry = (cx + t, cy) if along_x else (cx, cy + t)
        cyl("Makara", rx, ry, BELT_Z - 0.02, 0.028, w - 0.06, P["steel"],
            axis="Y" if along_x else "X", verts=10)
    legs = max(2, int(length / 1.5) + 1)
    for i in range(legs):
        t = -length / 2 + 0.1 + i * (length - 0.2) / (legs - 1)
        for side in (-1, 1):
            lx, ly = (cx + t, cy + side * (w / 2 - 0.03)) if along_x else (cx + side * (w / 2 - 0.03), cy + t)
            box("Bant_ayak", lx, ly, 0, 0.05, 0.05, BELT_Z - 0.1, P["mid"], 0.006)
            box("Bant_ayak_taban", lx, ly, 0, 0.12, 0.12, 0.015, P["dark"], 0.004)
        bx, by = (cx + t, cy) if along_x else (cx, cy + t)
        sx, sy = (0.04, w - 0.06) if along_x else (w - 0.06, 0.04)
        box("Bant_capraz", bx, by, 0.22, sx, sy, 0.04, P["mid"], 0.005)
    if items:
        k = int(length / 1.1)
        for i in range(k):
            t = -length / 2 + 0.6 + i * 1.1
            if t > length / 2 - 0.3:
                break
            ix, iy = (cx + t, cy) if along_x else (cx, cy + t)
            box("Urun_kasa", ix, iy, BELT_Z, 0.42, 0.42, 0.06, P["dark"], 0.006)
            box("Urun_anakart", ix, iy, BELT_Z + 0.06, 0.3, 0.3, 0.012, P["green"], 0.003)


def smt_machine(x, y, P):
    """SMT dizgi makinesi, bant x ekseninde içinden geçer. 2.6 × 1.5 × 1.55 m."""
    L, D = 2.6, 1.5
    box("SMT_kaide", x, y, 0, L - 0.08, D - 0.08, 0.14, P["dark"], 0.01)
    box("SMT_govde", x, y, 0.14, L, D, 0.9, P["white"], 0.03)
    box("SMT_mavi_bant", x, y - D / 2 - 0.002, 0.62, L - 0.1, 0.01, 0.1, P["blue"], 0.003)
    box("SMT_kapak", x, y, 1.04, L - 0.06, D - 0.12, 0.42, P["light"], 0.04)
    box("SMT_pencere", x - 0.25, y - (D - 0.12) / 2 - 0.004, 1.1, 1.5, 0.01, 0.3, P["glass"], 0.004)
    box("SMT_ust", x, y, 1.46, L - 0.3, D - 0.4, 0.08, P["white"], 0.02)
    for side in (-1, 1):
        box("SMT_agiz", x + side * (L / 2 + 0.001), y, BELT_Z - 0.06, 0.01, 0.8, 0.16, P["rubber"], 0)
    # Besleyici arabası: ön yüzde renkli makaralar
    box("SMT_besleyici", x + 0.35, y - D / 2 - 0.2, 0.14, 1.3, 0.4, 0.55, P["mid"], 0.015)
    reel = [P["blue"], P["dark"], P["yellow"], P["dark"], P["white"], P["blue"], P["dark"],
            P["orange"], P["dark"], P["blue"]]
    for i, m in enumerate(reel):
        cyl("SMT_makara", x - 0.2 + i * 0.12, y - D / 2 - 0.26, 0.85, 0.16, 0.035, m, axis="X", verts=20)
    light_tower(x + L / 2 - 0.2, y + D / 2 - 0.25, 1.54, P)
    monitor(x - L / 2 + 0.25, y - D / 2 - 0.05, 0.9, P)
    box("SMT_panel_seridi", x + 0.95, y - D / 2 - 0.003, 0.25, 0.4, 0.01, 0.3, P["light"], 0.003)


def assembly_station(x, y, P, rz=0.0, case_color="dark"):
    """PC montaj tezgâhı + test dolabı; tezgâh banda dik, operatör tarafı kameraya dönük."""
    def at(dx, dy):
        c, s = math.cos(rz), math.sin(rz)
        return x + dx * c - dy * s, y + dx * s + dy * c

    for dx in (-0.75, 0.75):
        for dy in (-0.35, 0.35):
            px, py = at(dx, dy)
            box("Tezgah_ayak", px, py, 0, 0.05, 0.05, 0.86, P["blue"], 0.006, rz)
    px, py = at(0, 0)
    box("Tezgah_ust", px, py, 0.86, 1.62, 0.8, 0.05, P["light"], 0.01, rz)
    box("Tezgah_alt_raf", px, py, 0.18, 1.5, 0.7, 0.03, P["mid"], 0.006, rz)
    px, py = at(-0.45, 0)
    box("Tezgah_cekmece", px, py, 0.21, 0.5, 0.6, 0.6, P["blue_dark"], 0.012, rz)
    for dx in (-0.75, 0.75):
        px, py = at(dx, 0.35)
        box("Tezgah_dikme", px, py, 0.91, 0.04, 0.04, 1.0, P["blue"], 0.006, rz)
    px, py = at(0, 0.3)
    box("Tezgah_ust_raf", px, py, 1.55, 1.55, 0.3, 0.03, P["mid"], 0.006, rz)
    box("Tezgah_lamba", px, py, 1.88, 1.5, 0.12, 0.04, P["lamp"], 0.005, rz)
    for i in range(6):
        px, py = at(-0.6 + i * 0.24, 0.3)
        m = (P["blue"], P["yellow"], P["blue"], P["orange"], P["blue"], P["yellow"])[i]
        box("Parca_kutusu", px, py, 1.58, 0.18, 0.22, 0.12, m, 0.01, rz)
    px, py = at(0.15, -0.05)
    box("Montaj_kasa", px, py, 0.91, 0.24, 0.48, 0.46, P[case_color], 0.012, rz)
    px, py = at(0.6, 0.0)
    monitor(px, py, 0.91, P, rz)
    # Test dolabı
    px, py = at(1.25, 0.05)
    box("Test_dolap", px, py, 0, 0.72, 0.7, 1.45, P["white"], 0.025, rz)
    qx, qy = at(1.25, -0.3)
    box("Test_dolap_mavi", qx, qy, 0.1, 0.62, 0.02, 0.55, P["blue"], 0.006, rz)
    qx, qy = at(1.25, -0.31)
    box("Test_dolap_cam", qx, qy, 0.85, 0.5, 0.02, 0.35, P["glass"], 0.004, rz)
    light_tower(px + 0.2, py + 0.2, 1.45, P)
    # Operatör (statik ölçek referansı)
    ox, oy = at(0.0, -0.75)
    operator(ox, oy, P)


def operator(x, y, P):
    for dx in (-0.09, 0.09):
        box("Op_bacak", x + dx, y, 0, 0.13, 0.17, 0.84, P["blue_dark"], 0.03)
    box("Op_govde", x, y, 0.84, 0.42, 0.24, 0.6, P["blue"], 0.06)
    box("Op_yelek", x, y - 0.005, 1.0, 0.43, 0.245, 0.3, P["yellow"], 0.04)
    for dx in (-0.25, 0.25):
        box("Op_kol", x + dx, y, 0.8, 0.1, 0.12, 0.58, P["blue"], 0.03)
    cyl("Op_bas", x, y, 1.58, 0.1, 0.2, mat("B_ten", "#C79A7A", 0.7))
    cyl("Op_kask", x, y, 1.69, 0.12, 0.07, P["white"])


def rack(x, y, P, w=2.2, d=0.6, h=2.2, rz=0.0):
    """Mavi palet rafı; raflarda koli ve plastik kasalar."""
    c, s = math.cos(rz), math.sin(rz)

    def at(dx, dy):
        return x + dx * c - dy * s, y + dx * s + dy * c

    for dx in (-w / 2, w / 2):
        for dy in (-d / 2, d / 2):
            px, py = at(dx, dy)
            box("Raf_dikme", px, py, 0, 0.07, 0.07, h, P["blue"], 0.006, rz)
    for z in (0.12, 0.85, 1.55):
        for dy in (-d / 2, d / 2):
            px, py = at(0, dy)
            box("Raf_kiris", px, py, z, w, 0.06, 0.09, P["orange"], 0.006, rz)
        px, py = at(0, 0)
        box("Raf_tabla", px, py, z + 0.09, w, d, 0.02, P["mid"], 0.003, rz)
        cx = -w / 2 + 0.1
        while cx < w / 2 - 0.25:
            kind = random.random()
            if kind < 0.55:
                bw, bd, bh = random.choice(((0.4, 0.4, 0.35), (0.5, 0.45, 0.4), (0.35, 0.5, 0.3)))
                m = P["card"] if random.random() < 0.7 else P["card_dark"]
            elif kind < 0.85:
                bw, bd, bh = 0.4, 0.5, 0.25
                m = random.choice((P["blue"], P["green"], P["blue"]))
            else:
                cx += 0.25
                continue
            if cx + bw > w / 2 - 0.05:
                break
            px, py = at(cx + bw / 2, 0)
            box("Raf_yuk", px, py, z + 0.11, bw, min(bd, d - 0.06), bh, m, 0.012, rz)
            cx += bw + 0.06


def cabinet(x, y, P, w=0.8, h=2.0, window=False):
    """Elektrik panosu, sağ duvara (+x) yaslı, kapağı -x'e bakar."""
    box("Pano", x, y, 0.08, 0.5, w, h, P["light"], 0.02)
    box("Pano_kaide", x, y, 0, 0.46, w - 0.04, 0.08, P["dark"], 0.006)
    box("Pano_kapak_ayrim", x - 0.251, y, 0.12, 0.004, 0.006, h - 0.1, P["dark"], 0)
    for dy in (-w / 4, w / 4):
        box("Pano_kol", x - 0.26, y + dy * 0.6, 1.0, 0.02, 0.03, 0.14, P["dark"], 0.004)
    if window:
        box("Pano_pencere", x - 0.252, y - w / 4, 1.2, 0.006, w * 0.35, 0.5, P["glass"], 0.003)
    box("Pano_etiket", x - 0.252, y + w / 4, 1.6, 0.004, 0.18, 0.1, P["yellow"], 0)


def pallet(x, y, P, load=1.0, rz=0.0):
    box("Palet", x, y, 0, 1.2, 0.8, 0.14, P["wood"], 0.008, rz)
    if load <= 0:
        return
    layers = max(1, int(round(3 * load)))
    for k in range(layers):
        for i in (-0.3, 0.3):
            for j in (-0.2, 0.2):
                if k == layers - 1 and random.random() < 0.3:
                    continue
                m = P["card"] if (i + j + k) % 2 else P["card_dark"]
                c, s = math.cos(rz), math.sin(rz)
                bx, by = x + i * c - j * s, y + i * s + j * c
                box("Koli", bx, by, 0.14 + k * 0.36, 0.56, 0.38, 0.34, m, 0.012, rz)


def fence(x0, y0, x1, y1, P, h=1.9):
    """Sarı direkli tel çit, eksene paralel tek kenar."""
    along_x = abs(x1 - x0) > abs(y1 - y0)
    length = abs(x1 - x0) if along_x else abs(y1 - y0)
    n = max(1, round(length / 1.5))
    step = length / n
    for i in range(n + 1):
        t = i * step
        px, py = (min(x0, x1) + t, y0) if along_x else (x0, min(y0, y1) + t)
        box("Cit_direk", px, py, 0, 0.06, 0.06, h, P["yellow"], 0.006)
        box("Cit_taban", px, py, 0, 0.14, 0.14, 0.012, P["yellow"], 0.003)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sx, sy = (length, 0.035) if along_x else (0.035, length)
    box("Cit_ust", cx, cy, h - 0.05, sx, sy, 0.04, P["yellow"], 0.004)
    box("Cit_alt", cx, cy, 0.12, sx, sy, 0.04, P["yellow"], 0.004)
    # Tel örgü: ince ızgara, gerçek tel geometrisi.
    me = bpy.data.meshes.new("Cit_tel")
    bm = bmesh.new()
    cells_u = int(length / 0.08)
    cells_v = int((h - 0.25) / 0.08)
    bmesh.ops.create_grid(bm, x_segments=cells_u, y_segments=cells_v, size=0.5)
    for v in bm.verts:
        u, w_ = v.co.x + 0.5, v.co.y + 0.5
        if along_x:
            v.co = (min(x0, x1) + u * length - cx, 0, 0.16 + w_ * (h - 0.25))
        else:
            v.co = (0, min(y0, y1) + u * length - cy, 0.16 + w_ * (h - 0.25))
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new("Cit_tel", me))
    ob.location = (cx, cy, 0)
    me.materials.append(P["mesh"])
    wf = ob.modifiers.new("Tel", "WIREFRAME")
    wf.thickness = 0.008
    wf.use_replace = True


def hatch(x, y, sx, sy, P):
    """Sarı-siyah taralı alan: 45° şeritli resim dokusu (glTF ile Godot'a taşınabilsin diye)."""
    import os
    os.makedirs(OUT, exist_ok=True)
    ppm = 100
    w, h = int(sx * ppm), int(sy * ppm)
    img = bpy.data.images.new("Tarama_dokusu", w, h)
    # Bayt resmin pikselleri sRGB kodlu tutulur: doğrusal değil, ham hex değerleri yazılır.
    yel = tuple(int("E3B11F"[i:i + 2], 16) / 255 for i in (0, 2, 4))
    blk = tuple(int("22262A"[i:i + 2], 16) / 255 for i in (0, 2, 4))
    px = []
    for j in range(h):
        for i in range(w):
            c = yel if ((i + j) / ppm / 0.42) % 1.0 > 0.5 else blk
            px.extend((*c, 1.0))
    img.pixels = px
    img.filepath_raw = OUT + f"/tarama_{w}x{h}.png"  # boyut başına ayrı dosya
    img.file_format = "PNG"
    img.save()
    m = bpy.data.materials.new("B_tarama")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(k for k in nt.nodes if k.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.6
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    t.interpolation = "Closest"
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, 0.004))
    ob = bpy.context.active_object
    ob.name = "Tarama"
    ob.scale = (sx, sy, 1)
    bpy.ops.object.transform_apply(scale=True)
    ob.data.materials.append(m)


# --- Sahne -----------------------------------------------------------------------------

def walls(P):
    H = 3.6
    # arka duvar (+y) ve sağ duvar (+x)
    for name, x, y, sx, sy in (("Duvar_arka", 0, HALF + 0.1, 2 * HALF + 0.4, 0.2),
                               ("Duvar_sag", HALF + 0.1, 0, 0.2, 2 * HALF)):
        box(name, x, y, 0, sx, sy, H, P["wall"], 0)
        box(name + "_alt", x - (0.11 if sy > 1 else 0), y - (0.11 if sx > 1 else 0), 0,
            sx if sx > 1 else 0.02, sy if sy > 1 else 0.02, 1.1, P["wall_low"], 0)
    # panel derzleri, pencere bandı, lambalar
    for i in range(13):
        t = -HALF + 0.6 + i * 1.2
        box("Duvar_derz", t, HALF - 0.005, 1.1, 0.012, 0.01, H - 1.1, P["mid"], 0)
        box("Duvar_derz", HALF - 0.005, t, 1.1, 0.01, 0.012, H - 1.1, P["mid"], 0)
    box("Pencere_bandi", 0, HALF - 0.008, 2.75, 2 * HALF - 1, 0.01, 0.6, P["window"], 0)
    box("Pencere_bandi", HALF - 0.008, 0, 2.75, 0.01, 2 * HALF - 1, 0.6, P["window"], 0)
    for i in range(5):
        t = -HALF + 1.5 + i * 3.0
        box("Duvar_lamba", t, HALF - 0.04, 2.45, 1.2, 0.06, 0.06, P["lamp"], 0.01)
        box("Duvar_lamba", HALF - 0.04, t, 2.45, 0.06, 1.2, 0.06, P["lamp"], 0.01)
    # kablo tavası sağ duvarda
    box("Kablo_tavasi", HALF - 0.25, 1.5, 2.25, 0.3, 9.0, 0.08, P["mid"], 0.006)


def floor_lines(P):
    y_line = P["yellow"]
    # yaya yolu çizgileri hattı çevreler
    strip("Cizgi", -0.9, -2.35, 12.0, 0.08, y_line)
    strip("Cizgi", -0.9, 5.3, 12.0, 0.08, y_line)
    strip("Cizgi", -6.9, 1.5, 0.08, 7.7, y_line)
    strip("Cizgi", 5.1, 1.5, 0.08, 7.7, y_line)
    # palet alanı köşeleri ve panoların önü taralı
    hatch(6.35, 3.5, 1.3, 4.6, P)


def camera_and_light(sc):
    sun_data = bpy.data.lights.new("Gunes", "SUN")
    sun_data.energy = 2.8
    sun_data.angle = math.radians(8)
    sun = bpy.data.objects.new("Gunes", sun_data)
    sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(42), 0, math.radians(45))
    for ix in range(-1, 2):
        for iy in range(-1, 2):
            ld = bpy.data.lights.new("Tavan", "AREA")
            ld.shape = "RECTANGLE"
            ld.size, ld.size_y = 2.0, 0.4
            ld.energy = 120
            lo = bpy.data.objects.new("Tavan", ld)
            lo.location = (ix * 5.0, iy * 5.0, 6.0)
            sc.collection.objects.link(lo)
    world = sc.world or bpy.data.worlds.new("World")
    sc.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.75, 0.78, 0.82, 1)
    bg.inputs["Strength"].default_value = 0.4

    cam_data = bpy.data.cameras.new("Kamera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 21.0
    cam = bpy.data.objects.new("Kamera", cam_data)
    sc.collection.objects.link(cam)
    cam.location = (-9.0, -14.0, 15.0)  # oyunun CAMERA_OFFSET'i (Godot → Blender)
    target = bpy.data.objects.new("Kamera_hedef", None)
    sc.collection.objects.link(target)
    target.location = (0.3, 0.6, 0)
    # Yükseklik açısı 30° (kullanıcı 2026-10-13): yatay uzaklık sqrt(9²+14²) · tan 30°.
    cam.location = (target.location.x - 9.0, target.location.y - 14.0,
                    math.hypot(9.0, 14.0) * math.tan(math.radians(30)))
    tr = cam.constraints.new("TRACK_TO")
    tr.target = target
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    sc.camera = cam

    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        pass
    sc.view_settings.view_transform = "AgX"
    sc.eevee.taa_render_samples = 48
    sc.eevee.use_raytracing = True


def build():
    global COLL
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    _MATS.clear()
    _MESHES.clear()
    sc = bpy.context.scene
    COLL = sc.collection
    P = palette()

    ns = {"__name__": "floor"}
    exec(open(FLOOR_SCRIPT, encoding="utf-8").read(), ns)
    v = next(x for x in ns["VARIANTS"] if x["name"] == "2_eskimis_beton")
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    fl = bpy.context.active_object
    fl.name = "Zemin"
    fl.scale = (2 * HALF + 10, 2 * HALF + 10, 1)
    bpy.ops.object.transform_apply(scale=True)
    fl.data.materials.append(ns["floor_mat"](v))

    walls(P)
    floor_lines(P)

    # L biçimli hat: x boyunca y=-1, köşe x=4'te, sonra +y boyunca
    conveyor(-6.6, -1.0, -2.55, -1.0, P)
    smt_machine(-1.25, -1.0, P)
    conveyor(0.05, -1.0, 3.64, -1.0, P)
    box("Kose_modulu", 4.0, -1.0, BELT_Z - 0.12, 0.72, 0.72, 0.14, P["dark"], 0.01)
    box("Kose_ust", 4.0, -1.0, BELT_Z - 0.0, 0.66, 0.66, 0.02, P["steel"], 0.004)
    for dx in (-0.3, 0.3):
        for dy in (-0.3, 0.3):
            box("Kose_ayak", 4.0 + dx, -1.0 + dy, 0, 0.05, 0.05, BELT_Z - 0.1, P["mid"], 0.006)
    conveyor(4.0, -0.64, 4.0, 4.8, P)

    assembly_station(-4.6, -2.05, P, 0.0)  # bandın önünde (-y), kameraya dönük
    assembly_station(2.85, 2.0, P, -math.pi / 2, "white")  # dikey kolun solunda

    # raflar arka duvarda
    for i, rx in enumerate((-5.9, -3.5, -1.1)):
        rack(rx, HALF - 0.45, P)
    # panolar sağ duvarda
    for i, py in enumerate((1.6, 2.45, 3.3, 4.15, 5.0)):
        cabinet(HALF - 0.28, py, P, window=(i % 2 == 0))
    # hat yanında paletler
    pallet(-6.0, 1.0, P, 1.0)
    pallet(-4.5, 1.0, P, 0.6)
    pallet(1.5, 1.3, P, 0.3)
    # çitli palet alanı ön sağ köşe
    fence(1.2, -3.4, 7.3, -3.4, P)
    fence(1.2, -7.3, 1.2, -4.6, P)
    for i, (px, py) in enumerate(((2.4, -4.6), (3.9, -4.6), (5.4, -4.6), (2.4, -6.1), (3.9, -6.1), (5.4, -6.1))):
        pallet(px, py, P, (1.0, 0.7, 1.0, 0.4, 1.0, 0.0)[i])
    camera_and_light(sc)


def render(name="b_tarzi_deneme"):
    import os
    os.makedirs(OUT, exist_ok=True)
    bpy.context.scene.render.filepath = f"{OUT}/{name}.png"
    bpy.ops.render.render(write_still=True)


GAME_GLB = ROOT + "/prosedürel/assets/models/b_style_test/b_style_test_scene.glb"


def export_glb(path=GAME_GLB):
    """Zemin, kamera ve ışıklar hariç her şeyi glTF olarak oyuna yazar (zemin oyunun kendi shader'ı)."""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name != "Zemin":
            ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_apply=True,
                              export_lights=False, export_cameras=False)


if __name__ == "__main__":
    build()
    render()
