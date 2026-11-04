"""Публикация рейтингов из банка в Threads и Instagram.

python scripts/publish.py threads     пост в Threads (картинка + текст)
python scripts/publish.py instagram   пост в Instagram (картинка + подпись)
--dry-run                             показать, что вышло бы, без публикации

Токены берутся из переменных окружения THREADS_TOKEN и IG_TOKEN
(секреты GitHub). Состояние: bank/state_<площадка>.json.
"""
import datetime as dt
import hashlib
import json
import os
import sys
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "bank")
REPO = os.environ.get("GITHUB_REPOSITORY", "aleksandr-pm/osnova-finance-data")
SHA = os.environ.get("GITHUB_SHA", "main")[:12]
REPEAT_DAYS = 90
THREADS = "https://graph.threads.net/v1.0"
IG = "https://graph.facebook.com/v25.0"
BUSINESS_ID = "167573054295268"  # бизнес-портфолио «Александр Максименко»
IG_USERNAME = "osnova_finance"

QUESTIONS = [
    "Кто удивил в этом списке?",
    "Кого не хватает в топе, по-вашему?",
    "Кто поднимется выше через 5 лет?",
]


def log(*a):
    print(*a, flush=True)


def now():
    return dt.datetime.now(dt.timezone.utc)


def load_state(platform):
    p = os.path.join(BANK, f"state_{platform}.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"posted": []}


def save_state(platform, st):
    with open(os.path.join(BANK, f"state_{platform}.json"), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def pick(rankings, st):
    """Следующий рейтинг: не публиковался 90 дней, блок не как у прошлого поста,
    в сутки не больше 2 из одного блока, если есть выбор."""
    cutoff = now() - dt.timedelta(days=REPEAT_DAYS)
    recent = {p["id"] for p in st["posted"] if dt.datetime.fromisoformat(p["at"]) > cutoff}
    pool = [r for r in rankings if r["id"] not in recent]
    if not pool:
        return None
    last_block = st["posted"][-1]["block"] if st["posted"] else None
    last_type = st["posted"][-1].get("type", "bars") if st["posted"] else None
    day_ago = now() - dt.timedelta(hours=24)
    per_block = {}
    for p in st["posted"]:
        if dt.datetime.fromisoformat(p["at"]) > day_ago:
            per_block[p["block"]] = per_block.get(p["block"], 0) + 1

    def score(r):
        h = int(hashlib.md5(r["id"].encode()).hexdigest(), 16) % 1000
        return (r["block"] == last_block, r.get("type", "bars") == last_type,
                per_block.get(r["block"], 0) >= 2, per_block.get(r["block"], 0), h)

    return min(pool, key=score)


def image_url(r):
    jpg = r["card"].replace(".png", ".jpg")
    return f"https://raw.githubusercontent.com/{REPO}/{SHA}/bank/{jpg}"


def ig_caption(r, i):
    return "\n".join([
        r["hook_text"] + ".",
        f"{r['title']} · {r['year']}. Источник: {r['source']}.",
        "",
        QUESTIONS[i % len(QUESTIONS)],
        "Рынки и данные 24/7 в Telegram @osnovafin, ссылка в профиле.",
        "Не является инвестиционной рекомендацией.",
    ])


def check(resp, what):
    try:
        js = resp.json()
    except Exception:  # noqa: BLE001
        js = {"raw": resp.text[:300]}
    if resp.status_code != 200 or "error" in js:
        err = js.get("error", js)
        raise RuntimeError(f"{what}: HTTP {resp.status_code} {json.dumps(err, ensure_ascii=False)[:400]}")
    return js


def post_threads(token, text, img):
    """img=None: текстовый пост."""
    data = {"media_type": "TEXT", "text": text, "access_token": token}
    if img:
        data.update(media_type="IMAGE", image_url=img)
    c = check(requests.post(f"{THREADS}/me/threads", data=data, timeout=60), "Threads контейнер")
    time.sleep(35)
    p = check(requests.post(f"{THREADS}/me/threads_publish", data={
        "creation_id": c["id"], "access_token": token,
    }, timeout=60), "Threads публикация")
    return p["id"]


def ig_user_id(token):
    """ID аккаунта Instagram: из IG_USER_ID или через бизнес-портфолио."""
    if os.environ.get("IG_USER_ID"):
        return os.environ["IG_USER_ID"]
    for edge in ("owned_instagram_accounts", "instagram_accounts"):
        r = requests.get(f"{IG}/{BUSINESS_ID}/{edge}", params={
            "fields": "id,username", "access_token": token}, timeout=30)
        if r.status_code == 200:
            for a in r.json().get("data", []):
                if a.get("username") == IG_USERNAME:
                    return a["id"]
    r = check(requests.get(f"{IG}/me/accounts", params={
        "fields": "instagram_business_account{id,username}", "access_token": token}, timeout=30),
        "Instagram аккаунт")
    for p in r.get("data", []):
        a = p.get("instagram_business_account") or {}
        if a.get("username") == IG_USERNAME:
            return a["id"]
    raise RuntimeError("Instagram: аккаунт osnova_finance не найден для этого ключа")


def post_instagram(token, caption, img):
    uid = ig_user_id(token)
    c = check(requests.post(f"{IG}/{uid}/media", data={
        "image_url": img, "caption": caption, "access_token": token,
    }, timeout=60), "Instagram контейнер")
    for _ in range(12):
        time.sleep(5)
        s = check(requests.get(f"{IG}/{c['id']}", params={
            "fields": "status_code", "access_token": token}, timeout=30), "Instagram статус")
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram: контейнер с ошибкой {s}")
    p = check(requests.post(f"{IG}/{uid}/media_publish", data={
        "creation_id": c["id"], "access_token": token,
    }, timeout=60), "Instagram публикация")
    return p["id"]


def main():
    platform = sys.argv[1]
    dry = "--dry-run" in sys.argv
    with open(os.path.join(BANK, "rankings.json"), encoding="utf-8") as f:
        rankings = json.load(f)
    st = load_state(platform)
    r = pick(rankings, st)
    if not r:
        log("Банк исчерпан: все рейтинги публиковались за последние 90 дней")
        return 1
    img = image_url(r)
    n = len(st["posted"])
    text = r["threads"] if platform == "threads" else ig_caption(r, n)
    log(f"{platform}: {r['id']} ({r['block']})\n{img}\n---\n{text}\n---")
    token = os.environ.get("THREADS_TOKEN" if platform == "threads" else "IG_TOKEN", "")
    if dry or not token:
        log("Публикации нет: " + ("dry-run" if dry else "токен не задан"))
        return 0
    if platform == "threads":
        with_img = n % 3 == 0  # картинка в каждом третьем посте, остальные текстом
        log("Threads: " + ("с картинкой" if with_img else "текстом"))
        pid = post_threads(token, text, img if with_img else None)
    else:
        pid = post_instagram(token, text, img)
    st["posted"].append({"id": r["id"], "block": r["block"], "type": r.get("type", "bars"),
                         "at": now().isoformat(), "post": pid})
    save_state(platform, st)
    left = len([x for x in rankings if x["id"] not in {p["id"] for p in st["posted"]}])
    log(f"Опубликовано: {pid}. Осталось новых рейтингов: {left}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
