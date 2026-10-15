"""02 işlemci montajının girdileri (2026-10-15): silikon çekirdek, işlemci taşıyıcısı, ısı yayıcı kapak.

Kaynak: docs/İstasyonlar/Anakart ve İşlemci - Giriş Çıkış Akışı.md (14 Ekim 2026): 02 ikmalden üç
ürün alır. Silikon çekirdek modele uygun gelir (oyunda üç seviye: temel / orta / üst).

Kurallar (kullanıcı): parçalar tek tek taşınır, bir stok karosunda (1 × 1 m) tek birim durur;
gerçekçi değil, okunur. Üç girdi uzaktan biçimiyle ayrışsın:
- Silikon çekirdek: açık taşıma kutusunda büyük yuvarlak plaka (wafer), yonga ızgaralı; ön kenarda
  seviye rengi (temel mavi, orta turuncu, üst kırmızı) şerit + etiket.
- İşlemci taşıyıcısı: siyah JEDEC tepside 3 × 2 yeşil taşıyıcı (altın ped alanı, kenarda kondansatör).
- Isı yayıcı kapak: açık gri tepside 3 × 2 gümüş kapak yığını (her yığında 4 kapak).

Ortak yardımcılar anakart_pcb_20261014.py'den. Her model kendi .blend'ine:
output/silikon_cekirdek_20261015/, islemci_tasiyicisi_20261015/, isi_yayici_kapak_20261015/
"""
import math

import bmesh
import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
H = {"__name__": "anakart_pcb_yardimci"}
exec(open(SCRIPTS + "/anakart_pcb_20261014.py", encoding="utf-8").read(), H)
mat, box, disc, link, tile_marks = H["mat"], H["box"], H["disc"], H["link"], H["tile_marks"]
R = {"__name__": "renk"}
exec(open(SCRIPTS + "/renk_paleti.py", encoding="utf-8").read(), R)
RENK = R["RENK"]

SEVIYE = {"temel": RENK["mavi"], "orta": RENK["turuncu"], "ust": RENK["kirmizi"]}


def palette():
    P = H["palette"]()
    P.update(
        carrier=mat("C_tasima_kutusu", "#2C3238", 0.5),
        carrier_rim=mat("C_kutu_kenar", "#4A5057", 0.5),
        wafer=mat("C_silikon", "#6F7A96", 0.18, 0.85),
        wafer_line=mat("C_silikon_cizgi", "#454D63", 0.3, 0.6),
        label=mat("C_etiket", "#F2F4F2", 0.6),
        label_ink=mat("C_etiket_yazi", "#2C3238", 0.6),
        tray=mat("E_jedec_tepsi", "#1D2125", 0.7),
        tray_light=mat("C_tepsi_acik", "#A9B2B5", 0.6),
        substrate=mat("C_tasiyici", "#2E7A43", 0.45),
        cap=mat("C_smd", "#C9A27A", 0.5),
        lid=mat("C_kapak_nikel", "#D3D8DB", 0.22, 0.9),
        lid_edge=mat("C_kapak_kenar", "#9AA1A6", 0.3, 0.85),
    )
    for k, hx in SEVIYE.items():
        P["tier_" + k] = mat("C_seviye_" + k, hx, 0.45)
    return P


def cyl(name, x, y, z, r, h, m, root, verts=64):
    return disc(name, x, y, z, r, h, m, root, verts)


def ring(name, x, y, z, r0, r1, h, m, root, verts=64):
    """İçi boş halka (kutunun yuvarlak duvarı)."""
    bm = bmesh.new()
    outer = bmesh.ops.create_circle(bm, cap_ends=False, segments=verts, radius=r1)["verts"]
    inner = bmesh.ops.create_circle(bm, cap_ends=False, segments=verts, radius=r0)["verts"]
    for i in range(verts):
        bm.faces.new((outer[i], outer[(i + 1) % verts], inner[(i + 1) % verts], inner[i]))
    geom = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))["geom"]
    for v in geom:
        if isinstance(v, bmesh.types.BMVert):
            v.co.z += h
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me), root)
    me.materials.append(m)
    ob.location = (x, y, z)
    return ob


