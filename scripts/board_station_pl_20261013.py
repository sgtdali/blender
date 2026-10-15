"""Anakart & işlemci istasyonu, Production Line kalıbı (2026-10-13; kurallar: prosedürel/docs/art_bible.md).

Oyunun yerel ekseninde kurulur: Blender x = bant boyunca hücre (a, 0..10), Blender y = -b
(b > 0 kameraya bakan yakın taraf, Godot +z). İstasyon başlangıç hücresinin merkezi (0, 0, 0).
Ayak izi 11 × 9 hücre (a 0..10, b -4..4); iş noktası a = 5; stok blokları a 0-2 / 4-6 / 8-10,
uzak taraf b -2..-4 (PCB, elektronik set, soket seti), yakın taraf b 2..4 (çekirdek, CPU taşıyıcı, kapak).
İkmal girişi (ray durağı) ayak izinin hemen dışında, a = 5, b = -5.

Çıktılar (prosedürel/assets/models/board_station/):
  board_station_pl.glb        sabit istasyon: iç bant, portal, plaka, robotlar (Robot_Far / Robot_Near
                              kökleri), operatör, pult, çit, babalar, alan ve blok çizgileri, boş karo işaretleri,
                              Status_Green / Status_Amber / Status_Red ışık kulesi, Conveyor_Entry / Conveyor_Exit
  stock/unit_<tür>.glb        tek stok birimi (karo merkezinde, taban 0): oyun stok sayısı kadar gösterir
"""
import math
import os

import bpy

ROOT = "C:/Users/tvural.REPKON/Desktop/ProjelerY"
V2 = ROOT + "/blender/scripts/b_style_test_scene_v2_20261013.py"
OUT_DIR = ROOT + "/prosedürel/assets/models/board_station"
BLEND = ROOT + "/blender/output/board_station_pl_20261013/board_station_pl.blend"
KINDS = ("pcb", "bins", "carton", "core", "carrier", "lid")

_v2 = {"__name__": "v2"}
exec(open(V2, encoding="utf-8").read(), _v2)
_v1 = _v2["_v1"]
_v2["LINE_Y"] = 0.0  # yerel çerçevede bant y = 0


def _reset():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    _v1["_MATS"].clear()
    _v1["_MESHES"].clear()
    _v1["COLL"] = bpy.context.scene.collection
    return _v1["palette"]()


def _empty(name, loc):
    e = bpy.data.objects.new(name, None)
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def _export(path, objects):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objects:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_apply=True,
                              export_lights=False, export_cameras=False)


def build_station():
    P = _reset()
    before = set(bpy.data.objects)
    _v1["conveyor"](-0.5, 0.0, 10.5, 0.0, P, items=False)
    _v2["station"](5.0, P, _v1["mat"]("B_tabela_turuncu", "#E2702A", 0.5), True,
                   far=[("pcb", 0), ("bins", 0), ("carton", 0)],
                   near=[("core", 0), ("carrier", 0), ("lid", 0)], margin=0.0)
    made = [o for o in bpy.data.objects if o not in before]
    # Işık kulesi lambaları oyunun durum lambaları olur.
    for ob in made:
        for src, dst in (("Kule_lamp_grn", "Status_Green"), ("Kule_lamp_yel", "Status_Amber"),
                         ("Kule_lamp_red", "Status_Red")):
            if ob.name.startswith(src):
                ob.name = dst
    # Robot parçaları tabanlarının etrafında dönebilsin diye birer köke bağlanır.
    roots = {"Robot_Far": _empty("Robot_Far", (5.9, 1.0, 0.0)),
             "Robot_Near": _empty("Robot_Near", (4.1, -1.0, 0.0))}
    for ob in made:
        if ob.name.startswith("Robot_"):
            root = roots["Robot_Far" if ob.matrix_world.translation.y > 0 else "Robot_Near"]
            mw = ob.matrix_world.copy()
            ob.parent = root
            ob.matrix_world = mw
    entry = _empty("Conveyor_Entry", (-0.5, 0.0, _v1["BELT_Z"]))
    exit_ = _empty("Conveyor_Exit", (10.5, 0.0, _v1["BELT_Z"]))
    work = _empty("Work_Spot", (5.0, 0.0, _v1["BELT_Z"]))
    objs = made + list(roots.values()) + [entry, exit_, work]
    _export(OUT_DIR + "/board_station_pl.glb", objs)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    return len(objs)


def build_units():
    for kind in KINDS:
        P = _reset()
        before = set(bpy.data.objects)
        _v2["stock_unit"](0.0, 0.0, P, kind)
        made = [o for o in bpy.data.objects if o not in before]
        _export(f"{OUT_DIR}/stock/unit_{kind}.glb", made)


def build_all():
    n = build_station()
    build_units()
    build_station()  # sahnede istasyon kalsın (kontrol için)
    return n


if __name__ == "__main__":
    build_all()
