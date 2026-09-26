# 🌌 NEBULA // GitHub Pages VPN Gateway

> **Полноценный шлюз рабочих VPN-конфигураций на базе GitHub Pages и GitHub Actions — без своего сервера и без абонентской платы.**

Этот репозиторий превращает GitHub Pages в **персональный сервер подписок (Subscription Server)** для клиентов **v2rayNG, Hiddify, V2Box, Clash Meta и Sing-Box**.

---

## ⚡ Как это работает

1. **GitHub Pages** бесплатно раздает статические файлы подписки:
   - `https://<ваш-логин>.github.io/<репозиторий>/sub.txt` — универсальная подписка (Base64).
   - `https://<ваш-логин>.github.io/<репозиторий>/clash.yaml` — профиль для Clash Meta / Mihomo.
   - `https://<ваш-логин>.github.io/<репозиторий>/sing-box.json` — конфиг для Sing-Box.
   - Красивая интерактивная страница `index.html` с генератором QR-кодов, кнопками импорта в 1 клик и списком нод.
2. **GitHub Actions** каждые 6 часов запускает скрипт в облаке Microsoft Azure, который собирает и валидирует свежие бесплатные узлы (Cloudflare WARP, VLESS, VMess, Trojan, Shadowsocks), обновляет файлы и автоматически деплоит изменения на GitHub Pages.
3. **Клиент на телефоне или ПК** автоматически обновляет список серверов раз в сутки. У вас всегда есть рабочее соединение.

---

## 🚀 Инструкция по запуску за 3 шага

### Шаг 1. Создайте репозиторий на GitHub
1. Перейдите на [github.com/new](https://github.com/new).
2. Задайте имя репозитория, например: `vpn-sub` или `my-vpn`.
3. Оставьте его **Public** (публичным, так как для бесплатных аккаунтов GitHub Pages работает на публичных репозиториях).
4. Нажмите **Create repository**.

### Шаг 2. Загрузите файлы в репозиторий
Вы можете загрузить файлы через Git из папки проекта:
```bash
cd C:\Users\goga0\.gemini\antigravity-ide\scratch\vpn-github-pages
git init
git add .
git commit -m "Initial commit of VPN Pages Gateway"
git branch -M main
git remote add origin https://github.com/<ВАШ_НИК_НА_GITHUB>/<ИМЯ_РЕПОЗИТОРИЯ>.git
git push -u origin main
```
*(Либо просто перетащите файлы через браузер с помощью кнопки **Upload files** на странице репозитория).*

### Шаг 3. Включите GitHub Pages
1. В репозитории на GitHub перейдите в **Settings** (Настройки).
2. В левой колонке выберите **Pages**.
3. В разделе **Build and deployment**:
   - **Source**: выберите `Deploy from a branch`.
   - **Branch**: выберите `main` и папку `/(root)`.
   - Нажмите **Save**.
4. Подождите 1–2 минуты. Вверху появится ссылка:
   `https://<ваш-ник>.github.io/<имя-репозитория>/`

### Шаг 4. Разрешите GitHub Actions автообновление (1 клик)
1. В репозитории откройте **Settings** → **Actions** → **General**.
2. Прокрутите вниз до раздела **Workflow permissions**.
3. Выберите пункт **Read and write permissions** (чтобы бот мог коммитить обновленные конфиги) и нажмите **Save**.

---

## 📱 Как подключиться к VPN

### 1. Быстрый импорт через веб-интерфейс
Откройте созданный сайт в браузере на телефоне или ПК:
- Нажмите кнопку **Hiddify**, **v2rayNG** или **V2Box** — приложение сразу откроется и импортирует подписку.
- Либо нажмите **QR-код** и отсканируйте камерой из приложения.

### 2. Вручную через ссылку подписки
Скопируйте URL:
```text
https://<ваш-ник>.github.io/<имя-репозитория>/sub.txt
```
Вставьте его в вашем клиенте в раздел **Subscriptions / Подписки**.

### Рекомендуемые приложения:
* **Android**: [v2rayNG](https://github.com/2dust/v2rayNG/releases), [Hiddify](https://github.com/hiddify/hiddify-next/releases)
* **iOS (iPhone/iPad)**: [V2Box](https://apps.apple.com/app/v2box-v2ray-client/id6446814042), [Streisand](https://apps.apple.com/app/streisand/id6450534064), [FoXray](https://apps.apple.com/app/foxray/id6448898396)
* **Windows**: [Hiddify Next](https://github.com/hiddify/hiddify-next/releases), [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases)
* **macOS**: [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases), [FoXray](https://apps.apple.com/app/foxray/id6448898396)

---

## 🔄 Ручной запуск обновления узлов
Если хотите принудительно обновить список серверов прямо сейчас:
1. Перейдите во вкладку **Actions** вашего репозитория.
2. Слева выберите **Auto-Update VPN Subscription**.
3. Нажмите кнопку **Run workflow** справа.
4. Через ~30 секунд скрипт проверит все источники и зальет новые узлы!
