"""Dựng trang duonglee.vn thành các tệp tĩnh trong site/.

Chạy: SITE_EMAIL=... python3 scripts/build.py   (cần Pillow và beautifulsoup4)
  SITE_EMAIL  email hỗ trợ hiện trên trang. Trên GitHub lấy từ biến kho SITE_EMAIL
              (Settings › Secrets and variables › Actions › Variables).
Nguồn:
  import/   nội dung và ảnh lấy từ trang WordPress cũ và App Store (không sửa tay)
  media/    ảnh thêm mới (Đỉnh Bò)
  src/      giao diện (styles.css, site.js), trang tiếng Việt viết tay (src/pages), tệp tĩnh (src/static)
"""

import base64
import hashlib
import html
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
IMP = ROOT / "import"
SRC = ROOT / "src"
DOMAIN = "https://duonglee.vn"
EMAIL = os.environ.get("SITE_EMAIL", "").strip()
if not EMAIL:
    if os.environ.get("CI"):
        sys.exit("Thiếu biến SITE_EMAIL: thêm ở Settings › Secrets and variables › Actions › Variables.")
    EMAIL = "support@example.com"
    print("Chưa đặt SITE_EMAIL, dùng địa chỉ mẫu để xem thử.")
YEAR = date.today().year

# ---------------------------------------------------------------- ảnh


def image(src, name, height, quality=80):
    """Thu nhỏ ảnh về chiều cao `height`, lưu WebP vào site/img, trả về (đường dẫn, rộng, cao)."""
    dest = OUT / "img" / f"{name}.webp"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(ROOT / src) as im:
        im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
        if im.height > height:
            im = im.resize((round(im.width * height / im.height), height), Image.LANCZOS)
        im.save(dest, "WEBP", quality=quality, method=6)
        return f"/img/{name}.webp", im.width, im.height


def img_tag(info, alt, cls="", eager=False):
    url, w, h = info
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    c = f' class="{cls}"' if cls else ""
    return f'<img{c} src="{url}" width="{w}" height="{h}" alt="{html.escape(alt)}" {loading}>'


# ---------------------------------------------------------------- dữ liệu các app

