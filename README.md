# duonglee.vn

Trang cá nhân của Duong Le: giới thiệu các app, game và chính sách quyền riêng tư của từng app.
Thay cho trang cũ duonglehoai.wordpress.com, giữ nguyên đường dẫn các trang chính sách cũ.

- `scripts/build.py` dựng toàn bộ trang vào `site/` (Python 3, Pillow, beautifulsoup4).
- `src/` giao diện (`styles.css`, `site.js`), phông chữ tự lưu, trang tiếng Việt viết tay (`src/pages/`).
- `import/` nội dung và ảnh lấy từ WordPress cũ và App Store (chạy một lần, không sửa tay).
- `media/` ảnh mới (Đỉnh Bò).
- `.github/workflows/pages.yml` dựng và đăng lên GitHub Pages khi đẩy code lên `main`.

Email hỗ trợ đọc từ biến `SITE_EMAIL` (Settings › Secrets and variables › Actions › Variables).

Xem thử trên máy: `SITE_EMAIL=... python3 scripts/build.py && python3 -m http.server -d site`
