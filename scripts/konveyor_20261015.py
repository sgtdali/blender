"""Ana bant: paletli konveyör (2026-10-15). Bütün hatta kullanılır; modüller 3 × 3 karoya oturur.

Kullanıcı kararları:
- Tip: paletli bant. Kasa bir taşıyıcı palet üstünde gider; iki yandaki ince bantlar paleti taşır,
  istasyonda palet durdurucuyla yerinde durur.
- Modüller: düz parça (duz), 90° döner tabla (donus), montaj durağı (durak). Baş/son sonra.
- 15 Ekim: modül 3 × 3 karo (en küçük yapı 2 × 2). Taşıyan bant ortada 1 m; iki yandaki 1'er m yürüme yolu +
  0.7 m sarı korkuluk (dekoratif). Düz modül ve durak 3 m; döner tabla 3 × 3: ortada tabla, açık yanlarda 1 m bant
  kolu (`*_kol_<yön>`), kapalı yanlarda yürüme yolu + korkuluk (`*_kapali_<yön>`); oyun bağlantıya göre seçer.

Ölçüler (x = akış yönü, y = genişlik, z yukarı; modül merkezi karo merkezi):
- Bant üstü BELT_Z = 0.75 m (montaj masasıyla aynı seviye).
- İki bant arası eksen ±0.3; kenar profilleri ±0.36; toplam genişlik ~0.8 m (1 karoya sığar).
- Palet 0.72 × 0.66 m; kasa (0.64 × 0.56, yan yatık) paletin köşe takozları arasında durur.

duz(P) tek mesh modül, palet(P) tek mesh palet döndürür; başka betikler bunları çağırır.
Çıktı: output/konveyor_20261015/konveyor.blend
"""
import math

import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
OUT = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/output"
R = {"__name__": "robot_yardimci"}              # robotun yardımcıları (merge, motor profili, malzemeler)
exec(open(SCRIPTS + "/robot_20261015.py", encoding="utf-8").read(), R)
H = R["H"]
mat, box, link = H["mat"], H["box"], H["link"]
ydisc, merge = R["ydisc"], R["merge"]

MOD_L = 3.0                    # modül boyu / genişliği (3 karo)
WALK_T = 0.04                  # yürüme yolu sacı kalınlığı
RAIL_H = 0.7                   # korkuluk üst borusu (kullanıcı: 0.7 m)
RAIL_E = 1.45                  # korkuluğun modül merkezine uzaklığı (dış kenar)
BELT_Z = 0.75                  # bant üstü
BELT_Y = 0.3                   # bant eksenleri ±
BELT_W, BELT_T = 0.05, 0.01    # bant genişliği, kalınlığı
PROF_Y = 0.36                  # kenar profili ekseni ±
PROF_W, PROF_H = 0.06, 0.11    # profil kesiti
GUIDE_H = 0.03                 # palet kılavuzu bant üstünden yüksekliği
PAL_L, PAL_W, PAL_T = 0.72, 0.66, 0.03
CASE_L, CASE_D = 0.64, 0.56    # bos_kasa ölçüsü (x, y)


def palette():
    P = R["palette"]()
    P.update(
        profile=mat("K_profil", "#9AA1A7", 0.35, 0.7),
        slot=mat("K_profil_kanal", "#3A4046", 0.6),
        belt=mat("K_bant", "#1D2125", 0.75),
        guide=mat("K_kilavuz", "#C5CBCE", 0.3, 0.8),
        leg=mat("K_ayak", "#6B7278", 0.45, 0.5),
        pallet=mat("K_palet", "#C5CBCE", 0.45, 0.3),
        wear=mat("K_palet_asinma", "#2C3238", 0.7),
        locator=mat("K_palet_takoz", R["RENK"]["kirmizi"], 0.45),
        stop=mat("K_sari", R["RENK"]["sari"], 0.5),
        led_green=mat("K_led_yesil", "#39C45A", 0.4, 0.0, 2.0),
        walk=mat("K_yurume_yolu", "#4A5057", 0.85),
        tread=mat("K_yurume_dis", "#3A3F45", 0.9),
    )
    return P