AS = "https://apps.apple.com"
APPS = [
    {
        "id": "number-defense", "kind": "game", "label": "Number Defense",
        "name": "Number Defense: Find & Destroy", "tint": "#E4572E",
        "icon": "import/appstore/icon-6752948624.png",
        "meta": "Puzzle game · iPhone & iPad · Ages 9+",
        "desc": "Find the numbers from 1 to 100 in the right order while viruses attack your board.",
        "links": [("App Store", f"{AS}/us/app/number-defense-find-destroy/id6752948624")],
        "policy": "/number-defense-find-destroy-privacy-policy/",
        "shots": [f"import/images/2025-09-iphone6.500{n:02d}.png" for n in (0, 2, 3, 4, 6, 7, 8, 9, 10)],
        "orient": "portrait",
    },
    {
        "id": "finding-animals", "kind": "game", "label": "Finding Animals",
        "name": "Finding Animals", "tint": "#2F8FE0",
        "icon": "import/appstore/icon-1635711570.png",
        "meta": "Learning game for kids · iPhone & iPad · Ages 4+",
        "desc": "Search for 72 kinds of animals and insects around the world, hear their sounds and count them.",
        "links": [("App Store", f"{AS}/vn/app/learning-game-for-kid-animal/id1635711570")],
        "policy": "/finding-animals-privacy-policy/",
        "shots": sorted(str(p.relative_to(ROOT)) for p in (IMP / "images").glob("2022-07-*.jpg")),
        "orient": "landscape",
    },
    {
        "id": "brain-hack", "kind": "game", "label": "Brain Hack",
        "name": "Brain Hack – Emoji Puzzle", "sub": "Đố vui – Bắt chữ – Hại não", "tint": "#F08A12",
        "icon": "import/appstore/icon-1665458705.png",
        "meta": "Word puzzle · iPhone & iPad · Ages 4+",
        "desc": "Funny word puzzles with emoji, in Vietnamese and English.",
        "links": [("App Store", f"{AS}/vn/app/brain-hack-emoji-puzzle/id1665458705")],
        "page": "/do-vui-bat-chu-hai-nao/",
        "policy": "/do-vui-bat-chu-hoi-ngu-hai-nao-privacy-policy/",
        "shots": [f"import/appstore/shot-1665458705-{n}.jpg" for n in range(1, 7)],
        "orient": "portrait",
    },
    {
        "id": "dinh-bo", "kind": "app", "label": "Đỉnh Bò",
        "name": "Đỉnh Bò – Chủ Quán", "sub": "Quản lý nhà hàng, kho, lãi lỗ", "tint": "#8E1F1F",
        "badge": "Coming soon",
        "icon": "media/dinh-bo/icon.png",
        "meta": "Restaurant management · iPhone · In Vietnamese",
        "desc": "Inventory, recipes, sales and profit & loss for restaurant owners, with cooking courses inside the app.",
        "links": [],
        "page": "/dinh-bo/",
        "policy": "/dinh-bo-privacy-policy/",
        "support": "/dinh-bo-support/",
        "shots": [f"media/dinh-bo/{n}.png" for n in ("tong-quan", "kho", "nhap-hang", "kiem-ke", "ban-hang", "bao-cao")],
        "captions": ["Tổng quan", "Kho", "Nhập hàng", "Kiểm kê", "Bán hàng", "Báo cáo lãi lỗ"],
        "orient": "portrait",
    },
    {
        "id": "chua-online", "kind": "app", "label": "Chùa Online",
        "name": "Tu Tại Gia – Chùa Online", "sub": "Online Pagoda", "tint": "#C9962B",
        "icon": "import/appstore/icon-6443436301.png",
        "meta": "Lifestyle · iOS & Android · Ages 4+",
        "desc": "Set up an altar, offer incense, read prayers and chant sutras on your phone.",
        "links": [
            ("App Store", f"{AS}/us/app/tu-t%E1%BA%A1i-gia-ch%C3%B9a-online/id6443436301"),
            ("Google Play", "https://play.google.com/store/apps/details?id=com.duongle.dichuaonline"),
        ],
        "page": "/tu-tai-gia-chua-online/",
        "policy": "/online-pagoda-privacy-policy/",
        "shots": [f"import/images/2022-09-{n}.jpg" for n in range(1, 9)],
        "orient": "landscape",
    },
    {
        "id": "infor-save", "kind": "app", "label": "Infor Save",
        "name": "Infor Save", "tint": "#5B45E8",
        "icon": "import/appstore/icon-1599040247.png",
        "meta": "Utilities · iPhone & iPad · Ages 4+",
        "desc": "Manage and store your private information safely. Everything stays on your device.",
        "links": [("App Store", f"{AS}/vn/app/infor-save/id1599040247")],
        "policy": "/infor-save-privacy-policy/",
        "shots": [f"import/images/2021-12-image-{n}.png" for n in (1, 2, 3, 5)],
        "captions": [
            "High security",
            "Very easy to use",
            "No user data leaks, everything is stored locally on your device",
            "Flexible in saving many kinds of information",
        ],
        "orient": "portrait",
    },
]
BY_ID = {a["id"]: a for a in APPS}


def prepare_media():
    for a in APPS:
        a["icon_img"] = image(a["icon"], f"icon-{a['id']}", 256, quality=88)
        h = 1000 if a["orient"] == "portrait" else 640
        a["shot_imgs"] = [image(s, f"{a['id']}-{i + 1}", h) for i, s in enumerate(a["shots"])]


# ---------------------------------------------------------------- khung trang

