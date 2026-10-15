"""Oyunun ortak canlı renk paleti (2026-10-15).

Kullanıcı kararı: soluk tonlar yok; zeminde görünür canlı renkler (kırmızı, sarı, turuncu).
Bütün model betikleri vurgu renklerini buradan alır; bir ton değişecekse yalnız burası değişir.

Kullanım:
- turuncu: robotun gövdesi (ve robot arabasının tablası)
- sari:    robotun vurgusu (şerit, motor kapakları, taban halkası, araba şeridi); ayrıca
           güvenlik / sınır öğeleri (çit dikmeleri, stoplar, tamponlar, zemin çizgileri)
- kirmizi: konveyör paletinin köşe takozları
- mavi:    gerekirse ikincil vurgu
"""
RENK = {
    "kirmizi": "#E8302A",
    "turuncu": "#FF7A1A",
    "sari": "#FFC21A",
    "mavi": "#2F6DB5",
}
