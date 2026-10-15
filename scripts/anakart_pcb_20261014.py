"""Boş anakart PCB (2026-10-14): 01B'nin çıktısı, 01 anakart montajının girdisi.

Gerçekçi değil, okunur: bileşenler takılmamış kart; nereye ne takılacağı altın/gümüş ped
alanları, beyaz serigrafi çerçeveleri ve bakır yollarla belli olur.

Ölçü kararları (kullanıcı, 14 Ekim 2026):
- PCB'ler tek tek taşınır; bir stok karosunda (1 × 1 m) tek bir PCB durur.
- Kart düzeni 0.40 × 0.32 m'lik birimlerle çizilir ve SCALE ile büyütülür:
  0.84 × 0.672 × 0.025 m (ATX oranı 1.25). Tüm ped, çizgi ve delikler aynı oranda büyür.
- Kart alçak antrasit ESD altlığının üstünde durur (0.9 × 0.74 × 0.04 m), karonun içinde kalır.
- Açık konu: art bible'daki kasa (0.46 × 0.44 m) bu kartı almaz; kasa ölçüsü ayrıca kararlaştırılacak.
- Malzemeler düz renk (glTF'ye aktarılabilir), renkler art bible paletinden.
- Kart tek mesh'e birleştirilir (oyunda tek obje).

Blender MCP execute_blender_code ile ya da `blender -b -P` ile çalışır.
build(scene) çağrısı verilen sahneye "PCB_stok_birimi" koleksiyonunu kurar.
"""
import math

import bmesh
import bpy

BOARD_W, BOARD_D, BOARD_T = 0.40, 0.32, 0.012   # çizim birimi: x, y, kalınlık
TOP = BOARD_T                                     # kart üst yüzü (kart tabanı z=0)
SCALE = 2.1                                       # 0.40 → 0.84 m
TRAY_H = 0.04                                     # ESD altlığı yüksekliği


def srgb(hex_str):
    h = hex_str.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


_MATS = {}


def mat(name, hex_str, rough=0.55, metal=0.0, emit=0.0):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*srgb(hex_str), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*srgb(hex_str), 1)
        b.inputs["Emission Strength"].default_value = emit
    _MATS[name] = m
    return m


def palette():
    return dict(
        pcb=mat("P_pcb_yesil", "#3E9A55", 0.5),
        trace=mat("P_pcb_yol", "#5BB56F", 0.42),          # maske altındaki bakır: açık yeşil
        edge=mat("P_pcb_kenar", "#2E7A43", 0.6),          # kart kenarı (FR4 kesit) biraz koyu
        silk=mat("P_serigrafi", "#F2F4F2", 0.6),
        gold=mat("P_altin_ped", "#D9A83A", 0.3, 0.9),
        tin=mat("P_kalay_ped", "#C9CDD0", 0.3, 0.85),
        hole=mat("P_delik", "#1A1E1C", 0.7),
        dark=mat("B_antrasit", "#2C3238", 0.55),
        mid=mat("B_orta_gri", "#858D93", 0.5),
        tile=mat("B_stok_bos", "#C9CED1", 0.6),
    )


COLL = None


def link(ob, parent=None):
    COLL.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


_MESHES = {}


def box_mesh(sx, sy, sz, bevel):
    key = ("box", round(sx, 5), round(sy, 5), round(sz, 5), bevel)
    if key in _MESHES:
        return _MESHES[key]
    me = bpy.data.meshes.new("pcb_box")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    if bevel > 0:
        b = min(bevel, sx * 0.3, sy * 0.3, sz * 0.3)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, segments=2, affect="EDGES",
                        profile=0.5, clamp_overlap=True)
    bm.to_mesh(me)
    bm.free()
    _MESHES[key] = me
    return me


def box(name, x, y, z, sx, sy, sz, m, parent=None, bevel=0.0, rz=0.0):
    """Kutu; (x, y) taban merkezi, z taban yüksekliği."""
    ob = link(bpy.data.objects.new(name, box_mesh(sx, sy, sz, bevel)), parent)
    ob.location = (x, y, z + sz / 2)
    ob.rotation_euler.z = rz
    if not ob.data.materials:
        ob.data.materials.append(m)
    elif ob.data.materials[0] != m:
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = m
    return ob