PRELOAD = ("bricolage-grotesque-latin-opsz-normal.woff2", "be-vietnam-pro-latin-400-normal.woff2")
NAV = {
    "en": [("Games", "/#games"), ("Apps", "/#apps"), ("Support", "/#support")],
    "vi": [("Game", "/#games"), ("Ứng dụng", "/#apps"), ("Hỗ trợ", "/#support")],
}
ASSET_V = {}
SITEMAP = []


def asset(name):
    if name not in ASSET_V:
        ASSET_V[name] = hashlib.sha1((OUT / "assets" / name).read_bytes()).hexdigest()[:8]
    return f"/assets/{name}?v={ASSET_V[name]}"


def protect_email(doc, lang):
    """Không để email hỗ trợ ở dạng chữ thường trong HTML: mã hóa, trình duyệt giải mã bằng site.js.
    Máy quét email đọc HTML thô sẽ không thấy địa chỉ; người xem vẫn thấy và bấm được như bình thường."""
    enc = base64.b64encode(EMAIL[::-1].encode()).decode()
    hidden = "[bật JavaScript để xem email]" if lang == "vi" else "[enable JavaScript to see the email]"
    doc = re.sub(
        r'href="mailto:' + re.escape(EMAIL) + r'(?:\?([^"]*))?"',
        lambda m: f'href="#" data-mail="{enc}"' + (f' data-q="{m.group(1)}"' if m.group(1) else ""),
        doc,
        flags=re.I,
    )
    doc = doc.replace(f'data-copy="{EMAIL}"', f'data-copy-mail="{enc}"')
    return re.sub(re.escape(EMAIL), f'<span data-mail="{enc}">{hidden}</span>', doc, flags=re.I)


def page(path, title, body, *, desc="", lang="en", image_url="/og.png", body_class=""):
    nav = "".join(f'<a href="{u}">{t}</a>' for t, u in NAV[lang])
    preload = "\n".join(
        f'<link rel="preload" href="/assets/fonts/{f}" as="font" type="font/woff2" crossorigin>' for f in PRELOAD
    )
    skip = "Bỏ qua, tới nội dung" if lang == "vi" else "Skip to content"
    policies = " ".join(f'<a href="{a["policy"]}">{html.escape(a["label"])}</a>' for a in APPS)
    pol_label = "Chính sách quyền riêng tư" if lang == "vi" else "Privacy policies"
    doc = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{DOMAIN}{path}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{DOMAIN}{path}">
<meta property="og:image" content="{DOMAIN}{image_url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#F3F4F8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E0F1D" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.png" type="image/png" sizes="64x64">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
{preload}
<link rel="stylesheet" href="{asset('styles.css')}">
</head>
<body class="{body_class}">
<a class="skip" href="#main">{skip}</a>
<header class="topbar" data-topbar>
  <div class="topbar-inner">
    <a class="brand" href="/" aria-label="Duong Le"><span class="brand-mark" aria-hidden="true">DL</span><span>Duong Le</span></a>
    <nav class="nav" aria-label="Main">{nav}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="footer">
  <div class="wrap footer-inner">
    <p>© {YEAR} Duong Le · <a href="mailto:{EMAIL}">{EMAIL}</a></p>
    <p class="footer-links"><span>{pol_label}:</span> {policies}</p>
  </div>
