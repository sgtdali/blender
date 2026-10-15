"""Oyunun kendi endüstriyel robotu (2026-10-15): 6 eksenli, tüm istasyonlarda kullanılır.

Kullanıcı kararı: KUKA modeli oyunda kullanılamaz; kendi robotumuz çizilir.

Tasarım: gerçekçi değil, okunur. Tıknaz gövde, büyük eklem göbekleri, turuncu gövde, koyu gri/siyah
eklemler, sarı vurgu (renk_paleti.py; kullanıcı beyazı fazla buldu, canlı renk istedi).
KR210 ölçeğinde: dinlenme pozunda ~2.3 m, uzanma ~2.7 m. Taban plakası 1 × 1 m (oyunun karo ızgarası).

Eklem zinciri (her halka tek mesh, orijini kendi ekseninde; poz = tek açı):
  Robot_taban (sabit)
  └ Robot_govde      A1  z ekseni
    └ Robot_alt_kol  A2  y ekseni
      └ Robot_ust_kol  A3  y ekseni
        └ Robot_on_kol   A4  x ekseni (kendi boyunca döner)
          └ Robot_bilek    A5  y ekseni
            └ Robot_flans    A6  x ekseni
              └ Robot_tutucu  (değiştirilebilir uç)
Yerel eksen: x ileri (kolun uzandığı yön), y yan, z yukarı. glTF'ye düğüm hiyerarşisi olarak çıkar.

robot(P, name, pose, location, rz) başka betiklerden çağrılabilir; pose = {"a1": derece, ...}.
Çıktı: output/robot_20261015/robot.blend
"""
import math

import bmesh
import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
H = {"__name__": "anakart_pcb_yardimci"}
exec(open(SCRIPTS + "/anakart_pcb_20261014.py", encoding="utf-8").read(), H)
mat, box, disc, link = H["mat"], H["box"], H["disc"], H["link"]
RENK = {}
exec(open(SCRIPTS + "/renk_paleti.py", encoding="utf-8").read(), RENK)
RENK = RENK["RENK"]                            # ortak canlı palet

# eklem ofsetleri (ebeveyn halkanın yerel koordinatında)
A1_Z = 0.48                    # taban → A1
A2_OFS = (0.30, 0.0, 0.52)     # A1 → A2 (omuz ileride ve yukarıda)
LOWER_L = 1.15                 # A2 → A3
A4_OFS = (0.32, 0.0, 0.20)     # A3 → A4 (ön kol yukarı kaydırılmış)
FORE_L = 0.95                  # A4 → A5
WRIST_L = 0.20                 # A5 → A6

REST = {"a1": 0, "a2": 8, "a3": -8, "a4": 0, "a5": 90, "a6": 0}


def palette():
    P = H["palette"]()
    P.update(
        body=mat("R_govde", RENK["turuncu"], 0.45),
        joint=mat("R_eklem", "#3A4046", 0.5, 0.3),
        motor=mat("R_motor", "#2C3238", 0.45, 0.4),
        accent=mat("R_vurgu", RENK["sari"], 0.45),
        steel=mat("R_celik", "#B9BFC3", 0.3, 0.85),
        base=mat("R_kaide", "#4A5057", 0.6),
        rubber=mat("R_kaucuk", "#1D2125", 0.8),
    )
    return P


# --- Yardımcılar ------------------------------------------------------------------------------

def ydisc(name, x, y, z, r, h, m, verts=32):
    """y eksenli silindir; (x, y, z) merkez."""
    d = disc(name, 0, 0, -h / 2, r, h, m, None, verts)
    d.rotation_euler.x = math.pi / 2
    d.location = (x, y, z)
    return d


def xdisc(name, x, y, z, r, h, m, verts=32):
    """x eksenli silindir; x başlangıç, (y, z) merkez."""
    d = disc(name, 0, 0, 0, r, h, m, None, verts)
    d.rotation_euler.y = math.pi / 2
    d.location = (x + h / 2, y, z)
    return d


def zdisc(name, x, y, z, r, h, m, verts=32):
    return disc(name, x, y, z, r, h, m, None, verts)


NOTCH = 0.17                   # motor profili: köşe çentiği / kenar


