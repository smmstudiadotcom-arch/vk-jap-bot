import requests
import random
import time
import os
import re
import json
import threading
from datetime import datetime, date
from curl_cffi import requests as curl_requests

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
VK_CHECK_INTERVAL = 60

# Группа 1: фонд (лайки 80-110)
VK_GROUP1_PAGES   = [
    "public218647080",
    "partner_bf_anna_maria",
    "meropriyatiya_bf_anna_maria",
    "fond_anna_maria"
]
VK_GROUP1_QTY_MIN = 80
VK_GROUP1_QTY_MAX = 110

# Группа 2: саморазвитие (лайки 50-120)
VK_GROUP2_PAGES   = [
    "pro_samorasvitie",
    "vera_lartseva"
]
VK_GROUP2_QTY_MIN = 50
VK_GROUP2_QTY_MAX = 120

# Группа 3: patronsanme (лайки 50-100)
VK_GROUP3_PAGES   = ["patronsanme"]
VK_GROUP3_QTY_MIN = 50
VK_GROUP3_QTY_MAX = 100

# Группа 4: временные (лайки 40-69, истекает 3 июня 2026)
from datetime import date as _date_cls
VK_GROUP4_PAGES   = [
    {"page": "vica.nikiforova", "expires": "2026-06-03"},
]
VK_GROUP4_QTY_MIN = 40
VK_GROUP4_QTY_MAX = 69

def vk_group4_active_pages():
    """Возвращает только не истёкшие страницы Группы 4"""
    today = _date_cls.today().isoformat()
    return [p["page"] for p in VK_GROUP4_PAGES if p["expires"] >= today]

# ══════════════════════════════════════
#  RUTUBE
# ══════════════════════════════════════
RUTUBE_CHANNEL_ID     = "56184868"
RUTUBE_SERVICE        = 10303
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
#  YOUTUBE (только стримы)
# ══════════════════════════════════════
YT_CHANNEL_HANDLE  = "ArmeniaTodayTV"
YT_CHECK_INTERVAL  = 60

# Услуга 1: просмотры
YT_SERVICE_1 = 1532
YT_QTY_MIN_1 = 500
YT_QTY_MAX_1 = 1000

# Услуга 2
YT_SERVICE_2 = 2085
YT_QTY_MIN_2 = 10
YT_QTY_MAX_2 = 25

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
    log("VK", f"📱 Запущен | Группа1 (80-110): {VK_GROUP1_PAGES}")
    log("VK", f"📱 Группа2 (50-120): {VK_GROUP2_PAGES}")
    log("VK", f"📱 Группа3 (50-100): {VK_GROUP3_PAGES}")
    log("VK", f"📱 Группа4 врем. (40-69): {[(p['page'], p['expires']) for p in VK_GROUP4_PAGES]}")
    state = load_state_dict("vk_last_posts.txt")
    
    # Инициализация для всех страниц
    initial_pages = VK_GROUP1_PAGES + VK_GROUP2_PAGES + VK_GROUP3_PAGES + vk_group4_active_pages()
    for page in initial_pages:
        if page not in state:
            post_id, _ = get_vk_post(page)
            if post_id:
                state[page] = post_id
                log("VK", f"📌 @{page} — последний пост: #{post_id}. Жду новые...")
    save_state_dict("vk_last_posts.txt", state)
    
    while True:
        time.sleep(VK_CHECK_INTERVAL)
        try:
            # Группа 4 может меняться по истечении дат
            group4_active = vk_group4_active_pages()
            all_pages = VK_GROUP1_PAGES + VK_GROUP2_PAGES + VK_GROUP3_PAGES + group4_active
            
            for page in all_pages:
                latest_id, post_url = get_vk_post(page)
                if not latest_id:
                    continue
                last_id = state.get(page)
                if latest_id != last_id:
                    log("VK", f"🆕 Новый пост @{page}: {post_url}")
                    
                    # Определяем диапазон для страницы
                    if page in VK_GROUP1_PAGES:
                        qty_min, qty_max = VK_GROUP1_QTY_MIN, VK_GROUP1_QTY_MAX
                    elif page in VK_GROUP2_PAGES:
                        qty_min, qty_max = VK_GROUP2_QTY_MIN, VK_GROUP2_QTY_MAX
                    elif page in VK_GROUP3_PAGES:
                        qty_min, qty_max = VK_GROUP3_QTY_MIN, VK_GROUP3_QTY_MAX
                    else:  # Группа 4 (временные)
                        qty_min, qty_max = VK_GROUP4_QTY_MIN, VK_GROUP4_QTY_MAX
                    
                    create_jap_order("VK", post_url, VK_SERVICE, qty_min, qty_max)
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
#  YOUTUBE (только стримы)
# ══════════════════════════════════════
def yt_get_channel_id():
    """Получить channel_id из @handle"""
    try:
        url = f"https://www.youtube.com/@{YT_CHANNEL_HANDLE}"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            log("YouTube", f"❌ Не могу открыть канал: {resp.status_code}")
            return None
        match = re.search(r'"channelId":"(UC[A-Za-z0-9_-]{22})"', resp.text)
        if not match:
            match = re.search(r'/channel/(UC[A-Za-z0-9_-]{22})', resp.text)
        if match:
            channel_id = match.group(1)
            log("YouTube", f"✅ Channel ID: {channel_id}")
            return channel_id
        log("YouTube", f"❌ Channel ID не найден")
        return None
    except Exception as e:
        log("YouTube", f"❌ Ошибка: {e}")
        return None

