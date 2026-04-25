import requests
import random
import time
import os
import re
import threading
import redis
from datetime import datetime

# ══════════════════════════════════════
#  JAP
# ══════════════════════════════════════
JAP_API_KEY = os.environ.get("JAP_KEY", "ec2fb6c8f5a4ea7ba6cf532e87a09895")
JAP_API_URL = "https://justanotherpanel.com/api/v2"

# ══════════════════════════════════════
#  SCRAPERAPI
# ══════════════════════════════════════
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "9d538a4836e83b0ff52157ccfe3aca8b")

# ══════════════════════════════════════
#  VKONTAKTE
# ══════════════════════════════════════
VK_TOKEN          = os.environ.get("VK_TOKEN", "vk1.a.3l-M4WzpxupxkQ1LO5QEJKxhXtlyzgP6m9f7UnUXmtmOCGTp8Pj26J5cdb_hPqB8-wSrFsRTgUVIwcwZQK6iL-cx8p23NQnt65AcdJ1yWNnqj21ZKOWnSrPyKiUudvEjdCQjzBNoDSF2vq6AjPKbPtvP-kOGAo28Uhiet66MoYaXUU9UktA3zGcZfrf7V0nKu7eUkOqnHAU9a-GcfGIW0Q")
VK_API_URL        = "https://api.vk.com/method"
VK_VERSION        = "5.131"
VK_SERVICE        = 3756
VK_QTY_MIN        = 20
VK_QTY_MAX        = 35
VK_PAGES          = ["biznes___13"]
VK_CHECK_INTERVAL = 3600  # каждый час

# ══════════════════════════════════════
#  RUTUBE
# ══════════════════════════════════════
RUTUBE_CHANNEL_ID     = "56184868"
RUTUBE_SERVICE        = 9777
RUTUBE_QTY_MIN        = 500
RUTUBE_QTY_MAX        = 1200
RUTUBE_CHECK_INTERVAL = 3600  # каждый час

# ══════════════════════════════════════
#  FACEBOOK — REELS (ScraperAPI)
# ══════════════════════════════════════
FB_PAGE_ID        = "100081997113052"
FB_REELS_SERVICE  = 9604
FB_REELS_QTY_MIN  = 500
FB_REELS_QTY_MAX  = 1000
FB_REELS_INTERVAL = 3600  # каждый час

# ══════════════════════════════════════
#  УТИЛИТЫ
# ══════════════════════════════════════

# Redis — постоянное хранилище (не теряется при рестарте)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
r = redis.from_url(REDIS_URL, decode_responses=True)

def log(platform, msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{platform}] {msg}", flush=True)

def load_state(key):
    return r.get(key)

def save_state(key, value):
    r.set(key, str(value))

def load_state_dict(key):
    data = r.hgetall(key)
    return data if data else {}

def save_state_dict(key, data):
    if data:
        r.delete(key)
        r.hset(key, mapping=data)

def is_in_set(key, value):
    return r.sismember(key, value)

def add_to_set(key, value):
    r.sadd(key, value)

def get_set(key):
    return r.smembers(key)

def create_jap_order(platform, link, service, qty_min, qty_max):
    quantity = random.randint(qty_min, qty_max)
    payload = {"key": JAP_API_KEY, "action": "add", "service": service, "link": link, "quantity": quantity}
    try:
        log(platform, f"📤 Заказ: service={service}, qty={quantity}")
        resp = requests.post(JAP_API_URL, data=payload, timeout=15)
        log(platform, f"📥 JAP: {resp.status_code} | {repr(resp.text[:150])}")
        if not resp.text.strip():
            log(platform, "❌ Пустой ответ JAP")
            return
        data = resp.json()
        if "order" in data:
            log(platform, f"✅ Заказ #{data['order']} | Услуга: {service} | Кол-во: {quantity}")
        elif "error" in data:
            log(platform, f"❌ JAP ошибка: {data['error']}")
    except Exception as e:
        log(platform, f"❌ Ошибка заказа: {e}")

def check_balance():
    try:
        resp = requests.post(JAP_API_URL, data={"key": JAP_API_KEY, "action": "balance"}, timeout=10)
        if resp.text.strip():
            data = resp.json()
            if "balance" in data:
                log("JAP", f"💰 Баланс: ${data['balance']} {data.get('currency', '')}")
    except Exception as e:
        log("JAP", f"❌ Ошибка баланса: {e}")