def notched(name, r, h, m):
    """Köşeleri kare çentikli kare prizma (servo motor profili); z ekseninde, merkez orijinde.
    r = yarım kenar (silindirdeki yarıçapın karşılığı)."""
    a, n = r, 2 * r * NOTCH
    pts = [(-a + n, -a), (a - n, -a), (a - n, -a + n), (a, -a + n), (a, a - n), (a - n, a - n),
           (a - n, a), (-a + n, a), (-a + n, a - n), (-a, a - n), (-a, -a + n), (-a + n, -a + n)]
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, -h / 2)) for x, y in pts])
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, 0, h), verts=[v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def ymotor(name, x, y, z, r, h, m, verts=None):
    """y eksenli motor bloğu; (x, y, z) merkez (ydisc ile aynı çağrı)."""
    o = notched(name, r, h, m)
    o.rotation_euler.x = math.pi / 2
    o.location = (x, y, z)
    return o


def xmotor(name, x, y, z, r, h, m, verts=None):
    """x eksenli motor bloğu; x başlangıç (xdisc ile aynı çağrı)."""
    o = notched(name, r, h, m)
    o.rotation_euler.y = math.pi / 2
    o.location = (x + h / 2, y, z)
    return o


def zmotor(name, x, y, z, r, h, m, verts=None):
    """z eksenli motor bloğu; z taban (zdisc ile aynı çağrı)."""
    o = notched(name, r, h, m)
    o.location = (x, y, z + h / 2)
    return o


def turret_shell(name, m, disc_r=0.44, disc_h=0.1, top=0.42, rect=(-0.38, 0.58, 0.31), corner=0.1,
                 fillet=0.08, edge=0.04, n=192):
    """Gövde kabuğu (tek parça döküm): altta dönen disk, üstte omuz bloğu; disk üstüyle bloğun
    yan duvarı içbükey radyusla birleşir, bloğun üst kenarı yuvarlatılmış.
    rect = (x0, x1, yarım genişlik), köşe radyusu corner. Her açıda diskten bloğa profil çizilir."""
    x0, x1, hy = rect
    cx, hx = (x0 + x1) / 2, (x1 - x0) / 2

    def inside(px, py):
        qx, qy = abs(px - cx) - (hx - corner), abs(py) - (hy - corner)
        out = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - corner
        return out <= 0

    def rect_dist(a):
        lo, hi = 0.0, 2.0
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if inside(mid * math.cos(a), mid * math.sin(a)) else (lo, mid)
        return lo

    seg_f, seg_e = 5, 3
    profiles = []
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = rect_dist(a)
        R = max(0.0, min(fillet, disc_r - rr))       # blok diskten taşıyorsa radyus yok
        prof = [(disc_r, 0.0), (disc_r, disc_h)]
        for i in range(seg_f + 1):                   # içbükey radyus: disk üstü → blok duvarı
            f = (math.pi / 2) * i / seg_f
            prof.append((rr + R - R * math.sin(f), disc_h + R - R * math.cos(f)))
        for i in range(seg_e + 1):                   # dışbükey üst kenar
            f = (math.pi / 2) * i / seg_e
            prof.append((rr - edge + edge * math.cos(f), top - edge + edge * math.sin(f)))
        profiles.append([(d * math.cos(a), d * math.sin(a), z) for d, z in prof])
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in prof] for prof in profiles]
    L = len(rings[0])
    for k in range(n):
        r0, r1 = rings[k], rings[(k + 1) % n]
        for i in range(L - 1):
            try:
                bm.faces.new((r0[i], r1[i], r1[i + 1], r0[i + 1]))
            except ValueError:
                pass
    bm.faces.new([r[0] for r in reversed(rings)])    # alt kapak
    bm.faces.new([r[-1] for r in rings])             # üst kapak
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def rrect_dist(a, ox, oy, rect, corner):
    """(ox, oy)'dan a açısıyla çıkan ışının köşe radyuslu dikdörtgenden çıktığı mesafe.
    rect = (x0, x1, yarım genişlik)."""
    x0, x1, hy = rect
    cx, hx = (x0 + x1) / 2, (x1 - x0) / 2

    def inside(px, py):
        qx, qy = abs(px - cx) - (hx - corner), abs(py) - (hy - corner)
        return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - corner <= 0

    lo, hi = 0.0, 2.0
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if inside(ox + mid * math.cos(a), oy + mid * math.sin(a)) else (lo, mid)
    return lo


