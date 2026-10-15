"""Robot ray arabası ve zemin rayı (2026-10-15): robot_20261015 bunun üstünde çalışır.

Kullanıcı kararı: robot istasyonlarda raylı arabanın üstünde durur (7. eksen); taban plakasının
son hali araba üstünde görülerek karar verilecek.

Izgara: oyun 1 × 1 m karolarla kurulur.
- Kızak 1.5 karo (1.5 m) genişliğinde, karo sayısı kadar uzun (ray(P, ad, karo_sayısı)); ray
  ekseni ortada. Kremayer, raylar, araba ve kablo kanalı bu genişliğin içinde kalır.
- Araba tablası 1 × 1 m; ray boyunca kayar.

Ray (y kesiti, karo içinde): ortada koyu kiriş, y = ±0.3'te iki lineer kılavuz ray, −y kenarında
dişli kremayer, +y kenarında kablo zinciri kanalı. Uçlarda sarı stoplar.
Araba: dört rulman bloğu, beyaz tabla + koyu yan etekler (camgöbeği şerit), −y tarafında kare
profilli sürücü motoru (pinyonu kremayerde), +y tarafında kablo zinciri bağlantısı, ±x uçlarında
sarı tamponlar. Araba tek mesh; robot arabaya bağlanır (araba kayınca robot da gider).

Çıktı: output/robot_arabasi_20261015/robot_arabasi.blend
"""
import math

import bmesh
import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
R = {"__name__": "robot_yardimci"}
exec(open(SCRIPTS + "/robot_20261015.py", encoding="utf-8").read(), R)
H = R["H"]
mat, box, link = H["mat"], H["box"], H["link"]
zdisc, ydisc, zmotor, merge = R["zdisc"], R["ydisc"], R["zmotor"], R["merge"]

BEAM_H = 0.12                  # ray kirişi üstü
GUIDE_Y, GUIDE_H = 0.3, 0.045  # kılavuz raylar
RACK_Y = -0.58                 # kremayer (kızağın ön şeridinde, koruma kapağı altında)
COVER_H = 0.2                  # kremayer kapağının üstü
CHAIN_Y = 0.62                 # kablo kanalı ekseni: arabanın yanında, kızağın içinde
SLED_W = 1.5                   # kızağın toplam genişliği (1.5 karo; ray ekseni ortada)
CH_FLOOR = 0.025               # kanal tabanı üstü
LINK_P, LINK_W, LINK_H = 0.075, 0.12, 0.075  # zincir baklası: adım, genişlik, yükseklik
BEND_R = 0.16                  # zincirin dönüş yarıçapı
CHAIN_LEN = 2.6                # zincir boyu (arabanın gezme aralığını karşılar)
CAR_LINK_X = 0.4               # zincirin arabaya bağlandığı yer (araba yerelinde x)
BLOCK_H = 0.07                 # rulman bloğu
DECK = 1.0                     # tabla kenarı (1 karo)
DECK_T = 0.08
DECK_Z = BEAM_H + GUIDE_H + BLOCK_H          # tabla altı
DECK_TOP = DECK_Z + DECK_T                   # robotun oturduğu yükseklik


def palette():
    P = R["palette"]()
    P.update(
        beam=mat("A_ray_kirisi", "#3A4046", 0.6),
        stop=mat("A_stop_sari", R["RENK"]["sari"], 0.5),
        chain=mat("A_kablo_zinciri", "#1D2125", 0.7),
        cover=mat("A_koruma_kapagi", "#C5CBCE", 0.5),
    )
    return P


# --- Ray --------------------------------------------------------------------------------------