</footer>
<script src="{asset('site.js')}" defer></script>
</body>
</html>
"""
    doc = protect_email(doc, lang)
    dest = OUT / path.strip("/") / "index.html" if path.endswith("/") else OUT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc, encoding="utf-8")
    SITEMAP.append(path)


def redirect(path, to):
    dest = OUT / path.strip("/") / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        f'<!doctype html><meta charset="utf-8"><title>Moved</title>'
        f'<link rel="canonical" href="{DOMAIN}{to}"><meta http-equiv="refresh" content="0; url={to}">'
        f'<a href="{to}">{DOMAIN}{to}</a>\n',
        encoding="utf-8",
    )


# ---------------------------------------------------------------- mảnh giao diện


def store_buttons(a):
    return "".join(
        f'<a class="btn btn-ink" href="{u}" rel="noopener">{l}<span aria-hidden="true">↗</span></a>' for l, u in a["links"]
    )


def card_actions(a):
    out = [store_buttons(a)]
    if a.get("page"):
        out.append(f'<a class="btn btn-ghost" href="{a["page"]}">About the app</a>')
    if a.get("support"):
        out.append(f'<a class="btn btn-ghost" href="{a["support"]}">Support</a>')
    out.append(f'<a class="text-link" href="{a["policy"]}">Privacy policy</a>')
    return "".join(out)


def shelf(a, label=None, eager=False):
    caps = a.get("captions") or []
    items = []
    for i, info in enumerate(a["shot_imgs"]):
        alt = caps[i] if i < len(caps) else f"{a['name']}, screenshot {i + 1}"
        cap = f"<figcaption>{html.escape(caps[i])}</figcaption>" if i < len(caps) else ""
        items.append(f"<li><figure>{img_tag(info, alt, 'shot', eager and i < 2)}{cap}</figure></li>")
    label = label or f"{a['name']} screenshots"
    return (
        f'<div class="shelf is-{a["orient"]}" data-shelf>'
        f'<ul class="shelf-track" tabindex="0" aria-label="{html.escape(label)}">{"".join(items)}</ul>'
        '<button class="shelf-btn prev" type="button" aria-label="Previous" hidden><span aria-hidden="true">←</span></button>'
        '<button class="shelf-btn next" type="button" aria-label="Next" hidden><span aria-hidden="true">→</span></button>'
        "</div>"
    )


def app_card(a):
    sub = f'<p class="app-sub">{html.escape(a["sub"])}</p>' if a.get("sub") else ""
    badge = f' <span class="badge">{html.escape(a["badge"])}</span>' if a.get("badge") else ""
    return f"""
<article class="app" id="{a['id']}" style="--tint:{a['tint']}">
  <div class="app-head">
    {img_tag(a['icon_img'], a['name'] + ' icon', 'app-icon')}
    <div class="app-text">
      <h3 class="app-title">{html.escape(a['name'])}{badge}</h3>
      {sub}
      <p class="app-meta">{html.escape(a['meta'])}</p>
      <p class="app-desc">{html.escape(a['desc'])}</p>
    </div>
    <div class="app-actions">{card_actions(a)}</div>
  </div>
  {shelf(a)}
</article>"""


# ---------------------------------------------------------------- trang chủ


def build_home():
    icons = "".join(
        f'<li style="--i:{i}"><a class="spring-icon" href="#{a["id"]}">'
        f'{img_tag(a["icon_img"], "", eager=True)}<span>{html.escape(a["label"])}</span></a></li>'
        for i, a in enumerate(APPS)
    )
    does = [
        ("Create apps & games", "for enriching people’s lives"),
        ("Different choice", "available for various appetites, from individuals to large teams"),
        ("Flexible", "in approaching your demands"),
        ("Try hard", "to satisfy customers"),
    ]
    does_html = "".join(f"<li><h3>{t}</h3><p>{d}</p></li>" for t, d in does)
    games = [a for a in APPS if a["kind"] == "game"]
    apps = [a for a in APPS if a["kind"] == "app"]
    body = f"""
<section class="springboard" aria-labelledby="hero-name">
  <div class="springboard-inner">
    <div class="widget-slot">
      <div class="widget">
        <h1 id="hero-name">Duong Le</h1>
        <p class="widget-role">Mobile App Developer</p>
        <p class="widget-lead">Build and manage mobile apps from beginning to end. Satisfy clients and end users, starting from the smallest requirement.</p>
        <a class="btn btn-light" href="#support">Get in touch</a>
      </div>
      <p class="spring-label" aria-hidden="true">About me</p>
    </div>
    <ul class="spring-icons" aria-label="My apps and games">{icons}</ul>
  </div>
