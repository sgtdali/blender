"""Elektronik bileşen seti (2026-10-14): 01 anakart montajının dış ikmal girdisi.

Kural (kullanıcı): parçalar tek tek taşınır, bir stok karosunda (1 × 1 m) tek birim durur.
Gerçekçi değil, okunur: bileşenler büyütülmüş, set tek bir kit tablası üstünde.

- Arkada: SMD makaraları (mavi flanş, koyu taşıyıcı bant sarımı), iki sütun × 4 makara,
  yüzleri kameraya (−y) bakar. Uzaktan "elektronik parça" diye okunan ana öğe.
- Önde solda: JEDEC tepsi yığını, üst tepside kalay bacaklı siyah yongalar.
- Önde sağda: bölmeli kutu; kondansatör, bobin ve düğme pil bölmeleri.
- Taban: alçak antrasit ESD kit tablası, 0.88 × 0.88 m.

Ortak yardımcılar anakart_pcb_20261014.py'den alınır. Malzemeler düz renk (glTF'ye uygun).
Çıktı: output/elektronik_bilesen_seti_20261014/elektronik_bilesen_seti.blend
"""
import math

import bmesh
import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
H = {"__name__": "anakart_pcb_yardimci"}
exec(open(SCRIPTS + "/anakart_pcb_20261014.py", encoding="utf-8").read(), H)
mat, box, disc, tile_marks = H["mat"], H["box"], H["disc"], H["tile_marks"]

BASE_H = 0.06


def palette():
    P = H["palette"]()
    P.update(
        reel=mat("E_makara_mavi", "#2F6DB5", 0.4),
        tape=mat("E_tasiyici_bant", "#1D2125", 0.6),
        hub=mat("E_makara_gobek", "#E6EAEA", 0.45),
        label=mat("E_etiket", "#F2F4F2", 0.6),
        tray=mat("E_jedec_tepsi", "#1D2125", 0.7),
        chip=mat("E_yonga", "#22262A", 0.45),
        dot=mat("E_yonga_nokta", "#E6EAEA", 0.5),
        cap=mat("E_kondansator", "#C9CDD0", 0.3, 0.8),
        cap_top=mat("E_kondansator_ust", "#2C3238", 0.5),
        choke=mat("E_bobin", "#6B7278", 0.5, 0.3),
        copper=mat("G_bakir", "#E3935A", 0.3, 0.7),
        bin=mat("E_kutu", "#C5CBCE", 0.5),
        rubber=mat("B_kaucuk", "#1D2125", 0.85),
        steel=mat("B_celik", "#B9BFC3", 0.35, 0.8),
    )
    return P


def rot_x(ob):
    """Z eksenli silindiri Y eksenine yatırır (yüz −y / +y'ye bakar)."""
    ob.rotation_euler.x = math.pi / 2
    return ob


def ycyl(name, x, y, z, r, h, m, root, verts=32):
    """Y eksenli silindir; (x, y, z) merkez."""
    ob = disc(name, 0, 0, 0, r, h, m, root, verts)
    rot_x(ob)
    ob.location = (x, y, z)
    return ob


# --- Kit tablası -----------------------------------------------------------------------------

