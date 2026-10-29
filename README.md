# Smart Union AI — bản web (MVP)

Hệ thống quản lý thi đua Liên đội. Python + FastAPI, SQLite, Jinja2 + Bootstrap 5.
Giai đoạn này chưa có AI Agent; các service được viết sẵn để Agent gọi làm công cụ ở giai đoạn 4.

## Chạy thử

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                    # mở http://127.0.0.1:8000
```

Lần chạy đầu tự tạo CSDL `smart_union.db` kèm dữ liệu mẫu (12 lớp, 5 tiêu chí, 6 tuần điểm).

| Vai trò   | Tên đăng nhập | Mật khẩu   | Quyền |
|-----------|---------------|------------|-------|
| Quản trị  | `admin`       | `admin123` | Toàn quyền: lớp, tiêu chí, tài khoản, sửa/xóa điểm |
| Giáo viên | `giaovien`    | `gv123456` | Xem, nhập điểm, xuất báo cáo (không sửa/xóa điểm) |

Đổi mật khẩu và `SECRET_KEY` (xem `.env.example`) trước khi dùng thật. Muốn bỏ dữ liệu mẫu: xóa file `.db`
và bỏ lời gọi `seed_if_empty` trong `app/main.py`.

Chạy kiểm thử: `pip install pytest && pytest`

## Cấu trúc MVC

```
app/
├── models/        MODEL      Bảng dữ liệu (SQLAlchemy): User, SchoolClass, Criterion, ScoreEntry, ScoreHistory
├── services/      MODEL      Nghiệp vụ: ranking_service (tính điểm/xếp hạng), score_service (nhập/sửa/xóa + lịch sử),
│                             report_service (báo cáo, Excel), period (tuần/tháng/học kỳ), auth_service, seed
├── controllers/   CONTROLLER Mỗi file một router: nhận request, kiểm tra quyền, gọi service, trả về view
├── views/         VIEW       Template Jinja2
│   ├── layouts/     khung trang (base, app, auth)
│   ├── components/  thành phần dùng lại (macro): sidebar, topbar, stat_card, ranking_table, leaderboard_hero,
│   │                period_filter, chart_card, entries_table, form_field, pagination, delete_button, ...
│   └── <trang>/     dashboard, rankings, scores, classes, criteria, reports, history, users, auth, errors
├── static/
│   ├── css/         tokens (màu, font) · layout · components · print
│   └── js/components/  chart-card.js · confirm-delete.js · auto-submit.js
├── core/          Tiện ích dùng chung: bảo mật mật khẩu, session/flash, phân quyền, render template
├── config.py · database.py · main.py
tests/             Kiểm chứng công thức điểm, đồng hạng, kỳ thi đua
```

Luồng một request: `controller` → `service` → `model` → CSDL, sau đó `controller` chọn `view` để render.
Controller không chứa công thức tính điểm; mọi phép tính nằm trong `services/`.

## Quy ước nghiệp vụ hiện tại (sửa theo quy chế trường)

- **Tổng điểm** = `BASE_SCORE` (mặc định 0, đặt trong `config.py`) + tổng điểm cộng + tổng điểm trừ trong kỳ.
- **Đồng điểm**: lớp bị trừ ít điểm hơn xếp trên; vẫn bằng nhau thì đồng hạng (1-1-3-4). Sửa ở `_assign_ranks` trong `ranking_service.py`.
- **Kỳ**: tuần thứ Hai–Chủ nhật; học kỳ 1 từ 01/09 đến 31/01, học kỳ 2 từ 01/02 đến 31/08. Sửa ở `services/period.py`.
- **Lịch sử**: thêm/sửa/xóa điểm đều ghi vào `score_history` kèm người thực hiện và nội dung trước/sau.
- Chỉ quản trị được sửa/xóa điểm. Lớp/tiêu chí đã có điểm không xóa được, chỉ ẩn.

## Chưa có trong bản này

- AI Agent (tra cứu xếp hạng, phân tích biến động, soạn bản nháp báo cáo).
- Xuất PDF trực tiếp: tạm dùng nút “In / Lưu PDF” của trình duyệt.
- Chống CSRF bằng token (hiện dựa vào cookie `SameSite=Lax`), giới hạn số lần đăng nhập sai.
- Migration CSDL (Alembic) khi chuyển sang PostgreSQL.
