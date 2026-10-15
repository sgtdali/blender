"""İşlemcili kasa (2026-10-15): 02 işlemci montajının çıktısı, 03 bellek ve depolamanın girdisi.

anakartli_kasa_20261015'in aynısı; yalnız sokette işlemci var: yeşil taşıyıcı üstünde gümüş ısı
yayıcı kapak (02'nin girdileri), tutucu çerçeve kapalı, kol inik ve kilitli. RAM/PCIe boş.

Çıktı: output/islemcili_kasa_20261015/islemcili_kasa.blend
"""
import math

import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
AK = {"__name__": "anakartli_kasa_yardimci"}
exec(open(SCRIPTS + "/anakartli_kasa_20261015.py", encoding="utf-8").read(), AK)
H = AK["H"]
mat, box, tile_marks = H["mat"], H["box"], H["tile_marks"]
TOP = AK["TOP"]


def palette():
    P = AK["palette"]()
    P.update(
        substrate=mat("C_tasiyici", "#2E7A43", 0.45),
        lid=mat("C_kapak_nikel", "#D3D8DB", 0.22, 0.9),
        lid_edge=mat("C_kapak_kenar", "#9AA1A6", 0.3, 0.85),
    )
    return P


def cpu_takili(P, r):
    """Soket + takılı işlemci (kart çizim birimi). Kol kapalı: sağ kenar boyunca yatık."""
    cx, cy = -0.03, 0.065
    S = 0.09
    box("Soket", cx, cy, TOP, S, S, 0.007, P["socket"], r, 0.001)
    box("Islemci_tasiyici", cx, cy, TOP + 0.007, 0.064, 0.064, 0.0025, P["substrate"], r, 0.0005)
    box("Islemci_kapak_flans", cx, cy, TOP + 0.0095, 0.058, 0.058, 0.002, P["lid_edge"], r, 0.0008)
    box("Islemci_kapak", cx, cy, TOP + 0.0115, 0.048, 0.048, 0.0025, P["lid"], r, 0.0008)
    # tutucu çerçeve kapalı: kapağın kenarlarına basar
    t = 0.008
    for (x, y, sx, sy) in ((cx, cy + S / 2 - t / 2, S, t), (cx, cy - S / 2 + t / 2, S, t),
                           (cx - S / 2 + t / 2, cy, t, S - 2 * t), (cx + S / 2 - t / 2, cy, t, S - 2 * t)):
        box("Soket_cerceve", x, y, TOP + 0.007, sx, sy, 0.006, P["frame"], r, 0.0008)
    box("Soket_kol", cx + S / 2 + 0.006, cy, TOP + 0.003, 0.004, S, 0.004, P["frame"], r, 0.001)
    box("Soket_kol_uc", cx + S / 2 + 0.01, cy - S / 2 - 0.002, TOP + 0.003, 0.012, 0.004, 0.004, P["frame"], r, 0.001)


AK["cpu"] = cpu_takili          # mounted_board bu adı çağırır


def islemcili_kasa(P, x=0.0, y=0.0):
    root = AK["anakartli_kasa"](P, x, y)
    root.name = "Islemcili_kasa"
    return root


def build(scene=None):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Islemcili_kasa")
    scene.collection.children.link(c)
    H["COLL"] = c
    tile_marks(P, 0, 0)
    return islemcili_kasa(P, 0, 0)


if __name__ == "__main__":
    build()
