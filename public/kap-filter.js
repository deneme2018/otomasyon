// Basit KAP filtresi (localStorage ile kalıcı)
// Bu versiyon, Python tarafından oluşturulan HTML tablosu (id="news-list")
// ve içindeki <tr> elemanları üzerinde çalışır.
(function () {
  const CHECK_KEY = 'includeKapNews';
  const checkbox = document.getElementById('include-kap-checkbox');
  // Python kodu tabloya id="news-list" atadığı için bu artık <table> elementidir.
  const newsList = document.getElementById('news-list'); 

  // Eğer filtreleme kutucuğu veya tablo bulunamazsa çalışmayı durdur.
  if (!checkbox || !newsList) return;

  function readStored() {
    const val = localStorage.getItem(CHECK_KEY);
    // Varsayılan: KAP içermesin (false)
    return val === null ? false : val === 'true';
  }

  function writeStored(v) {
    localStorage.setItem(CHECK_KEY, String(v));
  }

  function filterKap() {
    const includeKap = checkbox.checked;
    
    // Haberlerin bulunduğu tüm <tr> satırlarını seç.
    // to_html metodu <table> içinde <tbody> oluşturur.
    const items = newsList.querySelectorAll('tbody > tr'); 
    
    items.forEach(item => {
      // Haber başlığının (Konu) bulunduğu 3. sütunu (index 2) bul (0=Tarih, 1=Saat, 2=Konu).
      const subjectCell = item.children[2]; 
      
      if (subjectCell) {
        // Haber başlığı metnini al (link içindeki metni alabilmek için innerText/textContent kullanıyoruz).
        const subjectText = subjectCell.textContent || subjectCell.innerText;

        // Haber başlığı "KAP:" ile başlıyorsa bu bir KAP haberidir.
        const isKap = subjectText.trim().toUpperCase().startsWith('KAP:'); 
        
        if (isKap) {
          // Eğer KAP haberi ise: kutucuk işaretliyse göster, değilse gizle.
          item.style.display = includeKap ? '' : 'none';
        } else {
          // KAP dışındaki haberler her zaman gösterilir (gösteri işaretini kaldır).
          item.style.display = '';
        }
      }
    });
  }

  // Init: checkbox durumunu oku, uygula
  checkbox.checked = readStored();
  filterKap();

  // Olay dinleyicisini kur
  checkbox.addEventListener('change', () => {
    writeStored(checkbox.checked);
    filterKap();
  });
})();
