"""
HarmanLojistik — Teslim ZIP paketi oluşturucu.
Proje dosyalarını harmanlojistik.zip arşivine paketler.
"""

import os
import zipfile

# Proje kök dizini (bu scriptin bulunduğu klasör)
PROJE_KOKU = os.path.dirname(os.path.abspath(__file__))
ZIP_ADI = "harmanlojistik.zip"
ZIP_YOLU = os.path.join(PROJE_KOKU, ZIP_ADI)

# ZIP içindeki kök klasör adı (açılınca düzenli yapı için)
ZIP_KOK_KLASOR = "harmanlojistik"

# Dahil edilecek dosya ve klasörler
DAHIL_EDILECEKLER = [
    "core",
    "templates",
    "static",
    "data",
    "veri_uret.py",
    "app.py",
    "requirements.txt",
    "README.md",
    "zip_olustur.py",
]

# Hariç tutulacak dizin adları
HARIC_KLASORLER = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".cursor",
    ".idea",
    "node_modules",
}

# Hariç tutulacak dosya adları / uzantıları
HARIC_DOSYALAR = {
    ZIP_ADI,
    ".env",
    ".gitignore",
    ".DS_Store",
    "Thumbs.db",
}

HARIC_UZANTILAR = {".pyc", ".pyo", ".png"}


def _haric_mi(dosya_yolu: str, dosya_adi: str) -> bool:
    """Dosyanın ZIP'e dahil edilmemesi gerekip gerekmediğini kontrol eder."""
    # Üretilmiş PNG grafikleri hariç (klasör .gitkeep ile kalır)
    if dosya_adi.endswith(".png") and "static" in dosya_yolu.replace("\\", "/"):
        if "grafikler" in dosya_yolu.replace("\\", "/"):
            return True

    if dosya_adi in HARIC_DOSYALAR:
        return True

    for uzanti in HARIC_UZANTILAR:
        if dosya_adi.endswith(uzanti):
            # .gitkeep dosyası korunur
            if dosya_adi == ".gitkeep":
                return False
            return True

    return False


def _yol_haric_klasorde_mi(yol: str) -> bool:
    """Yol hariç tutulan bir klasörün içinde mi kontrol eder."""
    parcalar = yol.replace("\\", "/").split("/")
    return any(p in HARIC_KLASORLER for p in parcalar)


def zip_olustur() -> tuple[str, int, int]:
    """
    harmanlojistik.zip arşivini oluşturur.
    Döndürür: (zip_yolu, dosya_sayisi, boyut_byte)
    """
    eklenen_dosyalar: list[str] = []

    with zipfile.ZipFile(ZIP_YOLU, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for oge in DAHIL_EDILECEKLER:
            tam_yol = os.path.join(PROJE_KOKU, oge)

            if not os.path.exists(tam_yol):
                print(f"[UYARI] Bulunamadi, atlaniyor: {oge}")
                continue

            if os.path.isfile(tam_yol):
                if _haric_mi(tam_yol, os.path.basename(tam_yol)):
                    continue
                arcname = f"{ZIP_KOK_KLASOR}/{oge}"
                zf.write(tam_yol, arcname)
                eklenen_dosyalar.append(arcname)
            else:
                for kok, _, dosyalar in os.walk(tam_yol):
                    if _yol_haric_klasorde_mi(kok):
                        continue

                    for dosya in dosyalar:
                        dosya_yolu = os.path.join(kok, dosya)
                        if _haric_mi(dosya_yolu, dosya):
                            continue

                        goreli = os.path.relpath(dosya_yolu, PROJE_KOKU)
                        arcname = f"{ZIP_KOK_KLASOR}/{goreli.replace(os.sep, '/')}"
                        zf.write(dosya_yolu, arcname)
                        eklenen_dosyalar.append(arcname)

    boyut = os.path.getsize(ZIP_YOLU)
    return ZIP_YOLU, len(eklenen_dosyalar), boyut


def _boyut_okunakli(byte: int) -> str:
    """Byte cinsinden boyutu okunaklı formata çevirir."""
    if byte < 1024:
        return f"{byte} B"
    if byte < 1024 * 1024:
        return f"{byte / 1024:.1f} KB"
    return f"{byte / (1024 * 1024):.2f} MB"


def main():
    """ZIP oluşturur ve doğrulama bilgisini yazdırır."""
    print("HarmanLojistik ZIP paketi olusturuluyor...")
    print(f"Hedef: {ZIP_YOLU}\n")

    zip_yolu, dosya_sayisi, boyut = zip_olustur()

    print("=" * 50)
    print("ZIP basariyla olusturuldu!")
    print(f"  Dosya    : {zip_yolu}")
    print(f"  Icerik   : {dosya_sayisi} dosya")
    print(f"  Boyut    : {_boyut_okunakli(boyut)} ({boyut:,} byte)")
    print("=" * 50)

    # İçerik doğrulaması
    print("\nZIP icerigi:")
    with zipfile.ZipFile(zip_yolu, "r") as zf:
        for ad in sorted(zf.namelist()):
            bilgi = zf.getinfo(ad)
            print(f"  {ad} ({bilgi.file_size} byte)")


if __name__ == "__main__":
    main()
