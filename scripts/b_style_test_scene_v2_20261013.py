"""B tarzı deneme sahnesi v2 (2026-10-13): Production Line istasyon kalıbı.

Karar (kullanıcı): istasyonun içinde malzeme ilerlemez. Her istasyon =
  bantta sabit bir İŞ NOKTASI (kasa durur) + orada işi yapan ekipman (operatör, robot kol,
  üst portal) + çevresinde PARÇA BAŞINA BİR STOK ALANI.
SMT, fırın gibi üretim makineleri ana hatta değil, ayrı yerel üretim tesislerindedir.

Stok kuralı (kullanıcı, 2026-10-13): her stok BİRİMİ bir 1×1 m oyun karosu kaplar (palet/araba
boyunda kap) ve bir alt parça en çok 9 birim tutar, yani alt parça başına 3×3 m'lik stok bloğu.
İstasyonlar geniş düşünülür: 1. istasyon (anakart & işlemci) 6 blok, 2. istasyon (bellek &
depolama) 3 blok. Sahne 26 × 20 m salon köşesi; düz ana bant boydan boya.
İkmal (rayli_ikmal.md, ray_halkasi.md): tek yönlü kapalı monoray halkası istasyonların arkasından
banda paralel geçer (ray 3.15 m, sepet seyahati 2.12 m). Her istasyonun arkasında bir indirme
noktası var: sepet teslim masasına iner, kısa makaralı bant çitteki açıklıktan istasyona girer.
Bant ve karolar oyun hücrelerinin ortasına hizalıdır (Blender tam sayıları = hücre kenarları;
sahne merkezi Godot'ta (20, 0, 12)). Bantta kasalar ilerledikçe dolar: boş → anakart+CPU → +RAM/SSD.
Yardımcılar (bant, raf, pano, taralı alan, ışık, kamera) v1 betiğinden gelir.
"""
import math

import bpy

V1 = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts/b_style_test_scene_20261013.py"
_v1 = {"__name__": "v1"}
exec(open(V1, encoding="utf-8").read(), _v1)
# v1'in yardımcıları kendi ad alanlarının global'lerini kullanır (COLL, _MATS ...).
box, cyl, strip, mat = _v1["box"], _v1["cyl"], _v1["strip"], _v1["mat"]
OUT = _v1["ROOT"] + "/blender/output/b_tarzi_deneme_20261013"
GAME_GLB = _v1["ROOT"] + "/prosedürel/assets/models/b_style_test/b_style_test_scene_v2.glb"
BELT_Z = _v1["BELT_Z"]
LINE_Y = 0.5  # bant bir hücre sırasının ortasında
HALL = dict(x_min=-13.0, x_max=13.0, y_back=10.0, y_front=-10.0)
RAIL_Z = 3.15
RAIL_OUT, RAIL_RET = 7.5, 8.7  # halkanın istasyon önünden geçen ve dönen kolları (y)
TRAVEL_Z = 2.12


# --- Ürün: yan yatmış, kapağı açık kasa; aşamaya göre dolar -------------------------------

def pc_case(x, P, stage):
    """stage 0 boş, 1 anakart+CPU takılı, 2 + RAM ve SSD."""
    y, z = LINE_Y, BELT_Z
    box("Kasa_govde", x, y, z, 0.46, 0.44, 0.2, P["dark"], 0.012)
    box("Kasa_ic", x, y, z + 0.2, 0.42, 0.40, 0.004, P["mid"], 0)
    box("Kasa_on_panel", x + 0.22, y, z, 0.03, 0.44, 0.21, P["light"], 0.006)
    if stage >= 1:
        box("Kasa_anakart", x - 0.02, y + 0.02, z + 0.2, 0.3, 0.3, 0.012, P["green"], 0.003)
        box("Kasa_cpu", x - 0.02, y + 0.05, z + 0.212, 0.08, 0.08, 0.02, P["steel"], 0.004)
    if stage >= 2:
        for dy in (-0.08, -0.05):
            box("Kasa_ram", x + 0.08, y + dy, z + 0.212, 0.13, 0.012, 0.03, P["rubber"], 0.002)
        box("Kasa_ssd", x - 0.1, y - 0.1, z + 0.212, 0.08, 0.06, 0.008, P["white"], 0.002)


