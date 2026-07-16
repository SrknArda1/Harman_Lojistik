"""
HarmanLojistik — Flask web uygulaması.
Analiz ve görselleştirme modüllerini dashboard ve API ile sunar.
"""

import os
import time

from flask import Flask, jsonify, redirect, render_template, request, url_for

from core import analiz, gorseller
from veri_uret import veri_uret_ve_kaydet

app = Flask(__name__)
app.json.ensure_ascii = False

# Ham veri önbelleği (yeni veri üretilince sıfırlanır)
_ham_veri: dict | None = None
_png_zaman: float = 0


def _onbellegi_sifirla():
    """Veri ve grafik önbelleğini temizler."""
    global _ham_veri, _png_zaman
    _ham_veri = None
    _png_zaman = 0


def _ham_veri_yukle() -> dict:
    """Temizlenmiş ham veriyi yükler veya önbellekten döndürür."""
    global _ham_veri
    if _ham_veri is None:
        _ham_veri = analiz.veri_yukle_temizle()
    return _ham_veri


def _filtre_parametreleri() -> dict[str, str]:
    """İstekten filtre parametrelerini okur."""
    return {
        "kategori": request.args.get("kategori", "Tümü"),
        "rota": request.args.get("rota", "Tümü"),
        "tarih_araligi": request.args.get("tarih_araligi", "Tüm Zamanlar"),
    }


def _analizleri_calistir(
    kategori: str = "Tümü",
    rota: str = "Tümü",
    tarih_araligi: str = "Tüm Zamanlar",
    png_uret: bool = True,
) -> dict:
    """Filtrelere göre analizleri çalıştırır; isteğe bağlı PNG üretir."""
    global _png_zaman

    veriler = _ham_veri_yukle()
    sonuc = analiz.tum_analizleri_calistir(
        veriler,
        kategori=kategori,
        rota=rota,
        tarih_araligi=tarih_araligi,
    )

    if png_uret:
        grafikler = gorseller.tum_grafikleri_uret(sonuc)
        sonuc["grafikler"] = grafikler
        _png_zaman = time.time()
    else:
        # Mevcut PNG yollarını kullan (dosya adları sabit)
        sonuc["grafikler"] = {
            "isi_haritasi": "grafikler/silo_doluluk_isi_haritasi.png",
            "kategori_doluluk": "grafikler/kategori_doluluk.png",
            "rota_maliyet": "grafikler/rota_maliyet.png",
            "sicaklik_fire": "grafikler/sicaklik_fire.png",
            "talep_tahmini": "grafikler/talep_tahmini.png",
        }

    sonuc["png_zaman"] = _png_zaman
    return sonuc


@app.route("/")
def dashboard():
    """Ana dashboard sayfası."""
    filtreler = _filtre_parametreleri()
    sonuc = _analizleri_calistir(**filtreler, png_uret=True)
    ozet = analiz.ozet_olustur(sonuc)

    veriler = sonuc["veriler"]
    rota_ozet_df = sonuc["nakliye"]["rota_ozet"]

    return render_template(
        "dashboard.html",
        ozet=ozet,
        kritik_stok=ozet["kritik_stok"],
        grafikler=sonuc["grafikler"],
        kategori_ozet=sonuc["depo_doluluk"]["kategori_ozet"].to_dict(orient="records"),
        rota_ozet=rota_ozet_df.head(5).to_dict(orient="records") if not rota_ozet_df.empty else [],
        korelasyon=sonuc["fire"]["korelasyon"],
        talep_katsayi=sonuc["talep"]["katsayilar"],
        eksik_istatistik=veriler["eksik_istatistik"],
        aykiri_analiz=veriler["aykiri_analiz"],
        filtreler=filtreler,
        kategoriler=analiz.KATEGORILER,
        rotalar=["Tümü"] + veriler["rotalar"],
        tarih_araliklari=analiz.TARIH_ARALIKLARI,
        png_zaman=int(sonuc.get("png_zaman", 0)),
    )


@app.route("/api/ozet")
def api_ozet():
    """Özet kart ve kritik stok verilerini JSON olarak döndürür."""
    filtreler = _filtre_parametreleri()
    sonuc = _analizleri_calistir(**filtreler, png_uret=False)
    ozet = analiz.ozet_olustur(sonuc)
    ozet["filtreler"] = filtreler
    return jsonify(ozet)


@app.route("/api/grafik-veri")
def api_grafik_veri():
    """Chart.js için grafik verilerini JSON olarak döndürür."""
    filtreler = _filtre_parametreleri()
    sonuc = _analizleri_calistir(**filtreler, png_uret=False)
    return jsonify(analiz.grafik_verisi_hazirla(sonuc))


@app.route("/api/silolar")
def api_silolar():
    """Silo detay tablosu verilerini JSON olarak döndürür."""
    filtreler = _filtre_parametreleri()
    sonuc = _analizleri_calistir(**filtreler, png_uret=False)
    silolar = sonuc["silo_detay"]

    kayitlar = silolar.to_dict(orient="records") if not silolar.empty else []
    return jsonify({"silolar": kayitlar, "toplam": len(kayitlar), "filtreler": filtreler})


@app.route("/api/depo")
def api_depo():
    """Depo stok verilerini JSON olarak döndürür."""
    filtreler = _filtre_parametreleri()
    sonuc = _analizleri_calistir(**filtreler, png_uret=False)
    depo = sonuc["depo_doluluk"]

    return jsonify({
        "toplam_silo": depo["toplam_silo"],
        "ortalama_doluluk": depo["ortalama_doluluk"],
        "kategori_ozet": depo["kategori_ozet"].to_dict(orient="records"),
        "kritik_stok": depo["kritik_stok"].to_dict(orient="records"),
        "kritik_sayisi": len(depo["kritik_stok"]),
        "filtreler": filtreler,
    })


@app.route("/api/nakliye")
def api_nakliye():
    """Nakliye verilerini JSON olarak döndürür."""
    filtreler = _filtre_parametreleri()
    sonuc = _analizleri_calistir(**filtreler, png_uret=False)
    nak = sonuc["nakliye"]
    talep = sonuc["talep"]

    return jsonify({
        "toplam_sefer": nak["toplam_sefer"],
        "ortalama_maliyet": nak["ortalama_maliyet"],
        "rota_ozet": nak["rota_ozet"].to_dict(orient="records"),
        "talep_tahmini": talep["tahmin"].to_dict(orient="records"),
        "talep_katsayilar": talep["katsayilar"],
        "filtreler": filtreler,
    })


@app.route("/yeni-veri", methods=["POST"])
def yeni_veri():
    """Yeni örnek veri üretir, grafikleri yeniden çizer."""
    veri_uret_ve_kaydet()
    _onbellegi_sifirla()

    filtreler = _filtre_parametreleri()
    _analizleri_calistir(**filtreler, png_uret=True)

    # AJAX isteği ise JSON döndür
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"durum": "ok", "mesaj": "Yeni veriler uretildi ve grafikler guncellendi."})

    return redirect(url_for("dashboard", **filtreler))


if __name__ == "__main__":
    veri_yolu = os.path.join(os.path.dirname(__file__), "data", "depo_stok.csv")
    if not os.path.exists(veri_yolu):
        print("Uyari: Veri dosyalari bulunamadi. Once 'python veri_uret.py' calistirin.")

    app.run(debug=True, host="0.0.0.0", port=5000)
