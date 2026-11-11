"""Охваты за 7 дней: Threads (оба аккаунта), Instagram (посты и Reels). Пишет bank/logs/stats.txt. v1 11.11.2026"""
import os, time, json
import requests
TH = "https://graph.threads.net/v1.0"
IG = "https://graph.facebook.com/v25.0"
out = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); out.append(s)
since = int(time.time()) - 7 * 86400

for name, var in (("Threads @osnova_finance", "THREADS_TOKEN"), ("Threads @osnova_report", "THREADS_TOKEN_REPORT")):
    tok = os.environ.get(var)
    if not tok: p(name, "нет токена"); continue
    r = requests.get(f"{TH}/me/threads_insights", params={"metric": "views,likes,replies,reposts,followers_count",
        "since": since, "until": int(time.time()), "access_token": tok}, timeout=30).json()
    if "error" in r: p(name, "ошибка:", r["error"].get("message")); continue
    m = {}
    for d in r.get("data", []):
        v = d.get("total_value", {}).get("value")
        if v is None: v = sum(x.get("value", 0) for x in d.get("values", []))
        m[d["name"]] = v
    p(name, json.dumps(m, ensure_ascii=False))
    posts = requests.get(f"{TH}/me/threads", params={"fields": "id,text,timestamp", "since": since, "limit": 100, "access_token": tok}, timeout=30).json().get("data", [])
    best = []
    for x in posts[:60]:
        ins = requests.get(f"{TH}/{x['id']}/insights", params={"metric": "views", "access_token": tok}, timeout=30).json()
        v = next((d["values"][0]["value"] for d in ins.get("data", []) if d.get("values")), 0)
        best.append((v, (x.get("text") or "")[:60].replace("\n", " ")))
    best.sort(reverse=True)
    p(f"  постов за 7 дней: {len(posts)}, просмотров по постам: {sum(b[0] for b in best)}, медиана: {sorted(b[0] for b in best)[len(best)//2] if best else 0}")
    for v, t in best[:5]: p(f"  {v:>6}  {t}")

tok, uid = os.environ.get("IG_TOKEN"), os.environ.get("IG_USER_ID")
if tok and uid:
    acc = requests.get(f"{IG}/{uid}", params={"fields": "followers_count,media_count", "access_token": tok}, timeout=30).json()
    p("Instagram @osnova_finance", json.dumps(acc, ensure_ascii=False))
    media = requests.get(f"{IG}/{uid}/media", params={"fields": "id,media_type,media_product_type,timestamp,caption", "limit": 60, "access_token": tok}, timeout=30).json().get("data", [])
    rows = []
    for x in media:
        if x["timestamp"][:10] < time.strftime("%Y-%m-%d", time.gmtime(since)): continue
        ins = requests.get(f"{IG}/{x['id']}/insights", params={"metric": "views,reach,saved,shares,follows,profile_visits", "access_token": tok}, timeout=30).json()
        if "error" in ins:
            ins = requests.get(f"{IG}/{x['id']}/insights", params={"metric": "views,reach", "access_token": tok}, timeout=30).json()
        m = {d["name"]: d["values"][0]["value"] for d in ins.get("data", []) if d.get("values")}
        if "error" in ins: m = {"ошибка": ins["error"].get("message", "")[:80]}
        rows.append((m.get("views", 0), x.get("media_product_type"), (x.get("caption") or "")[:50].replace("\n", " "), m))
    rows.sort(key=lambda r: -(r[0] if isinstance(r[0], int) else 0))
    p(f"  публикаций за 7 дней: {len(rows)}, просмотров: {sum(r[0] for r in rows if isinstance(r[0], int))}")
    for r in rows[:8]: p(f"  {r[0]:>6} {r[1]:<6} {r[2]} {json.dumps(r[3], ensure_ascii=False)}")
os.makedirs("bank/logs", exist_ok=True)
open("bank/logs/stats.txt", "w").write("\n".join(out) + "\n")
