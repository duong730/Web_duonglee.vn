"""Lấy các trang, bài viết và ảnh từ duonglehoai.wordpress.com vào import/ (chạy trên GitHub Actions)."""
import json
import os
import re
import urllib.request

SITE = "duonglehoai.wordpress.com"
OUT = "import"
os.makedirs(f"{OUT}/images", exist_ok=True)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (site migration)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def save(name, data):
    with open(f"{OUT}/{name}", "wb") as f:
        f.write(data)


api = f"https://public-api.wordpress.com/wp/v2/sites/{SITE}"
pages = json.loads(get(f"{api}/pages?per_page=100&context=view"))
posts = json.loads(get(f"{api}/posts?per_page=100&context=view"))
save("pages.json", json.dumps(pages, ensure_ascii=False, indent=1).encode())
save("posts.json", json.dumps(posts, ensure_ascii=False, indent=1).encode())
save("home.html", get(f"https://{SITE}/"))
for p in pages:
    try:
        save(f"page-{p['slug']}.html", get(p["link"]))
    except Exception as e:  # noqa: BLE001
        print("skip page", p["link"], e)

html = open(f"{OUT}/home.html", encoding="utf-8", errors="ignore").read()
html += json.dumps(pages) + json.dumps(posts)
urls = set(re.findall(r"https://" + re.escape(SITE) + r"/wp-content/uploads/[^\"'\s?)\\]+", html))
urls |= set(re.findall(r"https://[a-z0-9.-]*files\.wordpress\.com/[^\"'\s?)\\]+", html))
print(len(urls), "ảnh")
for u in sorted(urls):
    name = "-".join(u.split("/wp-content/uploads/")[-1].split("/")) if "/wp-content/uploads/" in u else u.split("/")[-1]
    try:
        save(f"images/{name}", get(u))
    except Exception as e:  # noqa: BLE001
        print("skip image", u, e)
print("xong")
