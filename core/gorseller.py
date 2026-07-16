"""
HarmanLojistik — Görselleştirme modülü.
Matplotlib ve Seaborn ile grafikleri PNG olarak kaydeder.
"""

import os

import matplotlib
matplotlib.use("Agg")  # Sunucu ortamı için arka plan renderer

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Grafik çıktı klasörü
GRAFIK_KLASORU = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "grafikler")

# Kurumsal renk paleti
RENK_VURGU = "#E11D48"
RENK_IKINCIL = "#475569"
RENK_METIN = "#1A1C1E"
RENK_ARKA = "#FAFAFA"


def _klasor_hazirla():
    """Grafik klasörünü oluşturur."""
    os.makedirs(GRAFIK_KLASORU, exist_ok=True)


def _stil_ayarla():
    """Grafik stilini ayarlar."""
    sns.set_theme(style="whitegrid", font_scale=0.95)
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "text.color": RENK_METIN,
        "axes.labelcolor": RENK_METIN,
        "xtick.color": RENK_IKINCIL,
        "ytick.color": RENK_IKINCIL,
    })


def silo_doluluk_isi_haritasi(silo_bazli: pd.DataFrame) -> str:
    """Silo doluluk oranlarını ısı haritası olarak çizer."""
    _klasor_hazirla()
    _stil_ayarla()

    # Siloları gruplara böl (8x5 matris)
    silolar = silo_bazli.sort_values("silo_id").reset_index(drop=True)
    n = len(silolar)
    satir, sutun = 8, 5
    matris = np.full((satir, sutun), np.nan)

    for i, row in silolar.iterrows():
        if i >= satir * sutun:
            break
        r, c = divmod(i, sutun)
        matris[r, c] = row["doluluk_orani"]

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(
        matris,
        annot=True,
        fmt=".0f",
        cmap="RdYlGn",
        vmin=0,
        vmax=100,
        linewidths=0.5,
        cbar_kws={"label": "Doluluk (%)"},
        ax=ax,
    )
    ax.set_title("Silo Doluluk Isı Haritası", fontsize=14, fontweight="bold", color=RENK_METIN)
    ax.set_xlabel("Sütun")
    ax.set_ylabel("Satır")

    dosya = os.path.join(GRAFIK_KLASORU, "silo_doluluk_isi_haritasi.png")
    fig.tight_layout()
    fig.savefig(dosya, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return "grafikler/silo_doluluk_isi_haritasi.png"


def kategori_doluluk_cubuk(kategori_ozet: pd.DataFrame) -> str:
    """Kategori bazlı ortalama doluluk çubuk grafiği çizer."""
    _klasor_hazirla()
    _stil_ayarla()

    fig, ax = plt.subplots(figsize=(9, 5))
    renkler = sns.color_palette(["#E11D48", "#475569", "#0EA5E9", "#10B981"], n_colors=len(kategori_ozet))

    bars = ax.bar(
        kategori_ozet["kategori"],
        kategori_ozet["ortalama"],
        color=renkler,
        edgecolor="white",
        linewidth=0.8,
    )

    for bar, val in zip(bars, kategori_ozet["ortalama"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{val:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            color=RENK_METIN,
        )

    ax.set_ylabel("Ortalama Doluluk (%)")
    ax.set_title("Kategori Bazlı Doluluk Oranları", fontsize=14, fontweight="bold", color=RENK_METIN)
    ax.set_ylim(0, 110)
    ax.axhline(y=25, color=RENK_VURGU, linestyle="--", linewidth=1, label="Kritik eşik (%25)")
    ax.legend()

    dosya = os.path.join(GRAFIK_KLASORU, "kategori_doluluk.png")
    fig.tight_layout()
    fig.savefig(dosya, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return "grafikler/kategori_doluluk.png"


def rota_maliyet_karsilastirma(rota_ozet: pd.DataFrame) -> str:
    """Rota bazlı maliyet/km karşılaştırma çubuk grafiği çizer."""
    _klasor_hazirla()
    _stil_ayarla()

    sirali = rota_ozet.sort_values("ortalama_maliyet_km", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(
        sirali["rota"],
        sirali["ortalama_maliyet_km"],
        color=RENK_IKINCIL,
        edgecolor="white",
    )

    # En yüksek maliyetli rotayı vurgula (artan sıralamada son çubuk)
    bars[-1].set_color(RENK_VURGU)

    ax.set_xlabel("Ortalama Maliyet (TL/km)")
    ax.set_title("Rota Bazlı Maliyet Karşılaştırması", fontsize=14, fontweight="bold", color=RENK_METIN)

    dosya = os.path.join(GRAFIK_KLASORU, "rota_maliyet.png")
    fig.tight_layout()
    fig.savefig(dosya, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return "grafikler/rota_maliyet.png"


def sicaklik_fire_scatter(birlesik_veri: pd.DataFrame) -> str:
    """Sıcaklık-fire korelasyon scatter grafiği ve regresyon çizgisi çizer."""
    _klasor_hazirla()
    _stil_ayarla()

    fig, ax = plt.subplots(figsize=(9, 5))

    if len(birlesik_veri) >= 2:
        x = birlesik_veri["sicaklik_c"].values
        y = birlesik_veri["fire_orani"].values

        ax.scatter(x, y, alpha=0.7, color=RENK_IKINCIL, s=60, edgecolors="white", linewidth=0.5)

        # Regresyon çizgisi
        katsayilar = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = np.polyval(katsayilar, x_line)
        ax.plot(x_line, y_line, color=RENK_VURGU, linewidth=2, label="Regresyon çizgisi")

        r = np.corrcoef(x, y)[0, 1]
        ax.text(
            0.05, 0.95,
            f"r = {r:.3f}",
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", edgecolor=RENK_IKINCIL),
        )
        ax.legend()

    ax.set_xlabel("Sıcaklık (°C)")
    ax.set_ylabel("Fire Oranı (%)")
    ax.set_title("Sıcaklık — Fire Korelasyonu", fontsize=14, fontweight="bold", color=RENK_METIN)

    dosya = os.path.join(GRAFIK_KLASORU, "sicaklik_fire.png")
    fig.tight_layout()
    fig.savefig(dosya, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return "grafikler/sicaklik_fire.png"


def talep_tahmini_grafik(gecmis: pd.DataFrame, tahmin: pd.DataFrame) -> str:
    """Geçmiş sefer sayısı ve lineer talep tahmini çizgi grafiği çizer."""
    _klasor_hazirla()
    _stil_ayarla()

    fig, ax = plt.subplots(figsize=(11, 5))

    gecmis_ay = gecmis["ay"].tolist()
    gecmis_deger = gecmis["sefer_sayisi"].tolist()

    ax.plot(gecmis_ay, gecmis_deger, marker="o", color=RENK_IKINCIL, linewidth=2, label="Geçmiş sefer")

    if "trend" in gecmis.columns:
        ax.plot(gecmis_ay, gecmis["trend"], linestyle="--", color=RENK_VURGU, alpha=0.7, label="Trend")

    if len(tahmin) > 0:
        tahmin_ay = tahmin["ay"].tolist()
        tahmin_deger = tahmin["sefer_sayisi"].tolist()
        # Geçmişin son noktasından tahmine bağlantı
        baglanti_x = [gecmis_ay[-1]] + tahmin_ay
        baglanti_y = [gecmis_deger[-1]] + tahmin_deger
        ax.plot(baglanti_x, baglanti_y, marker="s", color=RENK_VURGU, linewidth=2, linestyle=":", label="Tahmin")

    ax.set_xlabel("Ay")
    ax.set_ylabel("Sefer Sayısı")
    ax.set_title("Aylık Sefer Talebi ve Lineer Tahmin", fontsize=14, fontweight="bold", color=RENK_METIN)
    ax.legend()
    plt.xticks(rotation=45, ha="right")

    dosya = os.path.join(GRAFIK_KLASORU, "talep_tahmini.png")
    fig.tight_layout()
    fig.savefig(dosya, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return "grafikler/talep_tahmini.png"


def tum_grafikleri_uret(analiz_sonuclari: dict) -> dict[str, str]:
    """Tüm grafikleri üretir ve dosya yollarını döndürür."""
    return {
        "isi_haritasi": silo_doluluk_isi_haritasi(analiz_sonuclari["depo_doluluk"]["silo_bazli"]),
        "kategori_doluluk": kategori_doluluk_cubuk(analiz_sonuclari["depo_doluluk"]["kategori_ozet"]),
        "rota_maliyet": rota_maliyet_karsilastirma(analiz_sonuclari["nakliye"]["rota_ozet"]),
        "sicaklik_fire": sicaklik_fire_scatter(analiz_sonuclari["fire"]["birlesik_veri"]),
        "talep_tahmini": talep_tahmini_grafik(
            analiz_sonuclari["talep"]["gecmis"],
            analiz_sonuclari["talep"]["tahmin"],
        ),
    }
