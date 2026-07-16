"""
HarmanLojistik — Veri analizi modülü.
Pandas ve NumPy ile hesaplamalar yapar; sadece veri döndürür.
"""

import os
from typing import Any

import numpy as np
import pandas as pd

# Veri dosyalarının bulunduğu klasör
VERI_KLASORU = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Kritik stok eşiği (% doluluk altında uyarı)
KRITIK_DOLULUK_ESIGI = 25

# Geçerli filtre değerleri
KATEGORILER = ["Tümü", "Tahıl", "Baklagil", "Yağlı Tohum"]
TARIH_ARALIKLARI = ["Tüm Zamanlar", "Son 1 Ay", "Son 3 Ay"]


def _iqr_aykiri_tespit(seri: pd.Series) -> dict[str, Any]:
    """IQR yöntemiyle aykırı değer analizi yapar."""
    temiz = seri.dropna()
    if len(temiz) < 4:
        return {"alt_sinir": None, "ust_sinir": None, "aykiri_sayisi": 0}

    q1 = np.percentile(temiz, 25)
    q3 = np.percentile(temiz, 75)
    iqr = q3 - q1
    alt = q1 - 1.5 * iqr
    ust = q3 + 1.5 * iqr
    aykiri = ((temiz < alt) | (temiz > ust)).sum()

    return {"alt_sinir": round(float(alt), 2), "ust_sinir": round(float(ust), 2), "aykiri_sayisi": int(aykiri)}


def _tarih_kesim_noktasi(tarih_araligi: str, referans: pd.Timestamp) -> pd.Timestamp | None:
    """Tarih aralığı seçimine göre kesim tarihini hesaplar."""
    if tarih_araligi == "Son 1 Ay":
        return referans - pd.Timedelta(days=30)
    if tarih_araligi == "Son 3 Ay":
        return referans - pd.Timedelta(days=90)
    return None


def veri_filtrele(
    depo: pd.DataFrame,
    nakliye: pd.DataFrame,
    operasyonel: pd.DataFrame,
    kategori: str = "Tümü",
    rota: str = "Tümü",
    tarih_araligi: str = "Tüm Zamanlar",
) -> dict[str, pd.DataFrame]:
    """
    Veri setlerini kategori, rota ve tarih aralığına göre filtreler.
    Pandas boolean indexing ve .loc kullanır.
    """
    depo_f = depo.copy()
    nakliye_f = nakliye.copy()
    operasyonel_f = operasyonel.copy()

    # Kategori filtresi (depo)
    if kategori and kategori != "Tümü":
        depo_f = depo_f.loc[depo_f["kategori"] == kategori]

    # Rota filtresi (nakliye)
    if rota and rota != "Tümü":
        nakliye_f = nakliye_f.loc[nakliye_f["rota"] == rota]

    # Tarih aralığı filtresi
    if tarih_araligi and tarih_araligi != "Tüm Zamanlar":
        ref_nakliye = nakliye["tarih"].max() if len(nakliye) else pd.Timestamp.now()
        ref_depo = depo["giris_tarihi"].max() if len(depo) else pd.Timestamp.now()
        ref_op = operasyonel["bakim_tarihi"].max() if len(operasyonel) else pd.Timestamp.now()

        kesim_nak = _tarih_kesim_noktasi(tarih_araligi, ref_nakliye)
        kesim_depo = _tarih_kesim_noktasi(tarih_araligi, ref_depo)
        kesim_op = _tarih_kesim_noktasi(tarih_araligi, ref_op)

        if kesim_nak is not None:
            nakliye_f = nakliye_f.loc[nakliye_f["tarih"] >= kesim_nak]
        if kesim_depo is not None:
            depo_f = depo_f.loc[depo_f["giris_tarihi"] >= kesim_depo]
        if kesim_op is not None:
            operasyonel_f = operasyonel_f.loc[operasyonel_f["bakim_tarihi"] >= kesim_op]

    # Operasyonel veriyi filtrelenmiş silolarla sınırla
    if len(depo_f) > 0:
        silo_set = set(depo_f["silo_id"].unique())
        operasyonel_f = operasyonel_f.loc[operasyonel_f["silo_id"].isin(silo_set)]

    return {"depo": depo_f, "nakliye": nakliye_f, "operasyonel": operasyonel_f}


