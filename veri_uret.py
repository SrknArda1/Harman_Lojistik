"""
HarmanLojistik — Örnek veri üretici script.
NumPy ile gerçekçi sahte CSV verileri oluşturur.
"""

import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Veri klasörü yolu
VERI_KLASORU = os.path.join(os.path.dirname(__file__), "data")
np.random.seed(42)

# Ürün ve kategori tanımları
URUNLER = {
    "Buğday": "Tahıl",
    "Arpa": "Tahıl",
    "Mısır": "Tahıl",
    "Ayçiçeği": "Yağlı Tohum",
    "Soya": "Yağlı Tohum",
    "Mercimek": "Baklagil",
    "Nohut": "Baklagil",
    "Pirinç": "Tahıl",
}

ROTALAR = [
    "İstanbul-Ankara",
    "Ankara-İzmir",
    "İzmir-Bursa",
    "Bursa-Adana",
    "Adana-Gaziantep",
    "Gaziantep-Konya",
    "Konya-Samsun",
    "Samsun-Trabzon",
]

SURUCULER = [
    "Ahmet Yılmaz", "Mehmet Kaya", "Ali Demir", "Fatma Şahin",
    "Hasan Öztürk", "Ayşe Çelik", "Mustafa Arslan", "Zeynep Aydın",
    "İbrahim Koç", "Elif Yıldız",
]


def _rastgele_tarih(baslangic: datetime, gun_sayisi: int, n: int) -> np.ndarray:
    """Belirli aralıkta rastgele tarihler üretir."""
    offsets = np.random.randint(0, gun_sayisi, size=n)
    return np.array([baslangic + timedelta(days=int(d)) for d in offsets])


