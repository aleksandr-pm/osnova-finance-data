"""@osnova.property: автопубликация Reels и постов из очереди (property/queue.json).

Режимы:
  python property/publish.py --check     найти ID аккаунта osnova.property, проверить доступ и лимит, без публикации
  python property/publish.py [--dry-run] опубликовать следующий ролик из очереди

Правила (из опыта OSNOVA Finance, Instagram_autopublish_guide.md):
  * публикация только если есть файл property/LIVE и не наступила пауза property/pause_until.txt;
  * 3 слота в день: Reels 11:41 и 19:41, пост 15:11 по Дубаю; Reels не чаще раза в 5 ч, пост раз в 20 ч;
  * любая ошибка на шаге media_publish = ролик помечается использованным, повторно не отправляется;
  * отказ Instagram в обработке ролика = ролик помечается failed, в этом же запуске одна замена следующим.
"""
import os, sys, json, time, datetime as dt
import requests

IG = "https://graph.facebook.com/v25.0"
USERNAME = "osnova.property"
BUSINESS_ID = "167573054295268"  # бизнес-портфолио «Александр Максименко», как в scripts/publish.py
HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE, STATE = os.path.join(HERE, "queue.json"), os.path.join(HERE, "state.json")
ID_FILE, LIVE, PAUSE = os.path.join(HERE, "ig_user_id.txt"), os.path.join(HERE, "LIVE"), os.path.join(HERE, "pause_until.txt")
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def now():
    return dt.datetime.now(dt.timezone.utc)


def get(path, tok, **p):
    r = requests.get(f"{IG}/{path}", params={**p, "access_token": tok}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:300]}


def check(r, what):
    try:
        d = r.json()
    except ValueError:
        d = {"raw": r.text[:300]}
    if r.status_code != 200 or "error" in d:
        raise RuntimeError(f"{what}: HTTP {r.status_code} {json.dumps(d, ensure_ascii=False)[:500]}")
    return d


# ---------- поиск ID и проверка доступа ----------
def find_user_id(tok):
    cands = {}
    sc, me = get("me", tok, fields="id,name")
    log("me:", sc, json.dumps(me, ensure_ascii=False)[:300])
    sc, bz = get("me/businesses", tok, fields="id,name")
    log("me/businesses:", sc, json.dumps(bz, ensure_ascii=False)[:300])
    biz = [{"id": BUSINESS_ID, "name": "portfolio"}] + [x for x in (bz.get("data") or []) if x["id"] != BUSINESS_ID]
    for b in biz:
        for edge in ("owned_instagram_accounts", "instagram_accounts", "client_instagram_assets"):
            sc, d = get(f"{b['id']}/{edge}", tok, fields="id,username", limit=50)
            log(f"{b['name']}/{edge}:", sc, json.dumps(d, ensure_ascii=False)[:500])
            for x in (d.get("data") or []):
                if x.get("username") == USERNAME:
                    cands[x["id"]] = f"{b['name']}/{edge}"
    sc, d = get("me/accounts", tok, fields="name,instagram_business_account{id,username}", limit=50)
    log("me/accounts:", sc, json.dumps(d, ensure_ascii=False)[:500])
    for p in (d.get("data") or []):
        ig = p.get("instagram_business_account") or {}
        if ig.get("username") == USERNAME:
            cands[ig["id"]] = "page " + p.get("name", "")
    other = os.environ.get("IG_USER_ID_FIN", "")
    if other:  # business discovery через уже подключённый аккаунт OSNOVA Finance
        sc, d = get(other, tok, fields=f"business_discovery.username({USERNAME}){{id,username,followers_count,media_count}}")
        log("business_discovery:", sc, json.dumps(d, ensure_ascii=False)[:400])
        bd = d.get("business_discovery") or {}
        if bd.get("id"):
            cands.setdefault(bd["id"], "business_discovery")
    return cands


def do_check(tok):
    uid = os.environ.get("IG_USER_ID_PROP") or (open(ID_FILE).read().strip() if os.path.exists(ID_FILE) else "")
    cands = {uid: "secret/file"} if uid else find_user_id(tok)
    log("Кандидаты:", cands)
    ok = None
    for cid in cands:
        sc, d = get(cid, tok, fields="username,followers_count,media_count")
        log(f"{cid}:", sc, json.dumps(d, ensure_ascii=False)[:300])
        sc2, lim = get(f"{cid}/content_publishing_limit", tok, fields="config,quota_usage")
        log(f"{cid}/content_publishing_limit:", sc2, json.dumps(lim, ensure_ascii=False)[:300])
        if sc == 200 and d.get("username") == USERNAME and sc2 == 200:
            ok = cid
    if ok:
        open(ID_FILE, "w").write(ok + "\n")
        log(f"ГОТОВО: доступ к @{USERNAME} есть, ID {ok} записан в property/ig_user_id.txt")
        return 0
    log(f"НЕТ ДОСТУПА к @{USERNAME} с этим токеном: аккаунт не добавлен в портфолио Meta или системному пользователю не выдан доступ «Контент»")
    return 1


# ---------- очередь и состояние ----------
def load(p, default):
    try:
        return json.load(open(p, encoding="utf-8"))
    except FileNotFoundError:
        return default