def ray(P, name="Robot_rayi", tiles=4):
    """x = 0'dan başlayıp tiles karo boyunca uzanan ray; y ekseninde karo ortası 0."""
    L = float(tiles)
    cx = L / 2
    s = [
        box("Ray_kirisi", cx, 0, 0, L - 0.04, 0.84, BEAM_H, P["beam"], None, 0.012),
    ]
    # kızak zemin plakası: tüm genişlik (kremayer, raylar, kablo kanalı), kenarlarda sarı şerit
    s.append(box("Kizak_plakasi", cx, 0, 0, L - 0.02, SLED_W, 0.02, P["beam"], None, 0.005))
    for sy in (-1, 1):
        s.append(box("Kizak_serit", cx, sy * (SLED_W / 2 - 0.04), 0.02, L - 0.12, 0.04, 0.003, P["stop"], None))
    for sy in (-1, 1):
        s.append(box("Kilavuz_ray", cx, sy * GUIDE_Y, BEAM_H, L - 0.12, 0.1, GUIDE_H, P["steel"], None, 0.006))
    # kremayer: koruma kapağının altında (görünmez); kapak üstünde pinyon milinin geçtiği fırçalı yarık
    s.append(box("Kremayer_kapagi", cx, RACK_Y, 0.02, L - 0.12, 0.16, COVER_H - 0.02, P["cover"], None, 0.02))
    s.append(box("Kapak_yarigi", cx, RACK_Y, COVER_H, L - 0.24, 0.03, 0.002, P["rubber"], None))
    for x in (0.12, L - 0.12):
        s.append(box("Kapak_uc", x, RACK_Y, 0.02, 0.04, 0.165, COVER_H - 0.015, P["stop"], None, 0.01))
    # kablo kanalı: rayın +y yanında U profil (taban rayın kirişine bağlı)
    s.append(box("Kablo_kanali_taban", cx, (0.42 + CHAIN_Y + 0.085) / 2, 0, L - 0.04, CHAIN_Y + 0.085 - 0.42, CH_FLOOR, P["beam"], None, 0.006))
    for dy in (-0.08, 0.08):
        s.append(box("Kablo_kanali_duvar", cx, CHAIN_Y + dy, 0, L - 0.04, 0.012, 0.13, P["beam"], None, 0.004))
    # zincirin sabit ucu: rayın ortasında kanal tabanına bağlı, kablolar aşağı iner
    s.append(box("Zincir_sabit_uc", L / 2 - 0.06, CHAIN_Y, CH_FLOOR, 0.1, LINK_W + 0.02, 0.05, P["joint"], None, 0.01))
    # uç stopları
    for x in (0.06, L - 0.06):
        s.append(box("Ray_stop", x, 0, BEAM_H, 0.1, 0.78, 0.12, P["stop"], None, 0.015))
        for sy in (-1, 1):
            s.append(box("Stop_tampon", x + (0.06 if x < 1 else -0.06), sy * GUIDE_Y, BEAM_H + 0.03, 0.03, 0.13, 0.07, P["rubber"], None, 0.01))
    return merge(name, s)


# --- Araba ------------------------------------------------------------------------------------

def araba(P, name="Robot_arabasi"):
    """Araba merkezi orijinde (ray ekseninde, x boyunca kayar); üstü DECK_TOP."""
    h = DECK / 2
    s = []
    # rulman blokları: kılavuz rayları sarar
    for sx in (-1, 1):
        for sy in (-1, 1):
            s.append(box("Rulman_blogu", sx * 0.32, sy * GUIDE_Y, BEAM_H + 0.02, 0.2, 0.16, GUIDE_H + BLOCK_H - 0.02, P["joint"], None, 0.012))
    # tabla
    s.append(box("Araba_tabla", 0, 0, DECK_Z, DECK, DECK, DECK_T, P["body"], None, 0.02))
    # yan etekler (y kenarlarında), camgöbeği şerit
    for sy in (-1, 1):
        s.append(box("Araba_etek", 0, sy * (h - 0.015), DECK_Z - 0.09, DECK - 0.04, 0.03, 0.1, P["joint"], None, 0.008))
        s.append(box("Araba_serit", 0, sy * (h + 0.001), DECK_Z + 0.025, DECK - 0.1, 0.004, 0.03, P["accent"], None))
    # sarı tamponlar (hareket yönü ±x)
    for sx in (-1, 1):
        s.append(box("Araba_tampon", sx * (h + 0.025), 0, DECK_Z - 0.04, 0.05, DECK - 0.16, 0.1, P["stop"], None, 0.015))
    # sürücü motoru (−y): tablanın yanındaki konsolda, kremayer kapağının üstünde; mili yarıktan iner
    mx, my = 0.3, RACK_Y
    y0, y1 = -h + 0.03, my - 0.105                       # tabla kenarından motorun dış kenarına
    s.append(box("Motor_konsolu", mx, (y0 + y1) / 2, DECK_Z, 0.22, y0 - y1, DECK_T, P["joint"], None, 0.015))
    s.append(box("Surucu_sanziman", mx, my, DECK_Z + DECK_T, 0.2, 0.2, 0.1, P["joint"], None, 0.015))
    s.append(zmotor("Surucu_motor", mx, my, DECK_TOP + 0.1, 0.085, 0.2, P["motor"]))
    s.append(zmotor("Surucu_motor_kapak", mx, my, DECK_TOP + 0.3, 0.088, 0.03, P["accent"]))
    s.append(box("Pinyon_mil", mx, my, COVER_H - 0.02, 0.025, 0.025, DECK_Z - COVER_H + 0.02, P["steel"], None))
    # kablo zinciri bağlantı kolu (+y): tablanın yanından kanalın üstüne uzanır, zincirin üst ucu buna bağlanır
    zt = CH_FLOOR + LINK_H + 2 * BEND_R - LINK_H / 2          # zincir üst kolunun alt yüzü
    s.append(box("Zincir_kolu", CAR_LINK_X, h + 0.02, DECK_Z, 0.12, 0.04, zt - DECK_Z, P["joint"], None, 0.006))
    s.append(box("Zincir_kolu_ust", CAR_LINK_X, (h + CHAIN_Y) / 2 + 0.03, zt - 0.03, 0.14, CHAIN_Y - h + 0.1, 0.03, P["joint"], None, 0.006))
    # köşe bağlantı cıvataları (robot tabanı için)
    for sx in (-1, 1):
        for sy in (-1, 1):
            s.append(zdisc("Tabla_civata", sx * 0.44, sy * 0.44, DECK_TOP, 0.025, 0.012, P["steel"], 12))
    return merge(name, s)