</section>

<section class="section" aria-labelledby="do-title">
  <div class="wrap does-grid">
    <div class="section-head">
      <p class="eyebrow">Meet me better</p>
      <h2 class="h2" id="do-title">What I do</h2>
    </div>
    <ul class="does">{does_html}</ul>
  </div>
</section>

<section class="section section-apps" id="games" aria-labelledby="games-title">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">In my games · {len(games)}</p>
      <h2 class="h2" id="games-title">Games</h2>
    </div>
    <div class="app-list">{''.join(app_card(a) for a in games)}</div>
  </div>
</section>

<section class="section section-apps" id="apps" aria-labelledby="apps-title">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">In my apps · {len(apps)}</p>
      <h2 class="h2" id="apps-title">Apps</h2>
    </div>
    <div class="app-list">{''.join(app_card(a) for a in apps)}</div>
  </div>
</section>

<section class="panel support" id="support" aria-labelledby="support-title">
  <div class="panel-inner">
    <h2 class="h2" id="support-title">Get support?</h2>
    <p class="support-lead">If you need any support, please contact me:</p>
    <a class="mail" href="mailto:{EMAIL}">{EMAIL}</a>
    <div class="support-actions">
      <a class="btn btn-light" href="mailto:{EMAIL}">Write an email</a>
      <button class="btn btn-glass" type="button" data-copy="{EMAIL}">Copy address</button>
    </div>
    <p class="support-note">Using Đỉnh Bò? Common questions are answered on the <a href="/dinh-bo-support/">Đỉnh Bò support page</a> (in Vietnamese).</p>
  </div>
