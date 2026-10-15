"""01 · Anakart montaj istasyonu (2026-10-15): yerleşim taslağı v2.

Kaynak: docs/İstasyonlar/Anakart ve İşlemci - Giriş Çıkış Akışı.md
- İkmalden 4 girdi: boş kasa, anakart PCB, elektronik bileşen seti, soket ve bağlantı seti.
- Tek montaj noktası; konveyörden kasa girmez, ana bant bu istasyondan başlar.
- Çıktı: anakartı takılmış kasa → konveyör → 02 işlemci montajı.

Kullanıcı kararları (15 Ekim 2026):
- Ana bant istasyonun ortasından kesintisiz geçer: paletli konveyör (konveyor_20261015), 15 × 1 m
  modül; ortadaki modül montaj durağı (palet durur, kalkar; robotlar montajı palet üstünde yapar).
- Bandın iki yanında banda paralel birer robot rayı (7. eksen); her robot kendi tarafındaki
  iki stok bloğuna kayarak gider, durağa döner.
- Her girdi için 3 × 3 stok karosu (1 × 1 m, karoda tek birim) → 36 karo.

Yerleşim (x sağ = bant akışı, y arka; oyun kamerası −x, −y'den bakar; merkez = montaj durağı):
- Arka (+y): boş kasa (sol) ve PCB (sağ) blokları; ön (−y): elektronik bileşen (sol) ve soket
  seti (sağ) blokları. Raylar bant ile bloklar arasında.
- Çit hücreyi çevreler: sol/sağda bant tünelleri, her bloğun dış kenarında ışık perdeli ikmal
  açıklığı. Robot kontrol dolapları sağda, operatör paneli önde, çitin dışında.

Stok birimleri ve çıktı kendi .blend dosyalarından koleksiyon örneği (instance) olarak gelir.
Bant modülleri konveyor_20261015'ten çağrılır. Robotlar oyunun kendi robotu ve raylı kızağıdır
(robot_20261015 / robot_arabasi_20261015; bu dosyalardan çağrılır, kopyalanmaz).

Arka planda çalışır: blender -b --factory-startup --python bu_dosya (build() çağrısı)
"""
import math

import bmesh
import bpy

BASE = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender"
SCRIPTS = BASE + "/scripts"
OUT = BASE + "/output"
A = {"__name__": "robot_arabasi_yardimci"}       # kendi robotumuz + kızak/araba (yardımcıları da içerir)
exec(open(SCRIPTS + "/robot_arabasi_20261015.py", encoding="utf-8").read(), A)
H = A["H"]
mat, box, disc, link = H["mat"], H["box"], H["disc"], H["link"]

KV = {"__name__": "konveyor_yardimci"}         # paletli konveyör modülleri
exec(open(SCRIPTS + "/konveyor_20261015.py", encoding="utf-8").read(), KV)

# Oyundaki ayak izi: 11 × 11 karo (akış boyunca giriş karosu x = −5 … çıkış karosu x = +5, yanlar ±5).
# Her şey bu karelerin içinde kalır (x, y ∈ [−5.5, 5.5]); bant dışarıda oyunun kendi karolarıyla devam eder.
BELT_X0, BELT_X1 = -5.5, 5.5             # istasyon içindeki bant: 11 × 1 m modül, ortadaki montaj durağı
RAIL_Y = 1.3                             # robot kızaklarının ekseni (±); kızak 1.5 m genişliğinde
TRACK_X0, TRACK_X1 = -5.0, 5.0           # kızak boyu 10 karo
BLOCK_Y = 2.2                            # stok bloklarının raya yakın kenarı (±)
COL_L, COL_R = -4.6, 1.6                 # blokların x başlangıcı (sol / sağ)
FENCE_X, FENCE_Y = 5.3, 5.45             # çit yarı ölçüleri (ayak izinin içinde)
FENCE_H = 2.0