# --- İş noktası ---------------------------------------------------------------------------

def gantry(x, P, sign_mat, w=4.0, h=3.2, half_d=1.3):
    """İş noktasının portalı: dikmeler iki yandaki koridorlarda, üstte kiriş ızgarası, ışık panosu,
    asılı alet dengeleyicileri, büyük tabela ve ışık kulesi."""
    for dx in (-w / 2, w / 2):
        for dy in (-half_d, half_d):
            box("Portal_dikme", x + dx, LINE_Y + dy, 0, 0.2, 0.2, h, P["blue"], 0.015)
            box("Portal_taban", x + dx, LINE_Y + dy, 0, 0.4, 0.4, 0.03, P["dark"], 0.006)
        box("Portal_kiris_y", x + dx, LINE_Y, h - 0.18, 0.2, 2 * half_d + 0.2, 0.2, P["blue"], 0.015)
    for dy in (-half_d, 0.0, half_d):
        box("Portal_kiris_x", x, LINE_Y + dy, h - 0.16, w + 0.2, 0.16, 0.16, P["blue"], 0.012)
    for dy in (-0.55, 0.55):
        box("Portal_lamba", x, LINE_Y + dy, h - 0.26, w - 0.6, 0.3, 0.06, P["lamp"], 0.012)
    for dx, dy in ((-0.8, -0.3), (0.8, 0.3)):  # alet dengeleyicileri
        box("Dengeleyici", x + dx, LINE_Y + dy, h - 0.42, 0.18, 0.18, 0.22, P["yellow"], 0.02)
        cyl("Alet_kablo", x + dx, LINE_Y + dy, (h - 0.42 + 1.35) / 2, 0.012, h - 0.42 - 1.35, P["dark"])
        box("Alet", x + dx, LINE_Y + dy, 1.15, 0.1, 0.1, 0.2, P["dark"], 0.01)
    box("Tabela", x, LINE_Y - half_d - 0.12, h - 0.1, 1.6, 0.06, 0.6, sign_mat, 0.02)
    box("Tabela_simge", x - 0.45, LINE_Y - half_d - 0.155, h + 0.03, 0.36, 0.01, 0.36, P["white"], 0)
    box("Tabela_cizgi", x + 0.25, LINE_Y - half_d - 0.155, h + 0.12, 0.7, 0.01, 0.07, P["white"], 0)
    box("Tabela_cizgi", x + 0.15, LINE_Y - half_d - 0.155, h + 0.0, 0.5, 0.01, 0.07, P["white"], 0)
    _v1["light_tower"](x + w / 2, LINE_Y - half_d, h, P)
    for dx in (-0.35, 0.35):  # bant üstünde durdurucu kollar
        box("Durdurucu", x + dx, LINE_Y + 0.42, BELT_Z - 0.05, 0.06, 0.08, 0.14, P["yellow"], 0.008)
    # Zemin plakası: iş noktasının altında koyu, sarı kenarlı çelik plaka (4 × 3 karo)
    plate = mat("B_celik_plaka", "#3B4248", 0.45, 0.6)
    strip("Is_plakasi", x, LINE_Y, w, 2 * half_d + 0.2, plate, 0.004)
    edge = P["yellow"]
    for sx, sy, ox, oy in ((w, 0.08, 0, half_d + 0.1), (w, 0.08, 0, -half_d - 0.1),
                           (0.08, 2 * half_d + 0.2, w / 2, 0), (0.08, 2 * half_d + 0.2, -w / 2, 0)):
        strip("Is_plakasi_kenar", x + ox, LINE_Y + oy, sx, sy, edge, 0.005)


def control_desk(x, y, P):
    """Kontrol pultu: eğik ekranlı ayaklı pano, kameraya bakar."""
    box("Pult_ayak", x, y, 0, 0.3, 0.3, 0.9, P["mid"], 0.01)
    box("Pult_taban", x, y, 0, 0.5, 0.5, 0.03, P["dark"], 0.005)
    d = box("Pult", x, y, 0.9, 0.7, 0.45, 0.28, P["white"], 0.02)
    d.rotation_euler.x = -0.35
    e = box("Pult_ekran", x, y - 0.12, 1.05, 0.5, 0.02, 0.2, P["screen"], 0)
    e.rotation_euler.x = -0.35
    for i, k in enumerate(("lamp_grn", "lamp_red")):
        cyl("Pult_dugme", x + 0.25, y - 0.2 + i * 0.0, 1.12 + i * 0.0, 0.03, 0.03, P[k])


