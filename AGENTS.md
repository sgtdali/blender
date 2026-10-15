# Blender atölyesi — ajan talimatları

Bu depo (`blender/`, uzak: https://github.com/sgtdali/blender) **Bilgisayar Fabrikası** oyununun 3B model
atölyesidir. Oyunun kendisi kardeş klasörde: `../prosedürel` (Godot 4.6 projesi, ayrı git deposu).
Bu dosya Codex, Claude ve diğer ajanlar için tek kaynaktır; `CLAUDE.md` buraya yönlendirir.
Kullanıcıyla **Türkçe** konuş. Kullanıcı adım adım, görerek çalışmayı sever: her değişiklikten sonra
görüntü al ve göster, büyük kararlarda önce sor.

## İki klasörün rolü

| Klasör | Rol | Ne durur |
|---|---|---|
| `blender/` (bu depo) | **Atölye**: modellerin kaynağı | `scripts/*.py` (kaynak), `output/<model>_<tarih>/` (.blend + önizleme png) |
| `../prosedürel/` | **Oyun** | yalnız dışa aktarılmış `.glb`'ler (`assets/models/...`) ve Godot kodu |

Akış: `scripts/<model>.py` → (canlı Blender'da dene) → `output/.../<model>.blend` → `scripts/export_godot.py` →
`../prosedürel/assets/models/<kategori>/<id>.glb` + `KATALOG.md` / `katalog.json` → Godot.

**Kurallar**
- Kaynak = betik. Model betikle kurulur; .blend ve .glb betikten yeniden üretilebilir olmalı. Elle
  yapılan Blender değişikliği betiğe işlenmeden "bitti" sayılmaz.
- Oyuna `.glb` elle konmaz/elle düzenlenmez. Yeni model oyuna girecekse `scripts/model_katalogu.py`'ye satır
  ekle, `export_godot.py` ile aktar.
- Her model kendi betiği ve kendi `output/<ad>_<YYYYMMDD>/` klasörü. Mevcut bir model değişiyorsa **aynı
  dosyalar yerinde güncellenir**; yeni tarihli kopya açılmaz (tarih yalnız modelin doğduğu gün).
- Ortak parçalar kopyalanmaz, çağrılır: robot, araba/kızak, konveyör, stok birimleri istasyon betiklerinden
  fonksiyonla kullanılır (örnek: `istasyon_01_anakart_montaji_20261015.py`).

## Araçlar ve komutlar

- Blender 5.2.1: `blender-5.2.1-windows-x64/blender.exe` (depoda değil, yerelde kurulu; `.gitignore`).
- Godot 4.6.1: `C:/Users/tvural.REPKON/Downloads/Godot_v4.6.1-stable_win64.exe/Godot_v4.6.1-stable_win64_console.exe`
- Bir modeli arka planda kur + kaydet: `blender.exe -b --factory-startup --python <betik>` (betiklerin `build(scene)`'i var).
- **Oyuna aktar** (bu klasörden):
  `blender-5.2.1-windows-x64/blender.exe -b --factory-startup --python scripts/export_godot.py -- hepsi`
  (ya da `-- robot palet` gibi id listesi). Ardından Godot içe aktarma:
  `<godot_console> --headless --path ../prosedürel --import`
- Godot önizlemesi (ana oyuna dokunmaz): `<godot_console> --path ../prosedürel --resolution 1600x900
  --script res://tools/preview_yeni_modeller.gd -- <çıktı_klasörü>` → `godot_istasyon_01.png`, `godot_galeri.png`.
- Render çıktı yollarını **mutlak** ver (`os.path.abspath`); göreli yol Blender'da sessizce başka yere yazar.
- STEP/IGES → GLB: `step2glb_occ.py` (OCP, `.occ_venv`), sadece referans CAD için. Üçüncü taraf CAD (KUKA vb.)
  oyuna ve bu depoya girmez.

## Canlı Blender (MCP) ile çalışma

Kullanıcı genelde modelin .blend'ini Blender'da açıp MCP eklentisini başlatır (port 9876). Küçük
düzeltmelerde hızlı döngü: betiği düzenle → canlı sahnede yeniden kur → `look` ile bak → göster.
- Önce `bpy.data.filepath` ile açık dosyayı kontrol et.
- `bpy.ops.wm.read_homefile` / dosya açma MCP bağlantısını öldürür. Başka model gerekiyorsa geçici sahne kur
  (`bpy.data.scenes.new`), iş bitince `bpy.data.libraries.write(path, {scene})` ile kendi dosyasına yaz,
  geçici sahneyi sil.
- Yeniden kurma fonksiyonunu `bpy.app.driver_namespace` içinde tutmak pratik (örn. `robot_rebuild`).
- MCP kapalıysa arka plan (`-b`) + render ile devam et.

## Görsel kurallar (kullanıcı kararları)

- **Izgara:** oyun 1 × 1 m karolarla kurulur. Stok alanında bir karoda **tek birim** durur; parçalar tek tek taşınır.
- **Eksenler:** x = bant akışı, y = arka, z = yukarı. Oyun kamerası ortografik, ~30° yükseklik, −x/−y'den bakar
  (`look` yönü `[-1, -1, 0.816]`). Godot'a geçişte (x, y, z)_Blender → (x, z, −y)_Godot.
- **Okunurluk > gerçekçilik:** parçalar büyütülmüş, sade, uzaktan seçilebilir.
- **Renk:** vurgular `scripts/renk_paleti.py`'den (canlı: kırmızı `#E8302A`, turuncu `#FF7A1A`, sarı `#FFC21A`,
  mavi `#2F6DB5`). Soluk/pastel vurgu yok (camgöbeği reddedildi). Büyük beyaz yüzey yok. Robot gövdesi turuncu +
  sarı vurgu; palet köşe takozları kırmızı; güvenlik/sınır öğeleri sarı.
- **Malzeme:** düz Principled renk (doku yok) → glTF'ye sorunsuz çıkar. sRGB hex → `mat(name, hex, rough, metal, emit)`.
- **Radyus:** sert birleşimler yerine radyuslu geçiş tercih edilir (döküm kabuk / döndürülmüş profil; bkz. robot
  `turret_shell`, `riser`, `lathe` + `fillet_foot`). Boolean + bevel kenarlarda bozuluyor, kullanma.
- Art bible (`../prosedürel/docs/art_bible.md`) **gevşek referans**; kullanıcı kararları geçerli, çelişkiyi
  tekrar tekrar açma.

## Model kütüphanesi (Ekim 2026)

| Betik | Ne | Not |
|---|---|---|
| `anakart_pcb_20261014.py` | Anakart PCB stok birimi + **ortak yardımcılar** (`mat`, `box`, `disc`, `link`, `tile_marks`, `palette`) | Diğer betikler `exec` ile yükler; `H["COLL"]` hedef koleksiyon |
| `pcb_girdileri_20261014.py` | Yalıtkan levha, bakır folyo | `build_sheet`, `build_foil` |
| `elektronik_bilesen_seti_…`, `soket_baglanti_seti_…`, `bos_kasa_…`, `metal_levha_…`, `baglanti_elemani_seti_…` | 01 istasyonunun girdileri | 1 × 1 m stok birimleri |
| `anakartli_kasa_20261015.py` | 01'in çıktısı (soket boş; işlemci 02'de) | |
| `robot_20261015.py` | **Oyunun robotu**: 6 eksen, eklem hiyerarşisi (`set_pose`, `REST`), `robot(P, ad, poz, konum, rz, plate)` | Plakalı (zemin) / plakasız (araba) |
| `robot_arabasi_20261015.py` | Robot kızağı (1.5 karo genişlik), araba (1 × 1 tabla), kapaklı kremayer, kablo zinciri | `ray`, `araba`, `kablo_zinciri` |
| `konveyor_20261015.py` | Paletli bant: `duz` (1 m), `donus` (1 × 1 döner tabla, tabla ayrı düğüm), `durak` (montaj durağı), `palet` | Bant üstü 0.75 m |
| `istasyon_01_anakart_montaji_20261015.py` | 01 hücresi: ortadan paletli bant + durak, iki yanda kızaklı robot, 4 × (3 × 3) stok bloğu, çit | `yerlesim()` → oyun yuvaları |
| `renk_paleti.py` | Ortak canlı renkler | |
| `model_katalogu.py`, `export_godot.py` | Oyuna aktarma | |

Eski/deneme betikleri (`b_style_test_scene_*`, `board_station_pl_*`, `floor_study_*`) tarihsel; yeni işte kullanma.

## Tasarım kaynakları (oyun deposunda)

- İstasyonlar ve girdiler: `../prosedürel/docs/İstasyonlar/` (özellikle `Anakart ve İşlemci - Giriş Çıkış Akışı.md`).
- Güncel tasarım indeksi: `../prosedürel/docs/tasarim/00_GUNCEL_TASARIM.md`.
- Görsel kararların özeti: `../prosedürel/docs/tasarim/gorsel_uretim_hatti.md`.

## Açık işler

- Konveyör: bant başı/sonu modülü; kızak için modüler (karo karo) ray; kablo zincirinin araba hareketine göre
  oyunda yeniden şekillenmesi.
- Robot pozları / animasyon (Godot'ta eklem düğümleri; `tools/preview_yeni_modeller.gd` `_pose` örneği).
- 02 işlemci montaj istasyonu ve girdileri (silikon çekirdek, taşıyıcı, ısı yayıcı kapak).
- Bant ve 01 hücresi oyunda (`../prosedürel/world/istasyon_01_view.gd`, `factory_view.gd`; hücre 11 × 11 karo,
  istasyon betiği bu sınıra sığacak şekilde). Sıradaki: diğer istasyonların yeni hatta geçmesi.

## Git

- Bu depo: `blender/`. Commit mesajları Türkçe, kısa. Büyük ikili (Blender kurulumu, venv, `.blend1`,
  üçüncü taraf CAD) girmez — `.gitignore`.
- Oyun deposu ayrı; oraya giden `.glb`'ler orada commit edilir.