</section>
"""
    page(
        "/",
        "Duong Le · Mobile App Developer",
        body,
        desc="Duong Le builds and manages mobile apps and games: Number Defense, Finding Animals, Brain Hack, "
        "Đỉnh Bò, Tu Tại Gia – Chùa Online and Infor Save.",
        body_class="home",
    )


# ---------------------------------------------------------------- chính sách cũ (làm sạch HTML của WordPress)

KEEP_ATTR = {"a": {"href"}, "td": {"colspan", "rowspan"}, "th": {"colspan", "rowspan"}}
JUNK = ["script", "style", "noscript", "iframe", "form", "button", "svg", "input", "img"]
UPPER_WORDS = re.compile(r"\b(eu|uk|us|usa|ccpa|gdpr|ip|cpra|vcdpa|ios)\b", re.I)


def norm(text):
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", norm(text).lower()).strip("-")[:48] or "section"


def clean_policy(raw):
    soup = BeautifulSoup(raw, "html.parser")
    ec = soup.find(class_="entry-content")
    for t in ec.find_all(JUNK):
        t.decompose()
    for t in ec.find_all(id=re.compile("atatags|wordads")):
        t.decompose()
    for t in ec.find_all(class_=re.compile("sharedaddy|jp-relatedposts|wpcnt|wp-block-jetpack")):
        t.decompose()
    for t in ec.find_all(["span", "div", "figure", "u", "font", "section", "mark"]):
        t.unwrap()
    for t in ec.find_all(True):
        keep = KEEP_ATTR.get(t.name, set())
        t.attrs = {k: v for k, v in t.attrs.items() if k in keep}

    # bậc tiêu đề: bậc lớn nhất thành h2, bậc kế thành h3, còn lại h4
    levels = sorted({int(h.name[1]) for h in ec.find_all(re.compile("^h[1-6]$"))})
    remap = {lvl: f"h{min(2 + i, 4)}" for i, lvl in enumerate(levels)}
    for h in ec.find_all(re.compile("^h[1-6]$")):
        h.name = remap[int(h.name[1])]

    # tiêu đề mục bị viết thành danh sách 1 dòng: <ol start="5"><li><strong>TIÊU ĐỀ</strong></li></ol>
    for ol in ec.find_all("ol"):
        lis = ol.find_all("li", recursive=False)
        text = norm(ol.get_text())
        if len(lis) == 1 and text.isupper() and len(text) < 120:
            h = soup.new_tag("h2")
            h.string = f"{ol.get('start', '1')}. {text}"
            ol.replace_with(h)
    # đoạn chỉ có chữ đậm → tiêu đề
    for p in ec.find_all("p"):
        strongs = p.find_all("strong")
        text = norm(p.get_text())
        if not text or not strongs or norm("".join(s.get_text() for s in strongs)) != text:
            continue
        if len(text) > 90 or text.endswith((".", ":", ",", "?")) and not re.match(r"^\d+\.\s", text):
            continue
        p.name = "h2" if (text.isupper() or re.match(r"^\d+\.\s", text)) else "h3"
        p.string = text

    meta = ""
    for el in ec.find_all(["h2", "h3", "p"]):
        text = norm(el.get_text())
        if text.upper() in ("PRIVACY NOTICE", "PRIVACY POLICY"):
            el.decompose()
            continue
        m = re.match(r"^Last updated (.+)$", text)
        if m and not meta:
            meta = f"Last updated {m.group(1)}"
            el.decompose()
    if not meta:
        m = re.search(r"effective as of (\d{4})-(\d{2})-(\d{2})", ec.get_text())
        if m:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            meta = f"Effective {d.strftime('%B')} {d.day}, {d.year}"

    # tiêu đề viết HOA → viết thường cho dễ đọc, gắn id để mục lục nhảy tới
    used, numbered = set(), {}
    for h in ec.find_all(["h2", "h3", "h4"]):
        text = norm(h.get_text())
        if text.isupper():
            text = re.sub(r"[a-z]", lambda m: m.group(0).upper(), text.lower(), count=1)
            text = UPPER_WORDS.sub(lambda m: m.group(1).upper(), text).replace("IOS", "iOS")
        h.string = text
        num = re.match(r"^(\d+)\.\s*", text)
        hid = f"section-{num.group(1)}" if num and h.name == "h2" else slugify(text)
        while hid in used:
            hid += "-2"
        used.add(hid)
        h["id"] = hid
        if num and h.name == "h2":
            numbered[num.group(1)] = (hid, text)

    # mục lục: dòng "N. ..." hoặc dòng trùng tên một mục → link tới mục đó
    by_title = {t.split(". ", 1)[-1].lower(): (hid, t) for hid, t in numbered.values()}
    for el in ec.find_all(["p", "li"]):
        if el.find("a") or el.name.startswith("h"):
            continue
        text = norm(el.get_text())
        m = re.match(r"^(\d+)\.\s+(.+)$", text)
        hit = numbered.get(m.group(1)) if m else by_title.get(text.lower())
        if hit:
            el.clear()
            a = soup.new_tag("a", href=f"#{hit[0]}")
            a.string = hit[1]
            el.append(a)

    # link hỏng trỏ vào máy tính cũ (/Users/...) hoặc trang cũ
    for a in ec.find_all("a"):
        href = a.get("href", "")
        if href.startswith(("/Users/", "file:")):
            target = norm(a.get_text()).lower()
            hit = next((hid for hid, t in numbered.values() if t.lower().split(". ", 1)[-1] == target), None)
            if hit:
                a["href"] = f"#{hit}"
            else:
                a.unwrap()
        elif "duonglehoai.wordpress.com" in href:
            a["href"] = re.sub(r"https?://duonglehoai\.wordpress\.com", "", href) or "/"

    for t in ec.find_all("table"):
        t.wrap(soup.new_tag("div", attrs={"class": "table-wrap"}))
    for br in ec.find_all("br"):
        nxt = br.next_sibling
        if nxt is None or (isinstance(nxt, NavigableString) and not nxt.strip() and nxt.next_sibling is None):
            br.decompose()
    for p in ec.find_all(["p", "li", "strong", "em"]):
        if not norm(p.get_text()):
            p.decompose()
    out = ec.decode_contents()
    return re.sub(r"\n{2,}", "\n", out).replace("\xa0", " "), meta


POLICIES = [
    ("number-defense-find-destroy-privacy-policy", "number-defense"),
    ("finding-animals-privacy-policy", "finding-animals"),
    ("do-vui-bat-chu-hoi-ngu-hai-nao-privacy-policy", "brain-hack"),
    ("online-pagoda-privacy-policy", "chua-online"),
    ("infor-save-privacy-policy", "infor-save"),
]


def doc_layout(a, title, meta, content, lang="en", eyebrow=None, aside_extra=""):
    home = "Trang chủ" if lang == "vi" else "Home"
    contact = "Liên hệ" if lang == "vi" else "Questions?"
    return f"""