# --- Silikon çekirdek ---------------------------------------------------------------------------

WAFER_R = 0.36


def silikon_cekirdek(P, x=0.0, y=0.0, seviye="temel"):
    root = link(bpy.data.objects.new("Silikon_cekirdek_" + seviye, None))
    tier = P["tier_" + seviye]
    # kare taşıma kutusu tabanı (köşeleri yuvarlatılmış) + yuvarlak iç duvar
    box("Kutu_taban", 0, 0, 0, 0.86, 0.86, 0.05, P["carrier"], root, 0.04)
    ring("Kutu_duvar", 0, 0, 0.05, WAFER_R + 0.015, WAFER_R + 0.05, 0.045, P["carrier_rim"], root)
    for sx in (-1, 1):                              # köşe ayakları (istif için)
        for sy in (-1, 1):
            cyl("Kutu_kose", sx * 0.36, sy * 0.36, 0.05, 0.035, 0.05, P["carrier_rim"], root, 16)
    # plaka: düz kenarlı (flat) disk, yonga ızgarası
    z = 0.06
    w = cyl("Silikon_plaka", 0, 0, z, WAFER_R, 0.012, P["wafer"], root)
    n = 9
    step = 2 * WAFER_R * 0.86 / n
    for i in range(1, n):
        o = -WAFER_R * 0.86 + i * step
        half = math.sqrt(max(0.0, (WAFER_R * 0.93) ** 2 - o * o))
        box("Yonga_cizgi", o, 0, z + 0.012, 0.004, 2 * half, 0.0008, P["wafer_line"], root)
        box("Yonga_cizgi", 0, o, z + 0.012, 2 * half, 0.004, 0.0008, P["wafer_line"], root)
    box("Plaka_duz_kenar", 0, -WAFER_R + 0.012, z, 0.2, 0.03, 0.0125, P["carrier"], root)
    # seviye: ön kenarda renkli şerit ve köşede etiket
    box("Seviye_serit", 0, -0.43 + 0.012, 0.0, 0.86, 0.024, 0.052, tier, root, 0.004)
    box("Seviye_serit", 0, 0.43 - 0.012, 0.0, 0.86, 0.024, 0.052, tier, root, 0.004)
    box("Etiket", 0.3, -0.33, 0.05, 0.16, 0.1, 0.002, P["label"], root)
    box("Etiket_seviye", 0.3, -0.36, 0.052, 0.14, 0.03, 0.001, tier, root)
    for k in range(2):
        box("Etiket_yazi", 0.29, -0.325 + k * 0.025, 0.052, 0.11, 0.008, 0.001, P["label_ink"], root)
    root.location = (x, y, 0)
    return root


# --- İşlemci taşıyıcısı -----------------------------------------------------------------------

TRAY_W, TRAY_D, TRAY_T = 0.84, 0.6, 0.035


def tray(P, root, m, z, pockets):
    box("Tepsi", 0, 0, z, TRAY_W, TRAY_D, TRAY_T, m, root, 0.006)
    for (px, py, s) in pockets:                    # cep: koyu çukur görünümü
        box("Tepsi_cep", px, py, z + TRAY_T, s + 0.03, s + 0.03, 0.002, P["hole"], root, 0.004)


def pocket_grid(s):
    return [(-0.26 + i * 0.26, -0.13 + j * 0.26, s) for j in range(2) for i in range(3)]