# ══════════════════════════════════════
#  VKONTAKTE
# ══════════════════════════════════════
def get_vk_post(page_slug):
    try:
        resp = requests.get(f"{VK_API_URL}/wall.get", params={
            "domain": page_slug, "count": 10, "filter": "owner",
            "access_token": VK_TOKEN, "v": VK_VERSION,
        }, timeout=15)
        data = resp.json()
        if "error" in data:
            log("VK", f"❌ API ошибка: {data['error']}")
            return None, None
        items = data.get("response", {}).get("items", [])
        if not items:
            return None, None
        non_pinned = [i for i in items if not i.get("is_pinned")]
        if not non_pinned:
            non_pinned = items
        latest = max(non_pinned, key=lambda x: x.get("date", 0))
        owner_id = latest["owner_id"]
        post_id = latest["id"]
        post_url = f"https://vk.com/wall{owner_id}_{post_id}"
        log("VK", f"✅ Последний пост @{page_slug}: {post_url}")
        return f"{owner_id}_{post_id}", post_url
    except Exception as e:
        log("VK", f"❌ Ошибка @{page_slug}: {e}")
        return None, None

def vk_bot():
    log("VK", f"📱 Запущен | Страницы: {VK_PAGES} | Услуга: {VK_SERVICE} | {VK_QTY_MIN}-{VK_QTY_MAX}")
    state = load_state_dict("vk:last_posts")
    for page in VK_PAGES:
        if page not in state:
            post_id, _ = get_vk_post(page)
            if post_id:
                state[page] = post_id
                log("VK", f"📌 @{page} — последний пост: #{post_id}. Жду новые...")
    save_state_dict("vk:last_posts", state)
    while True:
        time.sleep(VK_CHECK_INTERVAL)
        try:
            for page in VK_PAGES:
                latest_id, post_url = get_vk_post(page)
                if not latest_id:
                    continue
                last_id = state.get(page)
                if latest_id != last_id:
                    log("VK", f"🆕 Новый пост @{page}: {post_url}")
                    create_jap_order("VK", post_url, VK_SERVICE, VK_QTY_MIN, VK_QTY_MAX)
                    state[page] = latest_id
                    save_state_dict("vk:last_posts", state)
                else:
                    log("VK", f"🔍 @{page} — нет новых постов (последний: #{last_id})")
        except Exception as e:
            log("VK", f"❌ Ошибка: {e}")

# ══════════════════════════════════════
#  RUTUBE
# ══════════════════════════════════════
def get_rutube_videos():
    try:
        url = f"https://rutube.ru/api/video/person/{RUTUBE_CHANNEL_ID}/?format=json&page=1&pageSize=10&ordering=-created_ts"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://rutube.ru/"}
        resp = requests.get(url, headers=headers, timeout=15)
        log("Rutube", f"📥 API: {resp.status_code}")
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            log("Rutube", f"📊 Найдено видео: {len(results)}")
            return results
        return []
    except Exception as e:
        log("Rutube", f"❌ Ошибка: {e}")
        return []

def rutube_bot():
    log("Rutube", f"📺 Запущен | Channel: {RUTUBE_CHANNEL_ID} | Услуга: {RUTUBE_SERVICE} | {RUTUBE_QTY_MIN}-{RUTUBE_QTY_MAX}")
    last_id = load_state("rutube:last_id")
    if not last_id:
        videos = get_rutube_videos()
        if videos:
            vid_id = str(videos[0].get("id") or videos[0].get("uuid") or "")
            if vid_id:
                save_state("rutube:last_id", vid_id)
                last_id = vid_id
                log("Rutube", f"📌 Последнее видео: #{vid_id}. Жду новые...")
    while True:
        time.sleep(RUTUBE_CHECK_INTERVAL)
        try:
            videos = get_rutube_videos()
            if not videos:
                continue
            new_videos = []
            for video in videos:
                vid_id = str(video.get("id") or video.get("uuid") or "")
                if vid_id and vid_id != str(last_id):
                    new_videos.append(video)
                else:
                    break
            if new_videos:
                log("Rutube", f"🆕 Новых видео: {len(new_videos)}")
                latest_id = str(videos[0].get("id") or videos[0].get("uuid") or "")
                for video in new_videos:
                    vid_id = str(video.get("id") or video.get("uuid") or "")
                    vid_url = f"https://rutube.ru/video/{vid_id}/"
                    log("Rutube", f"🆕 {video.get('title', '')[:50]} | {vid_url}")
                    create_jap_order("Rutube", vid_url, RUTUBE_SERVICE, RUTUBE_QTY_MIN, RUTUBE_QTY_MAX)
                    time.sleep(2)
                save_state("rutube:last_id", latest_id)
                last_id = latest_id
            else:
                log("Rutube", f"🔍 Нет новых видео (последнее: #{last_id})")
        except Exception as e:
            log("Rutube", f"❌ Ошибка: {e}")