# --- Düz modül ---------------------------------------------------------------------------------

def duz(P, name="Konveyor_duz"):
    """3 × 3 düz modül; x = −1.5..1.5. Ortada bant, iki yanda yürüme yolu + korkuluk. Art arda dizilince
    bant, yol ve korkuluk kesintisiz sürer."""
    return merge(name, duz_parts(P) + yanlar(P))


def bant(P, name="Konveyor_bant_1m", L=1.0):
    """Yalnız taşıyan bant (yürüme yolu/korkuluk yok), L m; istasyonların iç bandı için."""
    return merge(name, duz_parts(P, L))


def yol(P, x, y, lx, ly, edge=None):
    """Yürüme yolu sacı (x, y merkez, lx × ly); edge = (eksen, işaret): banda bakan kenarda sarı şerit."""
    s = [box("Yol_saci", x, y, 0, lx, ly, WALK_T, P["walk"], None, 0.004)]
    along_x = lx >= ly
    n = int(round((lx if along_x else ly) / 0.25))
    for k in range(n):                                # kaymaz diş çizgileri
        t = -0.5 + (k + 0.5) / n
        if along_x:
            s.append(box("Yol_dis", x + t * lx, y, WALK_T, 0.03, ly - 0.16, 0.004, P["tread"], None))
        else:
            s.append(box("Yol_dis", x, y + t * ly, WALK_T, lx - 0.16, 0.03, 0.004, P["tread"], None))
    if edge:
        ax, sg = edge
        if ax == "y":
            s.append(box("Yol_serit", x, y + sg * (ly / 2 - 0.04), WALK_T, lx, 0.06, 0.003, P["stop"], None))
        else:
            s.append(box("Yol_serit", x + sg * (lx / 2 - 0.04), y, WALK_T, 0.06, ly, 0.003, P["stop"], None))
    return s


def korkuluk(P, a, b, posts):
    """Eksene paralel sarı korkuluk a → b (x, y): üst boru, ara boru, etek sacı; `posts` direk konumları."""
    (x0, y0), (x1, y1) = a, b
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    lx, ly = abs(x1 - x0) or 0.045, abs(y1 - y0) or 0.045
    s = [box("Korkuluk_ust", cx, cy, RAIL_H - 0.045, lx, ly, 0.045, P["stop"], None, 0.01),
         box("Korkuluk_ara", cx, cy, RAIL_H * 0.5, lx, ly, 0.035, P["stop"], None, 0.008),
         box("Korkuluk_etek", cx, cy, WALK_T, lx if lx > 0.05 else 0.012, ly if ly > 0.05 else 0.012, 0.1, P["stop"], None)]
    for px, py in posts:
        s.append(box("Korkuluk_direk", px, py, WALK_T, 0.05, 0.05, RAIL_H - WALK_T, P["stop"], None, 0.008))
        s.append(box("Korkuluk_taban", px, py, WALK_T, 0.11, 0.11, 0.01, P["leg"], None, 0.003))
    return s


def yanlar(P, L=MOD_L):
    """Düz modülün iki yanı: bandın dışında 1'er m yürüme yolu, dış kenarda korkuluk (direkler modül
    içinde, uçlarda değil: yan yana modüllerde çift direk olmaz)."""
    s = []
    for sy in (-1, 1):
        s += yol(P, 0, sy * 1.0, L, 1.0, ("y", -sy))
        s += korkuluk(P, (-L / 2, sy * RAIL_E), (L / 2, sy * RAIL_E), [(x, sy * RAIL_E) for x in (-1.0, 0.0, 1.0)])
    return s