<div class="doc" style="--tint:{a['tint']}">
  <header class="doc-hero wrap">
    <p class="crumbs"><a href="/">{home}</a><span aria-hidden="true">/</span><a href="/#{a['id']}">{html.escape(a['label'])}</a></p>
    <div class="doc-title">
      {img_tag(a['icon_img'], a['name'] + ' icon', 'doc-icon', eager=True)}
      <div>
        <p class="eyebrow">{html.escape(eyebrow or a['name'])}</p>
        <h1 class="h1">{html.escape(title)}</h1>
        {f'<p class="doc-meta">{html.escape(meta)}</p>' if meta else ''}
      </div>
    </div>
  </header>
  <div class="wrap doc-grid">
    <article class="prose">{content}</article>
    <aside class="doc-aside">
      <div class="aside-card">
        <p class="aside-name">{html.escape(a['name'])}</p>
        <div class="aside-links">{store_buttons(a)}{aside_extra}</div>
        <p class="aside-contact">{contact}<br><a href="mailto:{EMAIL}">{EMAIL}</a></p>
      </div>
    </aside>
  </div>
</div>"""


def build_policies():
    for slug, app_id in POLICIES:
        a = BY_ID[app_id]
        content, meta = clean_policy((IMP / f"page-{slug}.html").read_text(encoding="utf-8"))
        body = doc_layout(a, "Privacy Policy", meta, content)
        page(f"/{slug}/", f"{a['name']} · Privacy Policy", body,
             desc=f"Privacy policy for {a['name']} by Duong Le.", image_url=a["icon_img"][0])


# ---------------------------------------------------------------- trang tiếng Việt


def fragment(name, **subs):
    text = (SRC / "pages" / name).read_text(encoding="utf-8")
    for k, v in {"email": EMAIL, **subs}.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def build_vietnamese():
    pagoda = BY_ID["chua-online"]
    body = doc_layout(pagoda, "Tu Tại Gia – Chùa Online", "",
                      fragment("tu-tai-gia-chua-online.html", shelf=shelf(pagoda, "Ảnh trong app")),
                      lang="vi", eyebrow="Online Pagoda")
    page("/tu-tai-gia-chua-online/", "Tu Tại Gia – Chùa Online", body, lang="vi",
         desc="Tu Tại Gia – Chùa Online: lập ban thờ, thắp hương, đọc văn khấn, tụng kinh, gõ mõ trên điện thoại.",
         image_url=pagoda["icon_img"][0])
    redirect("/tu-tai-gia-chua-online1/", "/tu-tai-gia-chua-online/")

    hack = BY_ID["brain-hack"]
    body = doc_layout(hack, "Đố vui – Bắt chữ – Hại não", "",
                      fragment("do-vui-bat-chu-hai-nao.html", shelf=shelf(hack, "Ảnh trong game")),
                      lang="vi", eyebrow="Brain Hack – Emoji Puzzle")
    page("/do-vui-bat-chu-hai-nao/", "Đố vui – Bắt chữ – Hại não", body, lang="vi",
         desc="Brain Hack – Emoji Puzzle: game đuổi hình bắt chữ bằng emoji.", image_url=hack["icon_img"][0])

    bo = BY_ID["dinh-bo"]
    body = fragment("dinh-bo.html", shelf=shelf(bo, "Ảnh màn hình Đỉnh Bò", eager=True),
                    icon=img_tag(bo["icon_img"], "Biểu tượng Đỉnh Bò", "panel-icon", eager=True))
    page("/dinh-bo/", "Đỉnh Bò – Chủ Quán: quản lý nhà hàng, kho, lãi lỗ", body, lang="vi", body_class="theme-dinhbo",
         desc="App Đỉnh Bò – Chủ Quán: nhập hàng, tồn kho, công thức món, bán hàng và lãi lỗ cho chủ quán ăn. "
         "Có khóa học nấu lẩu và nước chấm.",
         image_url=bo["icon_img"][0])
    extra = (
        '<a class="btn btn-ghost" href="/dinh-bo/">Giới thiệu app</a>'
        '<a class="text-link" href="/dinh-bo-support/">Hỗ trợ</a>'
        '<a class="text-link" href="/dinh-bo-privacy-policy/">Chính sách quyền riêng tư</a>'
        '<a class="text-link" href="/dinh-bo-delete-account/">Xóa tài khoản</a>'
    )
    for slug, title, meta, desc in [
        ("dinh-bo-privacy-policy", "Chính sách quyền riêng tư", "Cập nhật ngày 24/11/2026",
         "Chính sách quyền riêng tư của app Đỉnh Bò – Chủ Quán."),
        ("dinh-bo-support", "Hỗ trợ", "", "Hỗ trợ app Đỉnh Bò – Chủ Quán: liên hệ và câu hỏi thường gặp."),
        ("dinh-bo-delete-account", "Xóa tài khoản", "", "Cách xóa tài khoản Đỉnh Bò – Chủ Quán và dữ liệu bị xóa."),
    ]:
        body = doc_layout(bo, title, meta, fragment(f"{slug}.html"), lang="vi", eyebrow="Đỉnh Bò – Chủ Quán", aside_extra=extra)
        page(f"/{slug}/", f"{title} · Đỉnh Bò – Chủ Quán", body, lang="vi", desc=desc,
             image_url=bo["icon_img"][0], body_class="theme-dinhbo")


def build_404():
    links = "".join(f'<li><a href="{a["policy"]}">{html.escape(a["name"])} · Privacy policy</a></li>' for a in APPS)
    body = f"""