def riser(name, m, base_rect, base_corner, rect, corner, z0, z1, fillet=0.06, edge=0.035, n=192):
    """Düz bir üst yüzden (base_rect, z0) yükselen blok (rect, z1'e kadar): tabanı içbükey
    radyusla yüzeye bağlanır, üst kenarı yuvarlatılmış. Alt kapak yok (yüzeye oturur)."""
    ox, oy = (rect[0] + rect[1]) / 2, 0.0
    seg_f, seg_e = 5, 3
    bm = bmesh.new()
    rings = []
    for k in range(n):
        a = 2 * math.pi * k / n
        rb = rrect_dist(a, ox, oy, base_rect, base_corner)
        rr = rrect_dist(a, ox, oy, rect, corner)
        R = max(0.0, min(fillet, rb - rr))
        prof = []
        for i in range(seg_f + 1):
            f = (math.pi / 2) * i / seg_f
            prof.append((rr + R - R * math.sin(f), z0 + R - R * math.cos(f)))
        for i in range(seg_e + 1):
            f = (math.pi / 2) * i / seg_e
            prof.append((rr - edge + edge * math.cos(f), z1 - edge + edge * math.sin(f)))
        rings.append([bm.verts.new((ox + d * math.cos(a), oy + d * math.sin(a), z)) for d, z in prof])
    L = len(rings[0])
    for k in range(n):
        r0, r1 = rings[k], rings[(k + 1) % n]
        for i in range(L - 1):
            bm.faces.new((r0[i], r1[i], r1[i + 1], r0[i + 1]))
    bm.faces.new([r[-1] for r in rings])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def lathe(name, profile, m, n=64):
    """(yarıçap, z) profilini z ekseni etrafında döndürür; ilk ve son nokta r=0 değilse
    o uçlar açık kalır (yüzeye oturan parçalar için)."""
    bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), z))
              for r, z in profile] for k in range(n)]
    for k in range(n):
        r0, r1 = rings[k], rings[(k + 1) % n]
        for i in range(len(profile) - 1):
            bm.faces.new((r0[i], r1[i], r1[i + 1], r0[i + 1]))
    bm.faces.new([r[-1] for r in rings])               # üst kapak
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


def fillet_foot(r, z0, z1, R, top_edge=0.0, seg=6):
    """Silindir profili: z0'daki yüzeye R içbükey radyusla oturur, z1'de biter (üst kenar
    top_edge kadar yuvarlatılmış)."""
    prof = []
    for i in range(seg + 1):
        f = (math.pi / 2) * i / seg
        prof.append((r + R - R * math.sin(f), z0 + R - R * math.cos(f)))
    if top_edge > 0:
        for i in range(1, 4):
            f = (math.pi / 2) * i / 3
            prof.append((r - top_edge + top_edge * math.cos(f), z1 - top_edge + top_edge * math.sin(f)))
    else:
        prof.append((r, z1))
    return prof

def merge(name, parts):
    """Parçaları tek mesh'e birleştirir; orijin (0,0,0) = halkanın ekseni."""
    active = parts[0]
    active.data = active.data.copy()            # önbellekteki ortak mesh'i bozma
    with bpy.context.temp_override(active_object=active, selected_editable_objects=parts,
                                   selected_objects=parts):
        bpy.ops.object.join()
    me = active.data
    me.transform(active.matrix_basis)
    active.matrix_basis.identity()
    for p in me.polygons:                       # yumuşak yüzey, keskin kenarlar; düz kapaklar düz
        p.use_smooth = len(p.vertices) <= 8
    me.set_sharp_from_angle(angle=math.radians(35))
    active.name = me.name = name
    return active


# --- Halkalar (her biri kendi ekseni orijinde) ------------------------------------------------

PLATE_T = 0.07                 # zemine sabit kurulumda taban plakası kalınlığı


def base_link(P, plate=True):
    """plate=False: plaka yok, etek doğrudan altındaki yüzeye (ör. ray arabası) radyusla oturur."""
    z = PLATE_T if plate else 0.0
    s = [
        # etek: altındaki yüzeye içbükey radyusla oturur
        lathe("Taban_etek", fillet_foot(0.43, z, z + 0.08, 0.05, 0.015), P["body"], 96),
        zdisc("Taban_kaide", 0, 0, z + 0.08, 0.4, 0.21, P["body"], 40),
        zdisc("Taban_bilezik", 0, 0, z + 0.29, 0.43, 0.07, P["joint"], 40),
        zdisc("Taban_kaide_vurgu", 0, 0, z + 0.17, 0.405, 0.035, P["accent"], 40),
        box("Taban_baglanti_kutusu", -0.41, 0, z, 0.14, 0.32, 0.2, P["joint"], None, 0.02),
    ]
    if plate:
        s.append(box("Taban_plaka", 0, 0, 0, 1.0, 1.0, PLATE_T, P["base"], None, 0.02))
        for sx in (-1, 1):
            for sy in (-1, 1):
                s.append(zdisc("Taban_civata", sx * 0.42, sy * 0.42, PLATE_T, 0.035, 0.03, P["steel"], 12))
    return merge("Robot_taban", s)


