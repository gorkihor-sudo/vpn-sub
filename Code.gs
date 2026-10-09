/**
 * NEXUS VPN Subscription Gateway on Google Apps Script
 * Неубиваемый шлюз подписок на защищённой инфраструктуре Google
 */

const UPSTREAM_RAW_URL = 'https://raw.githubusercontent.com/gorkihor-sudo/vpn-sub/main/sub_raw.txt';
const UPSTREAM_CLASH_URL = 'https://raw.githubusercontent.com/gorkihor-sudo/vpn-sub/main/clash.yaml';

function doGet(e) {
  const params = (e && e.parameter) || {};
  const format = (params.format || '').toLowerCase();
  const filter = (params.filter || '').toLowerCase();
  const country = (params.country || '').toUpperCase();
  const refresh = params.refresh === '1';

  // Если явно запрошен веб-интерфейс в браузере (?ui=1)
  if (params.ui === '1') {
    return renderWebPage(e);
  }

  // 1. Формат Clash Meta / Mihomo
  if (format === 'clash' || format === 'yaml') {
    const clashYaml = fetchUpstream(UPSTREAM_CLASH_URL, refresh);
    return ContentService.createTextOutput(clashYaml)
      .setMimeType(ContentService.MimeType.TEXT)
      .downloadAsFile('config.yaml');
  }

  // 2. Получаем список узлов
  let rawContent = fetchUpstream(UPSTREAM_RAW_URL, refresh);
  let lines = rawContent.split(/\r?\n/).filter(line => line.trim().length > 0);

  // Фильтр: только VLESS Reality
  if (filter === 'reality') {
    lines = lines.filter(line => line.toLowerCase().includes('security=reality'));
  }

  // Фильтр по стране
  if (country) {
    lines = lines.filter(line => line.toUpperCase().includes(country));
  }

  const resultText = lines.join('\n');

  // Формат RAW (чистые ссылки)
  if (format === 'raw' || format === 'txt') {
    return ContentService.createTextOutput(resultText)
      .setMimeType(ContentService.MimeType.TEXT);
  }

  // По умолчанию: Base64 подписка (Hiddify, Nekoray, v2rayNG, V2Box, Shadowrocket)
  const base64Sub = Utilities.base64Encode(resultText, Utilities.Charset.UTF_8);
  const output = ContentService.createTextOutput(base64Sub)
    .setMimeType(ContentService.MimeType.TEXT);

  output.downloadAsFile('sub.txt');
  return output;
}

/**
 * Получение данных с быстрым кэшированием на 60 секунд (для мгновенной синхронизации)
 */
function fetchUpstream(url, forceRefresh) {
  const cache = CacheService.getScriptCache();
  const cacheKey = Utilities.base64Encode(url).substring(0, 30);
  
  if (!forceRefresh) {
    const cached = cache.get(cacheKey);
    if (cached) {
      return cached;
    }
  }

  try {
    // Cache-buster параметр предотвращает кэширование GitHub CDN
    const fetchUrl = url + (url.indexOf('?') >= 0 ? '&' : '?') + '_t=' + new Date().getTime();
    const response = UrlFetchApp.fetch(fetchUrl, {
      muteHttpExceptions: true,
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
    });
    const text = response.getContentText();
    // Кэшируем всего на 60 секунд, чтобы новые данные сразу поступали в клиент
    cache.put(cacheKey, text, 60);
    return text;
  } catch (err) {
    return '# Error fetching upstream: ' + err.toString();
  }
}

/**
 * Веб-интерфейс (открывается при ?ui=1)
 */
function renderWebPage(e) {
  const scriptUrl = ScriptApp.getService().getUrl();
  const html = `
  <!DOCTYPE html>
  <html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Google Apps Script VPN Gateway</title>
    <style>
      body { background: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 30px 20px; text-align: center; }
      .card { max-width: 620px; margin: 0 auto; background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 25px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
      h2 { color: #58a6ff; margin-top: 0; }
      .badge { display: inline-block; background: #238636; color: #fff; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 15px; }
      .input-box { width: 100%; box-sizing: border-box; background: #0d1117; border: 1px solid #30363d; color: #58a6ff; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 13px; margin: 10px 0; word-break: break-all; }
      .btn { display: inline-block; margin: 6px 4px; padding: 10px 16px; background: #21262d; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; text-decoration: none; cursor: pointer; font-size: 13px; transition: all 0.2s; }
      .btn:hover { background: #30363d; border-color: #8b949e; color: #fff; }
      .btn-primary { background: #1f6feb; border-color: #388bfd; color: #fff; }
      .btn-primary:hover { background: #388bfd; }
    </style>
  </head>
  <body>
    <div class="card">
      <div class="badge">HOSTED ON GOOGLE CLOUD</div>
      <h2>VPN Subscription Gateway</h2>
      <p style="color:#8b949e; font-size:14px;">Неблокируемый шлюз подписки через <code>script.google.com</code></p>
      
      <div style="text-align: left; margin-top: 20px;">
        <label style="font-size:12px; font-weight:600; color:#8b949e;">URL ПОДПИСКИ ДЛЯ HIDDIFY / NEKORAY / V2RAYNG:</label>
        <input class="input-box" id="subUrl" readonly value="${scriptUrl}">
      </div>

      <div style="margin: 15px 0;">
        <button class="btn btn-primary" onclick="copyUrl('${scriptUrl}')">Скопировать ссылку</button>
        <button class="btn" onclick="copyUrl('${scriptUrl}?filter=reality')">Только VLESS Reality</button>
        <button class="btn" onclick="copyUrl('${scriptUrl}?format=clash')">Clash Meta (YAML)</button>
        <button class="btn" onclick="copyUrl('${scriptUrl}?refresh=1')">Сбросить кэш</button>
      </div>

      <p id="msg" style="color: #3fb950; font-size: 13px; min-height: 18px;"></p>
    </div>

    <script>
      function copyUrl(url) {
        navigator.clipboard.writeText(url).then(() => {
          document.getElementById('msg').innerText = 'Ссылка скопирована в буфер обмена!';
          setTimeout(() => { document.getElementById('msg').innerText = ''; }, 3000);
        });
      }
    </script>
  </body>
  </html>
  `;
  return HtmlService.createHtmlOutput(html)
    .setTitle('Google Apps Script VPN Gateway')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}