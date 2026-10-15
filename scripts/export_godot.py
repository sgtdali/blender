"""Modelleri oyuna (.glb) aktarır: blender/scripts → prosedürel/assets/models.

Kullanım (blender/ klasöründen):
  blender-5.2.1-windows-x64/blender.exe -b --factory-startup --python scripts/export_godot.py -- hepsi
  blender-5.2.1-windows-x64/blender.exe -b --factory-startup --python scripts/export_godot.py -- robot palet

Her model boş bir sahnede kaynak betiğinden yeniden kurulur (model_katalogu.py), önizleme yardımcıları
(karo işaretleri) silinir, koleksiyon örnekleri gerçek objeye çevrilir, modifikatörler uygulanır ve
katalogdaki tura göre birleştirilir. Sonunda assets/models/KATALOG.md ve katalog.json yeniden yazılır
(dışa aktarılmayan modellerin önceki kayıtları korunur).
"""
import datetime
import json
import math
import os
import sys

import bpy
from mathutils import Vector

BLENDER_DIR = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender"
SCRIPTS = BLENDER_DIR + "/scripts"
GAME = "C:/Users/tvural.REPKON/Desktop/ProjelerY/prosedürel"
MODELS = GAME + "/assets/models"

K = {}
exec(open(SCRIPTS + "/model_katalogu.py", encoding="utf-8").read(), K)
MODELLER = {m["id"]: m for m in K["MODELLER"]}


# --- Sahne yardımcıları ------------------------------------------------------------------------

def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def load_script(name):
    ns = {"__name__": "export_" + name.replace(".py", "")}
    exec(open(SCRIPTS + "/" + name, encoding="utf-8").read(), ns)
    return ns


def build(m, scene):
    ns = load_script(m["betik"])
    kur = m["kur"]
    if isinstance(kur, str):
        ns[kur](scene)
        return ns
    fn, kw = kur
    c = bpy.data.collections.new(m["id"])
    scene.collection.children.link(c)
    H = ns.get("H") or ns.get("G", {}).get("H")
    H["COLL"] = c
    P = ns["palette"]()
    if fn == "robot":                          # robot(P, name, pose, location, rz, plate)
        ns["robot"](P, kw.get("name", "Robot"), None, (0, 0, 0), 0.0, plate=kw.get("plate", True))
    else:
        ns[fn](P, **kw)
    return ns


def remove_helpers(scene):
    for o in list(scene.objects):
        if o.name.startswith("Karo_") or o.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(o, do_unlink=True)


def realize_instances(scene):
    """Koleksiyon örneklerini (instance empty) gerçek objelere çevirir; örnek empty'nin çocuğu olur."""
    changed = True
    while changed:
        changed = False
        for e in [o for o in scene.objects if o.instance_type == "COLLECTION" and o.instance_collection]:
            src = e.instance_collection
            mw = e.matrix_world.copy()
            copies = {}
            for o in src.all_objects:
                if o.name.startswith("Karo_"):
                    continue
                n = o.copy()
                for c in list(n.users_collection):
                    c.objects.unlink(n)
                for c in e.users_collection:
                    c.objects.link(n)
                copies[o] = n
            for o, n in copies.items():
                world = mw @ o.matrix_world
                n.parent = copies.get(o.parent, e)
                n.matrix_world = world
            e.instance_type = "NONE"
            e.instance_collection = None
            changed = True
            break


