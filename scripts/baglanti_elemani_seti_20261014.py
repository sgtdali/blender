"""Bağlantı elemanı seti (2026-10-14): 01A boş kasa üretiminin dış ikmal girdisi.

Kural (kullanıcı): parçalar tek tek taşınır, bir stok karosunda (1 × 1 m) tek birim durur.
Gerçekçi değil, okunur: bağlantı elemanları büyütülmüş.

- Kap: önü alçak, arkası yüksek, öne eğimli antrasit parça kovası (0.78 × 0.62 m); önde beyaz
  etiket yuvası. Diğer setlerin kaplarından (kit tablası, köpüklü çanta, palet) ayrışır.
- İçi: tepeleme yığın; gümüş vidalar, altıgen somunlar, pullar, birkaç pirinç ayak. Yığının
  altında boşluk görünmesin diye gri "dolgu" tepe. Dağılım rastgele ama sabit tohumlu.

Ortak yardımcılar anakart_pcb_20261014.py'den alınır. Malzemeler düz renk (glTF'ye uygun).
Çıktı: output/baglanti_elemani_seti_20261014/baglanti_elemani_seti.blend
"""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Vector

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
H = {"__name__": "anakart_pcb_yardimci"}
exec(open(SCRIPTS + "/anakart_pcb_20261014.py", encoding="utf-8").read(), H)
mat, box, disc, tile_marks = H["mat"], H["box"], H["disc"], H["tile_marks"]

W, D = 0.78, 0.62
BACK_H, FRONT_H = 0.38, 0.17
WALL = 0.02
FLOOR = 0.03


def palette():
    P = H["palette"]()
    P.update(
        bin=mat("BE_kova", "#2C3238", 0.5),
        bin_lip=mat("BE_kova_kenar", "#3A4046", 0.5),
        label=mat("E_etiket", "#F2F4F2", 0.6),
        ink=mat("G_etiket_yazi", "#2C3238", 0.6),
        zinc=mat("BE_cinko", "#C9CED2", 0.3, 0.85),
        zinc_dark=mat("BE_cinko_koyu", "#8C9399", 0.4, 0.8),
        brass=mat("K_piring_ayak", "#C9A24A", 0.35, 0.85),
        fill=mat("BE_dolgu", "#5A6268", 0.7, 0.3),
        hole=mat("P_delik", "#1A1E1C", 0.7),
    )
    return P


