# HarmanLojistik

**Veri Analitiği Destekli Tarım Deposu ve Nakliye Takip Sistemi**

HarmanLojistik; tarım ürünlerinin depolanması, stok takibi, fire analizi ve nakliye maliyetlerinin Pandas/NumPy ile analiz edildiği, Matplotlib/Seaborn grafikleri, Chart.js interaktif dashboard ve Flask API ile sunulduğu bir Python projesidir.

## Hızlı Başlangıç

```bash
pip install -r requirements.txt
python veri_uret.py
python app.py
```

Tarayıcıda **http://localhost:5000** adresini açın.

> `veri_uret.py` örnek CSV dosyalarını ve `static/grafikler/` altındaki PNG rapor grafiklerini üretir. İlk çalıştırmadan önce mutlaka bu adımı tamamlayın.

## Proje Yapısı



```
harmanlojistik/
├── data/                  # CSV veri dosyaları
│   ├── depo_stok.csv
│   ├── nakliye.csv
│   └── operasyonel.csv
├── core/
│   ├── analiz.py          # Pandas/NumPy hesaplamaları + filtreleme
│   └── gorseller.py       # Matplotlib/Seaborn PNG grafikleri
├── templates/
│   ├── base.html
│   └── dashboard.html     # Filtreler, Chart.js, tablo, auto-refresh
├── static/
│   └── grafikler/         # Üretilen PNG grafikler
├── veri_uret.py           # Örnek veri üretici
├── app.py                 # Flask uygulaması + API
└── requirements.txt
```

## Kurulum

### 1. Bağımlılıkları yükleyin

```bash
pip install -r requirements.txt
```

### 2. Örnek verileri üretin

```bash
python veri_uret.py
```

Bu komut `data/` klasörüne üç CSV dosyası oluşturur (her biri 220+ satır). Veriler bilerek eksik (NaN) değerler içerir; analiz modülü bunları temizler.

### 3. Uygulamayı başlatın

```bash
python app.py
```

Tarayıcınızda şu adresi açın: **http://localhost:5000**

## Kullanım

| Adres | Açıklama |
|-------|----------|
| `/` | Ana dashboard — filtreler, özet kartlar, kritik stok, Chart.js ve PNG grafikler, silo tablosu |
| `/api/ozet` | Özet kart verileri ve kritik stok (JSON, filtre parametreleri destekler) |
| `/api/grafik-veri` | Chart.js için grafik verisi (JSON) |
| `/api/silolar` | Silo detay tablosu + verimlilik skoru (JSON) |
| `/api/depo` | Depo stok verileri (JSON) |
| `/api/nakliye` | Nakliye ve talep tahmini verileri (JSON) |
| `/yeni-veri` | POST — yeni örnek veri üretir ve grafikleri yeniler |

### Filtre parametreleri

Tüm API uç noktaları ve dashboard şu sorgu parametrelerini destekler:

- `kategori`: Tahıl, Baklagil, Yağlı Tohum, Tümü
- `rota`: Belirli rota adı veya Tümü
- `tarih_araligi`: Son 1 Ay, Son 3 Ay, Tüm Zamanlar

Örnek: `/api/ozet?kategori=Tahıl&tarih_araligi=Son+3+Ay`

## Dinamik Özellikler

### Filtreleme
Dashboard üstündeki filtre çubuğu ile kategori, rota ve tarih aralığı seçilebilir. Filtre değişince kartlar, grafikler ve tablo yeniden hesaplanır.

### Otomatik güncelleme (Auto-refresh)
Dashboard her 10 saniyede `/api/ozet` endpoint'inden özet kartları ve kritik stok uyarılarını sayfa yenilemeden günceller. Üstte "Son güncelleme: HH:MM:SS" göstergesi bulunur.

### Yeni Veri Üret
"Yeni Veri Üret" butonu `/yeni-veri` POST endpoint'ini çağırır; CSV'ler yeniden üretilir, Matplotlib grafikleri çizilir ve sayfa yenilenir.

### İnteraktif grafikler (Chart.js)
Dashboard'da Chart.js ile etkileşimli grafikler:
- Kategori bazlı doluluk (bar, hover tooltip)
- Rota maliyet karşılaştırması (horizontal bar)
- Talep tahmini (line — geçmiş ve tahmin ayrı renkler)

Matplotlib PNG grafikleri rapor amaçlı ayrı bölümde korunur.

### Silo detay tablosu
Arama (silo ID / ürün adı), kolon başlığına tıklayarak sıralama, sayfa başına 10 kayıt ve sayfalama. Verimlilik skoru renk kodlu (yeşil ≥70, sarı 40–69, kırmızı <40).

### Verimlilik skoru
Her silo için 0–100 arası skor: yüksek doluluk, düşük fire ve düşük bozulma riski yüksek puan verir (NumPy min-max normalizasyon).

### Türkçe JSON
`app.json.ensure_ascii = False` ile API yanıtlarında Türkçe karakterler (Pirinç, Tahıl vb.) düzgün görünür.

## Temel Analiz Özellikleri

- **Veri temizleme:** `isnull()`, `fillna()`, tip dönüşümleri, IQR aykırı değer analizi
- **Depo analizi:** Kategori bazlı doluluk, kritik stok tespiti (%25 altı)
- **Fire analizi:** Ürün bazlı fire oranı, sıcaklık/nem korelasyonu (`numpy.corrcoef`)
- **Nakliye analizi:** Rota maliyet/km, yakıt verimliliği, pivot tablo
- **Talep tahmini:** Aylık sefer trendi (`numpy.polyfit` lineer regresyon)
- **Grafikler:** Isı haritası, çubuk, scatter+regresyon, tahmin çizgisi (PNG + Chart.js)

## Teknolojiler

- Python 3.10+
- Flask, Pandas, NumPy, Matplotlib, Seaborn
- Chart.js (CDN)

## Lisans

Bu proje eğitim ve demo amaçlıdır.
