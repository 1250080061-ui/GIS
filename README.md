# 📚 LibraryGIS — Hệ thống quản lý thư viện tích hợp GIS

## Tính năng

| Module | Mô tả |
|--------|-------|
| 🗺️ **GIS & Bản đồ** | Leaflet.js dark map, marker chi nhánh, heatmap độc giả, tìm chi nhánh gần nhất theo GPS |
| 📊 **Dashboard** | 12 stat cards, biểu đồ xu hướng 12 tháng, chart danh mục, sách hot, cảnh báo quá hạn |
| 📚 **Kho sách** | CRUD đầy đủ, tìm kiếm/lọc đa chiều, sort, phân trang |
| 👥 **Độc giả** | Quản lý thẻ, bản đồ phân bố, lịch sử mượn, thống kê phạt/đã trả |
| 📋 **Mượn/Trả** | Tạo phiếu, xác nhận trả, tự động tính phí 5.000đ/ngày quá hạn |
| 🔔 **Thông báo** | Tự động tạo alert quá hạn & sắp đến hạn (2 ngày), đánh dấu đã đọc |
| 💰 **Phí phạt** | Danh sách phạt, thu tiền (tiền mặt/chuyển khoản/thẻ), thống kê |
| 📑 **Đặt trước** | Đặt trước sách chưa có, quản lý trạng thái |
| 📈 **Báo cáo** | Phí phạt theo tháng, hoạt động 30 ngày, phân bố quá hạn, top độc giả, top danh mục |
| 📥 **Xuất CSV** | Xuất phiếu mượn / độc giả / kho sách (UTF-8 BOM, mở được Excel) |
| 🔍 **API GIS** | `/api/branches/geojson/`, `/api/branches/nearest/?lat=&lng=`, `/api/readers/heatmap/` |
| ⚡ **Autocomplete** | `/api/autocomplete/books/`, `/api/autocomplete/readers/` |

## Cài đặt nhanh

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data          # 5 chi nhánh, 8 danh mục, 15 sách, 10 độc giả, 20 phiếu
python manage.py runserver
```

→ http://127.0.0.1:8000 | admin: **admin / admin123**

## Cấu trúc

```
library_gis/
├── library_project/
│   ├── settings.py          # Cấu hình Django
│   └── urls.py
├── library_app/
│   ├── models.py            # Branch, Category, Book, Reader, BorrowRecord,
│   │                        # FinePayment, BookReservation, Notification
│   ├── views.py             # ~650 dòng — tất cả views + 6 API endpoints
│   ├── urls.py              # 32 URL patterns
│   ├── forms.py             # BookForm, ReaderForm, BorrowForm,
│   │                        # FinePaymentForm, ReservationForm
│   ├── admin.py             # Admin cho 8 models
│   ├── templates/           # 20 HTML templates — dark theme
│   └── management/commands/
│       └── seed_data.py     # Dữ liệu mẫu thực tế TP.HCM
├── manage.py
└── requirements.txt
```

## GIS — tìm chi nhánh gần nhất

```
GET /api/branches/nearest/?lat=10.776&lng=106.700
→ {"branches": [{"name": "...", "distance_km": 0.42, ...}, ...]}
```

Frontend gọi `navigator.geolocation.getCurrentPosition()` rồi fetch URL trên.

## Nâng cấp PostGIS (full spatial queries)

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        ...
    }
}
INSTALLED_APPS += ['django.contrib.gis']
```