def duz_parts(P, L=MOD_L):
    zt = BELT_Z - BELT_T                         # profil üstü
    s = []
    for sy in (-1, 1):
        y = sy * PROF_Y
        # alüminyum profil: gövde + dış yüzde T-kanal çizgileri
        s.append(box("Profil", 0, y, zt - PROF_H, L, PROF_W, PROF_H, P["profile"], None, 0.006))
        for z in (zt - 0.035, zt - 0.075):
            s.append(box("Profil_kanal", 0, y + sy * (PROF_W / 2 + 0.0005), z, L, 0.002, 0.012, P["slot"], None))
        # bant taşıyıcı kızak + bant (profilin iç kenarında)
        yb = sy * BELT_Y
        s.append(box("Bant_kizak", 0, yb, zt - 0.03, L, BELT_W + 0.02, 0.03, P["profile"], None, 0.004))
        s.append(box("Bant", 0, yb, zt, L, BELT_W, BELT_T, P["belt"], None))
        s.append(box("Bant_donus", 0, yb, zt - PROF_H + 0.01, L, BELT_W, BELT_T, P["belt"], None))
        # palet kılavuzu: bandın dış yanında alçak çelik dudak
        s.append(box("Palet_kilavuzu", 0, sy * (PAL_W / 2 + 0.012), zt, L, 0.012, BELT_T + GUIDE_H, P["guide"], None, 0.003))
        # modül eki: uçlarda bağlantı plakası (dizilince birleşim yeri belli olur)
        for ex in (-1, 1):
            s.append(box("Ek_plakasi", ex * (L / 2 - 0.02), y + sy * (PROF_W / 2 + 0.002), zt - 0.09, 0.04, 0.004, 0.08, P["leg"], None))
    # ara traversler ve ayaklar: her metrede (karo merkezlerinde) bir çift, ayar pabuçlu, alt çapraz
    for k in range(int(round(L))):
        x0 = -L / 2 + k + 0.5
        for x in (x0 - 0.3, x0 + 0.3):
            s.append(box("Travers", x, 0, zt - PROF_H + 0.02, 0.05, 2 * PROF_Y - PROF_W, 0.05, P["leg"], None, 0.004))
        for sy in (-1, 1):
            y = sy * PROF_Y
            s.append(box("Ayak", x0, y, 0.03, 0.06, 0.06, zt - PROF_H - 0.03, P["leg"], None, 0.005))
            s.append(box("Ayak_pabuc", x0, y, 0, 0.12, 0.12, 0.012, P["leg"], None, 0.004))
            s.append(box("Ayak_mil", x0, y, 0.012, 0.025, 0.025, 0.02, P["steel"], None))
        s.append(box("Ayak_capraz", x0, 0, 0.2, 0.05, 2 * PROF_Y, 0.05, P["leg"], None, 0.004))
    return s


# --- Montaj durağı -----------------------------------------------------------------------------

LIFT = 0.012                   # durakta paletin bantlardan kaldırılma yüksekliği


