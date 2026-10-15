"""Boş kasa (2026-10-14): 01 anakart montajının girdisi (01A'da yerel de üretilebilir).

Kurallar (kullanıcı, 14 Ekim 2026):
- Parçalar tek tek taşınır, bir stok karosunda (1 × 1 m) tek birim durur.
- Kasaya takılan kart, stoktaki 0.84 m'lik PCB ile aynı ölçüde olmak zorunda değil.

Ölçü: kasa bantta da taşınacağı için banda göre seçildi (raylar arası ~0.66 m).
Kasa yan yatık, sol kapağı çıkarılmış: 0.64 (x, kasa boyu) × 0.56 (y, derinlik) × 0.26 (z) m.
Ön panel −y (kameraya), arka panel +y. Kasanın üstü +x, PSU tarafı −x.
İçindeki kart yeri: temel kart düzeninin 1.2 katı (0.48 × 0.384 m); pirinç ayaklar o kartın
montaj deliklerine denk gelir.

Ortak yardımcılar anakart_pcb_20261014.py'den alınır. Malzemeler düz renk (glTF'ye uygun).
Çıktı: output/bos_kasa_20261014/bos_kasa.blend
"""
import math

import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
H = {"__name__": "anakart_pcb_yardimci"}
exec(open(SCRIPTS + "/anakart_pcb_20261014.py", encoding="utf-8").read(), H)
mat, box, disc, tile_marks = H["mat"], H["box"], H["disc"], H["tile_marks"]

L, D, HZ = 0.64, 0.56, 0.20          # x, y, z (alçak: oyun açısından içi görünsün)
T = 0.015                            # sac kalınlığı
FRONT = 0.035                        # ön panel kalınlığı
FEET = 0.012
BS = 1.2                             # kasa içi kart ölçeği (temel düzen 0.40 × 0.32)
HOLES = ((-0.185, 0.145), (0.045, 0.145), (0.185, 0.145),
         (-0.185, -0.12), (0.045, -0.12), (0.185, -0.12))   # anakart_pcb ile aynı


def palette():
    P = H["palette"]()
    P.update(
        shell=mat("K_kasa_govde", "#2C3238", 0.5),
        tray=mat("K_kasa_tabla", "#5E666D", 0.5),
        front=mat("K_on_panel", "#C5CBCE", 0.45),
        vent=mat("K_menfez", "#1D2125", 0.7),
        brass=mat("K_piring_ayak", "#C9A24A", 0.35, 0.85),
        grommet=mat("B_kaucuk", "#1D2125", 0.85),
        steel=mat("B_celik", "#B9BFC3", 0.35, 0.8),
        led=mat("K_guc_led", "#5FB3E0", 0.3, 0.0, 2.0),
        usb=mat("S_usb_mavi", "#2F6DB5", 0.4),
        cut=mat("K_aciklik", "#121517", 0.9),
    )
    return P


def board_frame():
    """Kart yerleşimi: kartın yerel −x kenarı (I/O) arkaya (+y) bakar; yerel +y (VRM) kasanın üstüne (+x).
    Dönüşüm: yerel (u, v) → dünya (cx + BS*v, cy − BS*u)."""
    bw, bd = 0.40 * BS, 0.32 * BS                       # y boyunca 0.48, x boyunca 0.384
    cx = L / 2 - T - 0.02 - bd / 2                       # üst duvara yakın
    cy = D / 2 - T - 0.005 - bw / 2                      # arka duvara yakın
    return cx, cy, bw, bd


def to_world(u, v):
    cx, cy, _, _ = board_frame()
    return cx + BS * v, cy - BS * u


def body(P, root):
    z0 = FEET
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("Kasa_ayak", sx * (L / 2 - 0.06), sy * (D / 2 - 0.06), 0, 0.06, 0.06, FEET, P["grommet"], root, 0.003)
    # tabla (sağ yan kapak, yatınca taban) + dört duvar
    box("Kasa_sag_kapak", 0, 0, z0, L, D, T, P["shell"], root, 0.006)
    box("Anakart_tablasi", 0.03, 0.02, z0 + T, L - 0.1, D - 0.12, 0.003, P["tray"], root)
    box("Kasa_ust_duvar", L / 2 - T / 2, 0, z0, T, D, HZ, P["shell"], root, 0.004)
    box("Kasa_alt_duvar", -L / 2 + T / 2, 0, z0, T, D, HZ, P["shell"], root, 0.004)
    box("Kasa_arka_duvar", 0, D / 2 - T / 2, z0, L - 2 * T, T, HZ, P["shell"], root, 0.004)
    # açık taraftaki kenar çerçevesi (sol kapak yuvası)
    for s in (-1, 1):
        box("Kapak_rayi", s * (L / 2 - T - 0.006), 0.0, z0 + HZ - 0.012, 0.012, D - FRONT - T, 0.012, P["shell"], root, 0.002)
    # ön panel (açık gri, kalın)
    fy = -D / 2 + FRONT / 2
    box("On_panel", 0, fy, z0, L, FRONT, HZ, P["front"], root, 0.012)
    zc = z0 + HZ / 2
    # havalandırma yarıkları: ön panelin alt 2/3'ünde yatay şeritler
    for k in range(7):
        box("On_menfez", -0.06, -D / 2 - 0.0008, zc - 0.075 + k * 0.025, 0.4, 0.002, 0.009, P["vent"], root)
    # güç düğmesi + LED + 2 USB: üst uçta (+x)
    d = disc("Guc_dugmesi", 0, 0, 0, 0.022, 0.006, P["steel"], root, 24)
    d.rotation_euler.x = math.pi / 2
    d.location = (L / 2 - 0.07, -D / 2 - 0.002, zc + 0.03)
    d = disc("Guc_led", 0, 0, 0, 0.006, 0.004, P["led"], root, 12)
    d.rotation_euler.x = math.pi / 2
    d.location = (L / 2 - 0.07, -D / 2 - 0.004, zc + 0.03)
    for k in range(2):
        box("On_usb", L / 2 - 0.07, -D / 2 - 0.0008, zc - 0.035 - k * 0.03, 0.036, 0.002, 0.014, P["usb"], root)