def veri_yukle_temizle() -> dict[str, Any]:
    """
    CSV dosyalarını okur, eksik değerleri temizler ve tip dönüşümleri yapar.
    Aykırı değer analizi sonuçlarını da döndürür.
    """
    depo = pd.read_csv(os.path.join(VERI_KLASORU, "depo_stok.csv"), parse_dates=["giris_tarihi", "son_kullanma_tarihi"])
    nakliye = pd.read_csv(os.path.join(VERI_KLASORU, "nakliye.csv"), parse_dates=["tarih"])
    operasyonel = pd.read_csv(os.path.join(VERI_KLASORU, "operasyonel.csv"), parse_dates=["bakim_tarihi"])

    # Eksik değer istatistikleri (temizleme öncesi)
    eksik_istatistik = {
        "depo": depo.isnull().sum().to_dict(),
        "nakliye": nakliye.isnull().sum().to_dict(),
        "operasyonel": operasyonel.isnull().sum().to_dict(),
    }

    # Sayısal sütunlarda medyan ile doldurma
    depo["doluluk_orani"] = depo["doluluk_orani"].fillna(depo["doluluk_orani"].median())
    depo["fire_orani"] = depo["fire_orani"].fillna(depo["fire_orani"].median())
    depo["bozulma_riski"] = depo["bozulma_riski"].fillna(depo["bozulma_riski"].median())

    nakliye["yakit_litre"] = nakliye["yakit_litre"].fillna(nakliye["yakit_litre"].median())
    nakliye["sure_dk"] = nakliye["sure_dk"].fillna(nakliye["sure_dk"].median())
    nakliye["maliyet_tl"] = nakliye["maliyet_tl"].fillna(nakliye["maliyet_tl"].median())

    operasyonel["sicaklik_c"] = operasyonel["sicaklik_c"].fillna(operasyonel["sicaklik_c"].median())
    operasyonel["nem_orani"] = operasyonel["nem_orani"].fillna(operasyonel["nem_orani"].median())
    operasyonel["enerji_tuketim_kwh"] = operasyonel["enerji_tuketim_kwh"].fillna(operasyonel["enerji_tuketim_kwh"].median())
    operasyonel["birim_maliyet"] = operasyonel["birim_maliyet"].fillna(operasyonel["birim_maliyet"].median())

    # Tip dönüşümleri
    depo["doluluk_orani"] = depo["doluluk_orani"].astype(float)
    depo["fire_orani"] = depo["fire_orani"].astype(float)
    nakliye["mesafe_km"] = nakliye["mesafe_km"].astype(float)
    nakliye["maliyet_tl"] = nakliye["maliyet_tl"].astype(float)

    # Tarih türevleri
    depo["depolama_gun"] = (depo["son_kullanma_tarihi"] - depo["giris_tarihi"]).dt.days
    nakliye["ay"] = nakliye["tarih"].dt.to_period("M").astype(str)
    operasyonel["bakim_yasi_gun"] = (pd.Timestamp.now() - operasyonel["bakim_tarihi"]).dt.days

    # Aykırı değer analizi
    aykiri_analiz = {
        "doluluk": _iqr_aykiri_tespit(depo["doluluk_orani"]),
        "fire": _iqr_aykiri_tespit(depo["fire_orani"]),
        "maliyet": _iqr_aykiri_tespit(nakliye["maliyet_tl"]),
        "sicaklik": _iqr_aykiri_tespit(operasyonel["sicaklik_c"]),
    }

    rotalar = sorted(nakliye["rota"].unique().tolist())

    return {
        "depo": depo,
        "nakliye": nakliye,
        "operasyonel": operasyonel,
        "eksik_istatistik": eksik_istatistik,
        "aykiri_analiz": aykiri_analiz,
        "rotalar": rotalar,
    }


