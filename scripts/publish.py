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


NEW_BLOCKS = {"companies", "billionaires"}


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
        # чередуем: рейтинги компаний и миллиардеров через пост со старыми рейтингами стран
        return ((r["block"] in NEW_BLOCKS) == (last_block in NEW_BLOCKS), r["block"] == last_block, r.get("type", "bars") == last_type,
                per_block.get(r["block"], 0) >= 2, per_block.get(r["block"], 0), h)

    return min(pool, key=score)


def raw(path):
    return f"https://raw.githubusercontent.com/{REPO}/{SHA}/bank/{path}"


def image_url(r):
    return raw(r["card"].replace(".png", ".jpg"))


def images(r):
    """Карусель: обложка на фото + график, если обложка есть; иначе только график."""
    out = [raw(r["cover"])] if r.get("cover") else []
    return out + [image_url(r)]


TAG_ITEM = {
    15: "пшеница", 56: "кукуруза", 27: "рис", 31: "рис", 44: "ячмень", 236: "соя",
    656: "кофе", 661: "какао", 667: "чай", 156: "сахар", 162: "сахар", 116: "картофель",
    515: "яблоки", 486: "бананы", 560: "виноград", 388: "томаты", 267: "подсолнечник",
    270: "рапс", 257: "пальмовоемасло", 261: "оливковоемасло", 564: "вино", 867: "говядина",
    1058: "курица", 882: "молоко", 1062: "яйца", 767: "хлопок", 572: "авокадо",
    490: "апельсины", 1182: "мёд", 403: "лук", 221: "миндаль", 225: "фундук",
    223: "фисташки", 268: "подсолнечноемасло", 1035: "свинина",
}
TAG_BLOCK = {
    "agro": ["сельскоехозяйство", "агро", "экспорт", "продовольствие"],
    "economy": ["экономика", "мироваяэкономика", "ввп", "макроэкономика"],
    "money": ["деньги", "капитал", "финансоваяграмотность", "мироваяэкономика"],
    "cis": ["снг", "экономикаснг", "казахстан", "узбекистан"],
    "companies": ["акции", "компании", "капитализация", "фондовыйрынок"],
    "billionaires": ["миллиардеры", "forbes", "богатство", "бизнес"],
}
TAG_BASE = ["инвестиции", "финансы", "статистика", "инфографика", "цифры", "рынки"]


def tag(word):
    return "#" + "".join(ch for ch in word.lower() if ch.isalnum())


def hashtags(r):
    tags = []
    try:
        code = int(r["id"].split("_")[-1])
        if code in TAG_ITEM:
            tags.append(TAG_ITEM[code])
    except ValueError:
        pass
    tags += TAG_BLOCK.get(r["block"], [])
    lead = next((s for s in r.get("series", []) if s.get("hl")), None) or r["top"][0]
    tags.append(lead["name"])
    tags += TAG_BASE
    out, seen = [], set()
    for t in tags:
        h = tag(t)
        if h not in seen and len(h) > 2:
            seen.add(h)
            out.append(h)
    return " ".join(out[:14])


def change(x):
    """Рост или падение для линии: «в 2,4 раза», «на 41%», «−12%»."""
    if x.get("growth"):
        g = x["growth"]
        return "+" + g[3:] if g.startswith("на ") else g
    return f"−{(1 - x['ratio']) * 100:.0f}%" if x.get("ratio", 1) < 1 else ""


def num1(v):
    t = f"{v:.1f}".replace(".", ",")
    return t[:-2] if t.endswith(",0") else t


def period(r):
    if r.get("period"):
        return r["period"]
    return f"{r['start']}-{r['year']}" if r.get("type") == "line" else str(r["year"])


def ten(r):
    """Список для текста: до 10 строк (флаг, страна, значение, изменение)."""
    kind = r.get("type", "bars")
    rows = []
    if kind == "line":
        for x in r.get("series_all", r["series"]):
            v = x["text"].split(", рост")[0]
            rows.append((x["rank"], x["flag"], x["name"], v + (f", {change(x)}" if change(x) else "")))
    elif kind == "donut":
        for x in r.get("top10", r["top"]):
            rows.append((x["rank"], x["flag"], x["name"], x["text"]))
    else:
        for x in r["top"][:10]:
            rows.append((x["rank"], x["flag"], x["name"], x["text"]))
    return rows