def durak(P, name="Konveyor_durak", sides=True, L=MOD_L):
    """3 m montaj durağı (3 × 3, yanları düz modül gibi): düz parça + kırmızı durdurucu (paletin ön burcuna dayanır), kaldırma/konumlama
    ünitesi (palet LIFT kadar kalkar, iki pim konum burçlarına girer), palet sensörü, köşede ışık kulesi.
    Palet durakta merkezde (x = 0) durur."""
    zt = BELT_Z - BELT_T
    s = duz_parts(P, L) + (yanlar(P, L) if sides else [])   # sides=False, L=1: istasyon içi durak
    # durdurucu: bantların arasında, paletin ön burcunun hemen önünde yükselmiş kırmızı piston
    xs = PAL_L / 2 + 0.03
    s.append(box("Durdurucu_govde", xs, 0, zt - PROF_H + 0.02, 0.08, 0.1, PROF_H - 0.05, P["slot"], None, 0.008))
    s.append(box("Durdurucu", xs, 0, zt - 0.03, 0.05, 0.08, 0.05 + LIFT, P["locator"], None, 0.008))
    # kaldırma/konumlama ünitesi: ortada koyu plaka + pnömatik silindir + iki konum pimi
    s.append(box("Kaldirma_silindiri", 0, 0, zt - PROF_H - 0.08, 0.12, 0.12, 0.1, P["profile"], None, 0.01))
    s.append(box("Kaldirma_plakasi", 0, 0, zt - 0.02, 0.62, 0.36, 0.02 + LIFT - 0.002, P["slot"], None, 0.006))
    for sx in (-1, 1):
        s.append(R["zdisc"]("Konum_pimi", sx * 0.28, 0, zt + LIFT - 0.002, 0.014, 0.03, P["steel"], 12))
    # palet sensörü: profilin dışında, yeşil ışıklı
    sy = -1
    ys = sy * (PROF_Y + PROF_W / 2 + 0.025)
    s.append(box("Sensor_konsol", 0.15, ys, zt - 0.06, 0.04, 0.05, 0.06, P["leg"], None, 0.004))
    s.append(box("Sensor", 0.15, ys, zt, 0.05, 0.04, 0.035, P["slot"], None, 0.006))
    s.append(box("Sensor_led", 0.15, ys + sy * 0.021, zt + 0.012, 0.016, 0.003, 0.012, P["led_green"], None))
    # ışık kulesi: arka köşede (oyun kamerasından paleti örtmesin) direk + yeşil/sarı/kırmızı
    tx, ty = 0.42, PROF_Y + PROF_W / 2 + 0.06
    s.append(box("Kule_ayak", tx, ty, 0, 0.1, 0.1, 0.012, P["leg"], None, 0.004))
    s.append(R["zdisc"]("Kule_direk", tx, ty, 0.012, 0.018, 1.25, P["leg"], 12))
    for k, m in enumerate((P["led_green"], P["stop"], P["locator"])):
        s.append(R["zdisc"]("Kule_isik", tx, ty, 1.26 + k * 0.075, 0.045, 0.07, m, 20))
    s.append(R["zdisc"]("Kule_kapak", tx, ty, 1.485, 0.047, 0.015, P["slot"], 20))
    return merge(name, s)


# --- Palet -------------------------------------------------------------------------------------

def palet(P, name="Palet"):
    """Taşıyıcı palet; merkez orijinde, alt yüzü z = 0 (bant üstüne oturur)."""
    s = [box("Palet_plaka", 0, 0, 0.008, PAL_L, PAL_W, PAL_T - 0.008, P["pallet"], None, 0.012)]
    # alt aşınma şeritleri: bantların üstüne oturur
    for sy in (-1, 1):
        s.append(box("Palet_asinma", 0, sy * BELT_Y, 0, PAL_L - 0.04, BELT_W + 0.01, 0.008, P["wear"], None))
    # kasa köşe takozları (L), kırmızı
    t, a = 0.03, 0.09
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (CASE_L / 2 + t / 2), sy * (CASE_D / 2 + t / 2)
            s.append(box("Kose_takozu", x, y - sy * (a / 2 - t / 2), PAL_T, t, a, 0.04, P["locator"], None, 0.006))
            s.append(box("Kose_takozu", x - sx * (a / 2 - t / 2), y, PAL_T, a, t, 0.04, P["locator"], None, 0.006))
    # durdurucu burcu (ön kenarda) ve konum delikleri
    s.append(box("Durdurucu_burcu", PAL_L / 2 - 0.03, 0, -0.02, 0.05, 0.12, 0.028, P["wear"], None, 0.006))
    for sx in (-1, 1):
        s.append(R["zdisc"]("Konum_burcu", sx * 0.28, 0, PAL_T - 0.001, 0.02, 0.003, P["steel"], 16))
    return merge(name, s)


# --- 90° dönüş: döner tabla ---------------------------------------------------------------------

TT_R = 0.45                    # döner tabla yarıçapı
TT_Z = 0.58                    # döner tabla altı
FRAME_Z = 0.54                 # sabit çerçeve üstü