def yt_get_streams(channel_id):
    """Получить последние стримы — RSS + парсинг страницы"""
    try:
        suffix = channel_id[2:]
        
        # Попытка 1-3: RSS playlists
        playlist_variants = [
            ("UULV" + suffix, "Live streams"),
            ("UULF" + suffix, "Long form videos"),
            ("UU"   + suffix, "All uploads"),
        ]
        
        for playlist_id, label in playlist_variants:
            url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                log("YouTube", f"📥 [{label}] {resp.status_code} | {len(resp.text)} симв.")
                if resp.status_code == 200:
                    streams = []
                    for m in re.finditer(r'<yt:videoId>([A-Za-z0-9_-]{11})</yt:videoId>', resp.text):
                        vid = m.group(1)
                        streams.append({"id": vid, "url": f"https://www.youtube.com/watch?v={vid}"})
                    if streams:
                        log("YouTube", f"📊 [{label}] Найдено: {len(streams)}")
                        return streams
            except Exception as e:
                log("YouTube", f"⚠️  [{label}] {e}")
        
        # Fallback: парсим страницу /streams
        log("YouTube", f"🔄 RSS не работает, парсю /streams...")
        url = f"https://www.youtube.com/@{YT_CHANNEL_HANDLE}/streams"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=20)
        log("YouTube", f"📥 /streams: {resp.status_code} | {len(resp.text)} симв.")
        
        if resp.status_code == 200:
            video_ids = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', resp.text)
            seen = set()
            unique_ids = []
            for vid in video_ids:
                if vid not in seen:
                    seen.add(vid)
                    unique_ids.append(vid)
            streams = [{"id": vid, "url": f"https://www.youtube.com/watch?v={vid}"} for vid in unique_ids[:20]]
            log("YouTube", f"📊 [/streams] Найдено: {len(streams)}")
            return streams
        
        return []
    except Exception as e:
        log("YouTube", f"❌ Ошибка: {e}")
        return []

def youtube_bot():
    log("YouTube", f"📺 Запущен | @{YT_CHANNEL_HANDLE}")
    log("YouTube", f"   Услуга 1: {YT_SERVICE_1} | {YT_QTY_MIN_1}-{YT_QTY_MAX_1}")
    log("YouTube", f"   Услуга 2: {YT_SERVICE_2} | {YT_QTY_MIN_2}-{YT_QTY_MAX_2}")
    
    # channel_id
    channel_id = None
    while not channel_id:
        channel_id = yt_get_channel_id()
        if not channel_id:
            log("YouTube", "⏳ Повтор через 60 сек...")
            time.sleep(60)
    
    # Загружаем обработанные стримы
    processed_file = "yt_processed_streams.txt"
    if os.path.exists(processed_file):
        with open(processed_file, "r") as f:
            processed = set(line.strip() for line in f if line.strip())
    else:
        processed = set()
    log("YouTube", f"📋 Обработанных стримов: {len(processed)}")
    
    # Первый запуск
    if not processed:
        streams = yt_get_streams(channel_id)
        if streams:
            for s in streams:
                processed.add(s["id"])
            with open(processed_file, "w") as f:
                for vid in processed:
                    f.write(f"{vid}\n")
            log("YouTube", f"📌 Запомнено {len(streams)} стримов. Жду новые...")
    
    while True:
        time.sleep(YT_CHECK_INTERVAL)
        try:
            streams = yt_get_streams(channel_id)
            if not streams:
                continue
            
            new_streams = [s for s in streams if s["id"] not in processed]
            
            if new_streams:
                log("YouTube", f"🆕 Новых стримов: {len(new_streams)}")
                for stream in new_streams:
                    log("YouTube", f"🆕 {stream['url']}")
                    # Заказ 1: просмотры
                    create_jap_order("YouTube", stream["url"], YT_SERVICE_1, YT_QTY_MIN_1, YT_QTY_MAX_1)
                    time.sleep(2)
                    # Заказ 2
                    create_jap_order("YouTube", stream["url"], YT_SERVICE_2, YT_QTY_MIN_2, YT_QTY_MAX_2)
                    processed.add(stream["id"])
                    with open(processed_file, "w") as f:
                        for vid in processed:
                            f.write(f"{vid}\n")
                    time.sleep(2)
            else:
                log("YouTube", f"🔍 Нет новых стримов")
        except Exception as e:
            log("YouTube", f"❌ Ошибка: {e}")

