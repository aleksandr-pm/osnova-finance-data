"""Разборы компаний в Threads. v3 (11.11.2026)

Два режима:
  python scripts/publish_report.py            @osnova_report: следующий пост из companies/posts.json (10:27 и 19:27 по Дубаю)
  python scripts/publish_report.py finance    @osnova_finance: разбор, вышедший в @osnova_report не меньше 20 часов назад (13:07 и 22:07)

После поста в Threads первым ответом идёт ссылка-приглашение в Telegram со своим кодом (rp или th).
Режим report дополнительно ставит разбор в Telegram-канал: tg/outbox_report.json, его отправляет воркер
(карточка + текст + таблица по годам, #разбор). Пустой или почти пустой банк = ошибка запуска, GitHub присылает письмо.
Секреты: THREADS_TOKEN_REPORT (report), THREADS_TOKEN (finance)."""
import html, json, os, subprocess, sys, time
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_company import render

THREADS = "https://graph.threads.net/v1.0"
REPO = os.environ.get("GITHUB_REPOSITORY", "aleksandr-pm/osnova-finance-data")
DRY = os.environ.get("DRY_RUN") == "yes"
STATE = "companies/state.json"
OUTBOX = "tg/outbox_report.json"
LINK = {"report": "https://t.me/+pfrKty7hzGM0OTli", "finance": "https://t.me/+sUoaHcDSC5NjNTQ6"}
REPLY = "Полный разбор с таблицей по годам и рынки 24/7 в Telegram: {}"
CTA = "Разборы компаний и рынки 24/7 в Telegram @osnovafin"


def check(r, what):
    if r.status_code != 200:
        raise RuntimeError(f"{what}: HTTP {r.status_code} {r.text[:300]}")
    return r.json()


def company(p):
    d = json.load(open(f"companies/data/{p['ticker']}.json"))
    for k, v in (p.get("override") or {}).items():
        d[k].update(v)
    return d


def card_for(p):
    d = company(p)
    if p["chart"] == "debt":
        a, b, an, bn, sub = d["total_debt"], d["equity"], "Долг", "Собственный капитал", "Долг и собственный капитал"
    else:
        a, b, an, bn, sub = d["revenue"], d["net_income"], "Выручка", "Чистая прибыль", "Выручка и чистая прибыль"
    ys = p.get("years") or sorted(set(a) & set(b))[-4:]  # у NVIDIA, Costco, Nike финансовый год не совпадает с календарным
    return dict(hook=[tuple(x) for x in p["hook"]], sub=sub, years=ys, a=[a[y] for y in ys], b=[b[y] for y in ys],
                a_name=an, b_name=bn, cur=d["currency"] or "AED", source="Yahoo Finance, отчётность компании")


def money(v, cur):
    """Сумма по-русски: $1,2 млрд, 356 млн AED."""
    a = abs(v)
    s = f"{a / 1e9:.2f}".rstrip("0").rstrip(".") + " млрд" if a >= 1e9 else f"{a / 1e6:.0f} млн"
    s = s.replace(".", ",")
    s = f"${s}" if cur == "USD" else f"{s} {cur}"
    return ("−" if v < 0 else "") + s


def tg_caption(p):
    c = card_for(p)
    body = p["text"].replace(CTA, "").strip()
    rows = "\n".join(f"{y}: {money(x, c['cur'])} · {money(z, c['cur'])}" for y, x, z in zip(c["years"], c["a"], c["b"]))
    title = " ".join(t for t, _ in c["hook"])
    cap = (f"📊 <b>{html.escape(title)}</b>\n\n{html.escape(body)}\n\n"
           f"<b>{c['a_name']} · {c['b_name'].lower()} по годам</b>\n{rows}\n\n#разбор")
    return cap[:1020]


def threads_post(tok, text, image_url=None, reply_to=None):
    data = {"media_type": "IMAGE" if image_url else "TEXT", "text": text, "access_token": tok}
    if image_url:
        data["image_url"] = image_url
    if reply_to:
        data["reply_to_id"] = reply_to
    c = check(requests.post(f"{THREADS}/me/threads", data=data, timeout=60), "контейнер")
    time.sleep(35 if image_url else 10)
    return check(requests.post(f"{THREADS}/me/threads_publish", data={"creation_id": c["id"], "access_token": tok}, timeout=60), "публикация")["id"]


