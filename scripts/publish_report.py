"""Автопостинг разборов компаний в Threads @osnova_report: 2 поста в день. v2 (08.11: годы по данным компании, пустой или почти пустой банк = ошибка запуска, GitHub присылает письмо)
Берёт следующий неопубликованный пост из companies/posts.json, рисует карточку, кладёт её в репозиторий
и публикует картинку с текстом. Состояние: companies/state.json. Секрет: THREADS_TOKEN_REPORT."""
import json, os, subprocess, sys, time
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_company import render

THREADS = "https://graph.threads.net/v1.0"
REPO = os.environ.get("GITHUB_REPOSITORY", "aleksandr-pm/osnova-finance-data")
Y = ["2022", "2023", "2024", "2025"]
DRY = os.environ.get("DRY_RUN") == "yes"

def check(r, what):
    if r.status_code != 200:
        raise RuntimeError(f"{what}: HTTP {r.status_code} {r.text[:300]}")
    return r.json()

def card_for(p):
    d = json.load(open(f"companies/data/{p['ticker']}.json"))
    for k, v in (p.get("override") or {}).items():
        d[k].update(v)
    if p["chart"] == "debt":
        a, b, an, bn, sub = d["total_debt"], d["equity"], "Долг", "Собственный капитал", "Долг и собственный капитал"
    else:
        a, b, an, bn, sub = d["revenue"], d["net_income"], "Выручка", "Чистая прибыль", "Выручка и чистая прибыль"
    ys = sorted(set(a) & set(b))[-4:]  # у NVIDIA, Costco, Nike финансовый год не совпадает с календарным
    return dict(hook=[tuple(x) for x in p["hook"]], sub=sub, years=ys, a=[a[y] for y in ys], b=[b[y] for y in ys],
                a_name=an, b_name=bn, cur=d["currency"] or "AED", source="Yahoo Finance, отчётность компании")

def main():
    posts = json.load(open("companies/posts.json"))
    st = json.load(open("companies/state.json")) if os.path.exists("companies/state.json") else {"done": []}
    todo = [p for p in posts if p["id"] not in st["done"]]
    if not todo:
        sys.exit("банк постов пуст: нужно пополнить companies/posts.json")
    p = todo[0]
    os.makedirs("companies/cards", exist_ok=True)
    path = f"companies/cards/{p['id']}.jpg"
    render(card_for(p), path)
    print("пост:", p["id"], "осталось после него:", len(todo) - 1)
    if DRY:
        print(p["text"]); return
    subprocess.run(["git", "add", path], check=True)
    subprocess.run(["git", "commit", "-m", f"report: карточка {p['id']} [skip ci]"], check=False)
    subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
    subprocess.run(["git", "push"], check=True)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    url = f"https://raw.githubusercontent.com/{REPO}/{sha}/{path}"
    time.sleep(10)
    tok = os.environ["THREADS_TOKEN_REPORT"]
    c = check(requests.post(f"{THREADS}/me/threads", data={"media_type": "IMAGE", "image_url": url, "text": p["text"], "access_token": tok}, timeout=60), "контейнер")
    time.sleep(35)
    r = check(requests.post(f"{THREADS}/me/threads_publish", data={"creation_id": c["id"], "access_token": tok}, timeout=60), "публикация")
    st["done"].append(p["id"])
    st.setdefault("log", []).append({"id": p["id"], "post": r["id"], "t": time.strftime("%Y-%m-%d %H:%M")})
    json.dump(st, open("companies/state.json", "w"), ensure_ascii=False, indent=1)
    subprocess.run(["git", "add", "companies/state.json"], check=True)
    subprocess.run(["git", "commit", "-m", f"report: опубликован {p['id']} [skip ci]"], check=True)
    subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("опубликовано:", r["id"])
    if len(todo) - 1 < 3:
        sys.exit(f"в банке осталось {len(todo) - 1} поста: пополнить companies/posts.json")

if __name__ == "__main__":
    main()
