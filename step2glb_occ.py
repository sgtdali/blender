"""STEP -> GLB (OCP / Open Cascade). Parça adları ve renkleri korunur, birim metreye, eksen Z-up'tan glTF Y-up'a çevrilir.

Kullanım:
    .occ_venv\\Scripts\\python step2glb_occ.py <girdi.step> <cikti.glb> [sapma_mm=0.5] [aci_rad=0.5]
"""
import sys
import time

from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.IFSelect import IFSelect_RetDone
from OCP.Message import Message_ProgressRange
from OCP.RWGltf import RWGltf_CafWriter
from OCP.RWMesh import RWMesh_CoordinateSystem_Zup
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_AsciiString, TCollection_ExtendedString
from OCP.collections import IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString, Sequence_TDF_Label
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_DocumentTool


def main():
    src, dst = sys.argv[1], sys.argv[2]
    defl = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    ang = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    t = time.time()

    doc = TDocStd_Document(TCollection_ExtendedString("XmlXCAF"))
    rd = STEPCAFControl_Reader()
    rd.SetNameMode(True)
    rd.SetColorMode(True)
    rd.SetLayerMode(True)
    if rd.ReadFile(src) != IFSelect_RetDone:
        sys.exit("STEP okunamadı")
    if not rd.Transfer(doc):
        sys.exit("STEP aktarılamadı")
    print(f"okundu {time.time() - t:.1f}s", flush=True)

    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    free = Sequence_TDF_Label()
    st.GetFreeShapes(free)
    for i in range(1, free.Length() + 1):
        BRepMesh_IncrementalMesh(st.GetShape_s(free.Value(i)), defl, False, ang, True)
    print(f"üçgenlendi {time.time() - t:.1f}s", flush=True)

    w = RWGltf_CafWriter(TCollection_AsciiString(dst), True)
    conv = w.ChangeCoordinateSystemConverter()
    conv.SetInputLengthUnit(0.001)  # OCCT STEP okuyucusu geometriyi mm'ye çevirir
    conv.SetInputCoordinateSystem(RWMesh_CoordinateSystem_Zup)
    if not w.Perform(doc, IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString(), Message_ProgressRange()):
        sys.exit("GLB yazılamadı")
    print(f"yazıldı {dst} {time.time() - t:.1f}s", flush=True)


if __name__ == "__main__":
    # Büyük montajlarda OCCT derin özyineleme yapar; Windows ana iş parçacığının yığını yetmeyip çöker.
    import threading
    threading.stack_size(256 * 1024 * 1024 - 4096)
    th = threading.Thread(target=main)
    th.start()
    th.join()