def donus(P, name="Konveyor_donus"):
    """3 × 3 modül; ortada 1 × 1 karo döner tabla. Sabit gövde (çerçeve, yatak, motor) + döner tabla (ayrı obje, çocuk;
    orijini merkezde: rotation_euler.z ile döner). Tabla 0°'de bant x yönünde; palet gelir, tabla
    90° döner, palet yeni yöne çıkar. Hangi iki kenarı bağlayacağı yerleştirirken döndürülerek seçilir."""
    zt = BELT_Z - BELT_T
    h = 0.43                                    # ayak/çerçeve yarım ölçüsü
    s = []
    for sx in (-1, 1):                          # kare çerçeve
        s.append(box("Cerceve", sx * h, 0, FRAME_Z - 0.06, 0.06, 2 * h + 0.06, 0.06, P["profile"], None, 0.006))
        s.append(box("Cerceve", 0, sx * h, FRAME_Z - 0.06, 2 * h - 0.06, 0.06, 0.06, P["profile"], None, 0.006))
    s.append(box("Cerceve_capraz", 0, 0, FRAME_Z - 0.06, 2 * h, 0.08, 0.05, P["leg"], None, 0.004))
    s.append(box("Cerceve_capraz", 0, 0, FRAME_Z - 0.06, 0.08, 2 * h, 0.05, P["leg"], None, 0.004))
    for sx in (-1, 1):                          # köşe ayakları
        for sy in (-1, 1):
            s.append(box("Ayak", sx * h, sy * h, 0.03, 0.06, 0.06, FRAME_Z - 0.09, P["leg"], None, 0.005))
            s.append(box("Ayak_pabuc", sx * h, sy * h, 0, 0.12, 0.12, 0.012, P["leg"], None, 0.004))
            s.append(box("Ayak_mil", sx * h, sy * h, 0.012, 0.025, 0.025, 0.02, P["steel"], None))
    for sy in (-1, 1):
        s.append(box("Ayak_capraz", 0, sy * h, 0.2, 2 * h, 0.05, 0.05, P["leg"], None, 0.004))
    # döner yatak bileziği
    s.append(R["zdisc"]("Doner_yatak", 0, 0, FRAME_Z - 0.01, 0.4, TT_Z - FRAME_Z + 0.01, P["slot"], 48))
    # tahrik motoru: çerçevenin altına asılı (dönen bant profilleri üstünden geçebilsin), sarı kapaklı
    mx, my = 0.22, -0.22
    zf = FRAME_Z - 0.06                          # çerçeve altı
    s.append(box("Motor_sanziman", mx, my, zf - 0.06, 0.14, 0.14, 0.06, P["slot"], None, 0.01))
    s.append(R["zmotor"]("Tabla_motoru", mx, my, zf - 0.21, 0.06, 0.15, P["motor"]))
    s.append(R["zmotor"]("Tabla_motoru_kapak", mx, my, zf - 0.235, 0.062, 0.025, P["stop"]))
    # köşe karoları: yalnız yürüme yolu (korkuluk kapalı yanlarla gelir; açık yanda komşu modülün yoluna bağlanır)
    for sx in (-1, 1):
        for sy in (-1, 1):
            s += yol(P, sx * 1.0, sy * 1.0, 1.0, 1.0)
    base = merge(name, s)
    # yan karolar: açık yanda 1 m bant kolu; kapalı yanda yol + o kenar boyunca (3 m) korkuluk.
    # Oyun bağlantıya göre birini gösterir. Düğüm orijini yan karonun merkezi, yerel +x dışarı.
    for tag, rz in (("xp", 0.0), ("yp", math.pi / 2), ("xn", math.pi), ("yn", -math.pi / 2)):
        arm = merge(name + "_kol_" + tag, duz_parts(P, 1.0))
        e = RAIL_E - 1.0
        closed = merge(name + "_kapali_" + tag,
                       yol(P, 0, 0, 1.0, 1.0) + korkuluk(P, (e, -1.5), (e, 1.5), [(e, y) for y in (-1.45, -0.5, 0.5, 1.45)]))
        for o in (arm, closed):
            o.location = (round(math.cos(rz)), round(math.sin(rz)), 0)
            o.rotation_euler.z = rz
            o.parent = base

    # döner tabla: disk + kısa çift bant + kılavuz + durdurucu
    t = [
        R["zdisc"]("Tabla_disk", 0, 0, TT_Z, TT_R, 0.025, P["profile"], 64),
        R["zdisc"]("Tabla_kenar", 0, 0, TT_Z + 0.025, TT_R, 0.006, P["stop"], 64),
        R["zdisc"]("Tabla_ic", 0, 0, TT_Z + 0.025, TT_R - 0.035, 0.007, P["profile"], 64),
    ]
    L = 0.84
    zb = TT_Z + 0.031                           # disk üstü
    for sy in (-1, 1):
        y = sy * PROF_Y
        t.append(box("Profil", 0, y, zb, L, PROF_W, zt - zb, P["profile"], None, 0.006))
        t.append(box("Profil_kanal", 0, y + sy * (PROF_W / 2 + 0.0005), zt - 0.05, L, 0.002, 0.012, P["slot"], None))
        t.append(box("Bant", 0, sy * BELT_Y, zt, L, BELT_W, BELT_T, P["belt"], None))
        t.append(box("Bant_kizak", 0, sy * BELT_Y, zt - 0.03, L, BELT_W + 0.02, 0.03, P["profile"], None, 0.004))
        t.append(box("Palet_kilavuzu", 0, sy * (PAL_W / 2 + 0.012), zt, L, 0.012, BELT_T + GUIDE_H, P["guide"], None, 0.003))
    t.append(box("Tabla_durdurucu", 0.3, 0, zt - 0.03, 0.04, 0.1, 0.05, P["locator"], None, 0.006))
    table = merge(name + "_tablasi", t)
    table.parent = base
    return base, table