# ══════════════════════════════════════
#  FACEBOOK
# ══════════════════════════════════════
FB_PAGES = [
    {
        "name":      "National-Centre-Russia",
        "page_id":   "100081997113052",
        "url":       "https://www.facebook.com/profile.php?id=100081997113052&sk=reels_tab",
        "service":   9604,
        "qty_min":   500,
        "qty_max":   1000,
        "all_posts": False,  # только Reels
    },
    {
        "name":      "kinshik",
        "page_id":   "kinshik",
        "url":       "https://www.facebook.com/kinshik",
        "service":   7654,
        "qty_min":   30,
        "qty_max":   55,
        "all_posts": True,  # все посты
    },
]

FB_CHECK_INTERVAL = 3600  # каждый час
FB_DAILY_LIMIT    = 10    # макс заказов в день на страницу

FB_C_USER = os.environ.get("FB_C_USER", "61553351803414")
FB_XS     = os.environ.get("FB_XS",     "23%3AUcW9QDH7Lw4OMA%3A2%3A1777366320%3A-1%3A-1%3A%3AAcxV4doD641eN1HEAQNfnkX0cE357pxRh9ixF-wCuA")
FB_DATR   = os.environ.get("FB_DATR",   "gvGqaR00HB8BBQCtWvA_ZrBw")
FB_FR     = os.environ.get("FB_FR",     "1BiHkrekV5y5wC9M4.AWcjA0M_D1BFpG4ArVdD9DEHJz1hf_Cp4e633bJFekyBL_WG64E.Bp8HUz..AAA.0.0.Bp8HUz.AWd2xaqh1GaCzn5odyasmAo3ovQ")
FB_SB     = os.environ.get("FB_SB",     "hfGqaZIWmBX2PQV9iqh9Tr1V")

FB_COOKIES_STR = f"c_user={FB_C_USER}; xs={FB_XS}; datr={FB_DATR}; fr={FB_FR}; sb={FB_SB}"

FB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": FB_COOKIES_STR,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Upgrade-Insecure-Requests": "1",
}

# State files для FB
FB_PROCESSED_FILE   = "fb_processed.json"
FB_DAILY_COUNT_FILE = "fb_daily_count.json"

def fb_load_processed():
    if os.path.exists(FB_PROCESSED_FILE):
        try:
            with open(FB_PROCESSED_FILE, "r") as f:
                data = json.load(f)
            return {k: set(v) for k, v in data.items()}
        except Exception:
            pass
    return {}

def fb_save_processed(data):
    with open(FB_PROCESSED_FILE, "w") as f:
        json.dump({k: list(v) for k, v in data.items()}, f)

