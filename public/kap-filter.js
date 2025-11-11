// Basit KAP filtresi (localStorage ile kalıcı)
// Gereksinim: her haber öğesinde data-source="<kaynak>" olmalı (ör. "KAP" veya "OTHER")
(function () {
  const CHECK_KEY = 'includeKapNews';
  const checkbox = document.getElementById('include-kap-checkbox');
  const newsList = document.getElementById('news-list');

  if (!checkbox || !newsList) return;

  function readStored() {
    const val = localStorage.getItem(CHECK_KEY);
    // Varsayılan: KAP içermesin (false)
    return val === null ? false : val === 'true';
  }

  function writeStored(v) {
    localStorage.setItem(CHECK_KEY, String(v));
  }

  function normalizeSource(s) {
    return (s || '').toString().trim().toLowerCase();
  }

  function filterKap() {
    const includeKap = checkbox.checked;
    const items = newsList.querySelectorAll('.news-item[data-source]');
    items.forEach(item => {
      const src = normalizeSource(item.getAttribute('data-source'));
      if (src === 'kap') {
        item.style.display = includeKap ? '' : 'none';
      } else {
        item.style.display = '';
      }
    });
  }

  // Init: checkbox durumunu oku, uygula
  checkbox.checked = readStored();
  filterKap();

  checkbox.addEventListener('change', () => {
    writeStored(checkbox.checked);
    filterKap();
  });

  // Eğer haberleri dinamik (API ile) çekiyorsanız, filterKap() fonksiyonunu
  // veri render edildikten hemen sonra çağırın.
  // Örnek:
  // fetch('/api/news').then(r => r.json()).then(renderNews).then(filterKap);
})();
