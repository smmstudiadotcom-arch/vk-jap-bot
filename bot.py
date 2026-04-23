import requests
import random
import time
import os
import re
import threading
from datetime import datetime

# ══════════════════════════════════════
#  JAP
# ══════════════════════════════════════
JAP_API_KEY = "ec2fb6c8f5a4ea7ba6cf532e87a09895"
JAP_API_URL = "https://justanotherpanel.com/api/v2"

# ══════════════════════════════════════
#  VKONTAKTE
# ══════════════════════════════════════
VK_TOKEN          = "vk1.a.3l-M4WzpxupxkQ1LO5QEJKxhXtlyzgP6m9f7UnUXmtmOCGTp8Pj26J5cdb_hPqB8-wSrFsRTgUVIwcwZQK6iL-cx8p23NQnt65AcdJ1yWNnqj21ZKOWnSrPyKiUudvEjdCQjzBNoDSF2vq6AjPKbPtvP-kOGAo28Uhiet66MoYaXUU9UktA3zGcZfrf7V0nKu7eUkOqnHAU9a-GcfGIW0Q"
VK_API_URL        = "https://api.vk.com/method"
VK_VERSION        = "5.131"
VK_SERVICE        = 3756
VK_QTY_MIN        = 20
VK_QTY_MAX        = 35
VK_PAGES          = ["biznes___13"]
VK_CHECK_INTERVAL = 60

# ══════════════════════════════════════
#  RUTUBE
# ══════════════════════════════════════
RUTUBE_CHANNEL_ID     = "56184868"
RUTUBE_SERVICE        = 9777
RUTUBE_QTY_MIN        = 500
RUTUBE_QTY_MAX        = 1200
RUTUBE_CHECK_INTERVAL = 60

# ══════════════════════════════════════
#  FACEBOOK (мобильная версия)
# ══════════════════════════════════════
FB_PAGE_URL       = "https://m.facebook.com/profile.php?id=100081997113052"
FB_SERVICE        = 9604
FB_QTY_MIN        = 500
FB_QTY_MAX        = 1000
FB_CHECK_INTERVAL = 60
C_USER = "61553351803414"
XS     = "8%3AeGYkn8717BMe-g%3A2%3A1774503965%3A-1%3A-1%3A%3AAcw0XpXFaM1nyL4JOlFdYs_Ud6Y079Nz9FGx2eBrLs8"
DATR   = "gvGqaR00HB8BBQCtWvA_ZrBw"
FR     = "1fXp7RjNu6E4tlLeA.AWc5dZieQn71hppDlUvFZLqzKA5QYrGNQzKXlgvHvbeVm7zLhgs.Bp6coy..AAA.0.0.Bp6coy.AWeEM5yj4-p0pnZr32HrLye4l9I"
SB     = "hfGqaZIWmBX2PQV9iqh9Tr1V"
FB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Cookie": f"c_user={C_USER}; xs={XS}; datr={DATR}; fr={FR}; sb={SB}; ps_l=1; ps_n=1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept-Encoding": "identity",
    "Referer": "https://m.facebook.com/",
}

def log(platform, msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{platform}] {msg}", flush=True)