def apply_modifiers(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type == "MESH" and o.modifiers:
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            o.modifiers.clear()
            o.data = me


def join(objs, name):
    """Mesh'leri tek objede birleştirir; sonuç dünya koordinatında, dönüşümü sıfır."""
    meshes = [o for o in objs if o.type == "MESH"]
    if not meshes:
        return None
    apply_modifiers(meshes)
    for o in meshes:                           # ortak mesh'ler (örnekler) bozulmasın
        if o.data.users > 1:
            o.data = o.data.copy()
    active = meshes[0]
    mws = {o: o.matrix_world.copy() for o in meshes}
    for o in meshes:
        o.parent = None
        o.matrix_world = mws[o]
    with bpy.context.temp_override(active_object=active, selected_editable_objects=meshes,
                                   selected_objects=meshes):
        bpy.ops.object.join()
    active.data.transform(active.matrix_world)
    active.matrix_world.identity()
    active.name = active.data.name = name
    return active


def subtree(o):
    return [o] + list(o.children_recursive)


# --- Türler ------------------------------------------------------------------------------------

def prepare(m, scene):
    tur = m["tur"]
    if tur == "tek_mesh":
        objs = list(scene.objects)
        join(objs, m["id"])
        for o in list(scene.objects):
            if o.type == "EMPTY":
                bpy.data.objects.remove(o, do_unlink=True)
    elif tur == "hiyerarsi":
        apply_modifiers(list(scene.objects))
    elif tur == "istasyon":
        # stok birimleri ve paletler export()'ta çıkarıldı (yerleşim dosyasına yazılır).
        # Arabalar (robotlarıyla) ayrı düğüm; gerisi tek statik mesh.
        cars = [o for o in scene.objects if o.name.startswith("Kizak_") and o.name.endswith("_arabasi")]
        keep = set()
        for car in cars:
            mw = car.matrix_world.copy()
            car.parent = None
            car.matrix_world = mw
            keep.update(subtree(car))
        apply_modifiers(list(keep))
        keep_names = {o.name for o in keep}
        static = [o for o in scene.objects if o.name not in keep_names]
        join(static, m["id"] + "_statik")
        for o in list(scene.objects):
            if o.type == "EMPTY" and o.name not in keep_names:
                bpy.data.objects.remove(o, do_unlink=True)


def bbox(scene):
    pts = [o.matrix_world @ Vector(c) for o in scene.objects if o.type == "MESH" for c in o.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return [round(v, 3) for v in lo], [round(v, 3) for v in hi]


def export(m):
    scene = fresh_scene()
    ns = build(m, scene)
    remove_helpers(scene)
    if m["tur"] == "istasyon":                 # stok/palet yerleri: oyun için yan dosya
        write_layout(m, ns)
        drop = {c.name for o in scene.objects if o.name.split(".")[0].endswith("_stok")
                or o.name.startswith("Palet_") for c in subtree(o)}   # oyunun dolduracakları .glb'ye girmez
        for nm in drop:
            bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    realize_instances(scene)
    prepare(m, scene)
    out_dir = MODELS + "/" + m["kategori"]
    os.makedirs(out_dir, exist_ok=True)
    path = out_dir + "/" + m["id"] + ".glb"
    lo, hi = bbox(scene)
    nodes = sorted(o.name for o in scene.objects)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=False,
                              export_apply=True, export_extras=True, export_yup=True)
    return dict(id=m["id"], kategori=m["kategori"], tur=m["tur"],
                glb="res://assets/models/%s/%s.glb" % (m["kategori"], m["id"]),
                kaynak="blender/scripts/" + m["betik"], not_=m.get("not_", ""),
                boyut_m=[round(hi[i] - lo[i], 3) for i in range(3)], alt=lo, ust=hi,
                dugum_sayisi=len(nodes), dugumler=nodes if len(nodes) <= 30 else nodes[:30] + ["..."],
                tarih=datetime.date.today().isoformat())


def to_godot(v):
    """Blender (x, y, z-yukarı) → Godot (x, y-yukarı, z) : (x, z, −y)."""
    return [round(v[0], 4) + 0.0, round(v[2], 4) + 0.0, round(-v[1], 4) + 0.0]


def write_layout(m, ns):
    slots = ns["yerlesim"]()
    for sl in slots:
        sl["konum_godot"] = to_godot(sl.pop("konum"))
        sl["glb"] = next(("res://assets/models/%s/%s.glb" % (x["kategori"], x["id"])
                          for x in K["MODELLER"] if x["id"] == sl["model"]), None)
    out_dir = MODELS + "/" + m["kategori"]
    os.makedirs(out_dir, exist_ok=True)
    with open(out_dir + "/" + m["id"] + "_yerlesim.json", "w", encoding="utf-8") as f:
        json.dump(dict(istasyon=m["id"], aciklama="Godot koordinatı (y yukarı), istasyon düğümüne göre. "
                       "stok: sira 0 ilk dolan / son tüketilen; durak: paletin durduğu yer.",
                       yuvalar=slots), f, ensure_ascii=False, indent=1)


# --- Katalog -----------------------------------------------------------------------------------

def write_catalog(results):
    jpath = MODELS + "/katalog.json"
    old = {}
    if os.path.exists(jpath):
        with open(jpath, encoding="utf-8") as f:
            old = {r["id"]: r for r in json.load(f)}
    old.update({r["id"]: r for r in results})
    order = [mid for mid in MODELLER if mid in old]
    rows = [old[mid] for mid in order]
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    lines = [
        "# Model kataloğu (otomatik üretilir — elle düzenleme)",
        "",
        "Bu dosya `blender/scripts/export_godot.py` tarafından yazılır. Kaynak: "
        "[sgtdali/blender](https://github.com/sgtdali/blender) deposu, kardeş klasör `../blender`.",
        "Modeli değiştirmek için .glb'yi değil kaynak betiği düzenle, sonra dışa aktarmayı yeniden çalıştır.",
        "Eksenler: Blender'da x = bant akışı, z = yukarı; glTF/Godot'ta y yukarı (x aynı, Blender −y → Godot z).",
        "Ölçü birimi metre; oyun ızgarası 1 × 1 m karo.",
        "",
        "| id | yol | tür | boyut (x × y × z, Blender m) | not | kaynak | tarih |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        b = r["boyut_m"]
        lines.append("| %s | `%s` | %s | %.2f × %.2f × %.2f | %s | `%s` | %s |" % (
            r["id"], r["glb"], r["tur"], b[0], b[1], b[2], r["not_"], r["kaynak"], r["tarih"]))
    with open(MODELS + "/KATALOG.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["hepsi"]
    ids = list(MODELLER) if (not args or args == ["hepsi"]) else args
    unknown = [i for i in ids if i not in MODELLER]
    if unknown:
        raise SystemExit("Bilinmeyen model: %s. Katalog: %s" % (unknown, list(MODELLER)))
    results = []
    for mid in ids:
        r = export(MODELLER[mid])
        print("AKTARILDI", mid, r["glb"], r["boyut_m"], r["dugum_sayisi"], "düğüm")
        results.append(r)
    write_catalog(results)
    print("BITTI", len(results))


main()
