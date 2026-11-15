"""@osnova.property: сбор статистики публикаций и отчёт по времени выхода.

Каждый день: для всех опубликованных материалов из state.json берёт лайки и комментарии (instagram_basic)
и, если у токена есть instagram_manage_insights, охват, просмотры, сохранения, репосты, визиты в профиль.
Пишет property/stats.json и property/stats_report.md: средние по набору времени (A/B), по слоту и по рубрике (слово DM).
"""
import os, json, datetime as dt
from collections import defaultdict
import requests

IG = "https://graph.facebook.com/v25.0"
HERE = os.path.dirname(os.path.abspath(__file__))
TOK = os.environ.get("IG_TOKEN", "")
UID = os.environ.get("IG_USER_ID_PROP") or open(os.path.join(HERE, "ig_user_id.txt")).read().strip()
REEL_M = "reach,views,saved,shares,likes,comments,total_interactions,ig_reels_avg_watch_time"
POST_M = "reach,views,saved,shares,likes,comments,total_interactions,profile_visits,follows"


def get(path, **p):
    r = requests.get(f"{IG}/{path}", params={**p, "access_token": TOK}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


def main():
    st = json.load(open(os.path.join(HERE, "state.json"), encoding="utf-8"))
    queue = {q["id"]: q for q in json.load(open(os.path.join(HERE, "queue.json"), encoding="utf-8"))}
    rows, notes = [], []
    for p in st["posted"]:
        pid = p.get("post", "")
        if not pid.isdigit():
            continue
        q = queue.get(p["id"], {})
        row = {"id": p["id"], "post": pid, "type": p.get("type", q.get("type", "reel")), "word": q.get("word", ""),
               "timeset": p.get("timeset", ""), "dubai_time": p.get("dubai_time", ""), "at": p["at"]}
        sc, d = get(pid, fields="like_count,comments_count,permalink,timestamp")
        row.update({"likes": d.get("like_count"), "comments": d.get("comments_count"), "permalink": d.get("permalink")})
        sc, ins = get(f"{pid}/insights", metric=REEL_M if row["type"] == "reel" else POST_M)
        if sc == 200:
            for m in ins.get("data", []):
                row[m["name"]] = (m.get("values") or [{}])[0].get("value", m.get("total_value", {}).get("value"))
        else:
            notes.append(f"{p['id']}: статистика охватов недоступна ({(ins.get('error') or {}).get('message', sc)})")
        rows.append(row)
    sc, acc = get(UID, fields="followers_count,media_count")
    out = {"at": dt.datetime.now(dt.timezone.utc).isoformat(), "followers": acc.get("followers_count"), "media": rows, "notes": notes[:5]}
    sc, onl = get(f"{UID}/insights", metric="online_followers", period="lifetime")
    if sc == 200:
        out["online_followers"] = onl.get("data", [{}])[0].get("values", [{}])[0].get("value")
    json.dump(out, open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # отчёт: что сравнивать в понедельник
    key = "reach" if any("reach" in r for r in rows) else "likes"
    L = [f"# @osnova.property · статистика на {out['at'][:10]}", "", f"Подписчиков: {out['followers']}. Публикаций: {len(rows)}. Метрика сравнения: {key}.", ""]
    for title, fld in (("Набор времени (A: 11:41/15:11/19:41, B: 08:41/13:11/21:41)", "timeset"), ("Время выхода (Дубай)", "dubai_time"),
                       ("Тип", "type"), ("Рубрика (слово DM)", "word")):
        g = defaultdict(list)
        for r in rows:
            g[r.get(fld) or "?"].append(r)
        L += [f"## {title}", "", "| Группа | Публикаций | Средний охват/лайки | Сохранения | Репосты | Визиты в профиль |", "|---|---|---|---|---|---|"]
        for k, rs in sorted(g.items(), key=lambda kv: -sum((x.get(key) or 0) for x in kv[1]) / len(kv[1])):
            avg = lambda f: round(sum((x.get(f) or 0) for x in rs) / len(rs), 1)
            L.append(f"| {k} | {len(rs)} | {avg(key)} | {avg('saved')} | {avg('shares')} | {avg('profile_visits')} |")
        L.append("")
    if out.get("online_followers"):
        hours = out["online_followers"]
        top = sorted(hours.items(), key=lambda kv: -kv[1])[:4]
        L += ["## Когда подписчики онлайн (часы UTC, Дубай = UTC+4)", "", ", ".join(f"{h}:00 UTC ({v})" for h, v in top), ""]
    if notes:
        L += ["## Ограничения", ""] + [f"- {n}" for n in notes[:3]]
    open(os.path.join(HERE, "stats_report.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