<section class="wrap notfound">
  <p class="eyebrow">404</p>
  <h1 class="h1">This page isn’t here.</h1>
  <p>It may have moved when this site left WordPress. Try the <a href="/">home page</a>, or one of these:</p>
  <ul>{links}</ul>
</section>"""
    page("404.html", "Page not found · Duong Le", body)
    SITEMAP.remove("404.html")


# ---------------------------------------------------------------- chạy


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    # phông chữ tự lưu: gộp @font-face vào đầu styles.css
    shutil.copytree(SRC / "fonts", OUT / "assets" / "fonts")
    (OUT / "assets" / "styles.css").write_text(
        (SRC / "fonts.css").read_text(encoding="utf-8") + "\n" + (SRC / "styles.css").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    shutil.copy(SRC / "site.js", OUT / "assets" / "site.js")
    for f in (SRC / "static").iterdir():
        shutil.copy(f, OUT / f.name)
    prepare_media()
    build_home()
    build_policies()
    build_vietnamese()
    build_404()
    redirect("/blog/", "/")
    (OUT / "CNAME").write_text("duonglee.vn\n")
    (OUT / ".nojekyll").write_text("")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    urls = "".join(f"<url><loc>{DOMAIN}{p}</loc></url>" for p in SITEMAP)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n'
    )
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"Xong: {len(SITEMAP)} trang, {size / 1e6:.1f} MB → {OUT}")


if __name__ == "__main__":
    main()