def disc(name, x, y, z, r, h, m, parent=None, verts=20):
    key = ("cyl", round(r, 5), round(h, 5), verts)
    me = _MESHES.get(key)
    if me is None:
        me = bpy.data.meshes.new("pcb_cyl")
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=h)
        bm.to_mesh(me)
        bm.free()
        _MESHES[key] = me
    ob = link(bpy.data.objects.new(name, me), parent)
    ob.location = (x, y, z + h / 2)
    if not me.materials:
        me.materials.append(m)
    elif me.materials[0] != m:
        ob.material_slots[0].link = "OBJECT"
        ob.material_slots[0].material = m
    return ob


def outline(name, x, y, sx, sy, w, m, parent, z=TOP):
    """Serigrafi çerçeve: dört ince şerit."""
    h = 0.0006
    for (cx, cy, lx, ly) in ((x, y + sy / 2, sx + w, w), (x, y - sy / 2, sx + w, w),
                             (x - sx / 2, y, w, sy), (x + sx / 2, y, w, sy)):
        box(name, cx, cy, z, lx, ly, h, m, parent)


def trace(name, pts, w, m, parent, z=TOP):
    """Bakır yol: noktalar arası düz parçalar (45°'lik kırılmalarla verilir)."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        ob = box(name, (x0 + x1) / 2, (y0 + y1) / 2, z, L + w, w, 0.0004, m, parent)
        ob.rotation_euler.z = math.atan2(y1 - y0, x1 - x0)


# --- Kart ---------------------------------------------------------------------------------

def board(P, root):
    """Kart yerel koordinatları: merkez (0, 0), x = genişlik (0.40), y = derinlik (0.32).
    Arka I/O kenarı -x tarafında, PCIe yuvaları alt yarıda yatay."""
    W, D = BOARD_W, BOARD_D
    box("Kart", 0, 0, 0, W, D, BOARD_T, P["pcb"], root, bevel=0.002)

    # Montaj delikleri (ATX düzenine benzer 6 delik): kalay halka + koyu delik
    for hx, hy in ((-0.185, 0.145), (0.045, 0.145), (0.185, 0.145),
                   (-0.185, -0.12), (0.045, -0.12), (0.185, -0.12)):
        disc("Montaj_deligi_halka", hx, hy, TOP, 0.0095, 0.0006, P["tin"], root)
        disc("Montaj_deligi", hx, hy, TOP, 0.0045, 0.0009, P["hole"], root)

    # CPU soketi alanı: altın LGA ped alanı + serigrafi çerçeve + köşe üçgeni
    cx, cy = -0.03, 0.065
    box("CPU_ped_alani", cx, cy, TOP, 0.072, 0.072, 0.0012, P["gold"], root)
    for i in range(1, 6):  # ped ızgarası çizgileri (yakın zoom için)
        o = -0.036 + i * 0.012
        box("CPU_ped_ayrim", cx + o, cy, TOP + 0.0012, 0.0012, 0.072, 0.0002, P["edge"], root)
        box("CPU_ped_ayrim", cx, cy + o, TOP + 0.0012, 0.072, 0.0012, 0.0002, P["edge"], root)
    outline("CPU_serigrafi", cx, cy, 0.094, 0.094, 0.003, P["silk"], root)
    tri = box("CPU_isaret", cx - 0.052, cy + 0.052, TOP, 0.01, 0.01, 0.0006, P["silk"], root)
    tri.rotation_euler.z = math.pi / 4
    # Soket tutucu montaj delikleri
    for dx, dy in ((-0.058, 0.058), (0.058, 0.058), (-0.058, -0.058), (0.058, -0.058)):
        disc("CPU_tutucu_deligi", cx + dx, cy + dy, TOP, 0.0045, 0.0006, P["tin"], root, 12)

    # VRM: CPU'nun solunda ve üstünde kalay ped sıraları
    for i in range(6):
        box("VRM_ped", cx - 0.075, cy - 0.04 + i * 0.016, TOP, 0.016, 0.01, 0.0008, P["tin"], root)
        box("VRM_ped", cx - 0.04 + i * 0.016, cy + 0.075, TOP, 0.01, 0.016, 0.0008, P["tin"], root)
    outline("VRM_serigrafi", cx - 0.075, cy + 0.0, 0.026, 0.11, 0.0022, P["silk"], root)
    outline("VRM_serigrafi", cx + 0.0, cy + 0.075, 0.11, 0.026, 0.0022, P["silk"], root)

    # RAM yuvaları: CPU'nun sağında 4 dikey ped sırası
    for i in range(4):
        rx = 0.075 + i * 0.018
        box("RAM_ped_sirasi", rx, cy - 0.005, TOP, 0.006, 0.15, 0.0009, P["gold"], root)
        outline("RAM_serigrafi", rx, cy - 0.005, 0.012, 0.165, 0.0018, P["silk"], root)
        for e in (-1, 1):  # yuva mandal delikleri
            disc("RAM_mandal_deligi", rx, cy - 0.005 + e * 0.088, TOP, 0.0032, 0.0006, P["tin"], root, 10)

    # 24 pin güç konnektörü: sağ kenarda 2 × 12 delik
    px = 0.172
    for r in range(2):
        for k in range(12):
            disc("Guc_pin", px + r * 0.009, cy - 0.055 + k * 0.009, TOP, 0.0032, 0.0006, P["tin"], root, 10)
    outline("Guc_serigrafi", px + 0.0045, cy - 0.0055, 0.024, 0.115, 0.002, P["silk"], root)

    # Yonga seti: sağ altta küçük altın kare
    box("Yonga_seti_ped", 0.085, -0.075, TOP, 0.04, 0.04, 0.0012, P["gold"], root)
    outline("Yonga_seti_serigrafi", 0.085, -0.075, 0.052, 0.052, 0.0022, P["silk"], root)

    # PCIe yuvaları: alt yarıda yatay 2 uzun + 1 kısa ped sırası
    for i, (length, py) in enumerate(((0.17, -0.025), (0.17, -0.085), (0.06, -0.135))):
        x0 = -0.2 + 0.035 + length / 2
        box("PCIe_ped_sirasi", x0, py, TOP, length, 0.006, 0.0009, P["gold"], root)
        outline("PCIe_serigrafi", x0, py, length + 0.012, 0.014, 0.0018, P["silk"], root)

    # NVMe (M.2) yuvası: PCIe'ler arasında
    box("M2_ped", -0.12, -0.055, TOP, 0.012, 0.01, 0.0008, P["gold"], root)
    outline("M2_serigrafi", -0.07, -0.055, 0.11, 0.022, 0.0018, P["silk"], root)
    disc("M2_vida_deligi", -0.012, -0.055, TOP, 0.003, 0.0006, P["tin"], root, 10)

    # Arka I/O alanı: sol kenarda konnektör ped blokları ve çerçeve
    for i, (h, py) in enumerate(((0.03, 0.12), (0.04, 0.075), (0.03, 0.03), (0.025, -0.005))):
        box("IO_ped", -0.188, py, TOP, 0.016, h, 0.0008, P["tin"], root)
    outline("IO_serigrafi", -0.185, 0.06, 0.026, 0.165, 0.0022, P["silk"], root)

    # Pil yuvası: daire çerçeve + ped
    disc("Pil_ped", 0.02, -0.12, TOP, 0.011, 0.0007, P["tin"], root, 24)
    disc("Pil_serigrafi", 0.02, -0.12, TOP, 0.0135, 0.0005, P["silk"], root, 24)

    # Ön panel / SATA pedleri: sağ alt kenar
    for k in range(4):
        box("SATA_ped", 0.135 + (k % 2) * 0.022, -0.105 - (k // 2) * 0.03, TOP, 0.016, 0.01, 0.0008, P["tin"], root)

    # Bakır yollar: CPU → RAM, CPU → PCIe, CPU → yonga seti, yonga seti → SATA
    w = 0.0022
    for k in range(5):
        trace("Yol", [(cx + 0.047, cy - 0.03 + k * 0.012), (0.068, cy - 0.03 + k * 0.012)], w, P["trace"], root)
    for k in range(4):
        o = k * 0.008
        trace("Yol", [(cx - 0.02 + o, cy - 0.047), (cx - 0.02 + o, -0.005 - o * 0.2), (-0.1 + o, -0.016 - o)], w, P["trace"], root)
    for k in range(3):
        o = k * 0.008
        trace("Yol", [(cx + 0.03 - o, cy - 0.047), (cx + 0.03 - o, -0.02 - o), (0.06, -0.06 - o)], w, P["trace"], root)
    for k in range(2):
        o = k * 0.008
        trace("Yol", [(0.105, -0.07 + o), (0.14, -0.07 + o), (0.15, -0.08 + o)], w, P["trace"], root)


def build_board(name, P, location=(0, 0, 0), rotation=(0, 0, 0)):
    root = link(bpy.data.objects.new(name, None))
    root.empty_display_size = 0.2
    board(P, root)
    root.location = location
    root.rotation_euler = rotation
    return root


# --- Tek mesh -------------------------------------------------------------------------------

def merge_board(root, name):
    """Kartın parçalarını tek mesh'e birleştirir, SCALE'i uygular; kök boş obje silinir."""
    parts = [c for c in root.children if c.type == "MESH"]
    active = parts[0]
    active.data = active.data.copy()          # paylaşılan önbellek mesh'ini bozma
    with bpy.context.temp_override(active_object=active, selected_editable_objects=parts,
                                   selected_objects=parts):
        bpy.ops.object.join()
    mw = active.matrix_world.copy()
    active.parent = None
    active.matrix_world = mw
    bpy.data.objects.remove(root, do_unlink=True)
    me = active.data
    me.transform(active.matrix_basis)
    active.matrix_basis.identity()
    for v in me.vertices:
        v.co *= SCALE
    me.update()
    active.name = name
    me.name = name
    return active


# --- Stok birimi: ESD altlığı + tek kart -----------------------------------------------------

def esd_tray(P, root):
    """Alçak antrasit ESD altlığı: taban, hafif yükseltilmiş kenar, köşe dayamaları."""
    W, D = BOARD_W * SCALE + 0.06, BOARD_D * SCALE + 0.07
    box("Altlik", 0, 0, 0, W, D, TRAY_H - 0.012, P["dark"], root, 0.01)
    rim = 0.025
    for s in (-1, 1):
        box("Altlik_kenar", 0, s * (D / 2 - rim / 2), TRAY_H - 0.012, W, rim, 0.018, P["dark"], root, 0.006)
        box("Altlik_kenar", s * (W / 2 - rim / 2), 0, TRAY_H - 0.012, rim, D - 2 * rim, 0.018, P["dark"], root, 0.006)
    # kartı tutan köşe dayamaları (orta gri)
    bx, by = BOARD_W * SCALE / 2, BOARD_D * SCALE / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("Altlik_dayama", sx * (bx + 0.006), sy * (by - 0.04), TRAY_H - 0.012, 0.012, 0.08, 0.04, P["mid"], root, 0.004)
            box("Altlik_dayama", sx * (bx - 0.04), sy * (by + 0.006), TRAY_H - 0.012, 0.08, 0.012, 0.04, P["mid"], root, 0.004)


def stock_unit(P, x=0.0, y=0.0):
    root = link(bpy.data.objects.new("PCB_stok_birimi", None))
    root.empty_display_size = 0.5
    esd_tray(P, root)
    b = build_board("Anakart_PCB_parcalar", P)
    pcb = merge_board(b, "Anakart_PCB")
    pcb.location = (0, 0, TRAY_H - 0.012)
    pcb.parent = root
    root.location = (x, y, 0)
    return root


def tile_marks(P, x=0.0, y=0.0):
    """1 × 1 m stok karosu sınırı (yalnız ölçü göstermek için, oyunda zemin çizer)."""
    for cx in (-0.38, 0.38):
        for cy in (-0.38, 0.38):
            box("Karo_kose", x + cx, y + cy, 0, 0.14, 0.04, 0.003, P["tile"])
            box("Karo_kose", x + cx, y + cy, 0, 0.04, 0.14, 0.003, P["tile"])
    for (cx, cy, sx, sy) in ((0, 0.5, 1.0, 0.01), (0, -0.5, 1.0, 0.01), (0.5, 0, 0.01, 1.0), (-0.5, 0, 0.01, 1.0)):
        box("Karo_sinir", x + cx, y + cy, 0, sx, sy, 0.002, P["mid"])


def build(scene=None):
    global COLL
    scene = scene or bpy.context.scene
    P = palette()
    COLL = bpy.data.collections.new("PCB_stok_birimi")
    scene.collection.children.link(COLL)
    tile_marks(P, 0, 0)
    return stock_unit(P, 0, 0)


if __name__ == "__main__":
    build()
