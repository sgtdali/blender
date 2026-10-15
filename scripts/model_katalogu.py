"""Oyuna giden modellerin tek listesi (kaynak betik → oyundaki .glb).

export_godot.py bu listeyi okur. Yeni bir model oyuna girecekse buraya bir satır eklenir;
oyunun assets/models/ klasörüne elle .glb konmaz.

Alanlar:
- id:       dosya adı (assets/models/<kategori>/<id>.glb); değişmez, oyun kodu buna bağlanır
- kategori: assets/models altındaki klasör
- betik:    scripts/ altındaki kaynak betik
- kur:      betikteki kurulum fonksiyonu
            "build"            → build(scene) (betiğin kendi önizleme kurulumu)
            ("fonk", {kw})     → fonk(P, **kw); P = betiğin palette()'i
- tur:      "tek_mesh"  — her şey tek mesh'e birleşir (stok birimleri, sabit parçalar)
            "hiyerarsi" — düğüm ağacı korunur (robot eklemleri, döner tabla)
            "istasyon"  — hareketli kısımlar (araba+robot, paletler) ayrı, gerisi tek statik mesh
- not:      oyun tarafı için kısa bilgi (KATALOG.md'ye yazılır)
"""

MODELLER = [
    # --- 01 anakart montajı: girdiler (stok birimi = 1 × 1 m karoda tek birim) ---
    dict(id="bos_kasa", kategori="stok", betik="bos_kasa_20261014.py", kur="build", tur="tek_mesh",
         not_="Boş kasa, yan yatık, sol kapak açık. 0.64 × 0.56 m. 01'in girdisi, 01A'nın çıktısı."),
    dict(id="anakart_pcb", kategori="stok", betik="anakart_pcb_20261014.py", kur="build", tur="tek_mesh",
         not_="ESD altlığında boş anakart PCB (0.84 m). 01'in girdisi, 01B'nin çıktısı."),
    dict(id="elektronik_bilesen_seti", kategori="stok", betik="elektronik_bilesen_seti_20261014.py",
         kur="build", tur="tek_mesh", not_="Kit tablası: SMD makaraları, JEDEC tepsi, bölmeli kutu. 01'in girdisi."),
    dict(id="soket_baglanti_seti", kategori="stok", betik="soket_baglanti_seti_20261014.py", kur="build",
         tur="tek_mesh", not_="Köpüklü çanta: CPU soketi, RAM/PCIe yuvaları, ATX, I/O. 01'in girdisi."),
    dict(id="metal_levha", kategori="stok", betik="metal_levha_20261014.py", kur="build", tur="tek_mesh",
         not_="Çelik rulo (sac bobini) paletin üstünde. 01A'nın girdisi."),
    dict(id="baglanti_elemani_seti", kategori="stok", betik="baglanti_elemani_seti_20261014.py", kur="build",
         tur="tek_mesh", not_="Parça kovasında vida/somun/pul yığını. 01A'nın girdisi."),
    dict(id="yalitkan_levha", kategori="stok", betik="pcb_girdileri_20261014.py", kur="build_sheet",
         tur="tek_mesh", not_="Yeşil FR4 levha, köşe koruyucu + çember. 01B'nin girdisi."),
    dict(id="bakir_folyo", kategori="stok", betik="pcb_girdileri_20261014.py", kur="build_foil",
         tur="tek_mesh", not_="Bakır folyo rulosu paletin üstünde. 01B'nin girdisi."),
    # --- 02 işlemci montajı: girdiler ---
    dict(id="silikon_cekirdek_temel", kategori="stok", betik="islemci_girdileri_20261015.py",
         kur=("silikon_cekirdek", dict(seviye="temel")), tur="tek_mesh",
         not_="Taşıma kutusunda silikon plaka, mavi seviye şeridi. 02'nin girdisi (die_basic)."),
    dict(id="silikon_cekirdek_orta", kategori="stok", betik="islemci_girdileri_20261015.py",
         kur=("silikon_cekirdek", dict(seviye="orta")), tur="tek_mesh",
         not_="Aynı plaka, turuncu seviye şeridi. 02'nin girdisi (die_mid)."),
    dict(id="silikon_cekirdek_ust", kategori="stok", betik="islemci_girdileri_20261015.py",
         kur=("silikon_cekirdek", dict(seviye="ust")), tur="tek_mesh",
         not_="Aynı plaka, kırmızı seviye şeridi. 02'nin girdisi (die_high)."),
    dict(id="islemci_tasiyicisi", kategori="stok", betik="islemci_girdileri_20261015.py",
         kur=("islemci_tasiyicisi", {}), tur="tek_mesh",
         not_="Siyah JEDEC tepside 3 × 2 yeşil taşıyıcı. 02'nin girdisi (cpu_substrate), 02A'nın çıktısı."),
    dict(id="isi_yayici_kapak", kategori="stok", betik="islemci_girdileri_20261015.py",
         kur=("isi_yayici_kapak", {}), tur="tek_mesh",
         not_="Açık gri tepside 3 × 2 gümüş kapak yığını. 02'nin girdisi (cpu_lid), 02B'nin çıktısı."),
    # --- ürün (bant üstünde paletle taşınan iş) ---
    dict(id="anakartli_kasa", kategori="urun", betik="anakartli_kasa_20261015.py", kur="build", tur="tek_mesh",
         not_="01'in çıktısı: kasada anakart, soket boş (işlemci 02'de). Palet üstünde PAL_T yukarıda durur."),
    dict(id="islemcili_kasa", kategori="urun", betik="islemcili_kasa_20261015.py", kur="build", tur="tek_mesh",
         not_="02'nin çıktısı: anakartlı kasa + sokette işlemci (kol kapalı). Palet üstünde PAL_T yukarıda."),
    # --- robot ---
    dict(id="robot", kategori="robot", betik="robot_20261015.py", kur="build", tur="hiyerarsi",
         not_="6 eksenli robot, 1 × 1 m taban plakalı (zemine sabit). Eklem düğümleri: *_govde (a1, z), "
              "*_alt_kol (a2, y), *_ust_kol (a3, y), *_on_kol (a4, x), *_bilek (a5, y), *_flans (a6, x), "
              "*_tutucu (uç). glTF extras: eklem, eksen. Poz = düğümün yerel dönüşü (Blender ekseni; Godot'ta "
              "Y-yukarı dönüşüme dikkat)."),
    dict(id="robot_plakasiz", kategori="robot", betik="robot_20261015.py",
         kur=("robot", dict(name="Robot", plate=False)), tur="hiyerarsi",
         not_="Aynı robot, plakasız: robot arabasının tablasına oturur."),
    dict(id="robot_arabasi", kategori="robot", betik="robot_arabasi_20261015.py", kur=("araba", {}),
         tur="tek_mesh", not_="Kızak arabası, 1 × 1 m tabla; robot_plakasiz bunun üstüne (DECK_TOP) bağlanır."),
    dict(id="kizak_10karo", kategori="robot", betik="robot_arabasi_20261015.py", kur=("ray", dict(tiles=10)),
         tur="tek_mesh", not_="10 karo uzunluğunda kızak (1.5 karo genişlik), x = 0..10. Kablo zinciri yok "
                             "(araba konumuna bağlı; oyunda ayrıca çözülecek)."),
    # --- konveyör (paletli bant, 3 × 3 modüller: ortada 1 m bant, yanlarda yürüme yolu + 0.7 m korkuluk) ---
    dict(id="konveyor_duz", kategori="konveyor", betik="konveyor_20261015.py", kur=("duz", {}), tur="tek_mesh",
         not_="3 × 3 düz modül, x = −1.5..1.5, bant üstü 0.75 m; yanlarda yol + korkuluk."),
    dict(id="konveyor_bant_1m", kategori="konveyor", betik="konveyor_20261015.py", kur=("bant", {}), tur="tek_mesh",
         not_="Yalnız 1 m bant (yol/korkuluk yok), x = −0.5..0.5; istasyonların iç bandı için."),
    dict(id="konveyor_durak", kategori="konveyor", betik="konveyor_20261015.py", kur=("durak", {}),
         tur="tek_mesh", not_="3 × 3 montaj durağı: durdurucu, kaldırma/konumlama, sensör, ışık kulesi; yanlarda yol."),
    dict(id="konveyor_donus", kategori="konveyor", betik="konveyor_20261015.py", kur=("donus", {}),
         tur="hiyerarsi", not_="3 × 3; ortada döner tabla (*_tablasi, Godot y ekseninde döner). Her yan için iki düğüm: "
         "*_kol_<xp|yp|xn|yn> (açık yan, 1 m bant kolu) ve *_kapali_<…> (kapalı yan, yol + korkuluk); birini göster. "
         "xp = Blender +x = Godot +x, yp = Blender +y = Godot −z."),
    dict(id="palet", kategori="konveyor", betik="konveyor_20261015.py", kur=("palet", {}), tur="tek_mesh",
         not_="Taşıyıcı palet 0.72 × 0.66; altı bant üstüne (0.75) oturur, kasa PAL_T (0.03) yukarıda."),
    # --- istasyonlar ---
    dict(id="istasyon_01_anakart_montaji", kategori="istasyon", betik="istasyon_01_anakart_montaji_20261015.py",
         kur="build", tur="istasyon",
         not_="01 anakart montaj hücresi (~10.6 × 11.2 m + bant). Arabalar+robotlar ve paletler ayrı düğüm."),
    dict(id="istasyon_02_islemci_montaji", kategori="istasyon", betik="istasyon_02_islemci_montaji_20261015.py",
         kur="build", tur="istasyon",
         not_="02 işlemci montaj hücresi (01 ile aynı iskelet, 11 × 11). 3 stok bloğu + ön sağda paketleme presi. "
              "Arabalar+robotlar ve paletler ayrı düğüm; yerleşimde pres yuvası (tur=pres)."),
]