def side_prism(name, x, pts_yz, thick, m, root):
    """(y, z) düzleminde çokgen, x yönünde thick kalınlıkta; x merkez."""
    bm = bmesh.new()
    vs = [bm.verts.new((x - thick / 2, y, z)) for y, z in pts_yz]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(thick, 0, 0), verts=[v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = H["link"](bpy.data.objects.new(name, me), root)
    me.materials.append(m)
    return ob


def hopper_bin(P, root):
    box("Kova_taban", 0, 0, 0, W, D, FLOOR, P["bin"], root, 0.006)
    box("Kova_arka", 0, D / 2 - WALL / 2, 0, W, WALL, BACK_H, P["bin"], root, 0.005)
    box("Kova_on", 0, -D / 2 + WALL / 2, 0, W, WALL, FRONT_H, P["bin"], root, 0.005)
    # yan duvarlar: arkada yüksek, önde alçak (eğimli üst kenar)
    pts = [(-D / 2, 0), (D / 2, 0), (D / 2, BACK_H), (-D / 2 + 0.12, FRONT_H + 0.04), (-D / 2, FRONT_H)]
    for s in (-1, 1):
        side_prism("Kova_yan", s * (W / 2 - WALL / 2), pts, WALL, P["bin"], root)
    # kenar dudakları (üst kenarlar biraz kalın, açık ton)
    box("Kova_on_dudak", 0, -D / 2 + 0.005, FRONT_H, W + 0.006, 0.03, 0.012, P["bin_lip"], root, 0.004)
    box("Kova_arka_dudak", 0, D / 2 - 0.01, BACK_H, W + 0.006, 0.03, 0.012, P["bin_lip"], root, 0.004)
    # etiket yuvası (ön yüz)
    box("Etiket_yuvasi", 0, -D / 2 - 0.004, 0.05, 0.24, 0.008, 0.08, P["bin_lip"], root, 0.003)
    box("Etiket", 0, -D / 2 - 0.009, 0.06, 0.2, 0.002, 0.06, P["label"], root)
    # etikette vida simgesi (yazı yerine): yatay gövde + baş
    box("Etiket_simge", 0.01, -D / 2 - 0.0105, 0.087, 0.07, 0.001, 0.008, P["ink"], root)
    box("Etiket_simge", -0.03, -D / 2 - 0.0105, 0.08, 0.012, 0.001, 0.022, P["ink"], root)


# --- Bağlantı elemanları ---------------------------------------------------------------------

def fastener_root(name, root, loc, rot):
    e = H["link"](bpy.data.objects.new(name, None), root)
    e.location = loc
    e.rotation_euler = rot
    return e


def screw(P, root, loc, rot, L=0.12, r=0.011):
    e = fastener_root("Vida", root, loc, rot)
    disc("Vida_govde", 0, 0, -L / 2, r, L - 0.012, P["zinc"], e, 12)
    disc("Vida_uc", 0, 0, -L / 2 - 0.012, r * 0.5, 0.012, P["zinc"], e, 10)
    disc("Vida_bas", 0, 0, L / 2 - 0.012, r * 2.3, 0.02, P["zinc"], e, 20)
    box("Vida_yiv", 0, 0, L / 2 + 0.007, r * 3, 0.006, 0.002, P["zinc_dark"], e)
    box("Vida_yiv", 0, 0, L / 2 + 0.007, 0.006, r * 3, 0.002, P["zinc_dark"], e)
    for k in range(4):  # diş halkaları
        disc("Vida_dis", 0, 0, -L / 2 + 0.01 + k * 0.022, r + 0.0015, 0.004, P["zinc_dark"], e, 12)
    return e


def nut(P, root, loc, rot, r=0.026, h=0.022, m=None):
    e = fastener_root("Somun", root, loc, rot)
    disc("Somun_govde", 0, 0, -h / 2, r, h, m or P["zinc"], e, 6)
    disc("Somun_delik", 0, 0, -h / 2 - 0.0005, r * 0.45, h + 0.001, P["hole"], e, 14)
    return e


def washer(P, root, loc, rot, r=0.03):
    e = fastener_root("Pul", root, loc, rot)
    disc("Pul_govde", 0, 0, -0.003, r, 0.006, P["zinc"], e, 24)
    disc("Pul_delik", 0, 0, -0.0035, r * 0.42, 0.007, P["hole"], e, 14)
    return e


def standoff(P, root, loc, rot):
    e = fastener_root("Pirinc_ayak", root, loc, rot)
    disc("Ayak_govde", 0, 0, -0.025, 0.014, 0.05, P["brass"], e, 6)
    disc("Ayak_vida", 0, 0, -0.045, 0.007, 0.02, P["brass"], e, 10)
    disc("Ayak_delik", 0, 0, 0.0245, 0.006, 0.001, P["hole"], e, 10)
    return e


def mound_height(x, y):
    """Yığın yüzeyi: kovanın ortasında tepe, kenarlara doğru alçalır (z, kova tabanından)."""
    nx, ny = x / (W / 2 - 0.05), (y - 0.04) / (D / 2 - 0.05)
    d = min(1.0, math.sqrt(nx * nx + ny * ny))
    return FLOOR + 0.13 + 0.09 * (1 - d * d)


def contents(P, root):
    # dolgu tepe: basık elipsoid, yığının altındaki boşluğu kapatır
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context="VERTS")
    me = bpy.data.meshes.new("Yigin_dolgu")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    f = H["link"](bpy.data.objects.new("Yigin_dolgu", me), root)
    f.scale = (W / 2 - WALL - 0.005, D / 2 - WALL - 0.01, 0.2)
    f.location = (0, 0.03, FLOOR + 0.02)
    me.materials.append(P["fill"])
    rnd = random.Random(7)
    kinds = ["screw"] * 34 + ["nut"] * 24 + ["washer"] * 18 + ["standoff"] * 8
    rnd.shuffle(kinds)
    placed = []
    for kind in kinds:
        for _ in range(40):   # çakışmayı azaltmak için birkaç deneme
            x = rnd.uniform(-W / 2 + 0.06, W / 2 - 0.06)
            y = rnd.uniform(-D / 2 + 0.07, D / 2 - 0.05)
            if all((x - px) ** 2 + (y - py) ** 2 > 0.045 ** 2 for px, py in placed):
                break
        placed.append((x, y))
        z = mound_height(x, y)
        tilt = Euler((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(0, math.pi)))
        if kind == "screw":
            lie = Euler((math.pi / 2 + rnd.uniform(-0.3, 0.3), 0, rnd.uniform(0, math.pi)))
            screw(P, root, (x, y, z + 0.012), lie)
        elif kind == "nut":
            nut(P, root, (x, y, z + 0.008), tilt)
        elif kind == "washer":
            washer(P, root, (x, y, z + 0.004), tilt)
        else:
            standoff(P, root, (x, y, z + 0.01), Euler((math.pi / 2, 0, rnd.uniform(0, math.pi))))


def baglanti_seti(P, x=0.0, y=0.0):
    root = H["link"](bpy.data.objects.new("Baglanti_elemani_seti", None))
    hopper_bin(P, root)
    contents(P, root)
    root.location = (x, y, 0)
    return root


def build(scene=None):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Baglanti_elemani_seti")
    scene.collection.children.link(c)
    H["COLL"] = c
    tile_marks(P, 0, 0)
    return baglanti_seti(P, 0, 0)


if __name__ == "__main__":
    build()