def fb_load_daily_count():
    if os.path.exists(FB_DAILY_COUNT_FILE):
        try:
            with open(FB_DAILY_COUNT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def fb_save_daily_count(data):
    with open(FB_DAILY_COUNT_FILE, "w") as f:
        json.dump(data, f)

def fb_today_count(daily, page_name):
    today = date.today().isoformat()
    page_data = daily.get(page_name, {})
    if page_data.get("date") != today:
        return 0
    return page_data.get("count", 0)

def fb_increment_count(daily, page_name):
    today = date.today().isoformat()
    page_data = daily.get(page_name, {})
    if page_data.get("date") != today:
        daily[page_name] = {"date": today, "count": 1}
    else:
        daily[page_name]["count"] = page_data.get("count", 0) + 1
    fb_save_daily_count(daily)

def fb_fetch_posts(page_url, page_name, all_posts=False):
    try:
        log("FB", f"🔄 [{page_name}] GET {page_url}")
        resp = curl_requests.get(
            page_url,
            headers=FB_HEADERS,
            impersonate="chrome120",
            timeout=30,
            allow_redirects=True
        )
        log("FB", f"📥 [{page_name}] Status: {resp.status_code} | HTML: {len(resp.text)} символов")
        
        if resp.status_code != 200:
            log("FB", f"⚠️  [{page_name}] {resp.text[:200]}")
            return []
        
        html = resp.text
        html_clean = html.replace("\\\\/", "/").replace("\\/", "/")
        
        urls = set()
        
        if all_posts:
            # Только /posts/pfbid... — без дублей
            for match in re.finditer(r'/posts/(pfbid[A-Za-z0-9]{20,}|\d{10,})', html_clean):
                urls.add(f"https://www.facebook.com/{page_name}/posts/{match.group(1)}")
            log("FB", f"📊 [{page_name}] Найдено постов: {len(urls)}")
        else:
            # Только Reels
            patterns = [
                r'/reel/(\d{10,})',
                r'"video_id":"(\d{10,})"',
                r'/videos/(\d{10,})',
                r'watch/\?v=(\d{10,})',
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, html_clean):
                    urls.add(f"https://www.facebook.com/reel/{match.group(1)}")
            log("FB", f"🎬 [{page_name}] Найдено Reels: {len(urls)}")
        
        return list(urls)
    except Exception as e:
        log("FB", f"❌ [{page_name}] Ошибка: {e}")
        return []

def fb_process_page(page, processed, daily):
    name = page["name"]
    
    today_count = fb_today_count(daily, name)
    if today_count >= FB_DAILY_LIMIT:
        log("FB", f"⏸  [{name}] Дневной лимит ({today_count}/{FB_DAILY_LIMIT})")
        return
    
    posts = fb_fetch_posts(page["url"], name, page.get("all_posts", False))
    if not posts:
        return
    
    page_processed = processed.get(name, set())
    
    if not page_processed:
        page_processed.update(posts)
        processed[name] = page_processed
        fb_save_processed(processed)
        log("FB", f"📌 [{name}] Запомнено {len(posts)}. Жду новые...")
        return
    
    new_posts = [url for url in posts if url not in page_processed]
    
    if not new_posts:
        log("FB", f"🔍 [{name}] Нет новых")
        return
    
    log("FB", f"🆕 [{name}] Новых: {len(new_posts)}")
    
    for post_url in new_posts:
        today_count = fb_today_count(daily, name)
        if today_count >= FB_DAILY_LIMIT:
            log("FB", f"⏸  [{name}] Лимит достигнут ({today_count}/{FB_DAILY_LIMIT})")
            break
        
        log("FB", f"🆕 [{name}] {post_url} ({today_count + 1}/{FB_DAILY_LIMIT})")
        
        # Создаём заказ через JAP (используем существующую функцию)
        quantity = random.randint(page["qty_min"], page["qty_max"])
        payload = {"key": JAP_API_KEY, "action": "add", "service": page["service"], "link": post_url, "quantity": quantity}
        try:
            log("FB", f"📤 [{name}] Заказ: service={page['service']}, qty={quantity}")
            r = requests.post(JAP_API_URL, data=payload, timeout=15)
            log("FB", f"📥 JAP: {r.status_code} | {repr(r.text[:150])}")
            if r.text.strip():
                d = r.json()
                if "order" in d:
                    log("FB", f"✅ [{name}] Заказ! ID: {d['order']} | Кол-во: {quantity}")
                    page_processed.add(post_url)
                    fb_increment_count(daily, name)
                    time.sleep(2)
                elif "error" in d:
                    log("FB", f"❌ JAP ошибка: {d['error']}")
        except Exception as e:
            log("FB", f"❌ Ошибка заказа: {e}")
    
    processed[name] = page_processed
    fb_save_processed(processed)

def facebook_bot():
    log("FB", f"📘 Запущен | Страниц: {len(FB_PAGES)} | Лимит: {FB_DAILY_LIMIT}/день")
    for p in FB_PAGES:
        log("FB", f"   • {p['name']} | Услуга: {p['service']} | {p['qty_min']}-{p['qty_max']}")
    
    processed = fb_load_processed()
    daily     = fb_load_daily_count()
    
    # Первый запуск
    for page in FB_PAGES:
        if page["name"] not in processed:
            log("FB", f"📌 [{page['name']}] Первый запуск...")
            fb_process_page(page, processed, daily)
            time.sleep(5)
    
    while True:
        time.sleep(FB_CHECK_INTERVAL)
        try:
            for page in FB_PAGES:
                fb_process_page(page, processed, daily)
                time.sleep(5)
        except Exception as e:
            log("FB", f"❌ Ошибка: {e}")

# ══════════════════════════════════════
#  MAIN
# ══════════════════════════════════════
def main():
    log("MAIN", "🚀 VK + Rutube + Twitter + YouTube + Facebook бот запущен!")
    check_balance()

    threads = [
        threading.Thread(target=vk_bot,       name="VK",       daemon=True),
        threading.Thread(target=rutube_bot,    name="Rutube",   daemon=True),
        threading.Thread(target=twitter_bot,   name="Twitter",  daemon=True),
        threading.Thread(target=youtube_bot,   name="YouTube",  daemon=True),
        threading.Thread(target=facebook_bot,  name="Facebook", daemon=True),
    ]

    for t in threads:
        t.start()
        time.sleep(3)

    log("MAIN", "✅ Все 5 ботов запущены! VK + Rutube + Twitter + YouTube + Facebook")

    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()