def interior(P, root):
    z = FEET + T + 0.003
    # PSU örtüsü: alt uçta (−x), tam derinlik
    px0, px1 = -L / 2 + T, -L / 2 + T + 0.15
    box("PSU_ortusu", (px0 + px1) / 2, 0.0, z, px1 - px0, D - FRONT - T, 0.09, P["shell"], root, 0.006)
    box("PSU_ortusu_ust", (px0 + px1) / 2, 0.0, z + 0.09, px1 - px0 - 0.01, D - FRONT - T - 0.01, 0.003, P["tray"], root)
    # kablo geçiş delikleri (lastik halkalı): kart yerinin ön kenarı boyunca
    cx, cy, bw, bd = board_frame()
    for k in range(3):
        gx = cx - bd / 2 + 0.06 + k * 0.13
        box("Kablo_deligi_halka", gx, cy - bw / 2 - 0.035, z, 0.07, 0.03, 0.004, P["grommet"], root, 0.008)
        box("Kablo_deligi", gx, cy - bw / 2 - 0.035, z + 0.001, 0.05, 0.016, 0.004, P["cut"], root, 0.006)
    # kart yerinin işareti: ince açık çerçeve (kart nereye oturacak)
    t = 0.004
    for (x, y, sx, sy) in ((cx, cy + bw / 2, bd, t), (cx, cy - bw / 2, bd, t),
                           (cx + bd / 2, cy, t, bw), (cx - bd / 2, cy, t, bw)):
        box("Kart_yeri_cizgi", x, y, z, sx, sy, 0.0008, P["tile"], root)
    # pirinç ayaklar (standoff): kartın 6 montaj deliği + CPU soğutucu arka plaka açıklığı
    for (u, v) in HOLES:
        x, y = to_world(u, v)
        disc("Pirinc_ayak", x, y, z, 0.013, 0.03, P["brass"], root, 6)
        disc("Pirinc_ayak_delik", x, y, z + 0.03, 0.005, 0.0008, P["cut"], root, 10)
    sx, sy = to_world(-0.03, 0.065)                      # CPU alanının arkası
    box("CPU_arka_aciklik", sx, sy, z, 0.13, 0.13, 0.001, P["cut"], root, 0.01)


def rear(P, root):
    y = D / 2 + 0.0008
    zc = FEET + HZ / 2
    # I/O kalkan açıklığı: kartın I/O alanı (yerel u≈−0.185, v −0.02…0.14) hizasında
    x0, _ = to_world(-0.185, -0.02)
    x1, _ = to_world(-0.185, 0.14)
    box("IO_acikligi", (x0 + x1) / 2, y, zc - 0.03, abs(x1 - x0), 0.002, 0.06, P["cut"], root)
    # genişleme kartı kapakları: PCIe hizası (v −0.15…−0.02)
    for k in range(5):
        xk, _ = to_world(-0.185, -0.15 + k * 0.03)
        box("Genisleme_kapagi", xk, y, zc - 0.07, 0.022, 0.002, 0.14, P["steel"], root)
        box("Genisleme_kapagi_yarik", xk, y + 0.001, zc - 0.07, 0.008, 0.002, 0.11, P["cut"], root)
    # PSU açıklığı + fan ızgarası (alt uçta)
    px = -L / 2 + T + 0.075
    box("PSU_acikligi", px, y, zc - 0.07, 0.13, 0.002, 0.1, P["cut"], root)
    for r in (0.04, 0.025):
        d = disc("PSU_izgara", 0, 0, 0, r, 0.002, P["steel"], root, 24)
        d.rotation_euler.x = math.pi / 2
        d.location = (px, y + 0.002, zc - 0.07)
        d2 = disc("PSU_izgara_ic", 0, 0, 0, r - 0.006, 0.002, P["cut"], root, 24)
        d2.rotation_euler.x = math.pi / 2
        d2.location = (px, y + 0.003, zc - 0.07)
    # arka fan ızgarası (üst uçta)
    fx = L / 2 - 0.09
    for r in (0.055, 0.04, 0.025):
        d = disc("Fan_izgara", 0, 0, 0, r, 0.002, P["steel"], root, 28)
        d.rotation_euler.x = math.pi / 2
        d.location = (fx, y + 0.002, zc + 0.04)
        d2 = disc("Fan_izgara_ic", 0, 0, 0, r - 0.006, 0.002, P["cut"], root, 28)
        d2.rotation_euler.x = math.pi / 2
        d2.location = (fx, y + 0.003, zc + 0.04)


def bos_kasa(P, x=0.0, y=0.0):
    root = H["link"](bpy.data.objects.new("Bos_kasa", None))
    body(P, root)
    interior(P, root)
    rear(P, root)
    root.location = (x, y, 0)
    return root


def build(scene=None):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Bos_kasa")
    scene.collection.children.link(c)
    H["COLL"] = c
    tile_marks(P, 0, 0)
    return bos_kasa(P, 0, 0)


if __name__ == "__main__":
    build()