# ══════════════════════════════════════
#  FACEBOOK — REELS (ScraperAPI)
# ══════════════════════════════════════
def fetch_fb_reels():
    target_url = f"https://www.facebook.com/{FB_PAGE_ID}/reels"
    scraper_url = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={requests.utils.quote(target_url)}&render=true&country_code=us"
    log("FB-Reels", f"🔄 ScraperAPI запрос...")
    try:
        resp = requests.get(scraper_url, timeout=60)
        log("FB-Reels", f"📥 Status: {resp.status_code} | HTML: {len(resp.text)} символов")
        html = resp.text

        urls = set()

        # Паттерн 1: прямые ссылки на Reels
        for match in re.finditer(r'https://www\.facebook\.com/reel/(\d+)', html):
            urls.add(f"https://www.facebook.com/reel/{match.group(1)}")

        # Паттерн 2: video_id в JSON
        for match in re.finditer(r'"video_id":"(\d{10,})"', html):
            urls.add(f"https://www.facebook.com/watch/?v={match.group(1)}")

        # Паттерн 3: /videos/ ссылки
        for match in re.finditer(r'href="(/[^"]+/videos/(\d+)[^"]*)"', html):
            urls.add(f"https://www.facebook.com{match.group(1)}")

        log("FB-Reels", f"🎬 Найдено Reels: {len(urls)}")
        return list(urls)
    except Exception as e:
        log("FB-Reels", f"❌ Ошибка ScraperAPI: {e}")
        return []

def facebook_reels_bot():
    log("FB-Reels", f"🎬 Запущен (ScraperAPI) | Услуга: {FB_REELS_SERVICE} | {FB_REELS_QTY_MIN}-{FB_REELS_QTY_MAX}")

    # Первый запуск — запоминаем существующие Reels, не крутим
    existing = get_set("fb:processed_reels")
    if not existing:
        log("FB-Reels", "📌 Первый запуск — запоминаю существующие Reels...")
        reels = fetch_fb_reels()
        if reels:
            for reel_url in reels:
                add_to_set("fb:processed_reels", reel_url)
            log("FB-Reels", f"📌 Запомнено {len(reels)} Reels. Жду новые...")

    while True:
        time.sleep(FB_REELS_INTERVAL)
        try:
            reels = fetch_fb_reels()
            new_reels = [url for url in reels if not is_in_set("fb:processed_reels", url)]

            if new_reels:
                log("FB-Reels", f"🆕 Новых Reels: {len(new_reels)}")
                for reel_url in new_reels:
                    log("FB-Reels", f"🆕 {reel_url}")
                    create_jap_order("FB-Reels", reel_url, FB_REELS_SERVICE, FB_REELS_QTY_MIN, FB_REELS_QTY_MAX)
                    add_to_set("fb:processed_reels", reel_url)
                    time.sleep(2)
            else:
                log("FB-Reels", f"🔍 Нет новых Reels")
        except Exception as e:
            log("FB-Reels", f"❌ Ошибка: {e}")

# ══════════════════════════════════════
#  MAIN
# ══════════════════════════════════════
def main():
    log("MAIN", "🚀 Общий бот запущен: VK + Rutube + FB-Reels")
    check_balance()

    threads = [
        threading.Thread(target=vk_bot,            name="VK",       daemon=True),
        threading.Thread(target=rutube_bot,         name="Rutube",   daemon=True),
        threading.Thread(target=facebook_reels_bot, name="FB-Reels", daemon=True),
    ]

    for t in threads:
        t.start()
        time.sleep(3)

    log("MAIN", "✅ Все 3 бота запущены!")

    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