def verimlilik_skoru_hesapla(silo_bazli: pd.DataFrame) -> pd.DataFrame:
    """
    Her silo için 0-100 arası verimlilik skoru hesaplar.
    Yüksek doluluk, düşük fire ve düşük bozulma riski yüksek skor verir.
  NumPy ile min-max normalizasyon uygulanır.
    """
    if silo_bazli.empty:
        return silo_bazli.copy()

    df = silo_bazli.copy()

    def _norm_yuksek_iyi(seri: pd.Series) -> np.ndarray:
        """Yüksek değer daha iyi — 0-100 normalize."""
        mn, mx = seri.min(), seri.max()
        if mx == mn:
            return np.full(len(seri), 50.0)
        return ((seri - mn) / (mx - mn) * 100).values

    def _norm_dusuk_iyi(seri: pd.Series) -> np.ndarray:
        """Düşük değer daha iyi — ters normalize."""
        mn, mx = seri.min(), seri.max()
        if mx == mn:
            return np.full(len(seri), 50.0)
        return ((mx - seri) / (mx - mn) * 100).values

    doluluk_skor = _norm_yuksek_iyi(df["doluluk_orani"])
    fire_skor = _norm_dusuk_iyi(df["fire_orani"])
    bozulma_skor = _norm_dusuk_iyi(df["bozulma_riski"])

    df["verimlilik_skoru"] = np.round((doluluk_skor + fire_skor + bozulma_skor) / 3, 1)
    return df


def silo_detay_listesi(depo: pd.DataFrame) -> pd.DataFrame:
    """Silo detay tablosu için verimlilik skorlu liste döndürür."""
    if depo.empty:
        return pd.DataFrame(columns=[
            "silo_id", "urun_adi", "kategori", "doluluk_orani",
            "fire_orani", "bozulma_riski", "verimlilik_skoru",
        ])

    silo_bazli = depo.sort_values("giris_tarihi").groupby("silo_id").last().reset_index()
    skorlu = verimlilik_skoru_hesapla(silo_bazli)

    return skorlu[[
        "silo_id", "urun_adi", "kategori", "doluluk_orani",
        "fire_orani", "bozulma_riski", "verimlilik_skoru",
    ]].sort_values("silo_id")


def depo_doluluk_analizi(
    depo: pd.DataFrame,
    kategori: str = "Tümü",
    rota: str = "Tümü",
    tarih_araligi: str = "Tüm Zamanlar",
) -> dict[str, Any]:
    """Kategori bazlı doluluk analizi ve kritik stok tespiti yapar."""
    if depo.empty:
        bos_df = pd.DataFrame(columns=["kategori", "ortalama", "min", "max", "std", "adet"])
        return {
            "kategori_ozet": bos_df,
            "kritik_stok": pd.DataFrame(),
            "toplam_silo": 0,
            "ortalama_doluluk": 0.0,
            "silo_bazli": pd.DataFrame(),
        }

    # Silo bazında son kayıt (her silo için en güncel)
    silo_bazli = depo.sort_values("giris_tarihi").groupby("silo_id").last().reset_index()

    kategori_ozet = (
        silo_bazli.groupby("kategori")["doluluk_orani"]
        .agg(ortalama="mean", min="min", max="max", std="std", adet="count")
        .round(2)
        .reset_index()
    )

    kritik_stok = silo_bazli.loc[silo_bazli["doluluk_orani"] < KRITIK_DOLULUK_ESIGI].copy()
    kritik_stok = kritik_stok.sort_values("doluluk_orani")

    return {
        "kategori_ozet": kategori_ozet,
        "kritik_stok": kritik_stok,
        "toplam_silo": int(silo_bazli["silo_id"].nunique()),
        "ortalama_doluluk": round(float(silo_bazli["doluluk_orani"].mean()), 2),
        "silo_bazli": silo_bazli,
    }


def fire_analizi(
    depo: pd.DataFrame,
    operasyonel: pd.DataFrame,
    kategori: str = "Tümü",
    rota: str = "Tümü",
    tarih_araligi: str = "Tüm Zamanlar",
) -> dict[str, Any]:
    """Ürün bazlı fire analizi ve sıcaklık/nem korelasyonu hesaplar."""
    if depo.empty:
        return {
            "urun_fire": pd.DataFrame(),
            "birlesik_veri": pd.DataFrame(),
            "korelasyon": {},
            "ortalama_fire": 0.0,
        }

    urun_fire = (
        depo.groupby("urun_adi")["fire_orani"]
        .agg(ortalama_fire="mean", max_fire="max", kayit_sayisi="count")
        .round(3)
        .reset_index()
        .sort_values("ortalama_fire", ascending=False)
    )

    silo_fire = depo.groupby("silo_id")["fire_orani"].mean().reset_index()
    silo_op = operasyonel.groupby("silo_id").agg(
        sicaklik_c=("sicaklik_c", "mean"),
        nem_orani=("nem_orani", "mean"),
    ).reset_index()

    birlesik = silo_fire.merge(silo_op, on="silo_id", how="inner")
    birlesik = birlesik.dropna()

    korelasyon = {}
    if len(birlesik) >= 3:
        sicaklik_fire = np.corrcoef(birlesik["sicaklik_c"], birlesik["fire_orani"])[0, 1]
        nem_fire = np.corrcoef(birlesik["nem_orani"], birlesik["fire_orani"])[0, 1]
        korelasyon = {
            "sicaklik_fire": round(float(sicaklik_fire), 4),
            "nem_fire": round(float(nem_fire), 4),
        }

    return {
        "urun_fire": urun_fire,
        "birlesik_veri": birlesik,
        "korelasyon": korelasyon,
        "ortalama_fire": round(float(depo["fire_orani"].mean()), 2),
    }


