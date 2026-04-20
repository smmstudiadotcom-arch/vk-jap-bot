import requests
import random
import time
import os
import threading
import xml.etree.ElementTree as ET
from datetime import datetime

# ══════════════════════════════════════
#  JAP
# ══════════════════════════════════════
JAP_API_KEY = "ec2fb6c8f5a4ea7ba6cf532e87a09895"
JAP_API_URL = "https://justanotherpanel.com/api/v2"

# ══════════════════════════════════════
#  FACEBOOK (RSS)
# ══════════════════════════════════════
FB_RSS_URL        = "https://fetchrss.com/feed/1wEkeiByC1ti1wEkddBg9EOA.rss"
FB_PAGE_URL       = "https://www.facebook.com/profile.php?id=100081997113052"
FB_SERVICE        = 9604
FB_QTY_MIN        = 500
FB_QTY_MAX        = 1000
FB_CHECK_INTERVAL = 43200  # 12 часов

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
#  FACEBOOK
# ══════════════════════════════════════
def get_fb_posts():
    try:
        log("Facebook", "📤 Читаю RSS ленту...")
        resp = requests.get(FB_RSS_URL, timeout=15)
        log("Facebook", f"📥 RSS: {resp.status_code}")
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.content)
        items = []
        for item in root.findall(".//item"):
            guid = item.findtext("guid") or ""
            link = item.findtext("link") or ""
            items.append({"postId": guid, "url": link})
        log("Facebook", f"📊 Найдено постов: {len(items)}")
        return items
    except Exception as e:
        log("Facebook", f"❌ Ошибка: {e}")
        return []

def facebook_bot():
    log("Facebook", f"📘 Запущен | Услуга: {FB_SERVICE} | {FB_QTY_MIN}-{FB_QTY_MAX} | Проверка каждые 12ч")
    last_id = load_state("last_fb_post_id.txt")
    if not last_id:
        posts = get_fb_posts()
        if posts:
            last_id = str(posts[0].get("postId") or "")
            if last_id:
                save_state("last_fb_post_id.txt", last_id)
                log("Facebook", f"📌 Последний пост: #{last_id}. Жду новые...")
    while True:
        time.sleep(FB_CHECK_INTERVAL)
        try:
            posts = get_fb_posts()
            if not posts:
                continue
            new_posts = []
            for post in posts:
                pid = str(post.get("postId") or "")
                if pid and pid != last_id:
                    new_posts.append(post)
                else:
                    break
            if new_posts:
                log("Facebook", f"🆕 Новых постов: {len(new_posts)}")
                latest_id = str(posts[0].get("postId") or "")
                for post in new_posts:
                    purl = post.get("url") or FB_PAGE_URL
                    log("Facebook", f"🆕 Пост: {purl}")
                    create_jap_order("Facebook", purl, FB_SERVICE, FB_QTY_MIN, FB_QTY_MAX)
                    time.sleep(2)
                save_state("last_fb_post_id.txt", latest_id)
                last_id = latest_id
            else:
                log("Facebook", f"🔍 Нет новых постов (последний: #{last_id})")
        except Exception as e:
            log("Facebook", f"❌ Ошибка: {e}")

# ══════════════════════════════════════
#  VKONTAKTE
# ══════════════════════════════════════
def get_vk_post(page_slug):
    try:
        resp = requests.get(f"{VK_API_URL}/wall.get", params={
            "domain": page_slug, "count": 5, "filter": "owner",
            "access_token": VK_TOKEN, "v": VK_VERSION,
        }, timeout=15)
        data = resp.json()
        if "error" in data:
            log("VK", f"❌ API ошибка: {data['error']}")
            return None, None
        items = data.get("response", {}).get("items", [])
        if not items:
            return None, None
        latest = items[0]
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
#  MAIN
# ══════════════════════════════════════
def main():
    log("MAIN", "🚀 Facebook + VK бот запущен!")
    check_balance()

    threads = [
        threading.Thread(target=facebook_bot, name="Facebook", daemon=True),
        threading.Thread(target=vk_bot, name="VK", daemon=True),
    ]

    for t in threads:
        t.start()
        time.sleep(3)

    log("MAIN", "✅ Оба бота запущены! Facebook + VK")

    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