def depo_stok_uret(satir_sayisi: int = 220) -> pd.DataFrame:
    """Depo stok verisi üretir."""
    urun_listesi = list(URUNLER.keys())
    silo_sayisi = 40

    silo_idler = [f"SILO-{i:03d}" for i in range(1, silo_sayisi + 1)]
    secilen_silolar = np.random.choice(silo_idler, size=satir_sayisi, replace=True)

    urun_adi = np.random.choice(urun_listesi, size=satir_sayisi)
    kategori = [URUNLER[u] for u in urun_adi]

    doluluk = np.clip(np.random.normal(65, 22, satir_sayisi), 5, 100).round(1)
    fire_orani = np.clip(np.random.exponential(2.5, satir_sayisi), 0.1, 15).round(2)

    baslangic = datetime(2024, 1, 1)
    giris_tarihi = _rastgele_tarih(baslangic, 400, satir_sayisi)
    son_kullanma = np.array([
        g + timedelta(days=int(np.random.randint(180, 540)))
        for g in giris_tarihi
    ])

    bozulma_riski = np.clip(
        (100 - doluluk) * 0.01 + fire_orani * 0.3 + np.random.uniform(0, 0.5, satir_sayisi),
        0, 10,
    ).round(2)

    df = pd.DataFrame({
        "silo_id": secilen_silolar,
        "urun_adi": urun_adi,
        "kategori": kategori,
        "doluluk_orani": doluluk,
        "giris_tarihi": giris_tarihi,
        "son_kullanma_tarihi": son_kullanma,
        "bozulma_riski": bozulma_riski,
        "fire_orani": fire_orani,
    })

    # Bilerek eksik değerler ekle (%5 civarı)
    nan_indeks = np.random.choice(satir_sayisi, size=int(satir_sayisi * 0.05), replace=False)
    for idx in nan_indeks[: len(nan_indeks) // 3]:
        df.loc[idx, "doluluk_orani"] = np.nan
    for idx in nan_indeks[len(nan_indeks) // 3: 2 * len(nan_indeks) // 3]:
        df.loc[idx, "fire_orani"] = np.nan
    for idx in nan_indeks[2 * len(nan_indeks) // 3:]:
        df.loc[idx, "bozulma_riski"] = np.nan

    return df


def nakliye_uret(satir_sayisi: int = 220) -> pd.DataFrame:
    """Nakliye sefer verisi üretir."""
    sefer_idler = [f"SEF-{i:05d}" for i in range(1, satir_sayisi + 1)]
    arac_idler = [f"ARAC-{np.random.randint(1, 25):03d}" for _ in range(satir_sayisi)]
    rotalar = np.random.choice(ROTALAR, size=satir_sayisi)
    mesafe = np.clip(np.random.normal(450, 150, satir_sayisi), 80, 900).round(0)
    sure = (mesafe / np.random.uniform(0.8, 1.2, satir_sayisi) * 1.2).astype(int)
    yakit = (mesafe * np.random.uniform(0.28, 0.42, satir_sayisi)).round(1)
    surucu = np.random.choice(SURUCULER, size=satir_sayisi)
    maliyet = (mesafe * np.random.uniform(4.5, 7.5, satir_sayisi) + yakit * 35).round(2)

    baslangic = datetime(2024, 6, 1)
    tarih = _rastgele_tarih(baslangic, 300, satir_sayisi)

    df = pd.DataFrame({
        "sefer_id": sefer_idler,
        "arac_id": arac_idler,
        "rota": rotalar,
        "mesafe_km": mesafe,
        "sure_dk": sure,
        "yakit_litre": yakit,
        "surucu": surucu,
        "maliyet_tl": maliyet,
        "tarih": tarih,
    })

    # Eksik değerler
    nan_indeks = np.random.choice(satir_sayisi, size=int(satir_sayisi * 0.04), replace=False)
    for i, idx in enumerate(nan_indeks):
        if i % 3 == 0:
            df.loc[idx, "yakit_litre"] = np.nan
        elif i % 3 == 1:
            df.loc[idx, "sure_dk"] = np.nan
        else:
            df.loc[idx, "maliyet_tl"] = np.nan

    return df


def operasyonel_uret(satir_sayisi: int = 220) -> pd.DataFrame:
    """Operasyonel sensör ve bakım verisi üretir."""
    silo_sayisi = 40
    silo_idler = [f"SILO-{i:03d}" for i in range(1, silo_sayisi + 1)]
    secilen = np.random.choice(silo_idler, size=satir_sayisi, replace=True)

    sicaklik = np.clip(np.random.normal(22, 5, satir_sayisi), 10, 38).round(1)
    nem = np.clip(np.random.normal(55, 12, satir_sayisi), 20, 85).round(1)
    enerji = np.clip(np.random.normal(120, 35, satir_sayisi), 40, 250).round(1)
    birim_maliyet = np.clip(np.random.normal(2.8, 0.6, satir_sayisi), 1.0, 5.5).round(2)

    baslangic = datetime(2023, 6, 1)
    bakim_tarihi = _rastgele_tarih(baslangic, 600, satir_sayisi)

    df = pd.DataFrame({
        "silo_id": secilen,
        "sicaklik_c": sicaklik,
        "nem_orani": nem,
        "enerji_tuketim_kwh": enerji,
        "bakim_tarihi": bakim_tarihi,
        "birim_maliyet": birim_maliyet,
    })

    # Eksik değerler
    nan_indeks = np.random.choice(satir_sayisi, size=int(satir_sayisi * 0.05), replace=False)
    for i, idx in enumerate(nan_indeks):
        sutun = ["sicaklik_c", "nem_orani", "enerji_tuketim_kwh", "birim_maliyet"][i % 4]
        df.loc[idx, sutun] = np.nan

    return df


def veri_uret_ve_kaydet(satir_sayisi: int = 220) -> dict[str, int]:
    """Tüm CSV dosyalarını üretir ve kaydeder. Satır sayılarını döndürür."""
    os.makedirs(VERI_KLASORU, exist_ok=True)

    depo = depo_stok_uret(satir_sayisi)
    nakliye = nakliye_uret(satir_sayisi)
    operasyonel = operasyonel_uret(satir_sayisi)

    depo.to_csv(os.path.join(VERI_KLASORU, "depo_stok.csv"), index=False, encoding="utf-8-sig")
    nakliye.to_csv(os.path.join(VERI_KLASORU, "nakliye.csv"), index=False, encoding="utf-8-sig")
    operasyonel.to_csv(os.path.join(VERI_KLASORU, "operasyonel.csv"), index=False, encoding="utf-8-sig")

    return {"depo": len(depo), "nakliye": len(nakliye), "operasyonel": len(operasyonel)}


def main():
    """Tüm CSV dosyalarını oluşturur."""
    sonuc = veri_uret_ve_kaydet()
    print(f"[OK] depo_stok.csv      - {sonuc['depo']} satir")
    print(f"[OK] nakliye.csv        - {sonuc['nakliye']} satir")
    print(f"[OK] operasyonel.csv    - {sonuc['operasyonel']} satir")
    print(f"\nVeriler '{VERI_KLASORU}' klasorune kaydedildi.")


if __name__ == "__main__":
    main()
