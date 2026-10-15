"""Soket ve bağlantı seti (2026-10-14): 01 anakart montajının dış ikmal girdisi.

Kural (kullanıcı): parçalar tek tek taşınır, bir stok karosunda (1 × 1 m) tek birim durur.
Gerçekçi değil, okunur: parçalar büyütülmüş; set köpük yuvalı, kapağı açık bir taşıma çantasında.

- Kap: açık gri gövde, siyah köpük iç, önde kilitler ve tutamak; kapak yok.
- İçerik: CPU soketi (altın pin alanı, gümüş çerçeve ve kol), 2 mavi RAM yuvası (beyaz mandal),
  açık gri PCIe yuvası, beyaz 24 pin güç konnektörü, arka I/O bloğu (USB, ethernet, ses).

Ortak yardımcılar anakart_pcb_20261014.py'den alınır. Malzemeler düz renk (glTF'ye uygun).
Çıktı: output/soket_baglanti_seti_20261014/soket_baglanti_seti.blend
"""
import math

import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
H = {"__name__": "anakart_pcb_yardimci"}
exec(open(SCRIPTS + "/anakart_pcb_20261014.py", encoding="utf-8").read(), H)
mat, box, disc, tile_marks = H["mat"], H["box"], H["disc"], H["tile_marks"]

CW, CD, CH = 0.86, 0.66, 0.14      # çanta gövdesi
FEET = 0.02
FOAM_TOP = FEET + CH - 0.012       # köpük üst yüzü


def palette():
    P = H["palette"]()
    P.update(
        shell=mat("S_canta_govde", "#C5CBCE", 0.45),
        shell_edge=mat("S_canta_kenar", "#2C3238", 0.5),
        foam=mat("S_kopuk", "#1D2125", 0.9),
        foam_cut=mat("S_kopuk_yuva", "#121517", 0.95),
        lid_foam=mat("S_kapak_kopuk", "#4A5057", 0.9),
        socket=mat("S_soket_govde", "#2C3238", 0.5),
        frame=mat("S_soket_cerceve", "#B9BFC3", 0.3, 0.85),
        ram=mat("S_ram_yuvasi", "#2F6DB5", 0.45),
        latch=mat("S_mandal", "#E6EAEA", 0.45),
        pcie=mat("S_pcie_yuvasi", "#C5CBCE", 0.45),
        atx=mat("S_atx_konnektor", "#E6EAEA", 0.5),
        io=mat("S_io_metal", "#858D93", 0.35, 0.6),
        usb=mat("S_usb_mavi", "#2F6DB5", 0.4),
        eth=mat("S_ethernet", "#1D2125", 0.6),
        jack_g=mat("S_ses_yesil", "#39C45A", 0.4),
        jack_p=mat("S_ses_pembe", "#E07AA0", 0.4),
        jack_b=mat("S_ses_mavi", "#5FB3E0", 0.4),
        hole=mat("P_delik", "#1A1E1C", 0.7),
    )
    return P


def cutout(P, root, x, y, sx, sy):
    """Köpükte parçanın yuvası: biraz büyük, daha koyu çukur."""
    box("Kopuk_yuva", x, y, FOAM_TOP, sx + 0.024, sy + 0.024, 0.002, P["foam_cut"], root)


# --- Çanta ----------------------------------------------------------------------------------

def case(P, root):
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("Canta_ayak", sx * (CW / 2 - 0.07), sy * (CD / 2 - 0.07), 0, 0.08, 0.08, FEET, P["shell_edge"], root, 0.004)
    box("Canta_govde", 0, 0, FEET, CW, CD, CH, P["shell"], root, 0.02)
    # üst kenar profili (koyu) ve köpük
    box("Canta_kenar", 0, 0, FEET + CH - 0.012, CW + 0.004, CD + 0.004, 0.014, P["shell_edge"], root, 0.006)
    box("Kopuk", 0, 0, FEET + CH - 0.04, CW - 0.05, CD - 0.05, 0.04, P["foam"], root, 0.006)
    # ön yüzde iki kilit ve tutamak
    for x in (-0.28, 0.28):
        box("Canta_kilit", x, -CD / 2 - 0.012, FEET + CH - 0.07, 0.06, 0.024, 0.05, P["shell_edge"], root, 0.006)
        box("Canta_kilit_dil", x, -CD / 2 - 0.026, FEET + CH - 0.045, 0.03, 0.008, 0.02, P["frame"], root, 0.002)
    box("Canta_tutamak", 0, -CD / 2 - 0.03, FEET + CH - 0.075, 0.2, 0.03, 0.035, P["shell_edge"], root, 0.012)
    # kapak yok (kullanıcı kararı): içerik açıkta, üstten görünür


# --- Parçalar --------------------------------------------------------------------------------

