import re
import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup

# --- Ayarlar ---
# Matriks haberlerinin listelendiği sayfanın URL'sini buraya yazın.
MATRIKS_HABER_URL = "https://www.matriksdata.com/website/matriks-haberler" # Örnek URL.
CSV_FILENAME = "matriks_haber_arsivi.csv"
ID_DOSYA = 'kayitli_haber_idleri.txt'

def id_kontrol_dosyasini_yukle(id_dosya_adi):
    """Daha önce kaydedilmiş haber ID'lerini dosyadan yükler."""
    try:
        with open(id_dosya_adi, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def id_kontrol_dosyasini_kaydet(id_dosya_adi, kayitli_idler):
    """Güncel haber ID'leri kümesini dosyaya kaydeder."""
    with open(id_dosya_adi, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(list(kayitli_idler))))

def temiz_konu_olustur(konu_ham):
    """
    CSV uyumluluğu için Konu metnini temizler:
    1. Yeni satır karakterlerini kaldırır.
    2. Birden fazla boşluğu tek bir boşluğa indirir.
    3. CSV ayırıcısı olan noktalı virgülleri (;) virgüle çevirir.
    """
    # 1. Yeni satır ve sekme karakterlerini boşlukla değiştir.
    konu = konu_ham.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    # 2. Birden fazla boşluğu tek bir boşluğa indir.
    konu = re.sub(r'\s+', ' ', konu).strip() 

    # 3. CSV ayırıcısı çakışmasını engellemek için tüm noktalı virgülleri virgüle çevir.
    konu = konu.replace(';', ',') 

    # 4. CSV'yi bozabilecek çift tırnak işaretlerini (') tek tırnakla değiştir.
    konu = konu.replace('"', "'") 
    
    return konu

def haberleri_ayristir_ve_kaydet():
    print(f"🔄 Matriks haberleri {MATRIKS_HABER_URL} adresinden çekiliyor...")
    
    # 1. HTML İçeriğini Çek
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(MATRIKS_HABER_URL, headers=headers, timeout=10)
        response.raise_for_status()
        html_icerik = response.text
        print("✅ HTML içeriği başarıyla çekildi.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Hata: URL'ye erişilemedi veya zaman aşımı: {e}")
        print("URL'yi kontrol edin. Sayfa oturum açma (login) gerektiriyorsa 'Selenium' yöntemine geçmeniz gerekebilir.")
        return

    # 2. Kayıtlı ID'leri yükle
    kayitli_idler = id_kontrol_dosyasini_yukle(ID_DOSYA)
    print(f"Yüklenen Toplam Kayıtlı ID: {len(kayitli_idler)}")

    # 3. HTML'i ayrıştır ve haberleri filtrele
    soup = BeautifulSoup(html_icerik, 'html.parser')
    # Haber tablosu satırlarını arıyoruz (style="cursor:pointer;" olanlar)
    haber_satirlari = soup.find_all('tr', style=re.compile("cursor:pointer;"))

    data = []
    id_deseni = re.compile(r'/(\d+)-')

    for satir in haber_satirlari:
        # URL'yi (linki) onclick özelliğinden al
        onclick_metni = satir.get('onclick', '')
        url_match = re.search(r"document\.location='([^']+)'", onclick_metni)
        
        if not url_match:
            continue
        
        haber_url = url_match.group(1)
        
        # URL'den benzersiz ID'yi al
        id_match = id_deseni.search(haber_url)
        haber_id = id_match.group(1) if id_match else haber_url

        # Tekrarlanan Kontrolü
        if haber_id in kayitli_idler:
            continue
        
        # Yeni haber! Verileri topla.
        sutunlar = satir.find_all('td')
        if len(sutunlar) >= 3:
            tarih = sutunlar[0].text.strip()
            saat = sutunlar[1].text.strip()
            konu_ham = sutunlar[2].text.strip()
            
            # Konu metnini temizleme fonksiyonu ile CSV'ye hazır hale getir.
            konu = temiz_konu_olustur(konu_ham) 
            
            data.append({
                'Tarih': tarih,
                'Saat': saat,
                'Konu': konu,
                'URL': haber_url
            })
            
            # Yeni ID'yi kayitli_idler kümesine ekle
            kayitli_idler.add(haber_id)

    # 4. Sonuçları Kaydet
    if data:
        try:
            # Mevcut arşiv dosyasını yükle (varsa)
            df_eski = pd.read_csv(CSV_FILENAME, sep=';', encoding='utf-8-sig')
            df_yeni = pd.DataFrame(data)
            df_final = pd.concat([df_eski, df_yeni], ignore_index=True)
        except FileNotFoundError:
            # Dosya yoksa sadece yeni veriyi kullan
            df_final = pd.DataFrame(data)
        
        # Güncellenmiş DataFrame'i CSV olarak kaydet
        # index=False: Satır numaralarını kaydetmez
        # encoding='utf-8-sig': Türkçe karakterler (ş,ç,ö) için Excel uyumlu kaydeder
        # sep=';': Ayırıcı olarak noktalı virgül kullanır
        df_final.to_csv(CSV_FILENAME, sep=';', encoding='utf-8-sig', index=False)
        id_kontrol_dosyasini_kaydet(ID_DOSYA, kayitli_idler)

        print(f"\n--- İŞLEM BAŞARILI ---")
        print(f"Arşive Eklenen Yeni Haber Sayısı: {len(data)}")
        print(f"Toplam Kaydedilmiş Benzersiz Haber: {len(kayitli_idler)}")
        print(f"Veriler '{CSV_FILENAME}' dosyasına kaydedildi.")
    else:
        print("\n--- İŞLEM TAMAMLANDI ---")
        print("Yeni haber bulunamadı veya tüm haberler zaten kayıtlıydı.")

if __name__ == "__main__":
    haberleri_ayristir_ve_kaydet()