def save_state(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def paused():
    try:
        s = open(PAUSE).read().strip()
        return s and now() < dt.datetime.fromisoformat(s)
    except FileNotFoundError:
        return False


def publish_reel(tok, uid, item):
    path = os.path.join(HERE, item["file"])
    c = check(requests.post(f"{IG}/{uid}/media", data={
        "media_type": "REELS", "upload_type": "resumable", "caption": item["caption"],
        "share_to_feed": "true", "thumb_offset": str(item.get("thumb_ms", 1500)), "access_token": tok}, timeout=60), "контейнер Reels")
    cid = c["id"]
    size = os.path.getsize(path)
    log(f"Контейнер {cid}, загрузка {size / 1e6:.1f} МБ")
    with open(path, "rb") as f:
        check(requests.post(f"https://rupload.facebook.com/ig-api-upload/v25.0/{cid}", data=f, headers={
            "Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size),
            "Content-Type": "application/octet-stream"}, timeout=600), "загрузка видео")
    for _ in range(60):
        time.sleep(10)
        s = check(requests.get(f"{IG}/{cid}", params={"fields": "status_code,status", "access_token": tok}, timeout=30), "статус")
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            raise ProcessingError(f"обработка не прошла: {s}")
    else:
        raise ProcessingError("видео не обработалось за 10 минут")
    # с этого места любая ошибка = ролик считается использованным (11.11 у OSNOVA Finance ответ 403, а пост вышел)
    try:
        r = requests.post(f"{IG}/{uid}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60)
        return check(r, "media_publish")["id"]
    except Exception as e:  # noqa: BLE001
        raise PublishStepError(str(e))


def publish_post(tok, uid, item):
    repo, sha = os.environ.get("GITHUB_REPOSITORY", "aleksandr-pm/osnova-finance-data"), os.environ.get("GITHUB_SHA", "main")
    url = f"https://raw.githubusercontent.com/{repo}/{sha}/property/{item['file']}"
    c = check(requests.post(f"{IG}/{uid}/media", data={"image_url": url, "caption": item["caption"], "access_token": tok}, timeout=60), "контейнер поста")
    cid = c["id"]
    log(f"Контейнер {cid}, картинка {url}")
    for _ in range(18):
        time.sleep(5)
        s = check(requests.get(f"{IG}/{cid}", params={"fields": "status_code", "access_token": tok}, timeout=30), "статус")
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            raise ProcessingError(f"обработка не прошла: {s}")
    try:
        r = requests.post(f"{IG}/{uid}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60)
        return check(r, "media_publish")["id"]
    except Exception as e:  # noqa: BLE001
        raise PublishStepError(str(e))


class ProcessingError(RuntimeError):
    pass


class PublishStepError(RuntimeError):
    pass


def main():
    args = sys.argv[1:]
    tok = os.environ.get("IG_TOKEN", "")
    if "--check" in args:
        return do_check(tok) if tok else (log("Нет токена") or 1)
    dry = "--dry-run" in args or not os.path.exists(LIVE)
    queue, st = load(QUEUE, []), load(STATE, {"posted": []})
    slot = os.environ.get("SLOT", "reel")
    used = {p["id"] for p in st["posted"]}
    todo = [q for q in queue if q["id"] not in used and q.get("type", "reel") == slot]
    log(f"Слот {slot}: в очереди {len(todo)} из {len(queue)}; LIVE={'да' if os.path.exists(LIVE) else 'нет'}")
    if not todo:
        log("Очередь пуста: нужны новые ролики")
        return 0
    if paused():
        log("Пауза до", open(PAUSE).read().strip())
        return 0
    kind = {q["id"]: q.get("type", "reel") for q in queue}
    real = [p for p in st["posted"] if p.get("post") not in ("failed",) and kind.get(p["id"], "reel") == slot]
    if real and not dry and "--force" not in args:
        gap = now() - dt.datetime.fromisoformat(real[-1]["at"])
        if gap < dt.timedelta(hours=5 if slot == "reel" else 20):
            log(f"Пропуск: прошлый ролик {int(gap.total_seconds() // 3600)} ч назад")
            return 0
    item = todo[0]
    log(f"Следующий: {item['id']} ({item['file']})\n---\n{item['caption']}\n---")
    if dry:
        log("Без публикации: " + ("dry-run" if "--dry-run" in args else "нет файла property/LIVE"))
        return 0
    if not tok:
        log("Нет токена IG_TOKEN")
        return 1
    uid = os.environ.get("IG_USER_ID_PROP") or open(ID_FILE).read().strip()
    for attempt in range(2):
        try:
            pid = (publish_post if item.get("type") == "post" else publish_reel)(tok, uid, item)
            st["posted"].append({"id": item["id"], "at": now().isoformat(), "post": pid})
            save_state(st)
            log(f"Опубликовано: {item['id']} → {pid}")
            return 0
        except PublishStepError as e:
            st["posted"].append({"id": item["id"], "at": now().isoformat(), "post": "error", "err": str(e)[:300]})
            save_state(st)
            log(f"Ошибка на media_publish, ролик помечен использованным (пост мог выйти, проверьте в приложении): {e}")
            return 1
        except Exception as e:  # noqa: BLE001  отказ до публикации: ролик failed, одна замена
            st["posted"].append({"id": item["id"], "at": now().isoformat(), "post": "failed", "err": str(e)[:300]})
            save_state(st)
            log(f"Ролик {item['id']} не принят: {e}")
            nxt = [q for q in todo if q["id"] not in {p["id"] for p in st["posted"]}]
            if attempt == 1 or not nxt:
                return 1
            item = nxt[0]
            log(f"Замена: {item['id']}")
    return 1


if __name__ == "__main__":
    code = 1
    try:
        code = main()
    finally:
        os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
        name = "check.txt" if "--check" in sys.argv else "last_publish.txt"
        open(os.path.join(HERE, "logs", name), "w", encoding="utf-8").write(
            "\n".join(LOG) + f"\nexit={code} {now().isoformat()}\n")
    sys.exit(code)