# --- Önizleme / dosya ---------------------------------------------------------------------------

def load_case():
    with bpy.data.libraries.load(OUT + "/anakartli_kasa_20261015/anakartli_kasa.blend", link=False) as (src, dst):
        dst.collections = ["Anakartli_kasa"]
    c = dst.collections[0]
    for o in list(c.all_objects):
        if o.name.startswith("Karo_"):
            bpy.data.objects.remove(o, do_unlink=True)
    return c


def build(scene=None):
    """Önizleme: L hat (3 × 3 modüller) — x yönünde düz, montaj durağı, düz; köşede döner tabla
    (−x ve +y kolları açık); +y yönünde 2 düz."""
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Konveyor")
    scene.collection.children.link(c)
    H["COLL"] = c
    for gx in range(-7, 5):
        for gy in range(-1, 8):
            if gy <= 1 or gx >= 2:
                H["tile_marks"](P, gx, gy)
    cells = [((-6, 0), 0), ((-3, 0), 0), ((0, 0), 0), ((3, 3), math.pi / 2), ((3, 6), math.pi / 2)]
    for i, ((x, y), rz) in enumerate(cells):
        m = durak(P, "Konveyor_durak") if i == 1 else duz(P, "Konveyor_duz")
        m.location = (x, y, 0)
        m.rotation_euler.z = rz
    base, table = donus(P, "Konveyor_donus")
    base.location = (3, 0, 0)
    for o in base.children:
        if "_kol_" in o.name or "_kapali_" in o.name:
            tag = o.name.split("_")[-1].split(".")[0]
            o.hide_viewport = o.hide_render = ("_kol_" in o.name) != (tag in ("xn", "yp"))
    table.rotation_euler.z = math.radians(45)          # örnek: palet dönüş halinde
    kasa = load_case()

    def pallet_at(x, y, rz, full=True, parent=None, z=BELT_Z):
        p = palet(P, "Palet")
        p.location = (x, y, z)
        p.rotation_euler.z = rz
        if parent:
            p.parent = parent
        if full:
            e = link(bpy.data.objects.new("Anakartli_kasa", None))
            e.instance_type = "COLLECTION"
            e.instance_collection = kasa
            e.location = (0, 0, PAL_T)
            e.parent = p
        return p

    pallet_at(-3, 0, 0, z=BELT_Z + LIFT)                # durakta, kaldırılmış
    pallet_at(-4.1, 0, 0, full=False)                   # durağa gelen boş palet
    pallet_at(0, 0, 0, parent=table, z=BELT_Z)          # tabla üstünde, tablayla birlikte döner
    pallet_at(3, 5.5, math.pi / 2, full=False)
    return c

if __name__ == "__main__":
    build()
