import re
import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- Ayarlar ---
MATRIKS_HABER_URL = "https://www.matriksdata.com/website/matriks-haberler"
CSV_FILENAME = "matriks_haber_arsivi.csv"
ID_DOSYA = "kayitli_haber_idleri.txt"
HTML_FILENAME = "index.html"

def id_kontrol_dosyasini_yukle(id_dosya_adi):
    """Daha önce kaydedilmiş haber ID'lerini dosyadan yükler."""
    try:
        with open(id_dosya_adi, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def id_kontrol_dosyasini_kaydet(id_dosya_adi, kayitli_idler):
    """Güncel haber ID'leri kümesini dosyaya kaydeder."""
    with open(id_dosya_adi, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(list(kayitli_idler))))

def temiz_konu_olustur(konu_ham):
    """Konu metnini CSV/HTML uyumlu hale getirir."""
    konu = konu_ham.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    konu = re.sub(r"\s+", " ", konu).strip()
    konu = konu.replace(";", ",").replace('"', "'")
    return konu

def haberleri_ayristir_ve_kaydet():
    print(f"🔄 Matriks haberleri {MATRIKS_HABER_URL} adresinden çekiliyor...")

    # 1. HTML İçeriğini Çek
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(MATRIKS_HABER_URL, headers=headers, timeout=10)
        response.raise_for_status()
        html_icerik = response.text
        print("✅ HTML içeriği başarıyla çekildi.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Hata: URL'ye erişilemedi: {e}")
        return

    # 2. Kayıtlı ID'leri yükle
    kayitli_idler = id_kontrol_dosyasini_yukle(ID_DOSYA)
    print(f"Yüklenen kayıtlı ID sayısı: {len(kayitli_idler)}")

    # 3. HTML'i ayrıştır
    soup = BeautifulSoup(html_icerik, "html.parser")
    haber_satirlari = soup.find_all("tr", style=re.compile("cursor:pointer;"))
    id_deseni = re.compile(r"/(\d+)-")
    data = []

    for satir in haber_satirlari:
        onclick_metni = satir.get("onclick", "")
        url_match = re.search(r"document\.location='([^']+)'", onclick_metni)
        if not url_match:
            continue
        haber_url = url_match.group(1)
        id_match = id_deseni.search(haber_url)
        haber_id = id_match.group(1) if id_match else haber_url
        if haber_id in kayitli_idler:
            continue

        sutunlar = satir.find_all("td")
        if len(sutunlar) >= 3:
            tarih = sutunlar[0].text.strip()
            saat = sutunlar[1].text.strip()
            konu = temiz_konu_olustur(sutunlar[2].text.strip())
            data.append({
                "Tarih": tarih,
                "Saat": saat,
                "Konu": konu,
                "URL": haber_url
            })
            kayitli_idler.add(haber_id)

    # 4. CSV Güncelle
    if data:
        try:
            df_eski = pd.read_csv(CSV_FILENAME, sep=";", encoding="utf-8-sig")
            df_yeni = pd.DataFrame(data)
            df_final = pd.concat([df_eski, df_yeni], ignore_index=True)
        except FileNotFoundError:
            df_final = pd.DataFrame(data)
    else:
        try:
            df_final = pd.read_csv(CSV_FILENAME, sep=";", encoding="utf-8-sig")
            print("ℹ️ Yeni haber yok, mevcut verilerle devam ediliyor.")
        except FileNotFoundError:
            print("⚠️ Henüz hiç haber kaydı yok.")
            return

    # 📅 Tarih + Saat birleştir ve azalan sırala (en güncel en üstte)
    df_final["Tarih_Saat"] = pd.to_datetime(
        df_final["Tarih"] + " " + df_final["Saat"],
        format="%d.%m.%Y %H:%M",
        errors="coerce"
    )
    df_final = df_final.sort_values(by="Tarih_Saat", ascending=False)

    # 🔄 CSV kaydet (artık sıralı)
    df_final.to_csv(CSV_FILENAME, sep=";", encoding="utf-8-sig", index=False)
    id_kontrol_dosyasini_kaydet(ID_DOSYA, kayitli_idler)
    print(f"✅ {len(data)} yeni haber eklendi." if data else "✅ Veri güncel, sadece sıralama yenilendi.")

    # 5. HTML Sayfası Oluştur
    try:
        # 5a. Otomasyon Çalışma Saati (TR Saati)
        utc_now = datetime.now()
        tr_now = utc_now + timedelta(hours=3)
        son_otomasyon_guncellemesi = tr_now.strftime("%Y-%m-%d %H:%M")

        # 5b. En Güncel Haber Bilgisini Bul
        if not df_final.empty:
            en_yeni_haber_tarihi = df_final["Tarih_Saat"].max().strftime("%d.%m.%Y %H:%M")
            haber_guncelligi_mesaji = f"<div class='latest-news'>🕓 En Güncel Haber: <b>{en_yeni_haber_tarihi}</b></div>"
        else:
            haber_guncelligi_mesaji = "<div class='latest-news'>Arşivde henüz haber bulunmuyor.</div>"

        # 5c. HTML Başlığı Oluşturma
        html_baslik = f"""
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Matriks Haber Arşivi</title>
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    background: #f8f9fa;
                    color: #333;
                    padding: 30px;
                }}
                h1 {{
                    color: #222;
                    margin-bottom: 10px;
                }}
                .latest-news {{
                    font-size: 1.2em;
                    font-weight: 600;
                    color: #007bff;
                    border-bottom: 3px solid #007bff;
                    display: inline-block;
                    margin-bottom: 20px;
                    padding-bottom: 5px;
                }}
                .update-time {{
                    font-size: 0.9em;
                    color: #666;
                    margin-bottom: 15px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    background: #fff;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background: #f0f0f0;
                }}
                tr:hover {{
                    background-color: #f9f9f9;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 0.9em;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <h1>📰 Matriks Haber Arşivi</h1>
            {haber_guncelligi_mesaji}
            <p class="update-time">Son Otomasyon Çalışma Saati (TR): {son_otomasyon_guncellemesi}</p>
        """

        html_tablo = df_final.drop(columns=["Tarih_Saat"]).to_html(index=False, escape=False, border=0)
        html_son = f"""
            {html_tablo}
            <div class="footer">
                <p>Bu sayfa otomatik olarak oluşturulmuştur.</p>
            </div>
        </body>
        </html>
        """

        with open(HTML_FILENAME, "w", encoding="utf-8") as f:
            f.write(html_baslik + html_son)

        print(f"✅ HTML sayfası '{HTML_FILENAME}' dosyasına kaydedildi.")
    except Exception as e:
        print(f"❌ HTML oluşturulamadı: {e}")

if __name__ == "__main__":
    haberleri_ayristir_ve_kaydet()