def threads_short(r):
    """Короткий формат, как ручные посты: заголовок, 10 мест с флагами, одна строка вывода, CTA."""
    kind = r.get("type", "bars")
    lines = [f"{r['title']}, {period(r)}:"]
    lines += [f"{rk}. {fl} {nm} · {v}" for rk, fl, nm, v in ten(r)]
    tail = r["hook_text"] + "."
    if kind == "bars":
        out = [c for c in r.get("cis", []) if c["rank"] > 10]
        if out:
            tail = ", ".join(f"{c['name']} на {c['rank']}-м" for c in out[:2]) + " месте."
    elif kind == "donut":
        tail = f"Остальной мир: {r['rest']:.0f}%."
    lines += [tail, "Больше в Telegram @osnovafin"]
    text = "\n".join(lines)
    if len(text) > 500 and kind == "line":  # лимит Threads: оставляем только изменение
        rows = [f"{rk}. {fl} {nm} · {v.split(', ', 1)[1] if ', ' in v else v}"
                for rk, fl, nm, v in ten(r)]
        text = "\n".join([lines[0]] + rows + lines[-2:])
    while len(text) > 500 and len(lines) > 6:   # длинные названия: убираем нижние места
        lines.pop(len(lines) - 3)
        text = "\n".join(lines)
    return text


def ig_caption(r, i):
    """Развёрнутая подпись: вывод, контекст из данных, список, вопрос, CTA, хэштеги."""
    kind = r.get("type", "bars")
    top = r["top"]
    para = []
    if kind == "line":
        ser = r["series"]
        g = next(s for s in ser if s.get("hl"))
        para.append(f"{r['title']}, {r['start']}-{r['year']}. "
                    f"Самый быстрый рост: {g['name']}, {g['growth']}, до {g['text'].split(', рост')[0]}.")
        para.append(f"Значения в {r['year']} году и изменение с {r['start']}:\n" + "\n".join(
            f"{rk}. {fl} {nm}: {v}" for rk, fl, nm, v in ten(r)))
    elif kind == "donut":
        para.append(f"{r['title']}, {r['year']} год. На пять крупнейших стран приходится "
                    f"{r['top_sum']:.0f}% мирового экспорта, на все остальные {r['rest']:.0f}%. "
                    f"Всего стран-экспортёров в данных: {r['countries']}.")
        para.append("Доли лидеров:\n" + "\n".join(f"{rk}. {fl} {nm}: {v}" for rk, fl, nm, v in ten(r)))
    else:
        a, b = top[0], top[1]
        ratio = a["value"] / b["value"] if b["value"] else 0
        cmp_ = f" Разрыв первого места со вторым ({b['name']}): в {num1(ratio)} раза." \
            if ratio >= 1.15 else f" Первое и второе место ({b['name']}) идут почти вровень."
        para.append(f"{r['title']}, {r['year']} год, данные {r['source']}." + cmp_
                    + (f" Учтены {r['note']}." if r.get("note") else ""))
        para.append("Топ-10:\n" + "\n".join(f"{rk}. {fl} {nm}: {v}" for rk, fl, nm, v in ten(r)))
        out = [c for c in r.get("cis", []) if c["rank"] > 10]
        if out:
            para.append(", ".join(f"{c['name']} на {c['rank']}-м" for c in out) + " месте.")
    parts = [r["hook_text"] + "."] + para + [
        QUESTIONS[i % len(QUESTIONS)],
        "Каждый день рынки, сделки инсайдеров из отчётов SEC и данные в Telegram @osnovafin, ссылка в профиле.",
        f"Источник: {r['source_full']}. Не является инвестиционной рекомендацией.",
        hashtags(r),
    ]
    return "\n\n".join(parts)


def check(resp, what):
    try:
        js = resp.json()
    except Exception:  # noqa: BLE001
        js = {"raw": resp.text[:300]}
    if resp.status_code != 200 or "error" in js:
        err = js.get("error", js)
        raise RuntimeError(f"{what}: HTTP {resp.status_code} {json.dumps(err, ensure_ascii=False)[:400]}")
    return js


def post_threads(token, text, imgs, reply_to=None):
    """imgs: [] текстовый пост, [url] картинка, [url, url] карусель. reply_to: id поста, если это ответ."""
    data = {"media_type": "TEXT", "text": text, "access_token": token}
    if reply_to:
        data["reply_to_id"] = reply_to
    if len(imgs) == 1:
        data.update(media_type="IMAGE", image_url=imgs[0])
    elif len(imgs) > 1:
        kids = []
        for u in imgs:
            k = check(requests.post(f"{THREADS}/me/threads", data={
                "media_type": "IMAGE", "image_url": u, "is_carousel_item": "true",
                "access_token": token}, timeout=60), "Threads слайд")
            kids.append(k["id"])
        time.sleep(20)
        data.update(media_type="CAROUSEL", children=",".join(kids))
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