def substrate(P, root, x, y, z):
    S = 0.2
    box("Tasiyici", x, y, z, S, S, 0.012, P["substrate"], root, 0.002)
    PA = 0.11
    box("Tasiyici_ped_alani", x, y, z + 0.012, PA, PA, 0.0015, P["gold"], root)
    for i in range(1, 5):
        o = -PA / 2 + i * PA / 5
        box("Ped_ayrim", x + o, y, z + 0.0135, 0.002, PA, 0.0004, P["substrate"], root)
        box("Ped_ayrim", x, y + o, z + 0.0135, PA, 0.002, 0.0004, P["substrate"], root)
    for k in range(4):                              # kenarda SMD kondansatör sırası
        box("Tasiyici_smd", x - 0.06 + k * 0.04, y - 0.078, z + 0.012, 0.018, 0.01, 0.006, P["cap"], root)
    t = box("Tasiyici_isaret", x - 0.082, y + 0.082, z + 0.012, 0.016, 0.016, 0.001, P["gold"], root)
    t.rotation_euler.z = math.pi / 4


def islemci_tasiyicisi(P, x=0.0, y=0.0):
    root = link(bpy.data.objects.new("Islemci_tasiyicisi", None))
    for k in range(3):                              # 2 boş tepsi + üstte dolu tepsi
        tray(P, root, P["tray"], k * TRAY_T, pocket_grid(0.2) if k == 2 else [])
    z = 3 * TRAY_T - 0.004
    for (px, py, _) in pocket_grid(0.2):
        substrate(P, root, px, py, z)
    root.location = (x, y, 0)
    return root


# --- Isı yayıcı kapak ---------------------------------------------------------------------------

def lid(P, root, x, y, z):
    S, T = 0.19, 0.016
    box("Kapak_flans", x, y, z, S, S, T * 0.5, P["lid_edge"], root, 0.006)
    box("Kapak_ust", x, y, z + T * 0.5, S - 0.03, S - 0.03, T * 0.5, P["lid"], root, 0.006)
    return T


def isi_yayici_kapak(P, x=0.0, y=0.0):
    root = link(bpy.data.objects.new("Isi_yayici_kapak", None))
    tray(P, root, P["tray_light"], 0, pocket_grid(0.19))
    for (px, py, _) in pocket_grid(0.19):
        z = TRAY_T - 0.004
        for k in range(4):
            z += lid(P, root, px, py, z) + 0.002
    root.location = (x, y, 0)
    return root


# --- Kurulum ----------------------------------------------------------------------------------

def _build(scene, coll_name, fn, **kw):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new(coll_name)
    scene.collection.children.link(c)
    H["COLL"] = c
    tile_marks(P, 0, 0)
    return fn(P, 0, 0, **kw)


def build_cekirdek(scene=None, seviye="temel"):
    """Silikon çekirdek → output/silikon_cekirdek_20261015/silikon_cekirdek.blend (koleksiyon başına seviye)"""
    return _build(scene, "Silikon_cekirdek_" + seviye, silikon_cekirdek, seviye=seviye)


def build_cekirdekler(scene=None):
    """Üç seviye tek dosyada (koleksiyon başına bir seviye, yan yana): silikon_cekirdek.blend"""
    out = []
    for i, s in enumerate(SEVIYE):
        r = build_cekirdek(scene, s)
        r.location.x = i * 1.2
        out.append(r)
    return out


def build_tasiyici(scene=None):
    """İşlemci taşıyıcısı → output/islemci_tasiyicisi_20261015/islemci_tasiyicisi.blend"""
    return _build(scene, "Islemci_tasiyicisi", islemci_tasiyicisi)


def build_kapak(scene=None):
    """Isı yayıcı kapak → output/isi_yayici_kapak_20261015/isi_yayici_kapak.blend"""
    return _build(scene, "Isi_yayici_kapak", isi_yayici_kapak)


def build(scene=None):
    """Önizleme: üç seviye çekirdek + taşıyıcı + kapak yan yana."""
    out = []
    for i, s in enumerate(SEVIYE):
        r = build_cekirdek(scene, s)
        r.location.x = -2 + i
        out.append(r)
    for i, f in enumerate((build_tasiyici, build_kapak)):
        r = f(scene)
        r.location.x = 1 + i
        out.append(r)
    return out


if __name__ == "__main__":
    build()