def turret_link(P):
    ax, az = A2_OFS[0], A2_OFS[2]
    s = [
        # dönen disk + omuz bloğu tek döküm kabuk; birleşim içbükey radyuslu
        turret_shell("Govde_kabuk", P["body"]),
        # önde yükselen kısım: kabuğun üst yüzüne radyusla bağlanır (A2 göbeklerini taşır)
        riser("Govde_omuz_on", P["body"], (-0.38 + 0.04, 0.58 - 0.04, 0.31 - 0.04), 0.06,
              (0.08, 0.5, 0.22), 0.06, 0.42, az),
        # A2 göbekleri (iki yanda, büyük koyu disk + gövde rengi kapak)
        ydisc("Omuz_gobek", ax, 0.255, az, 0.26, 0.07, P["joint"]),
        ydisc("Omuz_gobek", ax, -0.255, az, 0.26, 0.07, P["joint"]),
        # A1 ve A2 motorları
        zmotor("A1_motor", -0.24, 0.18, 0.3, 0.1, 0.24, P["motor"], 20),
        zmotor("A1_motor_kapak", -0.24, 0.18, 0.54, 0.105, 0.03, P["accent"], 20),
        ymotor("A2_motor", ax, -0.39, az, 0.12, 0.2, P["motor"], 24),
        ymotor("A2_motor_kapak", ax, -0.5, az, 0.125, 0.03, P["accent"], 24),
    ]
    return merge("Robot_govde", s)


def lower_link(P):
    L = LOWER_L
    s = [
        ydisc("Alt_kol_gobek", 0, 0, 0, 0.22, 0.42, P["body"]),
        box("Alt_kol", 0, 0, 0, 0.34, 0.38, L, P["body"], None, 0.06),
        ydisc("Dirsek_gobek", 0, 0, L, 0.19, 0.38, P["body"]),
        # yan yüzlerde vurgu şeridi
        box("Alt_kol_serit", 0, 0.191, 0.2, 0.12, 0.004, L - 0.4, P["accent"], None),
        box("Alt_kol_serit", 0, -0.191, 0.2, 0.12, 0.004, L - 0.4, P["accent"], None),
        # denge silindiri (büyük robotların tipik parçası): arkada, kol boyunca
        box("Denge_silindiri", -0.22, 0.0, 0.08, 0.12, 0.14, 0.6, P["joint"], None, 0.05),
        box("Denge_mili", -0.21, 0.0, 0.68, 0.05, 0.06, 0.3, P["steel"], None, 0.015),
    ]
    return merge("Robot_alt_kol", s)


def upper_link(P):
    ax, az = A4_OFS[0], A4_OFS[2]
    s = [
        ydisc("Dirsek_eklem", 0, 0, 0, 0.21, 0.46, P["joint"]),
        box("Ust_kol_govde", -0.06, 0, -0.12, 0.62, 0.42, 0.44, P["body"], None, 0.06),
        # arkada bilek motorları (A4–A6)
        box("Bilek_motor_yuvasi", -0.42, 0, az - 0.12, 0.16, 0.34, 0.24, P["motor"], None, 0.03),
        xmotor("A4_motor", -0.62, 0.09, az, 0.07, 0.2, P["motor"], 20),
        xmotor("A5_motor", -0.62, -0.09, az, 0.07, 0.2, P["motor"], 20),
        xmotor("A4_motor_kapak", -0.65, 0.09, az, 0.072, 0.03, P["accent"], 20),
        xmotor("A5_motor_kapak", -0.65, -0.09, az, 0.072, 0.03, P["accent"], 20),
        # A3 motoru A2'nin karşı yanında (A2 −y, A3 +y)
        ymotor("A3_motor", 0.0, 0.29, 0.0, 0.1, 0.16, P["motor"], 24),
        ymotor("A3_motor_kapak", 0.0, 0.38, 0.0, 0.105, 0.03, P["accent"], 24),
        # A4 yatak bileziği (ön kolun döndüğü yer)
        xdisc("A4_bilezik", ax - 0.06, 0, az, 0.17, 0.06, P["joint"]),
    ]
    return merge("Robot_ust_kol", s)