def ig_wait(token, cid):
    for _ in range(12):
        time.sleep(5)
        s = check(requests.get(f"{IG}/{cid}", params={
            "fields": "status_code", "access_token": token}, timeout=30), "Instagram статус")
        if s.get("status_code") == "FINISHED":
            return
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram: контейнер с ошибкой {s}")


def post_instagram(token, caption, imgs):
    uid = ig_user_id(token)
    if len(imgs) == 1:
        c = check(requests.post(f"{IG}/{uid}/media", data={
            "image_url": imgs[0], "caption": caption, "access_token": token,
        }, timeout=60), "Instagram контейнер")
    else:
        kids = []
        for u in imgs:
            k = check(requests.post(f"{IG}/{uid}/media", data={
                "image_url": u, "is_carousel_item": "true", "access_token": token,
            }, timeout=60), "Instagram слайд")
            ig_wait(token, k["id"])
            kids.append(k["id"])
        c = check(requests.post(f"{IG}/{uid}/media", data={
            "media_type": "CAROUSEL", "children": ",".join(kids), "caption": caption,
            "access_token": token}, timeout=60), "Instagram карусель")
    ig_wait(token, c["id"])
    p = check(requests.post(f"{IG}/{uid}/media_publish", data={
        "creation_id": c["id"], "access_token": token,
    }, timeout=60), "Instagram публикация")
    return p["id"]



def ig_paused():
    """12.11: Instagram ограничил действия аккаунта (код 4, подкод 2207051). Пауза до даты в bank/ig_pause_until.txt."""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bank", "ig_pause_until.txt")
    try:
        until = dt.datetime.fromisoformat(open(p).read().strip())
    except Exception:  # noqa: BLE001
        return None
    return until if dt.datetime.now(dt.timezone.utc) < until else None


def main():
    platform = sys.argv[1]
    dry = "--dry-run" in sys.argv
    if platform == "instagram" and not dry and ig_paused():
        log(f"Instagram на паузе до {ig_paused().isoformat()}")
        return 0
    with open(os.path.join(BANK, "rankings.json"), encoding="utf-8") as f:
        rankings = json.load(f)
    extra = os.path.join(BANK, "rankings_markets.json")
    if os.path.exists(extra):
        with open(extra, encoding="utf-8") as f:
            rankings += json.load(f)
    st = load_state(platform)
    r = pick(rankings, st)
    if not r:
        log("Банк исчерпан: все рейтинги публиковались за последние 90 дней")
        return 1
    img = image_url(r)
    n = len(st["posted"])
    text = threads_short(r) if platform == "threads" else ig_caption(r, n)
    log(f"{platform}: {r['id']} ({r['block']}, {r.get('type', 'bars')})\n" + "\n".join(images(r)) + f"\n---\n{text}\n---")
    token = os.environ.get("THREADS_TOKEN" if platform == "threads" else "IG_TOKEN", "")
    if dry or not token:
        log("Публикации нет: " + ("dry-run" if dry else "токен не задан"))
        return 0
    if platform == "threads":
        with_img = n % 3 == 0  # картинка в каждом третьем посте, остальные текстом
        log("Threads: " + ("с картинкой" if with_img else "текстом"))
        pid = post_threads(token, text, images(r) if with_img else [])
        try:  # 11.11: первым ответом ссылка-приглашение в Telegram (код th), один клик до канала
            rid = post_threads(token, "Рынки 24/7 и разборы компаний в Telegram: https://t.me/+sUoaHcDSC5NjNTQ6", [], reply_to=pid)
            log(f"Ответ со ссылкой: {rid}")
        except Exception as e:  # noqa: BLE001
            log(f"Ответ со ссылкой не вышел: {e}")
    else:
        carousel = n % 4 == 2  # из 4 постов в день 1 карусель (обложка + график), 3 одиночных
        log("Instagram: " + ("карусель" if carousel else "одиночный пост с графиком"))
        try:
            pid = post_instagram(token, text, images(r) if carousel else [image_url(r)])
        except RuntimeError:
            # 12.11: Instagram ответил ошибкой на media_publish, но пост вышел; повтор дал 5 одинаковых постов.
            # Рейтинг помечается как использованный, второй попытки с ним не будет.
            st["posted"].append({"id": r["id"], "block": r["block"], "type": r.get("type", "bars"), "at": now().isoformat(), "post": "error"})
            save_state(platform, st)
            raise
    st["posted"].append({"id": r["id"], "block": r["block"], "type": r.get("type", "bars"),
                         "at": now().isoformat(), "post": pid})
    save_state(platform, st)
    left = len([x for x in rankings if x["id"] not in {p["id"] for p in st["posted"]}])
    log(f"Опубликовано: {pid}. Осталось новых рейтингов: {left}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