def load_state(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            val = f.read().strip()
            return val if val else None
    return None

def load_state_dict(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = {}
            for line in f.read().strip().split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    data[k] = v
            return data
    return {}

def save_state(filename, value):
    with open(filename, "w") as f:
        f.write(str(value))

def save_state_dict(filename, data):
    with open(filename, "w") as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")

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
            log(platform, f"✅ Заказ! ID: {data['order']} | Услуга: {service} | Кол-во: {quantity}")
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
                log("JAP", f"💰 Баланс: ${data['balance']} {data.get('currency','')}")
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
    state = load_state_dict("vk_last_posts.txt")
    for page in VK_PAGES:
        if page not in state:
            post_id, _ = get_vk_post(page)
            if post_id:
                state[page] = post_id
                log("VK", f"📌 @{page} — последний пост: #{post_id}. Жду новые...")
    save_state_dict("vk_last_posts.txt", state)
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
                    save_state_dict("vk_last_posts.txt", state)
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
    last_id = load_state("last_rutube_id.txt")
    if not last_id:
        videos = get_rutube_videos()
        if videos:
            vid_id = str(videos[0].get("id") or videos[0].get("uuid") or "")
            if vid_id:
                save_state("last_rutube_id.txt", vid_id)
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
                    log("Rutube", f"🆕 {video.get('title','')[:50]} | {vid_url}")
                    create_jap_order("Rutube", vid_url, RUTUBE_SERVICE, RUTUBE_QTY_MIN, RUTUBE_QTY_MAX)
                    time.sleep(2)
                save_state("last_rutube_id.txt", latest_id)
                last_id = latest_id
            else:
                log("Rutube", f"🔍 Нет новых видео (последнее: #{last_id})")
        except Exception as e:
            log("Rutube", f"❌ Ошибка: {e}")

# ══════════════════════════════════════
#  FACEBOOK (мобильная версия)
# ══════════════════════════════════════
def get_fb_post():
    try:
        resp = requests.get(FB_PAGE_URL, headers=FB_HEADERS, timeout=15)
        log("Facebook", f"📥 Status: {resp.status_code}")
        if resp.status_code != 200:
            log("Facebook", f"❌ HTML: {resp.content[:200]}")
            return None, None
        html = resp.content.decode("utf-8", errors="ignore")

        # pfbid pattern
        matches = re.findall(r'pfbid[A-Za-z0-9]+', html)
        if matches:
            latest = matches[0]
            post_url = f"https://www.facebook.com/permalink.php?story_fbid={latest}&id=100081997113052"
            log("Facebook", f"✅ Пост (pfbid): {post_url}")
            return latest, post_url

        # story_fbid patterns
        all_ids = []
        for pattern in [r'"story_fbid":"(\d+)"', r'story_fbid=(\d+)', r'"top_level_post_id":"(\d+)"']:
            all_ids += re.findall(pattern, html)
        numeric = [x for x in set(all_ids) if x.isdigit() and len(x) > 10]
        if numeric:
            latest_id = max(numeric, key=lambda x: int(x))
            post_url = f"https://www.facebook.com/permalink.php?story_fbid={latest_id}&id=100081997113052"
            log("Facebook", f"✅ Пост: {post_url}")
            return latest_id, post_url

        log("Facebook", f"⚠️  Посты не найдены | HTML: {html[:300]}")
        return None, None
    except Exception as e:
        log("Facebook", f"❌ Ошибка: {e}")
        return None, None

def facebook_bot():
    log("Facebook", f"📘 Запущен (мобильная) | Услуга: {FB_SERVICE} | {FB_QTY_MIN}-{FB_QTY_MAX}")
    last_id = load_state("last_fb_post_id.txt")
    if not last_id:
        latest_id, _ = get_fb_post()
        if latest_id:
            save_state("last_fb_post_id.txt", latest_id)
            last_id = latest_id
            log("Facebook", f"📌 Последний пост: #{latest_id}. Жду новые...")
    while True:
        time.sleep(FB_CHECK_INTERVAL)
        try:
            latest_id, post_url = get_fb_post()
            if latest_id and latest_id != last_id:
                log("Facebook", f"🆕 Новый пост: {post_url}")
                create_jap_order("Facebook", post_url, FB_SERVICE, FB_QTY_MIN, FB_QTY_MAX)
                save_state("last_fb_post_id.txt", latest_id)
                last_id = latest_id
            else:
                log("Facebook", f"🔍 Нет новых постов (последний: #{last_id})")
        except Exception as e:
            log("Facebook", f"❌ Ошибка: {e}")

# ══════════════════════════════════════
#  MAIN
# ══════════════════════════════════════
def main():
    log("MAIN", "🚀 VK + Rutube + Facebook бот запущен!")
    check_balance()

    threads = [
        threading.Thread(target=vk_bot, name="VK", daemon=True),
        threading.Thread(target=rutube_bot, name="Rutube", daemon=True),
        threading.Thread(target=facebook_bot, name="Facebook", daemon=True),
    ]

    for t in threads:
        t.start()
        time.sleep(3)

    log("MAIN", "✅ Все 3 бота запущены! VK + Rutube + Facebook")

    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
