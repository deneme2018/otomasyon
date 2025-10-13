from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import re

# --- Ayarlar ---
chrome_options = Options()
chrome_options.add_argument("--start-maximized")

SEARCH_KEYWORD = "mum"

service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get("https://www.trendyol.com/")

wait = WebDriverWait(driver, 15)

data = []

# --- 1. Seviye: Ana (Parent) Kategoriler ---
print(f"\n🔍 '{SEARCH_KEYWORD}' için öneriler toplanıyor...")
try:
    search_box = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='suggestion']"))
    )
    search_box.send_keys(SEARCH_KEYWORD)
    time.sleep(3)

    suggestions = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='suggestion-item']")

    parent_keywords = []
    for s in suggestions:
        text = re.sub(r'[\r\n]+', ' ', s.text.strip())
        if text and text != SEARCH_KEYWORD:
            parent_keywords.append(text)
    print(f"✅ {len(parent_keywords)} ana kategori bulundu.")

except Exception as e:
    print(f"❌ Hata: {e}")
    driver.quit()
    exit()

# --- 2. Seviye: Alt (Child) Kategoriler ---
print("\n🔄 Alt kategoriler aranıyor...")
for parent in parent_keywords:
    try:
        print(f"   -> {parent} için alt kategoriler toplanıyor...")
        search_box.clear()
        time.sleep(1)
        search_box.send_keys(parent)
        time.sleep(3)

        child_elements = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='suggestion-item']")
        for c in child_elements:
            child_text = re.sub(r'[\r\n]+', ' ', c.text.strip())
            if child_text and child_text != parent:
                data.append({
                    "parent_keyword": parent,
                    "child_keyword": child_text
                })
    except Exception as e:
        print(f"   -> Hata oluştu: {e}")
        continue

driver.quit()

# --- CSV olarak kaydet ---
df = pd.DataFrame(data)
CSV_FILENAME = "trendyol_keywords.csv"

try:
    df.to_csv(CSV_FILENAME, sep=';', encoding='utf-8-sig', index=False)
    print(f"\n✅ Veriler '{CSV_FILENAME}' dosyasına kaydedildi ({len(df)} satır).")
except Exception as e:
    print(f"❌ Kaydetme hatası: {e}")

print("İşlem tamamlandı.")