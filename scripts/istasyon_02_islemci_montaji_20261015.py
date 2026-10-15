"""02 · İşlemci montaj istasyonu (2026-10-15): yerleşim taslağı v1.

Kaynak: docs/İstasyonlar/Anakart ve İşlemci - Giriş Çıkış Akışı.md
- Konveyörden anakartlı kasa gelir; ikmalden 3 girdi: modele uygun silikon çekirdek, işlemci
  taşıyıcısı, ısı yayıcı kapak.
- Tek montaj noktası: işlemci paketlenir (çekirdek + taşıyıcı + kapak) ve kasadaki anakarta takılır.
- Çıktı: işlemcili kasa → ana bant → 03 bellek ve depolama.

01 hücresiyle aynı iskelet (11 × 11 karo, ortadan paletli bant ve montaj durağı, iki yanda kızaklı
robot, 3 × 3 stok blokları, çit); ortak parçalar istasyon_01 betiğinden çağrılır, kopyalanmaz.

Yerleşim (x = bant akışı, y arka; merkez = montaj durağı):
- Arka (+y): silikon çekirdek (sol, seviyeler karışık) ve işlemci taşıyıcısı (sağ) blokları.
- Ön (−y): ısı yayıcı kapak (sol); ön sağda 2 × 2 işlemci paketleme presi (blok yerine). Arka robot
  çekirdek ve taşıyıcıyı prese, ön robot kapağı prese getirir; paketlenen işlemciyi ön robot
  duraktaki kasanın soketine takar.
- Çitte yalnız üç stok bloğunun dışında ikmal açıklığı.

Arka planda çalışır: blender -b --factory-startup --python bu_dosya (build() çağrısı)
"""
import math

import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
I1 = {"__name__": "istasyon_01_yardimci"}
exec(open(SCRIPTS + "/istasyon_01_anakart_montaji_20261015.py", encoding="utf-8").read(), I1)
A, H, KV = I1["A"], I1["H"], I1["KV"]
mat, box, disc, link = H["mat"], H["box"], H["disc"], H["link"]
COL_L, COL_R, BLOCK_Y = I1["COL_L"], I1["COL_R"], I1["BLOCK_Y"]
FENCE_X, FENCE_Y = I1["FENCE_X"], I1["FENCE_Y"]
load_collection, instance, tile_centers = I1["load_collection"], I1["instance"], I1["tile_centers"]

# girdi: (ad, [(blend, koleksiyon, adet), ...] doldurma sırasıyla, blok sol-alt köşe)
CEK = "silikon_cekirdek_20261015/silikon_cekirdek.blend"
INPUTS = [
    ("Silikon_cekirdek", [(CEK, "Silikon_cekirdek_temel", 3), (CEK, "Silikon_cekirdek_orta", 2),
                          (CEK, "Silikon_cekirdek_ust", 2)], (COL_L, BLOCK_Y)),
    ("Islemci_tasiyicisi", [("islemci_tasiyicisi_20261015/islemci_tasiyicisi.blend", "Islemci_tasiyicisi", 6)],
     (COL_R, BLOCK_Y)),
    ("Isi_yayici_kapak", [("isi_yayici_kapak_20261015/isi_yayici_kapak.blend", "Isi_yayici_kapak", 7)],
     (COL_L, -BLOCK_Y - 3)),
]
STOK_MODEL = {"Silikon_cekirdek": "silikon_cekirdek_temel", "Islemci_tasiyicisi": "islemci_tasiyicisi",
              "Isi_yayici_kapak": "isi_yayici_kapak"}
GELEN = ("Anakartli_kasa", "anakartli_kasa_20261015/anakartli_kasa.blend", "Anakartli_kasa")
CIKAN = ("Islemcili_kasa", "islemcili_kasa_20261015/islemcili_kasa.blend", "Islemcili_kasa")
PRESS = (COL_R + 1.5, -BLOCK_Y - 1.5)              # 2 × 2 pres merkezi (ön sağ bloğun ortası)
ROBOTS = ((1, -3.0), (-1, 1.5))                    # ön robot pres ile durak arasında


def yerlesim():
    """Oyunun dolduracağı yuvalar: 27 stok karosu (girdi başına 3 × 3, doldurma sırasıyla),
    montaj durağı ve pres yuvası (paketlenen işlemcinin durduğu yer). Çekirdek karolarında
    seviyeyi oyun seçer (model = temel; seviyeler alanında üçü)."""
    slots = []
    for name, _, (bx, by) in INPUTS:
        for k, (x, y) in enumerate(tile_centers(bx, by)):
            sl = dict(tur="stok", girdi=name, model=STOK_MODEL[name], sira=k, konum=[x, y, 0.006])
            if name == "Silikon_cekirdek":
                sl["seviyeler"] = ["silikon_cekirdek_" + s for s in ("temel", "orta", "ust")]
            slots.append(sl)
    slots.append(dict(tur="durak", model="palet", konum=[0.0, 0.0, KV["BELT_Z"] + KV["LIFT"]]))
    slots.append(dict(tur="pres", model=None, konum=[PRESS[0], PRESS[1], PRESS_TOP + 0.03]))
    return slots


def palette():
    P = I1["palette"]()
    P.update(
        press=mat("C_pres_govde", "#5E666D", 0.45, 0.3),
        press_frame=mat("C_pres_cerceve", A["R"]["RENK"]["kirmizi"], 0.45),
        press_steel=mat("B_celik", "#B9BFC3", 0.35, 0.8),
        nest=mat("C_pres_yuva", "#1D2125", 0.6),
        substrate=mat("C_tasiyici", "#2E7A43", 0.45),
        lid=mat("C_kapak_nikel", "#D3D8DB", 0.22, 0.9),
    )
    return P


