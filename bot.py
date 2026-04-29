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
VK_QTY_MIN        = 80
VK_QTY_MAX        = 110
VK_PAGES          = [
    "biznes___13",
    "public218647080",
    "partner_bf_anna_maria",
    "meropriyatiya_bf_anna_maria",
    "fond_anna_maria"
]
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
#  TWITTER
# ══════════════════════════════════════
TW_USERNAME    = "gowithRussia"
TW_SERVICE     = 1334
TW_QTY_MIN     = 800
TW_QTY_MAX     = 1500
TW_CHECK_INTERVAL = 60

TW_AUTH_TOKEN = "2dbd598ed7dac67ddcf07976325dbb708dd9e6e2"
TW_CT0        = "6b8b1822c5336aefde2892739247be0e645995eaa5f47fd6a99d109eb76596096ea8d667f91cc1c0021cd3afb84668920f8a01c06bd449302c70631c72a184816a16d96d8852c0d4b03c1aa75f4de043"

TW_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "Cookie": f"auth_token={TW_AUTH_TOKEN}; ct0={TW_CT0}",
    "X-Csrf-Token": TW_CT0,
    "X-Twitter-Auth-Type": "OAuth2Session",
    "X-Twitter-Active-User": "yes",
    "X-Twitter-Client-Language": "en",
    "Content-Type": "application/json",
    "Referer": "https://x.com/",
}

# ══════════════════════════════════════
#  УТИЛИТЫ
# ══════════════════════════════════════
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
#  TWITTER
# ══════════════════════════════════════
def get_twitter_user_id():
    url = "https://api.x.com/graphql/G3KGOASz96M-Qu0nwmGXNg/UserByScreenName"
    params = {
        "variables": f'{{"screen_name":"{TW_USERNAME}","withSafetyModeUserFields":true}}',
        "features": '{"hidden_profile_subscriptions_enabled":true,"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_is_identity_verified_enabled":true,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"responsive_web_twitter_article_notes_tab_enabled":true,"subscriptions_feature_can_gift_premium":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}',
    }
    resp = requests.get(url, headers=TW_HEADERS, params=params, timeout=15)
    log("Twitter", f"📥 UserByScreenName: {resp.status_code}")
    if resp.status_code != 200:
        log("Twitter", f"⚠️  Ошибка user ID: {resp.text[:200]}")
        return None
    data = resp.json()
    user_id = data["data"]["user"]["result"]["rest_id"]
    log("Twitter", f"✅ User ID: {user_id}")
    return user_id

def get_latest_tweet(user_id):
    url = "https://api.x.com/graphql/E3opETHurmVJflFsUBVuUQ/UserTweets"
    params = {
        "variables": f'{{"userId":"{user_id}","count":5,"includePromotedContent":true,"withQuickPromoteEligibilityTweetFields":true,"withVoice":true,"withV2Timeline":true}}',
        "features": '{"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}',
    }
    resp = requests.get(url, headers=TW_HEADERS, params=params, timeout=15)
    log("Twitter", f"📥 UserTweets: {resp.status_code}")
    if resp.status_code != 200:
        log("Twitter", f"⚠️  Ошибка твитов: {resp.text[:200]}")
        return None, None
    data = resp.json()
    entries = data["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"]
    tweet_ids = []
    for instruction in entries:
        if instruction.get("type") == "TimelineAddEntries":
            for entry in instruction.get("entries", []):
                entry_id = entry.get("entryId", "")
                if entry_id.startswith("tweet-"):
                    tid = entry_id.replace("tweet-", "")
                    tweet_ids.append(tid)
    if not tweet_ids:
        log("Twitter", "⚠️  Твиты не найдены")
        return None, None
    latest_id = max(tweet_ids, key=lambda x: int(x))
    tweet_url = f"https://x.com/{TW_USERNAME}/status/{latest_id}"
    log("Twitter", f"✅ Последний твит: {tweet_url}")
    return latest_id, tweet_url

def twitter_bot():
    log("Twitter", f"🐦 Запущен | @{TW_USERNAME} | Услуга: {TW_SERVICE} | {TW_QTY_MIN}-{TW_QTY_MAX}")

    user_id = None
    while not user_id:
        try:
            user_id = get_twitter_user_id()
        except Exception as e:
            log("Twitter", f"❌ Ошибка получения user ID: {e}")
        if not user_id:
            log("Twitter", "⏳ Повтор через 30 сек...")
            time.sleep(30)

    last_id = load_state("last_tweet_id.txt")
    if not last_id:
        try:
            latest_id, _ = get_latest_tweet(user_id)
            if latest_id:
                save_state("last_tweet_id.txt", latest_id)
                last_id = latest_id
                log("Twitter", f"📌 Последний твит: #{latest_id}. Жду новые...")
        except Exception as e:
            log("Twitter", f"❌ Ошибка: {e}")

    while True:
        time.sleep(TW_CHECK_INTERVAL)
        try:
            latest_id, tweet_url = get_latest_tweet(user_id)
            if latest_id and last_id and int(latest_id) > int(last_id):
                log("Twitter", f"🆕 Новый твит: {tweet_url}")
                create_jap_order("Twitter", tweet_url, TW_SERVICE, TW_QTY_MIN, TW_QTY_MAX)
                save_state("last_tweet_id.txt", latest_id)
                last_id = latest_id
            else:
                log("Twitter", f"🔍 Нет новых твитов (последний: #{last_id})")
        except Exception as e:
            log("Twitter", f"❌ Ошибка: {e}")

# ══════════════════════════════════════
#  MAIN
# ══════════════════════════════════════
def main():
    log("MAIN", "🚀 VK + Rutube + Twitter бот запущен!")
    check_balance()

    threads = [
        threading.Thread(target=vk_bot,      name="VK",      daemon=True),
        threading.Thread(target=rutube_bot,   name="Rutube",  daemon=True),
        threading.Thread(target=twitter_bot,  name="Twitter", daemon=True),
    ]

    for t in threads:
        t.start()
        time.sleep(3)

    log("MAIN", "✅ Все 3 бота запущены! VK + Rutube + Twitter")

    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