# --- Kablo zinciri -----------------------------------------------------------------------------

def stadium_plate(name, L, Hh, t, m, n=8):
    """Yuvarlak uçlu yan plaka (x boyu L, z yüksekliği Hh, y kalınlığı t); merkez orijinde."""
    r, c = Hh / 2, L / 2 - Hh / 2
    pts = []
    for i in range(n + 1):                                   # sağ yarım daire
        a = -math.pi / 2 + math.pi * i / n
        pts.append((c + r * math.cos(a), r * math.sin(a)))
    for i in range(n + 1):                                   # sol yarım daire
        a = math.pi / 2 + math.pi * i / n
        pts.append((-c + r * math.cos(a), r * math.sin(a)))
    bm = bmesh.new()
    f0 = [bm.verts.new((x, -t / 2, z)) for x, z in pts]
    f1 = [bm.verts.new((x, t / 2, z)) for x, z in pts]
    bm.faces.new(f0)
    bm.faces.new(list(reversed(f1)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((f0[i], f0[j], f1[j], f1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def chain_link(P, outer):
    """Tek bakla (x zincir boyu, y genişlik, z yükseklik): iki yan plaka, üst/alt köprüler.
    Baklalar bir dış bir iç: dış baklanın plakaları komşularının üstüne biner, uçlarında pim."""
    t = 0.012
    w = LINK_W / 2 - t / 2 + (t if outer else 0.0)
    s = []
    for sy in (-1, 1):
        pl = stadium_plate("Bakla_plaka", LINK_P * 1.4, LINK_H, t, P["chain"])
        pl.location = (0, sy * w, 0)
        s.append(pl)
        if outer:
            for ex in (-1, 1):
                s.append(ydisc("Bakla_pim", ex * LINK_P * 0.5, sy * (w + t / 2 + 0.002), 0, 0.013, 0.004, P["joint"], 12))
        else:
            s.append(ydisc("Bakla_delik", 0, sy * (w + t / 2 + 0.001), 0, 0.016, 0.002, P["joint"], 14))
    for z in (LINK_H / 2 - 0.014, -LINK_H / 2 + 0.002):
        s.append(box("Bakla_kopru", 0, 0, z, 0.028, LINK_W - 2 * t, 0.012, P["chain"], None))
    return merge("Zincir_bakla_" + ("dis" if outer else "ic"), s)


def kablo_zinciri(P, name, x_fix, x_car, length=CHAIN_LEN):
    """Alt kol kanal tabanında x_fix'ten dönüşe (+x), U dönüş, üst kol dönüşten arabanın bağlantı
    noktasına (x_car) geri gelir. Zincir boyu sabit: dönüş noktası araba konumuna göre kayar."""
    z0 = CH_FLOOR + LINK_H / 2
    xb = (length - math.pi * BEND_R + x_fix + x_car) / 2          # dönüşün başladığı x
    l1, l2 = xb - x_fix, math.pi * BEND_R
    total = l1 + l2 + (xb - x_car)
    protos = (chain_link(P, False), chain_link(P, True))
    parts = []
    for i in range(int(total / LINK_P)):
        u = (i + 0.5) * LINK_P
        if u < l1:
            x, z, th = x_fix + u, z0, 0.0
        elif u < l1 + l2:
            a = (u - l1) / BEND_R                               # 0 → π
            x, z, th = xb + BEND_R * math.sin(a), z0 + BEND_R - BEND_R * math.cos(a), a
        else:
            x, z, th = xb - (u - l1 - l2), z0 + 2 * BEND_R, math.pi
        o = link(bpy.data.objects.new("Bakla", protos[i % 2].data))
        o.location = (x, CHAIN_Y, z)
        o.rotation_euler.y = -th
        parts.append(o)
    for pr in protos:
        bpy.data.objects.remove(pr, do_unlink=True)
    return merge(name, parts)


# --- Önizleme / dosya ---------------------------------------------------------------------------

def build(scene=None, tiles=4, carriage_x=2.0, with_robot=True):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Robot_arabasi")
    scene.collection.children.link(c)
    H["COLL"] = c
    for k in range(tiles):
        H["tile_marks"](P, k + 0.5, 0)
    rail = ray(P, "Robot_rayi", tiles)
    car = araba(P, "Robot_arabasi")
    car.location = (carriage_x, 0, 0)
    kablo_zinciri(P, "Kablo_zinciri", tiles / 2, carriage_x + CAR_LINK_X)
    if with_robot:
        rb = R["robot"](P, "Robot", None, (0, 0, DECK_TOP), plate=False)
        rb.parent = car
    return rail, car


if __name__ == "__main__":
    build()