# girdi: (ad, blend, koleksiyon, blok sol-alt köşe (x, y), dolu karo sayısı)
INPUTS = [
    ("Bos_kasa", "bos_kasa_20261014/bos_kasa.blend", "Bos_kasa", (COL_L, BLOCK_Y), 7),
    ("Anakart_PCB", "anakart_pcb_20261014/anakart_pcb.blend", "PCB_stok_birimi", (COL_R, BLOCK_Y), 6),
    ("Elektronik_bilesen", "elektronik_bilesen_seti_20261014/elektronik_bilesen_seti.blend",
     "Elektronik_bilesen_seti", (COL_L, -BLOCK_Y - 3), 8),
    ("Soket_seti", "soket_baglanti_seti_20261014/soket_baglanti_seti.blend", "Soket_baglanti_seti",
     (COL_R, -BLOCK_Y - 3), 5),
]
OUTPUT = ("Anakartli_kasa", "anakartli_kasa_20261015/anakartli_kasa.blend", "Anakartli_kasa")
# oyundaki karşılıkları (model_katalogu id'leri): export yerleşim dosyası için
STOK_MODEL = {"Bos_kasa": "bos_kasa", "Anakart_PCB": "anakart_pcb",
              "Elektronik_bilesen": "elektronik_bilesen_seti", "Soket_seti": "soket_baglanti_seti"}


def yerlesim():
    """Oyunun dolduracağı yuvalar (Blender koordinatı, istasyon merkezine göre):
    36 stok karosu (girdi başına 3 × 3, doldurma sırasıyla) ve montaj durağı."""
    slots = []
    for name, _, _, (bx, by), _ in INPUTS:
        for k, (x, y) in enumerate(tile_centers(bx, by)):
            slots.append(dict(tur="stok", girdi=name, model=STOK_MODEL[name], sira=k, konum=[x, y, 0.006]))
    slots.append(dict(tur="durak", model="palet", konum=[0.0, 0.0, KV["BELT_Z"] + KV["LIFT"]]))
    return slots
# robotlar: (taraf, dünyada x) — arkadaki kasa bloğunun önünde, öndeki montaj durağının önünde;
# ikisinin de kolu +y'ye bakar (arkadaki bloğa, öndeki durağa)
ROBOTS = ((1, -3.0), (-1, 0.0))


def palette():
    P = A["palette"]()
    P.update(
        epoxy=mat("I_epoksi", "#A9B2B5", 0.6),
        walk=mat("I_yaya_yolu", A["R"]["RENK"]["sari"], 0.6),
        post=mat("I_cit_dikme", A["R"]["RENK"]["sari"], 0.5),
        mesh=mat("I_cit_tel", "#3A4046", 0.5, 0.4),
        belt_frame=mat("I_bant_sase", "#858D93", 0.4, 0.6),
        roller=mat("I_rulo", "#C5CBCE", 0.3, 0.8),
        cabinet=mat("I_dolap", "#C5CBCE", 0.5),
        dark=mat("I_koyu", "#1D2125", 0.6),
        curtain=mat("I_isik_perdesi", "#1D2125", 0.5),
        curtain_led=mat("I_perde_led", "#E8473C", 0.4, 0.0, 1.5),
        green=mat("I_isik_yesil", "#39C45A", 0.4, 0.0, 2.0),
        amber=mat("I_isik_sari", "#F2B33D", 0.4),
        red=mat("I_isik_kirmizi", "#E8473C", 0.4),
        screen=mat("I_ekran", "#5FB3E0", 0.3, 0.0, 1.2),
    )
    return P


# --- Zemin ve karolar --------------------------------------------------------------------------

def floor(P, root):
    box("Hucre_zemini", 0, 0, 0, 2 * FENCE_X + 0.4, 2 * FENCE_Y + 0.4, 0.006, P["epoxy"], root)
    # robot hareket alanları: her rayın çevresinde sarı çizgi
    x0, x1, hw = TRACK_X0 - 0.15, TRACK_X1 + 0.15, 0.85
    for s in (-1, 1):
        y = s * RAIL_Y
        for e in (-1, 1):
            box("Robot_alani_cizgi", (x0 + x1) / 2, y + e * hw, 0.006, x1 - x0, 0.05, 0.002, P["walk"], root)
        for x in (x0, x1):
            box("Robot_alani_cizgi", x, y, 0.006, 0.05, 2 * hw, 0.002, P["walk"], root)


