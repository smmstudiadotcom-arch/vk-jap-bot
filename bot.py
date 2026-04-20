import requests
import random
import time
import os
from datetime import datetime

JAP_API_KEY    = "ec2fb6c8f5a4ea7ba6cf532e87a09895"
JAP_API_URL    = "https://justanotherpanel.com/api/v2"
JAP_SERVICE    = 3756
QUANTITY_MIN   = 20
QUANTITY_MAX   = 35

VK_TOKEN       = "vk1.a.3l-M4WzpxupxkQ1LO5QEJKxhXtlyzgP6m9f7UnUXmtmOCGTp8Pj26J5cdb_hPqB8-wSrFsRTgUVIwcwZQK6iL-cx8p23NQnt65AcdJ1yWNnqj21ZKOWnSrPyKiUudvEjdCQjzBNoDSF2vq6AjPKbPtvP-kOGAo28Uhiet66MoYaXUU9UktA3zGcZfrf7V0nKu7eUkOqnHAU9a-GcfGIW0Q"
VK_API_URL     = "https://api.vk.com/method"
VK_VERSION     = "5.131"
VK_PAGES       = ["biznes___13"]
CHECK_INTERVAL = 60
STATE_FILE     = "vk_last_posts.txt"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = {}
            for line in f.read().strip().split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    data[k] = v
            return data
    return {}

def save_state(data):
    with open(STATE_FILE, "w") as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")

def get_latest_post(page_slug):
    try:
        resp = requests.get(f"{VK_API_URL}/wall.get", params={
            "domain": page_slug,
            "count": 5,
            "filter": "owner",
            "access_token": VK_TOKEN,
            "v": VK_VERSION,
        }, timeout=15)
        log(f"📥 VK @{page_slug}: {resp.status_code}")
        data = resp.json()
        if "error" in data:
            log(f"❌ VK API ошибка: {data['error']}")
            return None, None
        items = data.get("response", {}).get("items", [])
        if not items:
            log(f"⚠️  Посты не найдены для @{page_slug}")
            return None, None
        latest = items[0]
        owner_id = latest["owner_id"]
        post_id = latest["id"]
        post_url = f"https://vk.com/wall{owner_id}_{post_id}"
        log(f"✅ Последний пост @{page_slug}: {post_url}")
        return f"{owner_id}_{post_id}", post_url
    except Exception as e:
        log(f"❌ Ошибка VK @{page_slug}: {e}")
        return None, None

def create_jap_order(post_url):
    quantity = random.randint(QUANTITY_MIN, QUANTITY_MAX)
    payload = {
        "key":      JAP_API_KEY,
        "action":   "add",
        "service":  JAP_SERVICE,
        "link":     post_url,
        "quantity": quantity,
    }
    try:
        log(f"📤 Заказ: service={JAP_SERVICE}, qty={quantity}, link={post_url}")
        resp = requests.post(JAP_API_URL, data=payload, timeout=15)
        log(f"📥 JAP: {resp.status_code} | {repr(resp.text[:200])}")
        if not resp.text.strip():
            log("❌ Пустой ответ JAP")
            return
        data = resp.json()
        if "order" in data:
            log(f"✅ Заказ создан! ID: {data['order']} | Услуга: {JAP_SERVICE} | Кол-во: {quantity}")
        elif "error" in data:
            log(f"❌ Ошибка JAP: {data['error']}")
    except Exception as e:
        log(f"❌ Ошибка заказа: {e}")

def check_balance():
    try:
        resp = requests.post(JAP_API_URL, data={"key": JAP_API_KEY, "action": "balance"}, timeout=10)
        if resp.text.strip():
            data = resp.json()
            if "balance" in data:
                log(f"💰 Баланс JAP: ${data['balance']} {data.get('currency','')}")
    except Exception as e:
        log(f"❌ Ошибка баланса: {e}")

def main():
    log("🚀 VK бот запущен!")
    log(f"📋 Страницы: {VK_PAGES}")
    log(f"⚙️  Услуга: {JAP_SERVICE} | Кол-во: {QUANTITY_MIN}-{QUANTITY_MAX}")
    check_balance()
    state = load_state()
    for page in VK_PAGES:
        if page not in state:
            post_id, _ = get_latest_post(page)
            if post_id:
                state[page] = post_id
                log(f"📌 @{page} — последний пост: #{post_id}. Жду новые...")
    save_state(state)
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            for page in VK_PAGES:
                latest_id, post_url = get_latest_post(page)
                if not latest_id:
                    continue
                last_id = state.get(page)
                if latest_id != last_id:
                    log(f"🆕 Новый пост @{page}: {post_url}")
                    create_jap_order(post_url)
                    state[page] = latest_id
                    save_state(state)
                else:
                    log(f"🔍 @{page} — нет новых постов (последний: #{last_id})")
        except Exception as e:
            log(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