def fore_link(P):
    L = FORE_L
    s = [
        xdisc("On_kol_boru", 0, 0, 0, 0.145, L - 0.2, P["body"]),
        xdisc("On_kol_uc", L - 0.22, 0, 0, 0.12, 0.06, P["joint"]),
        xdisc("On_kol_serit", 0.12, 0, 0, 0.148, 0.05, P["accent"]),
        # çatal: bileği iki yandan tutar
        box("Catal", L - 0.12, 0.125, -0.13, 0.24, 0.06, 0.26, P["body"], None, 0.03),
        box("Catal", L - 0.12, -0.125, -0.13, 0.24, 0.06, 0.26, P["body"], None, 0.03),
        ydisc("Catal_gobek", L, 0.125, 0, 0.13, 0.06, P["body"]),
        ydisc("Catal_gobek", L, -0.125, 0, 0.13, 0.06, P["body"]),
        # kablo hortumu: ön kolun üstünde
        xdisc("Kablo_hortumu", 0.05, 0, 0.17, 0.035, L - 0.35, P["rubber"], 12),
    ]
    for x in (0.15, 0.55):
        s.append(box("Hortum_kelepce", x, 0, 0.13, 0.04, 0.09, 0.08, P["joint"], None, 0.01))
    return merge("Robot_on_kol", s)


def wrist_link(P):
    s = [
        ydisc("Bilek_eklem", 0, 0, 0, 0.11, 0.19, P["joint"]),
        xdisc("Bilek_govde", 0, 0, 0, 0.1, WRIST_L - 0.02, P["joint"]),
    ]
    return merge("Robot_bilek", s)


def flange_link(P):
    s = [
        xdisc("Flans", 0, 0, 0, 0.1, 0.035, P["steel"]),
        xdisc("Flans_vurgu", 0.035, 0, 0, 0.095, 0.012, P["accent"]),
    ]
    return merge("Robot_flans", s)


def gripper(P):
    """Basit paralel tutucu: gövde + iki parmak (x ileri). Uç parça; başka tutucuyla değişebilir."""
    s = [
        xdisc("Tutucu_adaptor", 0.0, 0, 0, 0.08, 0.06, P["joint"]),
        box("Tutucu_govde", 0.12, 0, -0.08, 0.13, 0.42, 0.16, P["motor"], None, 0.025),
        box("Tutucu_ray", 0.195, 0, -0.04, 0.02, 0.4, 0.08, P["steel"], None),
    ]
    for sy in (-1, 1):
        s.append(box("Tutucu_parmak", 0.3, sy * 0.15, -0.045, 0.2, 0.05, 0.09, P["body"], None, 0.012))
        s.append(box("Tutucu_ped", 0.36, sy * 0.122, -0.035, 0.08, 0.01, 0.07, P["accent"], None))
    return merge("Robot_tutucu", s)


# --- Montaj ve poz ------------------------------------------------------------------------------

JOINTS = (("Robot_govde", "z"), ("Robot_alt_kol", "y"), ("Robot_ust_kol", "y"),
          ("Robot_on_kol", "x"), ("Robot_bilek", "y"), ("Robot_flans", "x"))


def set_pose(root, pose):
    """pose: {"a1": derece, ... "a6": derece}; eksik eklem 0 kabul edilir."""
    for i, (_, ax) in enumerate(JOINTS, 1):
        o = next((c for c in root.children_recursive if c.get("eklem") == "a%d" % i), None)
        if o is None:
            continue
        o.rotation_euler = (0, 0, 0)
        setattr(o.rotation_euler, ax, math.radians(pose.get("a%d" % i, 0)))


def robot(P, name="Robot", pose=None, location=(0, 0, 0), rz=0.0, plate=True):
    """plate=False: ray arabası gibi bir tablaya oturan, plakasız robot."""
    base = base_link(P, plate)
    links = [turret_link(P), lower_link(P), upper_link(P), fore_link(P), wrist_link(P), flange_link(P)]
    a1z = A1_Z if plate else A1_Z - PLATE_T
    offsets = [(0, 0, a1z), A2_OFS, (0, 0, LOWER_L), A4_OFS, (FORE_L, 0, 0), (WRIST_L, 0, 0)]
    parent = base
    for i, (ln, ofs) in enumerate(zip(links, offsets), 1):
        ln.parent = parent
        ln.location = ofs
        ln["eklem"] = "a%d" % i
        ln["eksen"] = JOINTS[i - 1][1]
        parent = ln
    g = gripper(P)
    g.parent = parent
    g.location = (0.035, 0, 0)
    base.name = name
    base.location = location
    base.rotation_euler.z = rz
    for o in [base] + list(base.children_recursive):
        if o is not base:
            o.name = name + "_" + o.name.replace("Robot_", "").split(".")[0]
    set_pose(base, REST if pose is None else pose)
    return base


def build(scene=None):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Robot")
    scene.collection.children.link(c)
    H["COLL"] = c
    return robot(P, "Robot")


if __name__ == "__main__":
    build()