def stock_tiles(P, root):
    """36 karo: her blok 3 × 3; karo merkezleri blok köşesinden 0.5 m içeride."""
    for _, _, _, (bx, by), _ in INPUTS:
        for i in range(3):
            for j in range(3):
                H["tile_marks"](P, bx + 0.5 + i, by + 0.5 + j)
    for o in list(H["COLL"].objects):          # karo işaretleri kök altına
        if o.parent is None and o.name.startswith("Karo_"):
            o.parent = root
            o.location.z += 0.006


def tile_centers(bx, by):
    """Doldurma sırası: raydan uzak satırlar önce dolu (robot yakın satırdan tüketir)."""
    rows = [2, 1, 0] if by > 0 else [0, 1, 2]
    return [(bx + 0.5 + i, by + 0.5 + j) for j in rows for i in range(3)]


# --- Dış dosyalardan gelenler --------------------------------------------------------------------

def load_collection(rel_path, coll_name, new_name):
    with bpy.data.libraries.load(OUT + "/" + rel_path, link=False) as (src, dst):
        dst.collections = [coll_name]
    c = dst.collections[0]
    for o in list(c.all_objects):
        if o.name.startswith("Karo_"):
            bpy.data.objects.remove(o, do_unlink=True)
    c.name = new_name + "_birim"
    return c


def instance(coll, name, loc, root, rz=0.0):
    e = link(bpy.data.objects.new(name, None), root)
    e.instance_type = "COLLECTION"
    e.instance_collection = coll
    e.location = loc
    e.rotation_euler.z = rz
    return e


def stock(P, root):
    for name, rel, cname, (bx, by), filled in INPUTS:
        c = load_collection(rel, cname, name)
        for k, (x, y) in enumerate(tile_centers(bx, by)):
            if k < filled:
                instance(c, name + "_stok", (x, y, 0.006), root)


# --- Ana bant: paletli konveyör ----------------------------------------------------------------

def belt(root):
    """15 × 1 m paletli modül; ortadaki (x = 0) montaj durağı. Konveyör betiğinin modülleri."""
    KV["H"]["COLL"] = H["COLL"]
    KP = KV["palette"]()
    n = int(round(BELT_X1 - BELT_X0))
    for k in range(n):
        x = BELT_X0 + 0.5 + k
        m = KV["durak"](KP, "Montaj_duragi") if abs(x) < 0.01 else KV["duz"](KP, "Bant_modulu")
        m.location = (x, 0, 0)
        m.parent = root
    return KP


def pallets(root, KP):
    """Durakta kasalı palet (kaldırılmış), çıkışta kasalı palet, girişte durağa gelen boş palet."""
    name, rel, cname = OUTPUT
    c = load_collection(rel, cname, name)
    for x, z, full, nm in ((0.0, KV["BELT_Z"] + KV["LIFT"], True, "durakta"),
                           (3.5, KV["BELT_Z"], True, "cikista"),
                           (-2.2, KV["BELT_Z"], False, "giriste")):
        p = KV["palet"](KP, "Palet_" + nm)
        p.location = (x, 0, z)
        p.parent = root
        if full:
            e = instance(c, "Anakartli_kasa_" + nm, (0, 0, KV["PAL_T"]), root)
            e.parent = p


# --- Kızaklar ve robotlar (robot_arabasi_20261015) ---------------------------------------------

