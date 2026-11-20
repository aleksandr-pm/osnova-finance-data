"""Pixabay: видео и фото для вставок в ролики @aleksandr_markets.
Запрос: am/research/pix/request.txt, строки вида  video|dubai traffic|3  или  photo|coca cola|2
Файлы уходят в ветку pix-cache (перезаписывается), в git только manifest.json с авторами и ссылками."""
import os, json, re, subprocess, requests

KEY = os.environ["PIXABAY_KEY"]
OUT = "pix_out"; os.makedirs(OUT, exist_ok=True)
lines = [l.strip() for l in open("am/research/pix/request.txt", encoding="utf-8") if "|" in l]
man = []
for ln in lines:
    kind, q, n = (ln.split("|") + ["3"])[:3]; n = int(n)
    slug = re.sub(r"[^a-z0-9]+", "_", q.lower()).strip("_")
    if kind == "video":
        r = requests.get("https://pixabay.com/api/videos/", params={"key": KEY, "q": q, "per_page": 50, "safesearch": "true"}, timeout=30).json()
        hits = sorted(r.get("hits", []), key=lambda h: (h["videos"]["large"]["height"] > h["videos"]["large"]["width"], h.get("likes", 0)), reverse=True)[:n]
        for i, h in enumerate(hits):
            v = h["videos"]["large"] if h["videos"]["large"]["url"] else h["videos"]["medium"]
            fn = f"{slug}_{i + 1}.mp4"
            raw = os.path.join(OUT, "_raw.mp4")
            try:
                open(raw, "wb").write(requests.get(v["url"], timeout=180).content)
                # вертикаль 1080x1920, до 12 сек, без звука: файлы маленькие, ветка не раздувается
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-t", "12", "-an", "-vf",
                                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", os.path.join(OUT, fn)], check=True)
                os.remove(raw)
            except Exception as e:  # noqa: BLE001
                man.append({"file": fn, "error": str(e)}); continue
            man.append({"file": fn, "q": q, "w": v["width"], "h": v["height"], "sec": h["duration"], "user": h["user"], "page": h["pageURL"]})
    else:
        r = requests.get("https://pixabay.com/api/", params={"key": KEY, "q": q, "per_page": 50, "image_type": "photo", "safesearch": "true"}, timeout=30).json()
        for i, h in enumerate(r.get("hits", [])[:n]):
            fn = f"{slug}_{i + 1}.jpg"
            open(os.path.join(OUT, fn), "wb").write(requests.get(h["largeImageURL"], timeout=60).content)
            man.append({"file": fn, "q": q, "w": h["imageWidth"], "h": h["imageHeight"], "user": h["user"], "page": h["pageURL"]})
json.dump(man, open("am/research/pix/manifest.json", "w"), indent=1, ensure_ascii=False)
print(len(man), "files")
