"""Anakartlı kasa (2026-10-15): 01 anakart montaj istasyonunun çıktısı, 02 işlemci montajının girdisi.

Kaynak: docs/İstasyonlar/Anakart ve İşlemci - Giriş Çıkış Akışı.md (14 Ekim 2026 kararı):
01 "anakartı takılmış kasa" çıkarır; işlemci 02'de takılır. Soket boş (altın pin alanı, kol açık);
RAM ve PCIe yuvaları boş, soğutucu ve kablo yok.

Kurallar (kullanıcı): parçalar tek tek taşınır, bir stok karosunda (1 × 1 m) tek birim durur;
gerçekçi değil, okunur.

- Gövde: bos_kasa_20261014'ün aynısı (yan yatık, sol kapak açık); kart yeri çizgileri kalkar,
  arka I/O açıklığına I/O kalkanı takılır.
- Kart: anakart_pcb_20261014.board() düzeni, kasa içi ölçek BS = 1.2, pirinç ayakların üstünde
  vidalı. Üstüne takılı bileşenler: boş soket (kol açık), VRM soğutucuları, bobin/kondansatörler,
  4 RAM yuvası (mavi/gri, beyaz mandal), 24 pin güç konnektörü, yonga seti soğutucusu,
  2 PCIe + 1 kısa yuva, M.2 soğutucu plakası, arka I/O bloğu, CMOS pili, SATA soketleri.
  Bileşenler kart çizim birimiyle (0.40 × 0.32) yerleştirilir, kartla birlikte ölçeklenir.

Çıktı: output/anakartli_kasa_20261015/anakartli_kasa.blend
"""
import math

import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
K = {"__name__": "bos_kasa_yardimci"}
exec(open(SCRIPTS + "/bos_kasa_20261014.py", encoding="utf-8").read(), K)
H = K["H"]
mat, box, disc, tile_marks = H["mat"], H["box"], H["disc"], H["tile_marks"]
TOP = H["TOP"]
BS = K["BS"]
STANDOFF_TOP = K["FEET"] + K["T"] + 0.003 + 0.03     # bos_kasa.interior pirinç ayak üstü


def palette():
    P = K["palette"]()
    P.update(
        socket=mat("S_soket_govde", "#2C3238", 0.5),
        frame=mat("S_soket_cerceve", "#B9BFC3", 0.3, 0.85),
        sink=mat("A_sogutucu", "#3A4046", 0.45, 0.5),
        sink_accent=mat("A_sogutucu_cizgi", "#B9BFC3", 0.3, 0.85),
        ram=mat("S_ram_yuvasi", "#2F6DB5", 0.45),
        ram2=mat("A_ram_yuvasi_gri", "#5E666D", 0.45),
        latch=mat("S_mandal", "#E6EAEA", 0.45),
        pcie=mat("S_pcie_yuvasi", "#C5CBCE", 0.45),
        atx=mat("S_atx_konnektor", "#E6EAEA", 0.5),
        io=mat("S_io_metal", "#858D93", 0.35, 0.6),
        choke=mat("E_bobin", "#6B7278", 0.5, 0.3),
        cap=mat("E_kondansator", "#C9CDD0", 0.3, 0.8),
        cap_top=mat("E_kondansator_ust", "#2C3238", 0.5),
        sata=mat("A_sata", "#1D2125", 0.6),
        hole=mat("P_delik", "#1A1E1C", 0.7),
    )
    return P


# --- Karta takılı bileşenler (kart çizim birimi, z = TOP kart üstü) -----------------------------