# --- Stok bloğu karoları ve stok -----------------------------------------------------------------

def stock_tiles(P, root):
    for _, _, (bx, by) in INPUTS:
        for i in range(3):
            for j in range(3):
                H["tile_marks"](P, bx + 0.5 + i, by + 0.5 + j)
    for o in list(H["COLL"].objects):
        if o.parent is None and o.name.startswith("Karo_"):
            o.parent = root
            o.location.z += 0.006


def stock(P, root):
    colls = {}
    for name, parts, (bx, by) in INPUTS:
        tiles = iter(tile_centers(bx, by))
        for rel, cname, n in parts:
            if cname not in colls:
                colls[cname] = load_collection(rel, cname, cname)
            for _ in range(n):
                x, y = next(tiles)
                instance(colls[cname], name + "_stok", (x, y, 0.006), root)


# --- İşlemci paketleme presi (2 × 2) ------------------------------------------------------------

PRESS_TOP = 0.9          # tabla üstü


def press(P, root):
    px, py = PRESS
    r = link(bpy.data.objects.new("Paketleme_presi", None), root)
    r.location = (px, py, 0)
    # taban dolabı + tabla
    box("Pres_govde", 0, 0, 0, 1.5, 1.2, PRESS_TOP - 0.06, P["press"], r, 0.03)
    box("Pres_tabla", 0, 0, PRESS_TOP - 0.06, 1.6, 1.3, 0.06, P["press_steel"], r, 0.01)
    # kırmızı C çerçeve (arka yanda iki dikme + üst kiriş), pres başlığı ve silindir
    for x in (-0.55, 0.55):
        box("Pres_dikme", x, 0.45, PRESS_TOP, 0.16, 0.2, 1.0, P["press_frame"], r, 0.02)
    box("Pres_ust_kiris", 0, 0.2, PRESS_TOP + 1.0, 1.3, 0.7, 0.22, P["press_frame"], r, 0.03)
    disc("Pres_silindir", 0, 0.05, PRESS_TOP + 1.22, 0.16, 0.3, P["press_steel"], r, 32)
    disc("Pres_mil", 0, 0.05, PRESS_TOP + 0.55, 0.04, 0.45, P["press_steel"], r, 16)
    box("Pres_kafa", 0, 0.05, PRESS_TOP + 0.45, 0.3, 0.3, 0.1, P["press"], r, 0.01)
    # tabla üstünde yuva: taşıyıcı + kapak (paketlenmekte olan işlemci)
    box("Pres_yuva", 0, 0.05, PRESS_TOP, 0.36, 0.36, 0.03, P["nest"], r, 0.006)
    box("Yuvada_tasiyici", 0, 0.05, PRESS_TOP + 0.03, 0.2, 0.2, 0.012, P["substrate"], r, 0.002)
    box("Yuvada_kapak", 0, 0.05, PRESS_TOP + 0.042, 0.17, 0.17, 0.016, P["lid"], r, 0.004)
    # ön kenarda sarı güvenlik şeridi ve ışık perdesi dikmeleri
    box("Pres_serit", 0, -0.64, PRESS_TOP - 0.06, 1.6, 0.03, 0.062, P["walk"], r)
    for x in (-0.7, 0.7):
        box("Pres_perde", x, -0.55, PRESS_TOP, 0.06, 0.06, 0.6, P["curtain"], r, 0.008)
        box("Pres_perde_led", x, -0.55, PRESS_TOP + 0.55, 0.065, 0.065, 0.04, P["curtain_led"], r)
    return r


# --- Bant üstü: paletler -----------------------------------------------------------------------

def pallets(root, KP):
    gelen = load_collection(*GELEN[1:], GELEN[0])
    cikan = load_collection(*CIKAN[1:], CIKAN[0])
    for x, z, c, nm in ((0.0, KV["BELT_Z"] + KV["LIFT"], gelen, "durakta"),
                        (3.5, KV["BELT_Z"], cikan, "cikista"),
                        (-2.5, KV["BELT_Z"], gelen, "giriste")):
        p = KV["palet"](KP, "Palet_" + nm)
        p.location = (x, 0, z)
        p.parent = root
        e = instance(c, c.name + "_" + nm, (0, 0, KV["PAL_T"]), root)
        e.parent = p


# --- Çit ---------------------------------------------------------------------------------------

def fence(P, root):
    fl = I1["fence_line"]
    fl(P, root, -FENCE_X, FENCE_X, FENCE_Y, "x", [(COL_L, COL_L + 3), (COL_R, COL_R + 3)])
    fl(P, root, -FENCE_X, FENCE_X, -FENCE_Y, "x", [(COL_L, COL_L + 3)])
    for x in (-FENCE_X, FENCE_X):
        fl(P, root, -FENCE_Y, FENCE_Y, x, "y", [(-0.5, 0.5)])
        I1["belt_tunnel"](P, root, x)


def istasyon(P):
    root = link(bpy.data.objects.new("Istasyon_02_islemci_montaji", None))
    I1["floor"](P, root)
    stock_tiles(P, root)
    stock(P, root)
    KP = I1["belt"](root)
    pallets(root, KP)
    I1["ROBOTS"] = ROBOTS
    for side, x in ROBOTS:
        I1["sled"](P, root, side, x)
    press(P, root)
    fence(P, root)
    I1["controls"](P, root)          # dolaplar sağ köşelerde, HMI ön çitte kapak bloğu ile pres arasında
    return root


def build(scene=None):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Istasyon_02_islemci_montaji")
    scene.collection.children.link(c)
    H["COLL"] = c
    return istasyon(P)


if __name__ == "__main__":
    build()