def cpu_socket(P, root, x, y):
    S = 0.24
    cutout(P, root, x, y, S + 0.04, S)
    z = FOAM_TOP
    box("Soket_govde", x, y, z, S, S, 0.03, P["socket"], root, 0.004)
    box("Soket_pin_alani", x, y, z + 0.03, S * 0.62, S * 0.62, 0.003, P["gold"], root)
    for i in range(1, 8):  # pin ızgarası
        o = -S * 0.31 + i * S * 0.62 / 8
        box("Soket_pin_ayrim", x + o, y, z + 0.033, 0.0015, S * 0.62, 0.0005, P["socket"], root)
        box("Soket_pin_ayrim", x, y + o, z + 0.033, S * 0.62, 0.0015, 0.0005, P["socket"], root)
    # gümüş tutucu çerçeve (dört kenar)
    t = 0.025
    for (cx, cy, sx, sy) in ((x, y + S / 2 - t / 2, S, t), (x, y - S / 2 + t / 2, S, t),
                             (x - S / 2 + t / 2, y, t, S - 2 * t), (x + S / 2 - t / 2, y, t, S - 2 * t)):
        box("Soket_cerceve", cx, cy, z + 0.03, sx, sy, 0.008, P["frame"], root, 0.002)
    # kol: sağ kenar boyunca çubuk + kıvrık uç
    box("Soket_kol", x + S / 2 + 0.018, y, z + 0.012, 0.012, S, 0.012, P["frame"], root, 0.004)
    box("Soket_kol_uc", x + S / 2 + 0.03, y - S / 2 - 0.006, z + 0.012, 0.035, 0.012, 0.012, P["frame"], root, 0.004)
    # köşe işareti
    t2 = box("Soket_isaret", x - S * 0.28, y + S * 0.28, z + 0.034, 0.018, 0.018, 0.001, P["silk"], root)
    t2.rotation_euler.z = math.pi / 4


def slot(P, root, name, x, y, L, m, latch=True):
    cutout(P, root, x, y, L + (0.04 if latch else 0.02), 0.04)
    z = FOAM_TOP
    box(name, x, y, z, L, 0.034, 0.05, m, root, 0.004)
    box(name + "_yarik", x, y, z + 0.05, L - 0.02, 0.008, 0.0015, P["hole"], root)
    box(name + "_centik", x + L * 0.12, y, z + 0.046, 0.008, 0.036, 0.006, m, root)   # anahtar çentiği
    if latch:
        for s in (-1, 1):
            box(name + "_mandal", x + s * (L / 2 + 0.008), y, z, 0.016, 0.03, 0.065, P["latch"], root, 0.004)


def atx_connector(P, root, x, y):
    W, D = 0.13, 0.05
    cutout(P, root, x, y, W, D)
    z = FOAM_TOP
    box("ATX_konnektor", x, y, z, W, D, 0.055, P["atx"], root, 0.004)
    for r in range(2):
        for k in range(12):
            box("ATX_pin_delik", x - W / 2 + 0.008 + k * 0.0103, y - 0.011 + r * 0.022, z + 0.055, 0.007, 0.012, 0.001, P["hole"], root)
    box("ATX_tirnak", x, y + D / 2 + 0.006, z + 0.02, 0.025, 0.012, 0.035, P["atx"], root, 0.003)


def io_block(P, root, x, y):
    W, D, Hh = 0.17, 0.08, 0.075
    cutout(P, root, x, y, W, D)
    z = FOAM_TOP
    box("IO_govde", x, y, z, W, D, Hh, P["io"], root, 0.004)
    fy = y - D / 2 - 0.0008
    # USB yığını (2 mavi port), ethernet (siyah kare), ses girişleri (3 renkli yuvarlak)
    for k in range(2):
        box("USB_port", x - 0.055, fy, z + 0.016 + k * 0.028, 0.034, 0.002, 0.014, P["usb"], root)
    box("Ethernet_port", x + 0.0, fy, z + 0.02, 0.036, 0.002, 0.034, P["eth"], root)
    for k, m in enumerate((P["jack_g"], P["jack_p"], P["jack_b"])):
        d = disc("Ses_girisi", 0, 0, 0, 0.008, 0.002, m, root, 16)
        d.rotation_euler.x = math.pi / 2
        d.location = (x + 0.055, fy, z + 0.016 + k * 0.02)


def soket_seti(P, x=0.0, y=0.0):
    root = H["link"](bpy.data.objects.new("Soket_baglanti_seti", None))
    case(P, root)
    cpu_socket(P, root, -0.2, -0.01)
    slot(P, root, "RAM_yuvasi", 0.17, 0.2, 0.34, P["ram"])
    slot(P, root, "RAM_yuvasi", 0.17, 0.12, 0.34, P["ram"])
    slot(P, root, "PCIe_yuvasi", 0.17, 0.035, 0.32, P["pcie"])
    atx_connector(P, root, 0.29, -0.17)
    io_block(P, root, 0.07, -0.17)
    root.location = (x, y, 0)
    return root


def build(scene=None):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Soket_baglanti_seti")
    scene.collection.children.link(c)
    H["COLL"] = c
    tile_marks(P, 0, 0)
    return soket_seti(P, 0, 0)


if __name__ == "__main__":
    build()