def cpu(P, r):
    cx, cy = -0.03, 0.065
    S = 0.09
    box("Soket", cx, cy, TOP, S, S, 0.007, P["socket"], r, 0.001)
    t = 0.008   # gümüş tutucu çerçeve
    for (x, y, sx, sy) in ((cx, cy + S / 2 - t / 2, S, t), (cx, cy - S / 2 + t / 2, S, t),
                           (cx - S / 2 + t / 2, cy, t, S - 2 * t), (cx + S / 2 - t / 2, cy, t, S - 2 * t)):
        box("Soket_cerceve", x, y, TOP + 0.007, sx, sy, 0.003, P["frame"], r, 0.0008)
    # işlemci yok (02'de takılır): boş altın pin alanı, ızgara çizgileri
    PA = 0.062
    box("Soket_pin_alani", cx, cy, TOP + 0.007, PA, PA, 0.0012, P["gold"], r)
    for i in range(1, 6):
        o = -PA / 2 + i * PA / 6
        box("Soket_pin_ayrim", cx + o, cy, TOP + 0.0082, 0.0012, PA, 0.0003, P["socket"], r)
        box("Soket_pin_ayrim", cx, cy + o, TOP + 0.0082, PA, 0.0012, 0.0003, P["socket"], r)
    tri = box("Soket_isaret", cx - 0.036, cy + 0.036, TOP + 0.007, 0.006, 0.006, 0.0012, P["silk"], r)
    tri.rotation_euler.z = math.pi / 4
    # açık kol: sağ kenarda menteşeden yukarı kalkık
    k = box("Soket_kol", cx + S / 2 + 0.006, cy + S / 2, TOP + 0.003, 0.004, S, 0.004, P["frame"], r, 0.001)
    k.location.y = cy + S / 2 - 0.002
    k.data = k.data.copy()
    for v in k.data.vertices:                 # pivot menteşede: mesh'i +y'ye kaydır
        v.co.y -= S / 2
    k.rotation_euler.x = -1.2
    box("Soket_kol_uc", cx + S / 2 + 0.01, cy + S / 2 + 0.002, TOP + 0.003, 0.012, 0.004, 0.004, P["frame"], r, 0.001)


def vrm(P, r):
    cx, cy = -0.03, 0.065
    # iki koyu soğutucu blok (sol ve üst), üstte ince yiv çizgileri
    for (x, y, sx, sy, along_x) in ((cx - 0.075, cy, 0.024, 0.11, False), (cx, cy + 0.075, 0.11, 0.024, True)):
        box("VRM_sogutucu", x, y, TOP, sx, sy, 0.02, P["sink"], r, 0.002)
        for k in range(4):
            o = -0.0075 + k * 0.005
            if along_x:
                box("VRM_yiv", x, y + o, TOP + 0.02, sx - 0.006, 0.0012, 0.0006, P["sink_accent"], r)
            else:
                box("VRM_yiv", x + o, y, TOP + 0.02, 0.0012, sy - 0.006, 0.0006, P["sink_accent"], r)
    # soğutucuların iç kenarında bobin sırası
    for i in range(5):
        box("VRM_bobin", cx - 0.056, cy - 0.036 + i * 0.016, TOP, 0.011, 0.011, 0.008, P["choke"], r, 0.001)
        box("VRM_bobin", cx - 0.036 + i * 0.016, cy + 0.056, TOP, 0.011, 0.011, 0.008, P["choke"], r, 0.001)
    # birkaç katı kondansatör
    for (x, y) in ((cx + 0.05, cy + 0.06), (cx + 0.058, cy + 0.06), (cx - 0.06, cy - 0.06), (cx - 0.06, cy - 0.052)):
        disc("Kondansator", x, y, TOP, 0.0035, 0.011, P["cap"], r, 12)
        disc("Kondansator_ust", x, y, TOP + 0.011, 0.0034, 0.0006, P["cap_top"], r, 12)


def ram_slots(P, r):
    cy = 0.065 - 0.005
    for i in range(4):
        rx = 0.075 + i * 0.018
        box("RAM_yuvasi", rx, cy, TOP, 0.008, 0.15, 0.011, P["ram"] if i % 2 == 0 else P["ram2"], r, 0.001)
        box("RAM_yuvasi_yarik", rx, cy, TOP + 0.011, 0.0025, 0.14, 0.0005, P["hole"], r)
        for e in (-1, 1):   # açık mandallar (bellek takılmamış)
            m = box("RAM_mandal", rx, cy + e * 0.079, TOP, 0.007, 0.006, 0.015, P["latch"], r, 0.001)
            m.rotation_euler.x = e * 0.35


def power(P, r):
    px, cy = 0.172 + 0.0045, 0.065 - 0.0055
    box("ATX_24pin", px, cy, TOP, 0.022, 0.112, 0.014, P["atx"], r, 0.0015)
    for k in range(12):
        for c in range(2):
            box("ATX_pin_delik", px - 0.0045 + c * 0.009, cy - 0.05 + k * 0.009, TOP + 0.014, 0.005, 0.005, 0.0005, P["hole"], r)


