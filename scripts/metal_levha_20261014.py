"""Metal levha (2026-10-14): 01A boş kasa üretiminin dış ikmal girdisi.

Kural (kullanıcı): parçalar tek tek taşınır, bir stok karosunda (1 × 1 m) tek birim durur.
Kullanıcı kararı: düz sac yerine çelik rulo (sac bobini). Tasarım bakır folyo rulosunun aynısı
(pcb_girdileri_20261014.copper_foil), yalnız rulo renkleri çelik.

Çıktı: output/metal_levha_20261014/metal_levha.blend
"""
import bpy

SCRIPTS = "C:/Users/tvural.REPKON/Desktop/ProjelerY/blender/scripts"
G = {"__name__": "pcb_girdileri_yardimci"}
exec(open(SCRIPTS + "/pcb_girdileri_20261014.py", encoding="utf-8").read(), G)
mat, tile_marks = G["mat"], G["tile_marks"]


def palette():
    P = G["palette"]()
    # bakır rulonun malzeme anahtarları çelik renklerle değiştirilir
    P["copper"] = mat("M_celik_rulo", "#C3C9CD", 0.28, 0.8)
    P["copper_dark"] = mat("M_celik_rulo_koyu", "#8C9399", 0.35, 0.8)
    return P


def metal_levha(P, x=0.0, y=0.0):
    root = G["copper_foil"](P, x, y)
    root.name = "Metal_levha_stok"
    for o in root.children_recursive:
        if o.name.startswith("Bakir_rulo"):
            o.name = "Celik_rulo"
    return root


def build(scene=None):
    scene = scene or bpy.context.scene
    P = palette()
    c = bpy.data.collections.new("Metal_levha")
    scene.collection.children.link(c)
    G["set_coll"](c)
    tile_marks(P, 0, 0)
    return metal_levha(P, 0, 0)


if __name__ == "__main__":
    build()
