"""01B anakart PCB üretiminin girdileri (2026-10-14): yalıtkan levha ve bakır folyo.

İkisi de dış ikmalden gelir, yerel üretilmez. Kural (kullanıcı, 14 Ekim 2026): parçalar tek tek
taşınır, bir stok karosunda (1 × 1 m) tek birim durur.

- Yalıtkan levha: FR-4 benzeri soluk bej levha, ahşap palet üstünde; köşe koruyucular,
  iki çember bandı ve etiket. PCB yeşilinden ayrışsın diye bej.
- Bakır folyo: yatay bakır rulo, iki çelik V-beşik üstünde, palet üzerinde; uç yüzde sarım
  halkaları, dışa taşan karton göbek, hafif açılmış folyo ucu.

Ortak yardımcılar (renk, kutu, silindir, karo işareti) anakart_pcb_20261014.py'den alınır.
Malzemeler düz renk (glTF'ye aktarılabilir).
"""
import math

import bmesh
import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
H = {"__name__": "anakart_pcb_yardimci"}
exec(open(SCRIPTS + "/anakart_pcb_20261014.py", encoding="utf-8").read(), H)
mat, box, disc, tile_marks = H["mat"], H["box"], H["disc"], H["tile_marks"]

PALLET_H = 0.13


def palette():
    P = H["palette"]()
    P.update(
        wood=mat("B_ahsap", "#A47B4C", 0.85),
        sheet=mat("G_levha_yesil", "#5AAE6A", 0.28),      # PCB yeşilinden bir ton açık, daha parlak
        fr4_edge=mat("G_levha_cekirdek", "#D8DDB8", 0.6),  # cam elyaf çekirdek (kenarda)
        card=mat("B_karton", "#B88954", 0.8),
        strap=mat("G_cember", "#2C3238", 0.5),
        label=mat("G_etiket", "#F2F4F2", 0.6),
        label_ink=mat("G_etiket_yazi", "#2C3238", 0.6),
        copper=mat("G_bakir", "#E3935A", 0.3, 0.7),
        copper_dark=mat("G_bakir_koyu", "#B0653A", 0.4, 0.7),
        core=mat("G_karton_gobek", "#8F8A80", 0.8),
        steel=mat("B_celik", "#B9BFC3", 0.35, 0.8),
        rubber=mat("B_kaucuk", "#1D2125", 0.85),
    )
    return P


def set_coll(c):
    H["COLL"] = c


def pallet(P, root, w=0.9, d=0.9):
    """Art bible ahşap paleti: 3 kızak + üst tahtalar, 0.13 m."""
    for y in (-d / 2 + 0.05, 0, d / 2 - 0.05):
        box("Palet_kizak", 0, y, 0, w, 0.1, 0.1, P["wood"], root, 0.008)
    n = 5
    for i in range(n):
        x = -w / 2 + 0.07 + i * (w - 0.14) / (n - 1)
        box("Palet_tahta", x, 0, 0.1, 0.14, d, 0.03, P["wood"], root, 0.006)


# --- Yalıtkan levha ---------------------------------------------------------------------------

def insulating_sheet(P, x=0.0, y=0.0):
    """Çıplak yeşil levha: bakır, ped, serigrafi yok. Kenarda açık renkli cam elyaf çekirdek
    görünür (üst ve alt yüz yeşil kaplama, ortası açık). Palet üstünde; karton köşe
    koruyucular ve iki çember bandıyla sabitli."""
    root = H["link"](bpy.data.objects.new("Yalitkan_levha_stok", None))
    pallet(P, root)
    W, D, T = 0.86, 0.72, 0.03
    z = PALLET_H
    skin = 0.006
    # çekirdek (kenardan görünür) + üst/alt yeşil kaplama
    box("Levha_cekirdek", 0, 0, z + skin, W - 0.004, D - 0.004, T - 2 * skin, P["fr4_edge"], root, 0.002)
    box("Levha_alt", 0, 0, z, W, D, skin, P["sheet"], root, 0.002)
    box("Levha_ust", 0, 0, z + T - skin, W, D, skin, P["sheet"], root, 0.002)
    # köşe koruyucular (karton L)
    c = 0.09
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (W / 2 - c / 2 + 0.008), sy * (D / 2 - c / 2 + 0.008)
            box("Kose_koruyucu", cx, sy * (D / 2 + 0.004), z - 0.004, c, 0.012, T + 0.016, P["card"], root, 0.003)
            box("Kose_koruyucu", sx * (W / 2 + 0.004), cy, z - 0.004, 0.012, c, T + 0.016, P["card"], root, 0.003)
            box("Kose_koruyucu", cx, cy, z + T, c, c, 0.008, P["card"], root, 0.003)
    # iki çember bandı (levha + paleti sarar)
    for bx in (-0.22, 0.22):
        box("Cember_ust", bx, 0, z + T, 0.03, D + 0.02, 0.003, P["strap"], root)
        for sy in (-1, 1):
            box("Cember_yan", bx, sy * (D / 2 + 0.011), 0.02, 0.03, 0.003, z + T - 0.02, P["strap"], root)
    root.location = (x, y, 0)
    return root


