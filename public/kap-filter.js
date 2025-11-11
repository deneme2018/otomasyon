// Basit KAP filtresi (localStorage ile kalıcı)
// Artık tablo yapısındaki TR'ler üzerinde çalışır ve "KAP:" metnine bakar.
(function () {
  const CHECK_KEY = 'includeKapNews';
  const checkbox = document.getElementById('include-kap-checkbox');
  const newsList = document.getElementById('news-list'); // Canlı sitede bu ID, <table> elementine karşılık geliyor

  // Canlı sitede filtre görünmediği için bu kontrol başarısız olabilir.
  // Varsayalım ki bu betiği, filtreleme kutucuğu DOM'a eklenmeden önce çağırıyor.
  // Bu kodun çalışması için, hem #include-kap-checkbox hem de #news-list ID'lerinin
  // Python tarafından üretilen HTML'de var olması GEREKİR.
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
    // newsList (muhtemelen <table>) içindeki tüm <tr> elemanlarını seç
    // Canlı sitedeki haberler <tbody> içindeki <tr>'ler
    const items = newsList.querySelectorAll('tbody > tr'); 
    
    items.forEach(item => {
      // Haber başlığının (Konu) bulunduğu 3. sütunu (index 2) bul
      const subjectCell = item.children[2]; 
      
      if (subjectCell) {
        // Haber başlığı "KAP:" ile başlıyorsa bu bir KAP haberidir.
        const isKap = subjectCell.textContent.trim().toUpperCase().startsWith('KAP:'); 
        
        if (isKap) {
          // Eğer KAP haberi ise: kutucuk işaretliyse göster, değilse gizle.
          item.style.display = includeKap ? '' : 'none';
        } else {
          // KAP dışındaki haberler her zaman gösterilir.
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