def base(P, root):
    W = 0.88
    box("Kit_tabla", 0, 0, 0.012, W, W, BASE_H - 0.012, P["dark"], root, 0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("Kit_ayak", sx * (W / 2 - 0.06), sy * (W / 2 - 0.06), 0, 0.08, 0.08, 0.012, P["rubber"], root, 0.003)
    r = 0.02
    for s in (-1, 1):
        box("Kit_kenar", 0, s * (W / 2 - r / 2), BASE_H, W, r, 0.02, P["dark"], root, 0.005)
        box("Kit_kenar", s * (W / 2 - r / 2), 0, BASE_H, r, W - 2 * r, 0.02, P["dark"], root, 0.005)


# --- SMD makaraları --------------------------------------------------------------------------

def reel(P, root, x, y, z, R=0.17):
    """Tek makara: iki mavi flanş, arada koyu bant sarımı, beyaz göbek, flanşta etiket.
    Eksen y; (x, y, z) merkez."""
    w = 0.05                                    # flanşlar arası
    ycyl("Makara_flans", x, y - w / 2 - 0.002, z, R, 0.004, P["reel"], root, 40)
    ycyl("Makara_flans", x, y + w / 2 + 0.002, z, R, 0.004, P["reel"], root, 40)
    ycyl("Bant_sarimi", x, y, z, R * 0.78, w, P["tape"], root, 40)
    ycyl("Makara_gobek", x, y, z, 0.045, w + 0.012, P["hub"], root, 24)
    ycyl("Gobek_delik", x, y, z, 0.016, w + 0.016, P["tape"], root, 16)
    # flanştaki pencereler: 6 küçük, simetrik (3 büyük pencere yüz gibi okunuyordu)
    for k in range(6):
        a = k * math.pi / 3
        ycyl("Flans_pencere", x + math.cos(a) * R * 0.62, y - w / 2 - 0.0045, z + math.sin(a) * R * 0.62,
             0.022, 0.001, P["tape"], root, 14)
    # etiket: göbeğin hemen üstünde, yatay şerit
    box("Makara_etiket", x, y - w / 2 - 0.0048, z + 0.052, 0.09, 0.001, 0.03, P["label"], root)


def reel_rack(P, root):
    """İki sütun × 4 makara; arkaya doğru dizili, önden ilk makara yüzü görünür."""
    R = 0.17
    z = BASE_H + 0.03 + R
    for cx in (-0.21, 0.21):
        box("Makara_rayi", cx, 0.25, BASE_H, 0.12, 0.38, 0.02, P["mid"], root, 0.004)
        for i in range(4):
            y = 0.1 + i * 0.09
            for s in (-1, 1):
                box("Makara_destek", cx + s * 0.05, y, BASE_H + 0.02, 0.025, 0.06, 0.025, P["mid"], root, 0.004)
            reel(P, root, cx, y, z, R)


# --- JEDEC tepsi yığını --------------------------------------------------------------------

def tray_stack(P, root, cx=-0.21, cy=-0.2):
    W, D, T = 0.36, 0.3, 0.025
    for k in range(3):
        box("JEDEC_tepsi", cx, cy, BASE_H + k * T, W, D, T - 0.002, P["tray"], root, 0.004)
    top = BASE_H + 3 * T - 0.002
    for i in range(4):
        for j in range(3):
            x = cx - 0.12 + i * 0.08
            y = cy - 0.08 + j * 0.08
            box("Yonga_bacak", x, y, top, 0.058, 0.058, 0.004, P["tin"], root)
            box("Yonga", x, y, top + 0.002, 0.048, 0.048, 0.012, P["chip"], root, 0.002)
            disc("Yonga_nokta", x - 0.015, y - 0.015, top + 0.014, 0.004, 0.0008, P["dot"], root, 10)


# --- Bölmeli kutu --------------------------------------------------------------------------

def compartment_box(P, root, cx=0.21, cy=-0.2):
    W, D, Hb = 0.36, 0.3, 0.05
    z0 = BASE_H
    box("Kutu_taban", cx, cy, z0, W, D, 0.01, P["bin"], root, 0.003)
    t = 0.01
    for s in (-1, 1):
        box("Kutu_duvar", cx, cy + s * (D / 2 - t / 2), z0, W, t, Hb, P["bin"], root, 0.003)
        box("Kutu_duvar", cx + s * (W / 2 - t / 2), cy, z0, t, D, Hb, P["bin"], root, 0.003)
    box("Kutu_bolme", cx, cy, z0, W - 2 * t, 0.006, Hb - 0.01, P["bin"], root)
    for k in (-1, 1):
        box("Kutu_bolme", cx + k * W / 6, cy, z0, 0.006, D - 2 * t, Hb - 0.01, P["bin"], root)
    cw, cd = (W - 2 * t) / 3, (D - 2 * t) / 2
    cells = [(cx - W / 3, cy + cd / 2), (cx, cy + cd / 2), (cx + W / 3, cy + cd / 2),
             (cx - W / 3, cy - cd / 2), (cx, cy - cd / 2), (cx + W / 3, cy - cd / 2)]
    zc = z0 + 0.01
    for idx, (x, y) in enumerate(cells):
        kind = ("cap", "choke", "cap", "choke", "cell", "cap")[idx]
        if kind == "cap":
            for a in range(2):
                for b in range(2):
                    px, py = x - 0.025 + a * 0.05, y - 0.03 + b * 0.06
                    disc("Kondansator", px, py, zc, 0.019, 0.075, P["cap"], root, 20)
                    disc("Kondansator_ust", px, py, zc + 0.075, 0.0185, 0.003, P["cap_top"], root, 20)
        elif kind == "choke":
            for a in range(2):
                for b in range(2):
                    px, py = x - 0.025 + a * 0.05, y - 0.03 + b * 0.06
                    box("Bobin", px, py, zc, 0.042, 0.042, 0.035, P["choke"], root, 0.004)
                    box("Bobin_tel", px, py - 0.0215, zc + 0.008, 0.026, 0.002, 0.018, P["copper"], root)
        else:
            for k in range(4):
                disc("Dugme_pil", x - 0.01 + (k % 2) * 0.02, y - 0.02 + (k // 2) * 0.04, zc + k * 0.0, 0.02, 0.006, P["steel"], root, 24)


def bilesen_seti(P, x=0.0, y=0.0):
    root = H["link"](bpy.data.objects.new("Elektronik_bilesen_seti", None))
    base(P, root)
    reel_rack(P, root)
    tray_stack(P, root)
    compartment_box(P, root)
    root.location = (x, y, 0)
    return root


def build(scene=None):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Elektronik_bilesen_seti")
    scene.collection.children.link(c)
    H["COLL"] = c
    tile_marks(P, 0, 0)
    return bilesen_seti(P, 0, 0)


if __name__ == "__main__":
    build()