# --- Bakır folyo -----------------------------------------------------------------------------

def ring(name, r_out, r_in, depth, m, root, segs=48):
    """Halka (anulus) prizma, eksen z."""
    bm = bmesh.new()
    outer = bmesh.ops.create_circle(bm, cap_ends=False, segments=segs, radius=r_out)["verts"]
    inner = bmesh.ops.create_circle(bm, cap_ends=False, segments=segs, radius=r_in)["verts"]
    for i in range(segs):
        bm.faces.new((outer[i], outer[(i + 1) % segs], inner[(i + 1) % segs], inner[i]))
    r = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    bmesh.ops.translate(bm, vec=(0, 0, depth), verts=[v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = abs(p.normal.z) < 0.5
    ob = H["link"](bpy.data.objects.new(name, me), root)
    me.materials.append(m)
    return ob


def copper_foil(P, x=0.0, y=0.0):
    root = H["link"](bpy.data.objects.new("Bakir_folyo_stok", None))
    pallet(P, root)
    R, L, RC = 0.27, 0.72, 0.075          # rulo yarıçapı, genişliği (x boyunca), göbek
    zc = PALLET_H + 0.06 + R               # rulo ekseni yüksekliği
    # V-beşikler (çelik) + kauçuk ped
    for bx in (-0.26, 0.26):
        box("Besik_taban", bx, 0, PALLET_H, 0.1, 0.5, 0.03, P["steel"], root, 0.004)
        for s in (-1, 1):
            b = box("Besik_kol", bx, s * 0.14, PALLET_H + 0.02, 0.08, 0.2, 0.05, P["steel"], root, 0.004)
            b.rotation_euler.x = -s * math.radians(35)
            b.location.z = PALLET_H + 0.07
    # rulo gövdesi
    roll = ring("Bakir_rulo", R, RC + 0.01, L, P["copper"], root, 64)
    roll.rotation_euler.y = math.pi / 2
    roll.location = (-L / 2, 0, zc)
    # uç yüzlerde sarım halkaları (biraz koyu ince halkalar)
    for side in (-1, 1):
        for k in range(1, 6):
            rr = RC + 0.01 + k * (R - RC - 0.01) / 6
            h = ring("Sarim_halkasi", rr + 0.0025, rr - 0.0025, 0.002, P["copper_dark"], root, 64)
            h.rotation_euler.y = math.pi / 2
            h.location = ((L / 2 + 0.0005) if side > 0 else (-L / 2 - 0.0025), 0, zc)
    # karton göbek (dışa taşar)
    core = ring("Karton_gobek", RC + 0.01, RC - 0.012, L + 0.08, P["core"], root, 40)
    core.rotation_euler.y = math.pi / 2
    core.location = (-L / 2 - 0.04, 0, zc)
    # rulo gövdesinde yapışkan bant (folyo ucunu tutar) ve iki koruma bandı
    for bx in (-0.22, 0.22):
        b = ring("Koruma_bandi", R + 0.004, R - 0.002, 0.04, P["strap"], root, 64)
        b.rotation_euler.y = math.pi / 2
        b.location = (bx - 0.02, 0, zc)
    # etiket rulonun göbek ucunda
    box("Etiket", L / 2 + 0.002, 0, zc - 0.17, 0.003, 0.12, 0.08, P["label"], root).location.z = zc - 0.17
    root.location = (x, y, 0)
    return root


def _build(scene, coll_name, fn):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new(coll_name)
    scene.collection.children.link(c)
    set_coll(c)
    tile_marks(P, 0, 0)
    return fn(P, 0, 0)


def build_sheet(scene=None):
    """Yalıtkan levha → ayrı dosya: output/yalitkan_levha_20261014/yalitkan_levha.blend"""
    return _build(scene, "Yalitkan_levha", insulating_sheet)


def build_foil(scene=None):
    """Bakır folyo → ayrı dosya: output/bakir_folyo_20261014/bakir_folyo.blend"""
    return _build(scene, "Bakir_folyo", copper_foil)


if __name__ == "__main__":
    import sys
    (build_foil if "folyo" in sys.argv else build_sheet)()
