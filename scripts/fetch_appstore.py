"""Lấy biểu tượng và thông tin các app của Duong Le trên App Store (chạy trên GitHub Actions)."""
import json
import os
import urllib.request

OUT = "import/appstore"
APP_IDS = ["6752948624", "1635711570", "6443436301", "1599040247"]
os.makedirs(OUT, exist_ok=True)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (site migration)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


apps = {}
artists = set()
for country in ["vn", "us"]:
    data = json.loads(get(f"https://itunes.apple.com/lookup?id={','.join(APP_IDS)}&country={country}"))
    for a in data.get("results", []):
        apps.setdefault(str(a["trackId"]), a)
        artists.add(a.get("artistId"))
    for artist in filter(None, artists):
        more = json.loads(get(f"https://itunes.apple.com/lookup?id={artist}&entity=software&country={country}&limit=200"))
        for a in more.get("results", []):
            if a.get("wrapperType") == "software":
                apps.setdefault(str(a["trackId"]), a)

for tid, a in apps.items():
    art = a.get("artworkUrl512") or a.get("artworkUrl100")
    if not art:
        continue
    url = art.rsplit("/", 1)[0] + "/512x512bb.png"
    try:
        with open(f"{OUT}/icon-{tid}.png", "wb") as f:
            f.write(get(url))
    except Exception as e:  # noqa: BLE001
        print("skip icon", tid, e)

# Ảnh chụp màn hình cho app chưa có ảnh trên trang cũ (Brain hack - Emoji puzzle)
for tid in ["1665458705"]:
    for i, u in enumerate(apps.get(tid, {}).get("screenshotUrls", []), 1):
        try:
            with open(f"{OUT}/shot-{tid}-{i}.{u.rsplit('.', 1)[-1]}", "wb") as f:
                f.write(get(u))
        except Exception as e:  # noqa: BLE001
            print("skip shot", u, e)

with open(f"{OUT}/apps.json", "w", encoding="utf-8") as f:
    json.dump(list(apps.values()), f, ensure_ascii=False, indent=1)
print(len(apps), "app:", ", ".join(a["trackName"] for a in apps.values()))