def sled(P, root, side, robot_x):
    """Bir kızak: ray + araba + kablo zinciri + plakasız robot. Kızağın yerel ekseninde ray x = 0..L;
    kablo zinciri yerel +y'de: her iki tarafta da stok bloklarına bakar, kapaklı kremayer banda."""
    L = TRACK_X1 - TRACK_X0
    k = link(bpy.data.objects.new("Kizak_" + ("arka" if side > 0 else "on"), None), root)
    k.location = (TRACK_X0 if side > 0 else TRACK_X1, side * RAIL_Y, 0)
    k.rotation_euler.z = 0.0 if side > 0 else math.pi
    rail = A["ray"](P, k.name + "_rayi", int(L))
    rail.parent = k
    cx = robot_x - TRACK_X0 if side > 0 else TRACK_X1 - robot_x          # arabanın yerel x'i
    car = A["araba"](P, k.name + "_arabasi")
    car.parent = k
    car.location = (cx, 0, 0)
    ch = A["kablo_zinciri"](P, k.name + "_kablo_zinciri", L / 2, cx + A["CAR_LINK_X"],
                            L / 2 + math.pi * A["BEND_R"] + 0.6)
    ch.parent = k
    # kol dünyada +y'ye: arka kızakta yerel +y, ön kızak 180° döndüğü için yerel −y
    rb = A["R"]["robot"](P, "Robot_" + ("arka" if side > 0 else "on"), None, (0, 0, A["DECK_TOP"]),
                         math.pi / 2 if side > 0 else -math.pi / 2, plate=False)
    rb.parent = car
    return k


# --- Çit -------------------------------------------------------------------------------------

def mesh_panel(P, root, x0, y0, x1, y1):
    """Tel örgü panel: ince ızgara + wireframe; (x0,y0)-(x1,y1) yatay doğrultuda."""
    L = math.hypot(x1 - x0, y1 - y0)
    nx = max(2, int(L / 0.15))
    ny = int((FENCE_H - 0.25) / 0.15)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=nx, y_segments=ny, size=0.5)
    for v in bm.verts:
        v.co = (v.co.x * L, 0, (v.co.y + 0.5) * (FENCE_H - 0.25))
    me = bpy.data.meshes.new("Cit_tel")
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new("Cit_tel", me), root)
    me.materials.append(P["mesh"])
    w = ob.modifiers.new("tel", "WIREFRAME")
    w.thickness = 0.008
    w.use_replace = True
    ob.location = ((x0 + x1) / 2, (y0 + y1) / 2, 0.12)
    ob.rotation_euler.z = math.atan2(y1 - y0, x1 - x0)
    for z in (0.1, FENCE_H - 0.13):
        b = box("Cit_cerceve", (x0 + x1) / 2, (y0 + y1) / 2, z, L, 0.03, 0.03, P["post"], root)
        b.rotation_euler.z = ob.rotation_euler.z


def post(P, root, x, y):
    box("Cit_dikme", x, y, 0, 0.06, 0.06, FENCE_H, P["post"], root, 0.006)
    box("Cit_ayak", x, y, 0, 0.16, 0.16, 0.012, P["post"], root, 0.004)


def fence_line(P, root, a, b, fixed, axis, openings=()):
    """axis='x': y=fixed doğrusu a→b; axis='y': x=fixed doğrusu. openings: [(o0, o1)] açık kalır."""
    segs, cur = [], a
    for o0, o1 in sorted(openings):
        if o0 > cur:
            segs.append((cur, o0))
        cur = o1
    if cur < b:
        segs.append((cur, b))
    for s0, s1 in segs:
        n = max(1, math.ceil((s1 - s0) / 1.5))
        pts = [s0 + (s1 - s0) * k / n for k in range(n + 1)]
        for p in pts:
            post(P, root, *((p, fixed) if axis == "x" else (fixed, p)))
        for p0, p1 in zip(pts, pts[1:]):
            if axis == "x":
                mesh_panel(P, root, p0, fixed, p1, fixed)
            else:
                mesh_panel(P, root, fixed, p0, fixed, p1)
    for o0, o1 in openings:                       # açıklık: ışık perdesi dikmeleri + eşik
        for p in (o0, o1):
            x, y = (p, fixed) if axis == "x" else (fixed, p)
            box("Isik_perdesi", x, y, 0, 0.08, 0.08, 1.7, P["curtain"], root, 0.01)
            box("Isik_perdesi_led", x, y, 1.6, 0.085, 0.085, 0.06, P["curtain_led"], root)
        m = (o0 + o1) / 2
        x, y = (m, fixed) if axis == "x" else (fixed, m)
        sx, sy = (o1 - o0, 0.12) if axis == "x" else (0.12, o1 - o0)
        box("Ikmal_esigi", x, y, 0.006, sx, sy, 0.003, P["walk"], root)