def link_between(name, p0, p1, thick, m):
    """p0→p1 arasında kalınlığı `thick` olan kutu bağlantı (kol parçası)."""
    from mathutils import Vector
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    ob = box(name, 0, 0, 0, thick, thick, d.length, m, 0.025)
    ob.location = (p0 + p1) / 2
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    return ob


def robot_arm(x, y, P, reach_rz=math.pi, k=1.0):
    """Beyaz-mavi altı eksenli kol, tabanı (x, y); `reach_rz` yönünde bant üstüne uzanır, `k` ölçek."""
    c, s = math.cos(reach_rz), math.sin(reach_rz)
    axis = "X" if abs(s) > 0.5 else "Y"
    box("Robot_kaide", x, y, 0, 0.6 * k, 0.6 * k, 0.14 * k, P["dark"], 0.01)
    cyl("Robot_govde", x, y, 0.38 * k, 0.2 * k, 0.5 * k, P["white"])
    shoulder = (x, y, 0.7 * k)
    elbow = (x - c * 0.15 * k, y - s * 0.15 * k, 1.5 * k)
    wrist = (x + c * 1.0, y + s * 1.0, 1.25 * k)
    tool = (x + c * 1.0, y + s * 1.0, BELT_Z + 0.45)
    cyl("Robot_omuz", *shoulder, 0.17 * k, 0.34 * k, P["blue"], axis=axis)
    link_between("Robot_ust_kol", shoulder, elbow, 0.19 * k, P["white"])
    cyl("Robot_dirsek", *elbow, 0.13 * k, 0.28 * k, P["blue"], axis=axis)
    link_between("Robot_on_kol", elbow, wrist, 0.15 * k, P["white"])
    cyl("Robot_bilek", *wrist, 0.09 * k, 0.2 * k, P["blue"], axis=axis)
    link_between("Robot_tutucu", wrist, tool, 0.11 * k, P["dark"])


# --- Stok: birim = 1 karo, alt parça = 3×3 blok ------------------------------------------

def stock_unit(x, y, P, kind):
    """Bir stok birimi, karonun ortasında ~0.9 m'lik kap: parçanın gerçek taşıma kabı."""
    if kind == "pcb":  # ESD rafı: koyu kasa, içinde dikey yeşil kartlar
        box("Pcb_raf", x, y, 0, 0.86, 0.7, 0.55, P["dark"], 0.015)
        for i in range(12):
            box("Pcb", x - 0.36 + i * 0.065, y, 0.55, 0.014, 0.6, 0.3, P["green"], 0.003)
    elif kind == "bins":  # elektronik set: istif mavi plastik kasalar
        for k in range(3):
            box("Bilesen_kasa", x, y, k * 0.3, 0.8, 0.6, 0.28, P["blue"], 0.02)
        box("Bilesen_ic", x, y, 0.9, 0.7, 0.5, 0.004, P["yellow"], 0)
    elif kind in ("carton", "ssd", "hdd"):  # palet üstünde koliler / kutular
        box("Palet", x, y, 0, 0.9, 0.9, 0.13, P["wood"], 0.01)
        m = {"carton": (P["card"], P["card_dark"]), "ssd": (P["white"], P["light"]),
             "hdd": (P["steel"], P["light"])}[kind]
        for k in range(2):
            for dx in (-0.21, 0.21):
                for dy in (-0.21, 0.21):
                    box("Koli", x + dx, y + dy, 0.13 + k * 0.33, 0.4, 0.4, 0.32,
                        m[(k + (dx > 0) + (dy > 0)) % 2], 0.012)
    elif kind in ("core", "carrier", "ram"):  # tepsi arabası
        box("Araba", x, y, 0.15, 0.86, 0.66, 0.04, P["mid"], 0.008)
        for dx in (-0.38, 0.38):
            for dy in (-0.28, 0.28):
                cyl("Araba_teker", x + dx, y + dy, 0.07, 0.065, 0.045, P["rubber"], axis="Y")
        box("Araba_kol", x - 0.42, y, 0.19, 0.035, 0.62, 0.8, P["blue"], 0.008)
        tray = {"core": P["rubber"], "carrier": mat("B_tepsi_yesil", "#2F6B4C", 0.6),
                "ram": P["rubber"]}[kind]
        for i in range(10):
            box("Tepsi", x + 0.02, y, 0.19 + i * 0.05, 0.76, 0.6, 0.045, tray, 0.006)
        top = 0.69
        if kind == "core":
            for dx in (-0.25, 0.0, 0.25):
                for dy in (-0.18, 0.0, 0.18):
                    box("Cekirdek", x + 0.02 + dx, y + dy, top, 0.12, 0.12, 0.01, P["steel"], 0.002)
        elif kind == "ram":
            for dy in (-0.2, -0.1, 0.0, 0.1, 0.2):
                box("Ram", x + 0.02, y + dy, top, 0.62, 0.05, 0.015, P["green"], 0.003)
    elif kind == "lid":  # tel kafes kutu (gitterbox), içinde çelik kapak yığını
        box("Kafes_taban", x, y, 0, 0.88, 0.7, 0.12, P["mid"], 0.008)
        box("Kafes", x, y, 0.12, 0.84, 0.66, 0.6, P["mesh"], 0.01)
        box("Kapak_yigin", x, y, 0.72, 0.7, 0.52, 0.02, P["steel"], 0.004)