def nakliye_maliyet_analizi(
    nakliye: pd.DataFrame,
    kategori: str = "Tümü",
    rota: str = "Tümü",
    tarih_araligi: str = "Tüm Zamanlar",
) -> dict[str, Any]:
    """Rota bazlı maliyet ve yakıt verimliliği analizi yapar."""
    if nakliye.empty:
        return {
            "rota_ozet": pd.DataFrame(),
            "pivot_maliyet": pd.DataFrame(),
            "toplam_sefer": 0,
            "ortalama_maliyet": 0.0,
            "nakliye_df": nakliye.copy(),
        }

    nakliye = nakliye.copy()
    nakliye["maliyet_km"] = nakliye["maliyet_tl"] / nakliye["mesafe_km"]
    nakliye["yakit_verimliligi"] = nakliye["mesafe_km"] / nakliye["yakit_litre"]

    rota_ozet = (
        nakliye.groupby("rota")
        .agg(
            ortalama_maliyet=("maliyet_tl", "mean"),
            ortalama_maliyet_km=("maliyet_km", "mean"),
            ortalama_mesafe=("mesafe_km", "mean"),
            ortalama_yakit=("yakit_litre", "mean"),
            ortalama_verimlilik=("yakit_verimliligi", "mean"),
            sefer_sayisi=("sefer_id", "count"),
        )
        .round(2)
        .reset_index()
        .sort_values("ortalama_maliyet_km", ascending=False)
    )

    pivot = pd.pivot_table(
        nakliye,
        values="maliyet_tl",
        index="rota",
        columns="ay",
        aggfunc="mean",
    ).round(2)

    return {
        "rota_ozet": rota_ozet,
        "pivot_maliyet": pivot,
        "toplam_sefer": len(nakliye),
        "ortalama_maliyet": round(float(nakliye["maliyet_tl"].mean()), 2),
        "nakliye_df": nakliye,
    }


def talep_tahmini(
    nakliye: pd.DataFrame,
    tahmin_ay: int = 3,
    kategori: str = "Tümü",
    rota: str = "Tümü",
    tarih_araligi: str = "Tüm Zamanlar",
) -> dict[str, Any]:
    """
    Basit lineer trend ile aylık sefer talebi tahmini yapar.
    NumPy polyfit kullanır.
    """
    if nakliye.empty:
        return {"gecmis": pd.DataFrame(), "tahmin": pd.DataFrame(), "katsayilar": None, "tum_veri": pd.DataFrame()}

    aylik = (
        nakliye.groupby("ay")
        .size()
        .reset_index(name="sefer_sayisi")
        .sort_values("ay")
    )

    if len(aylik) < 2:
        return {"gecmis": aylik, "tahmin": pd.DataFrame(), "katsayilar": None, "tum_veri": aylik}

    x = np.arange(len(aylik))
    y = aylik["sefer_sayisi"].values.astype(float)

    katsayilar = np.polyfit(x, y, 1)
    trend = np.polyval(katsayilar, x)

    gelecek_x = np.arange(len(aylik), len(aylik) + tahmin_ay)
    gelecek_y = np.polyval(katsayilar, gelecek_x)

    son_ay = pd.Period(aylik["ay"].iloc[-1], freq="M")
    tahmin_aylar = [(son_ay + i).strftime("%Y-%m") for i in range(1, tahmin_ay + 1)]

    tahmin_df = pd.DataFrame({
        "ay": tahmin_aylar,
        "sefer_sayisi": np.maximum(gelecek_y, 0).round(0).astype(int),
        "tip": "tahmin",
    })

    gecmis_df = aylik.copy()
    gecmis_df["tip"] = "gecmis"
    gecmis_df["trend"] = trend.round(1)

    return {
        "gecmis": gecmis_df,
        "tahmin": tahmin_df,
        "katsayilar": {"egim": round(float(katsayilar[0]), 3), "kesim": round(float(katsayilar[1]), 3)},
        "tum_veri": pd.concat([
            gecmis_df[["ay", "sefer_sayisi", "tip"]],
            tahmin_df[["ay", "sefer_sayisi", "tip"]],
        ], ignore_index=True),
    }


