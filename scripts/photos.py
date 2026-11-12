"""Фото для обложек: Pixabay API (бесплатная лицензия Pixabay, атрибуция не обязательна). v1.

Запрос подбирается по теме рейтинга: товар (поле пшеницы, кофе) или город страны-лидера.
Фото скачиваются к себе (Pixabay запрещает прямые ссылки на свои файлы).
"""
import hashlib
import os
import time

import requests

API = "https://pixabay.com/api/"

COMMODITY = {
    15: "wheat field", 56: "corn field", 27: "rice paddy", 31: "rice paddy",
    44: "barley field", 236: "soybean field", 656: "coffee beans", 661: "cocoa beans",
    667: "tea plantation", 156: "sugar cane field", 162: "sugar cane field",
    116: "potato harvest", 515: "apple orchard", 486: "banana plantation",
    560: "vineyard", 388: "tomatoes harvest", 267: "sunflower field",
    270: "rapeseed field", 257: "palm oil plantation", 261: "olive grove",
    564: "wine cellar barrels", 867: "cattle pasture", 1058: "poultry farm",
    882: "dairy cows pasture", 1062: "eggs farm", 767: "cotton field",
    572: "avocado", 490: "orange grove", 1182: "honey bees hive", 403: "onion harvest",
    221: "almond orchard", 225: "hazelnuts", 223: "pistachio", 268: "sunflower field",
    1035: "pig farm",
}
CITY = {
    "US": "new york skyline", "CN": "shanghai skyline", "IN": "mumbai skyline",
    "RU": "moscow city skyline", "JP": "tokyo skyline", "DE": "frankfurt skyline",
    "GB": "london skyline", "FR": "paris skyline", "BR": "sao paulo skyline",
    "CA": "toronto skyline", "AU": "sydney skyline", "KZ": "almaty city",
    "UZ": "tashkent city", "AE": "dubai skyline", "SA": "riyadh skyline",
    "SG": "singapore skyline", "HK": "hong kong skyline", "CH": "zurich city",
    "KR": "seoul skyline", "TR": "istanbul skyline", "ID": "jakarta skyline",
    "MX": "mexico city skyline", "NL": "amsterdam", "IT": "milan skyline",
    "ES": "madrid skyline", "EE": "tallinn old town", "LT": "vilnius city",
    "LV": "riga city", "GE": "tbilisi city", "AM": "yerevan city", "AZ": "baku city",
    "BY": "minsk city", "TJ": "dushanbe", "KG": "bishkek", "VN": "ho chi minh city skyline",
    "TH": "bangkok skyline", "MY": "kuala lumpur skyline", "QA": "doha skyline",
    "IE": "dublin city", "LU": "luxembourg city", "NO": "oslo city", "IR": "tehran city",
    "NP": "kathmandu", "EG": "cairo city", "PH": "manila skyline", "BD": "dhaka city",
}
TOPIC = {
    "fi_res": "gold bars", "cm_mkt": "stock exchange trading", "trf_pwkr": "money transfer",
}


def query_for(r):
    rid = r["id"]
    for key, q in TOPIC.items():
        if key in rid:
            return q, "business"
    parts = rid.split("_")
    if rid.startswith(("fao_", "share_", "line_agro")):
        try:
            code = int(parts[-1])
            if code in COMMODITY:
                return COMMODITY[code], "nature" if code not in (656, 661, 564, 1182) else "food"
        except ValueError:
            pass
    lead = None
    for s in r.get("series", []):
        if s.get("hl"):
            lead = s["iso2"]
    lead = lead or (r["top"][0]["iso2"] if r.get("top") else None)
    return CITY.get(lead, "city skyline night"), "buildings"


BAN = {"poppy", "poppies", "cannabis", "marijuana", "hemp", "opium", "weapon", "gun", "war", "soldier", "alcohol", "cigarette", "smoking"}


def search(key, q, category):
    params = {"key": key, "q": q, "image_type": "photo", "safesearch": "true",
              "per_page": 30, "min_width": 1600, "category": category, "order": "popular"}
    for attempt in range(3):
        r = requests.get(API, params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(30)
            continue
        if r.status_code != 200:
            return []
        return r.json().get("hits", [])
    return []


def fetch_photo(key, r, out_dir, used, log):
    """Скачивает фото для рейтинга, возвращает путь или None."""
    q, cat = query_for(r)
    hits = search(key, q, cat) or search(key, q.split()[0] + " " + q.split()[-1], "")
    time.sleep(0.8)  # лимит Pixabay: 100 запросов в минуту
    must = q.split()[0].lower()  # 12.11: на «corn field» пришли маки. Ключевое слово запроса обязано быть в тегах фото
    for h in hits:
        if h["id"] in used:
            continue
        tags = {t.strip().lower() for t in (h.get("tags") or "").split(",")}
        if BAN & {w for t in tags for w in t.split()}:
            continue
        if cat != "buildings" and not any(must in t for t in tags):
            continue
        url = h.get("largeImageURL")
        if not url:
            continue
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200:
            continue
        used.add(h["id"])
        path = os.path.join(out_dir, f"{r['id']}.jpg")
        with open(path, "wb") as f:
            f.write(resp.content)
        r["photo"] = {"source": "Pixabay", "pixabay_id": h["id"], "query": q,
                      "page": h.get("pageURL"), "author": h.get("user")}
        return path
    log(f"  фото {r['id']}: нет подходящего по запросу «{q}»")
    return None


def stable_pick(items, seed):
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return items[h % len(items)]