def stock_block(x0, y0, P, kind, count):
    """Bir alt parçanın stoğu: 3×3 karo, karo başına bir birim; (x0, y0) blok merkezi.
    Boş karolar köşe işaretleriyle, blok sarı çerçeveyle belli olur."""
    edge = mat("B_stok_cizgi", "#E3B11F", 0.5)
    mark = mat("B_stok_bos", "#C9CED1", 0.6)
    for i in range(9):
        tx, ty = x0 + (i % 3 - 1), y0 + (i // 3 - 1)
        if i < count:
            stock_unit(tx, ty, P, kind)
        else:
            for cx in (-0.38, 0.38):
                for cy in (-0.38, 0.38):
                    strip("Bos_kose", tx + cx, ty + cy, 0.14 if cx < 0 else 0.14, 0.04, mark, 0.004)
                    strip("Bos_kose", tx + cx, ty + cy, 0.04, 0.14, mark, 0.004)
    t = 0.06
    for sx, sy, ox, oy in ((3, t, 0, 1.5), (3, t, 0, -1.5), (t, 3, 1.5, 0), (t, 3, -1.5, 0)):
        strip("Stok_blok_cizgi", x0 + ox, y0 + oy, sx, sy, edge)


def zone(x, y, sx, sy, P):
    """İstasyon ayak izinin zemin çerçevesi: açık gri boyalı çizgi."""
    edge = mat("B_istasyon_cizgi", "#D9DDDF", 0.6)
    t = 0.07
    strip("Bolge", x, y + sy / 2, sx, t, edge)
    strip("Bolge", x, y - sy / 2, sx, t, edge)
    strip("Bolge", x - sx / 2, y, t, sy, edge)
    strip("Bolge", x + sx / 2, y, t, sy, edge)


def bollard(x, y, P):
    """Sarı çarpma direği (koruma babası), 1 m."""
    cyl("Baba", x, y, 0.5, 0.07, 1.0, P["yellow"])
    cyl("Baba_bant", x, y, 0.85, 0.072, 0.08, P["dark"])
    cyl("Baba_taban", x, y, 0.01, 0.12, 0.02, P["dark"])


def station_fence(x0, x1, y0, y1, P, h=1.2):
    """Görüşü kapatmayan çevre: kameradan uzak kenarda (+y) alçak tel çit, uzak köşelerde kısa yan
    parçalar; kameraya bakan kenarda (-y) yalnız köşe direkleri. Bant girip çıktığı yerde açık."""
    gap = 0.6  # bant ve koridor geçişi için kenarlardan boşluk
    xm = (x0 + x1) / 2  # arka ortada ikmal bandı için 1.2 m açıklık
    i = 0.12  # çit ve babalar alan çizgisinin hemen içinde, komşu hücreye taşmaz
    _v1["fence"](x0 + gap, y1 - i, xm - 0.6, y1 - i, P, h=h)
    _v1["fence"](xm + 0.6, y1 - i, x1 - gap, y1 - i, P, h=h)
    for xe in (x0 + i, x1 - i):
        _v1["fence"](xe, y1 - i - 2.6, xe, y1 - i, P, h=h)
    for xb in (x0 + i, x1 - i):
        bollard(xb, y0 + i, P)
    for xb in (x0 + 3.5, x1 - 3.5):
        bollard(xb, y0 + i, P)


# --- Monoray ikmali ------------------------------------------------------------------------

def rail_segment(x0, y0, x1, y1, P):
    """Düz ray parçası: I profil kiriş, alt yüzü RAIL_Z'de."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    lx, ly = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (lx, 0.1) if lx > ly else (0.1, ly)
    box("Ray", cx, cy, RAIL_Z, sx, sy, 0.18, P["mid"], 0.01)
    fx, fy = (lx, 0.22) if lx > ly else (0.22, ly)
    box("Ray_flans", cx, cy, RAIL_Z, fx, fy, 0.03, P["dark"], 0.004)


def monorail_loop(x0, x1, P):
    """Kapalı halka: istasyonların arkasında iki paralel kol ve uçlarda U dönüşler; sarı askılar."""
    rail_segment(x0, RAIL_OUT, x1, RAIL_OUT, P)
    rail_segment(x0, RAIL_RET, x1, RAIL_RET, P)
    r = (RAIL_RET - RAIL_OUT) / 2
    yc = (RAIL_OUT + RAIL_RET) / 2
    for xe, sgn in ((x0, -1), (x1, 1)):
        n = 8
        for i in range(n):
            a0, a1 = math.pi * i / n, math.pi * (i + 1) / n
            p0 = (xe + sgn * r * math.sin(a0), yc - r * math.cos(a0))
            p1 = (xe + sgn * r * math.sin(a1), yc - r * math.cos(a1))
            link = _v1["box"]("Ray_donus", 0, 0, 0, 0.1, 0.1, 0.18, P["mid"], 0)
            link.scale.x = math.dist(p0, p1) / 0.1 + 0.2
            link.location = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, RAIL_Z + 0.09)
            link.rotation_euler.z = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    x = x0
    while x <= x1:
        box("Ray_askisi", x, yc, 0, 0.16, 0.16, RAIL_Z + 0.35, P["yellow"], 0.01)
        box("Ray_askisi_taban", x, yc, 0, 0.36, 0.36, 0.03, P["dark"], 0.005)
        box("Ray_kol", x, yc, RAIL_Z + 0.18, 0.12, RAIL_RET - RAIL_OUT + 0.3, 0.14, P["yellow"], 0.01)
        x += 4.0


def basket(x, y, z, P, load):
    """Mavi ikmal sepeti (z = sepet tabanı) ve içindeki yükün rengi."""
    box("Sepet", x, y, z, 0.8, 0.6, 0.4, P["blue"], 0.02)
    box("Sepet_yuk", x, y, z + 0.4, 0.68, 0.48, 0.06, load, 0.01)


def trolley(x, y, P, basket_z, load):
    """Raydaki taşıyıcı, halatlarla asılı sepet."""
    box("Tasiyici", x, y, RAIL_Z - 0.3, 0.55, 0.3, 0.3, P["dark"], 0.02)
    box("Tasiyici_isik", x + 0.28, y, RAIL_Z - 0.2, 0.01, 0.12, 0.06, P["lamp_yel"], 0)
    top = basket_z + 0.46
    for dx in (-0.3, 0.3):
        cyl("Halat", x + dx, y, (RAIL_Z - 0.3 + top) / 2, 0.012, RAIL_Z - 0.3 - top, P["dark"])
    basket(x, y, basket_z, P, load)


def drop_point(x, P, delivering, load):
    """İstasyonun indirme noktası: halkanın altında teslim masası, sarı kılavuz direkleri, taralı
    zemin; masadan istasyona kısa makaralı bant. `delivering` ise sepet masaya inmiş durumdadır."""
    y = RAIL_OUT
    _v1["hatch"](x, y, 2.0, 1.6, P)
    for dx in (-0.75, 0.75):
        box("Kilavuz", x + dx, y + 0.45, 0, 0.1, 0.1, RAIL_Z - 0.35, P["yellow"], 0.01)
    box("Kilavuz_kiris", x, y + 0.45, RAIL_Z - 0.45, 1.6, 0.1, 0.1, P["yellow"], 0.01)
    box("Teslim_masasi", x, y, 0.0, 1.0, 0.8, BELT_Z, P["mid"], 0.01)
    box("Teslim_masasi_ust", x, y, BELT_Z, 1.04, 0.84, 0.04, P["steel"], 0.006)
    _v1["conveyor"](x, y - 0.42, x, LINE_Y + 4.6, P, items=False)
    box("Tabela_ikmal", x + 0.8, y + 0.45, 2.2, 0.04, 0.5, 0.35, P["blue"], 0.01)
    trolley(x, y, P, BELT_Z + 0.04 if delivering else TRAVEL_Z, load)


def station(x, P, sign, robot, far, near, operator_dx=-0.3, margin=1.0):
    """Sabit iş noktası istasyonu, merkez x. `far`/`near`: (tür, adet) blokları, bandın uzak (+y) ve
    yakın (-y) yanında 1 m aralıklı 3×3 m bloklar; bantla bloklar arasında 1 m çalışma koridoru."""
    n = max(len(far), len(near))
    width = n * 3 + (n - 1) + margin  # margin 0: alan tam blok sınırında (oyun ayak izi)
    top = 4.5 if far else 1.5
    bottom = 4.5 if near else 1.5
    zone(x, LINE_Y + (top - bottom) / 2, width, top + bottom, P)
    station_fence(x - width / 2, x + width / 2, LINE_Y - bottom, LINE_Y + top, P)
    gantry(x, P, sign)
    # Robotlar bandın iki yanındaki koridor hücrelerinde, operatör ve pult yakın koridorda.
    if robot:
        robot_arm(x + 0.9, LINE_Y + 1.0, P, reach_rz=-math.pi / 2, k=1.25)
    robot_arm(x - 0.9, LINE_Y - 1.0, P, reach_rz=math.pi / 2, k=1.25)
    _v1["operator"](x + 0.6 + operator_dx, LINE_Y - 0.95, P)
    control_desk(x + 1.6, LINE_Y - 1.0, P)
    for row, side in ((far, 1), (near, -1)):
        x0 = x - (len(row) - 1) * 2.0
        for i, (kind, count) in enumerate(row):
            stock_block(x0 + i * 4.0, LINE_Y + side * 3.0, P, kind, count)


# --- Salon ---------------------------------------------------------------------------------

def hall(P, x_min, x_max, y_back, y_front):
    """Arka (+y) ve sağ (+x) duvar, pencere bandı, lambalar, raflar ve panolar (v1'in duvar dili)."""
    H = 3.6
    cx, cy = (x_min + x_max) / 2, (y_back + y_front) / 2
    lx, ly = x_max - x_min, y_back - y_front
    box("Duvar_arka", cx, y_back + 0.1, 0, lx + 0.4, 0.2, H, P["wall"], 0)
    box("Duvar_arka_alt", cx, y_back - 0.01, 0, lx, 0.02, 1.1, P["wall_low"], 0)
    box("Duvar_sag", x_max + 0.1, cy, 0, 0.2, ly, H, P["wall"], 0)
    box("Duvar_sag_alt", x_max - 0.01, cy, 0, 0.02, ly, 1.1, P["wall_low"], 0)
    t = x_min + 0.6
    while t < x_max:
        box("Duvar_derz", t, y_back - 0.005, 1.1, 0.012, 0.01, H - 1.1, P["mid"], 0)
        t += 1.2
    t = y_front + 0.6
    while t < y_back:
        box("Duvar_derz", x_max - 0.005, t, 1.1, 0.01, 0.012, H - 1.1, P["mid"], 0)
        t += 1.2
    box("Pencere", cx, y_back - 0.008, 2.75, lx - 1, 0.01, 0.6, P["window"], 0)
    box("Pencere", x_max - 0.008, cy, 2.75, 0.01, ly - 1, 0.6, P["window"], 0)
    t = x_min + 1.5
    while t < x_max - 1:
        box("Duvar_lamba", t, y_back - 0.04, 2.45, 1.2, 0.06, 0.06, P["lamp"], 0.01)
        t += 3.0
    t = y_front + 1.5
    while t < y_back - 1:
        box("Duvar_lamba", x_max - 0.04, t, 2.45, 0.06, 1.2, 0.06, P["lamp"], 0.01)
        t += 3.0
    for i, py in enumerate((-3.5, -4.35, -5.2)):
        _v1["cabinet"](x_max - 0.28, py, P, window=(i % 2 == 0))
    _v1["hatch"](x_max - 1.15, -4.35, 1.3, 2.6, P)


def build():
    v1 = _v1
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    v1["_MATS"].clear()
    v1["_MESHES"].clear()
    sc = bpy.context.scene
    v1["COLL"] = sc.collection
    P = v1["palette"]()

    ns = {"__name__": "floor"}
    exec(open(v1["FLOOR_SCRIPT"], encoding="utf-8").read(), ns)
    fv = next(x for x in ns["VARIANTS"] if x["name"] == "2_eskimis_beton")
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    fl = bpy.context.active_object
    fl.name = "Zemin"
    fl.scale = (60, 44, 1)
    bpy.ops.object.transform_apply(scale=True)
    fl.data.materials.append(ns["floor_mat"](fv))

    hall(P, **HALL)
    y_line = P["yellow"]
    strip("Yol", -0.5, LINE_Y - 5.3, 25.0, 0.08, y_line)
    strip("Yol", -0.5, RAIL_RET + 0.8, 25.0, 0.08, y_line)

    # Monoray halkası ve istasyonların indirme noktaları; bir sepet 1. istasyona iniyor,
    # bir sepet halkada yolda.
    monorail_loop(-12.0, 12.0, P)
    drop_point(-6.5, P, True, P["green"])
    drop_point(6.5, P, False, P["white"])
    trolley(0.5, RAIL_RET, P, TRAVEL_Z, P["card"])

    # Ana bant boydan boya; kasalar dolu/boş aşamalarıyla
    v1["conveyor"](-12.9, LINE_Y, 12.9, LINE_Y, P, items=False)
    for cx, stage in ((-12.2, 0), (-11.0, 0), (-6.5, 1), (-1.4, 1), (-0.2, 1), (6.5, 2), (11.0, 2), (12.2, 2)):
        pc_case(cx, P, stage)

    # 1. istasyon: anakart & işlemci, altı alt parça = altı 3×3 blok.
    station(-6.5, P, mat("B_tabela_turuncu", "#E2702A", 0.5), True,
            far=[("pcb", 7), ("bins", 9), ("carton", 3)],
            near=[("core", 6), ("carrier", 2), ("lid", 8)])
    # 2. istasyon: bellek & depolama, üç alt parça.
    station(6.5, P, mat("B_tabela_mavi", "#2F6DB5", 0.45), False,
            far=[("ram", 8), ("ssd", 5), ("hdd", 0)], near=[], operator_dx=0.2)

    v1["camera_and_light"](sc)
    cam = sc.camera
    cam.data.ortho_scale = 30.0
    tgt = bpy.data.objects["Kamera_hedef"]
    tgt.location = (-0.5, LINE_Y + 2.5, 0)
    cam.location = (tgt.location.x - 9.0, tgt.location.y - 14.0,
                    math.hypot(9.0, 14.0) * math.tan(math.radians(30)))
    for lo in [o for o in bpy.data.objects if o.name.startswith("Tavan")]:
        lo.location.x *= 2.4
        lo.location.y = lo.location.y * 1.2 + LINE_Y


def render(name="v2"):
    import os
    os.makedirs(OUT, exist_ok=True)
    bpy.context.scene.render.filepath = f"{OUT}/{name}.png"
    bpy.ops.render.render(write_still=True)


def export_glb(path=GAME_GLB):
    _v1["export_glb"](path)


if __name__ == "__main__":
    build()
    render()
