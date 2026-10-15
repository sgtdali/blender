# Bilgisayar Fabrikası — Blender atölyesi

Oyunun (`../prosedürel`, Godot 4.6) 3B modellerinin kaynak betikleri ve .blend dosyaları.

- `scripts/` — her model bir Python betiği (kaynak). `renk_paleti.py` ortak renkler.
- `output/<model>_<tarih>/` — betikten üretilen .blend ve önizleme görselleri.
- `scripts/model_katalogu.py` + `scripts/export_godot.py` — modelleri oyuna `.glb` olarak aktarır
  (`../prosedürel/assets/models/`, katalog: `KATALOG.md`).

Oyuna aktarma:

```
blender-5.2.1-windows-x64/blender.exe -b --factory-startup --python scripts/export_godot.py -- hepsi
```

Çalışma kuralları ve ayrıntılar: [AGENTS.md](AGENTS.md).