def tum_analizleri_calistir(
    veriler: dict[str, Any],
    kategori: str = "Tümü",
    rota: str = "Tümü",
    tarih_araligi: str = "Tüm Zamanlar",
) -> dict[str, Any]:
    """Filtrelenmiş veri üzerinde tüm analizleri çalıştırır."""
    filtreli = veri_filtrele(
        veriler["depo"],
        veriler["nakliye"],
        veriler["operasyonel"],
        kategori=kategori,
        rota=rota,
        tarih_araligi=tarih_araligi,
    )

    depo = filtreli["depo"]
    nakliye = filtreli["nakliye"]
    operasyonel = filtreli["operasyonel"]

    return {
        "veriler": veriler,
        "filtreli": filtreli,
        "depo_doluluk": depo_doluluk_analizi(depo, kategori, rota, tarih_araligi),
        "fire": fire_analizi(depo, operasyonel, kategori, rota, tarih_araligi),
        "nakliye": nakliye_maliyet_analizi(nakliye, kategori, rota, tarih_araligi),
        "talep": talep_tahmini(nakliye, kategori=kategori, rota=rota, tarih_araligi=tarih_araligi),
        "silo_detay": silo_detay_listesi(depo),
        "filtreler": {"kategori": kategori, "rota": rota, "tarih_araligi": tarih_araligi},
    }


def grafik_verisi_hazirla(sonuc: dict[str, Any]) -> dict[str, Any]:
    """Chart.js için JSON grafik verisi hazırlar."""
    depo_s = sonuc["depo_doluluk"]
    nak_s = sonuc["nakliye"]
    talep_s = sonuc["talep"]

    kategori = depo_s["kategori_ozet"]
    kategori_doluluk = {
        "etiketler": kategori["kategori"].tolist() if not kategori.empty else [],
        "degerler": kategori["ortalama"].tolist() if not kategori.empty else [],
    }

    rota = nak_s["rota_ozet"].sort_values("ortalama_maliyet_km", ascending=True)
    rota_maliyet = {
        "etiketler": rota["rota"].tolist() if not rota.empty else [],
        "degerler": rota["ortalama_maliyet_km"].tolist() if not rota.empty else [],
    }

    gecmis = talep_s["gecmis"]
    tahmin = talep_s["tahmin"]
    talep = {
        "gecmis_etiketler": gecmis["ay"].tolist() if not gecmis.empty else [],
        "gecmis_degerler": gecmis["sefer_sayisi"].tolist() if not gecmis.empty else [],
        "tahmin_etiketler": tahmin["ay"].tolist() if not tahmin.empty else [],
        "tahmin_degerler": tahmin["sefer_sayisi"].tolist() if not tahmin.empty else [],
    }

    return {
        "kategori_doluluk": kategori_doluluk,
        "rota_maliyet": rota_maliyet,
        "talep_tahmini": talep,
    }


def ozet_olustur(sonuc: dict[str, Any]) -> dict[str, Any]:
    """Dashboard özet kartları ve kritik stok listesi oluşturur."""
    depo = sonuc["depo_doluluk"]
    fire = sonuc["fire"]
    nak = sonuc["nakliye"]

    kritik = depo["kritik_stok"]
    kritik_liste = []
    if not kritik.empty:
        kritik_liste = kritik[
            ["silo_id", "urun_adi", "kategori", "doluluk_orani", "bozulma_riski"]
        ].to_dict(orient="records")

    return {
        "toplam_silo": depo["toplam_silo"],
        "ortalama_doluluk": depo["ortalama_doluluk"],
        "ortalama_fire": fire["ortalama_fire"],
        "toplam_sefer": nak["toplam_sefer"],
        "ortalama_maliyet": nak["ortalama_maliyet"],
        "kritik_stok": kritik_liste,
        "kritik_sayisi": len(kritik_liste),
    }
