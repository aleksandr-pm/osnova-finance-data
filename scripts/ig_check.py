"""Проверка Instagram без публикации: лимит публикаций за 24 часа и доступ к аккаунту."""
import os, json, requests
IG = "https://graph.facebook.com/v25.0"
tok, uid = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"]
for path, params in ((f"{uid}", {"fields": "username,followers_count,media_count"}),
                     (f"{uid}/content_publishing_limit", {"fields": "config,quota_usage"}),
                     (f"{uid}/media", {"fields": "id,media_product_type,timestamp,caption", "limit": 12})):
    r = requests.get(f"{IG}/{path}", params={**params, "access_token": tok}, timeout=30)
    d = r.json()
    if "data" in d and path.endswith("media"):
        d = [(x["timestamp"], x.get("media_product_type"), (x.get("caption") or "")[:50].replace("\n", " ")) for x in d["data"]]
    print(path.split("/")[-1], r.status_code, json.dumps(d, ensure_ascii=False)[:1500])