def belt_tunnel(P, root, x):
    """Bandın çitten geçtiği yerde dışa doğru kısa kafes tünel."""
    cx = x - (0.5 if x > 0 else -0.5)            # çitin içine doğru (ayak izi dışına taşmasın)
    for s in (-1, 1):                              # ±0.5: kızakların (y ≥ 0.55) içinde kalır
        box("Tunel_yan", cx, s * 0.5, 0, 1.0, 0.04, 1.3, P["mesh"], root)
        box("Tunel_ust", cx, s * 0.5, 1.3, 1.0, 0.06, 0.04, P["post"], root)
    box("Tunel_cati", cx, 0, 1.3, 1.0, 1.04, 0.03, P["post"], root)


def fence(P, root):
    ops = [(COL_L, COL_L + 3), (COL_R, COL_R + 3)]     # her bloğun dışında ikmal açıklığı
    fence_line(P, root, -FENCE_X, FENCE_X, -FENCE_Y, "x", ops)
    fence_line(P, root, -FENCE_X, FENCE_X, FENCE_Y, "x", ops)
    for x in (-FENCE_X, FENCE_X):                       # sol ve sağ: bant tünelleri
        fence_line(P, root, -FENCE_Y, FENCE_Y, x, "y", [(-0.5, 0.5)])
        belt_tunnel(P, root, x)


# --- Dolap ve panel ----------------------------------------------------------------------------

def controls(P, root):
    for y in (-4.6, 4.6):                                # her robotun kendi kontrol dolabı, çitin içinde köşede
        x = FENCE_X - 0.35
        box("Robot_kontrol_dolabi", x, y, 0, 0.6, 0.8, 1.8, P["cabinet"], root, 0.02)
        box("Dolap_kapak_cizgi", x - 0.302, y, 0.1, 0.004, 0.004, 1.6, P["dark"], root)
        box("Dolap_kolu", x - 0.31, y + 0.25, 0.95, 0.03, 0.03, 0.15, P["dark"], root, 0.006)
        disc("Isik_kulesi_mil", x + 0.15, y - 0.25, 1.8, 0.02, 0.15, P["belt_frame"], root, 12)
        for j, m in enumerate((P["green"], P["amber"], P["red"])):
            disc("Isik_kulesi", x + 0.15, y - 0.25, 1.95 + j * 0.08, 0.045, 0.075, m, root, 20)
    # operatör paneli (HMI): ön çitin içinde, durak hizasında (iki ön blok arasında)
    px, py = 0.0, -FENCE_Y + 0.45
    box("HMI_ayak", px, py, 0, 0.08, 0.08, 1.2, P["belt_frame"], root)
    box("HMI", px, py, 1.2, 0.45, 0.08, 0.32, P["cabinet"], root, 0.015)
    box("HMI_ekran", px, py - 0.045, 1.24, 0.36, 0.01, 0.24, P["screen"], root)


def istasyon(P):
    root = link(bpy.data.objects.new("Istasyon_01_anakart_montaji", None))
    floor(P, root)
    stock_tiles(P, root)
    stock(P, root)
    KP = belt(root)
    pallets(root, KP)
    for side, x in ROBOTS:
        sled(P, root, side, x)
    fence(P, root)
    controls(P, root)
    return root


def build(scene=None):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Istasyon_01_anakart_montaji")
    scene.collection.children.link(c)
    H["COLL"] = c
    return istasyon(P)


if __name__ == "__main__":
    build()