def reply_link(tok, post_id, account):
    try:
        rid = threads_post(tok, REPLY.format(LINK[account]), reply_to=post_id)
        print("ответ со ссылкой:", rid)
    except Exception as e:  # noqa: BLE001  ссылка в ответе не должна ломать сам пост
        print("ответ со ссылкой не вышел:", e)


def git_push(paths, msg):
    subprocess.run(["git", "add", *paths], check=True)
    subprocess.run(["git", "commit", "-m", msg], check=False)
    for _ in range(3):
        if subprocess.run(["git", "pull", "--rebase", "origin", "main"]).returncode == 0 and subprocess.run(["git", "push"]).returncode == 0:
            return
        time.sleep(5)
    raise RuntimeError("git push не прошёл")


def to_telegram(p, path):
    box = json.load(open(OUTBOX)) if os.path.exists(OUTBOX) else []
    item = f"report-{p['id']}"
    if any(x["id"] == item for x in box):
        return
    box = (box + [{"id": item, "t": int(time.time()), "caption": tg_caption(p),
                   "photo": f"https://raw.githubusercontent.com/{REPO}/main/{path}"}])[-20:]
    os.makedirs("tg", exist_ok=True)
    json.dump(box, open(OUTBOX, "w"), ensure_ascii=False, indent=1)


def run_report(posts, st):
    todo = [p for p in posts if p["id"] not in st["done"]]
    if not todo:
        sys.exit("банк постов пуст: нужно пополнить companies/posts.json")
    p = todo[0]
    os.makedirs("companies/cards", exist_ok=True)
    path = f"companies/cards/{p['id']}.jpg"
    render(card_for(p), path)
    print("пост:", p["id"], "осталось после него:", len(todo) - 1)
    if DRY:
        print(p["text"], "\n---\n", tg_caption(p)); return
    git_push([path], f"report: карточка {p['id']} [skip ci]")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    time.sleep(10)
    tok = os.environ["THREADS_TOKEN_REPORT"]
    pid = threads_post(tok, p["text"], image_url=f"https://raw.githubusercontent.com/{REPO}/{sha}/{path}")
    reply_link(tok, pid, "report")
    st["done"].append(p["id"])
    st.setdefault("log", []).append({"id": p["id"], "post": pid, "t": time.strftime("%Y-%m-%d %H:%M"), "ts": int(time.time())})
    json.dump(st, open(STATE, "w"), ensure_ascii=False, indent=1)
    to_telegram(p, path)
    git_push([STATE, OUTBOX], f"report: опубликован {p['id']} [skip ci]")
    print("опубликовано:", pid)
    if len(todo) - 1 < 3:
        sys.exit(f"в банке осталось {len(todo) - 1} поста: пополнить companies/posts.json")


def run_finance(posts, st):
    by = {p["id"]: p for p in posts}
    done = set(st.setdefault("finance_done", []))
    now = time.time()
    ready = [x for x in st.get("log", []) if x["id"] not in done and x["id"] in by
             and now - x.get("ts", time.mktime(time.strptime(x["t"], "%Y-%m-%d %H:%M"))) >= 20 * 3600]
    if not ready:
        print("для @osnova_finance нет разбора старше 20 часов"); return
    p = by[ready[0]["id"]]
    path = f"companies/cards/{p['id']}.jpg"
    if not os.path.exists(path):
        render(card_for(p), path)
        git_push([path], f"report: карточка {p['id']} [skip ci]")
    print("osnova_finance, разбор:", p["id"])
    if DRY:
        return
    tok = os.environ["THREADS_TOKEN"]
    pid = threads_post(tok, p["text"], image_url=f"https://raw.githubusercontent.com/{REPO}/main/{path}")
    reply_link(tok, pid, "finance")
    st["finance_done"].append(p["id"])
    json.dump(st, open(STATE, "w"), ensure_ascii=False, indent=1)
    git_push([STATE], f"finance: разбор {p['id']} [skip ci]")
    print("опубликовано:", pid)


def main():
    posts = json.load(open("companies/posts.json"))
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"done": []}
    (run_finance if "finance" in sys.argv[1:] else run_report)(posts, st)


if __name__ == "__main__":
    main()