def chipset(P, r):
    x, y = 0.085, -0.075
    box("Yonga_seti_sogutucu", x, y, TOP, 0.054, 0.054, 0.008, P["sink"], r, 0.002)
    box("Yonga_seti_logo", x, y, TOP + 0.008, 0.03, 0.006, 0.0006, P["sink_accent"], r)


def expansion(P, r):
    for i, (length, py) in enumerate(((0.17, -0.025), (0.17, -0.085), (0.06, -0.135))):
        x0 = -0.2 + 0.035 + length / 2
        m = P["frame"] if i == 0 else P["pcie"]          # üst yuva metal takviyeli
        box("PCIe_yuvasi", x0, py, TOP, length, 0.009, 0.011, m, r, 0.001)
        box("PCIe_yuvasi_yarik", x0, py, TOP + 0.011, length - 0.008, 0.003, 0.0005, P["hole"], r)
        box("PCIe_mandal", x0 + length / 2 + 0.004, py, TOP, 0.008, 0.009, 0.013, P["latch"], r, 0.001)
    box("M2_sogutucu", -0.07, -0.055, TOP, 0.11, 0.02, 0.004, P["sink"], r, 0.0015)
    box("M2_sogutucu_cizgi", -0.07, -0.055, TOP + 0.004, 0.09, 0.003, 0.0005, P["sink_accent"], r)


def rear_io(P, r):
    # I/O bloğu kartın −x kenarından taşar (dünyada arka panele dayanır)
    box("IO_blok", -0.19, 0.06, TOP, 0.03, 0.165, 0.034, P["io"], r, 0.0015)
    box("IO_blok_ust", -0.19, 0.06, TOP + 0.034, 0.024, 0.155, 0.001, P["sink"], r)


def misc(P, r):
    disc("CMOS_pil", 0.02, -0.12, TOP, 0.011, 0.003, P["cap"], r, 24)
    for k in range(4):
        box("SATA_soket", 0.135 + (k % 2) * 0.022, -0.105 - (k // 2) * 0.03, TOP, 0.016, 0.01, 0.007, P["sata"], r, 0.001)
    # montaj vidaları: 6 deliğe vida başı
    for hx, hy in K["HOLES"]:
        disc("Kart_vidasi", hx, hy, TOP, 0.0075, 0.003, P["steel"], r, 16)
        box("Kart_vidasi_yiv", hx, hy, TOP + 0.003, 0.009, 0.0015, 0.0006, P["hole"], r)


def mounted_board(P, parent):
    """Kart kökü: yerel (u, v) → dünya (cx + BS·v, cy − BS·u), yani z ekseninde −90°."""
    cx, cy, _, _ = K["board_frame"]()
    r = H["link"](bpy.data.objects.new("Anakart", None), parent)
    r.location = (cx, cy, STANDOFF_TOP)
    r.rotation_euler = (0, 0, -math.pi / 2)
    r.scale = (BS, BS, BS)
    H["board"](P, r)
    for f in (cpu, vrm, ram_slots, power, chipset, expansion, rear_io, misc):
        f(P, r)
    return r


def anakartli_kasa(P, x=0.0, y=0.0):
    root = K["bos_kasa"](P, 0, 0)
    root.name = "Anakartli_kasa"
    for o in list(root.children):
        if o.name.startswith(("Kart_yeri_cizgi", "CPU_arka_aciklik")):
            bpy.data.objects.remove(o, do_unlink=True)
    # arka I/O kalkanı: açıklığın üstüne metal plaka
    for o in root.children:
        if o.name.startswith("IO_acikligi"):
            o.material_slots[0].link = "OBJECT"       # mesh önbellekte paylaşılıyor
            o.material_slots[0].material = P["io"]
    mounted_board(P, root)
    root.location = (x, y, 0)
    return root


def build(scene=None):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Anakartli_kasa")
    scene.collection.children.link(c)
    H["COLL"] = c
    tile_marks(P, 0, 0)
    return anakartli_kasa(P, 0, 0)


if __name__ == "__main__":
    build()
