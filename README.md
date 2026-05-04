# 📚 LibraryGIS — Hệ thống quản lý thư viện tích hợp GIS

# HƯỚNG DẪN CÀI ĐẶT DỰ ÁN LIBRARY-GIS

Hệ thống quản lý thư viện thông minh tích hợp bản đồ GIS.

## 1. Yêu cầu hệ thống
* **Python**: Phiên bản 3.10 trở lên.
* **SQL Server**: Bản Express hoặc Developer.
* **SSMS**: SQL Server Management Studio.

## 2. Khôi phục Cơ sở dữ liệu (Database)
1. Mở SSMS và kết nối vào Server.
2. Chuột phải vào **Databases** -> **New Database** -> Đặt tên là `LibraryGIS_DB`.
3. Mở file script `.sql` của dự án, nhấn **Execute** để tạo bảng và dữ liệu.

## 3. Cài đặt mã nguồn (Source Code)
Mở Terminal tại thư mục dự án và chạy các lệnh sau:

### 3.1. Tạo và kích hoạt môi trường ảo
```bash
python -m venv venv
# Kích hoạt trên Windows:
venv\Scripts\activate

### 3.2. Cài đặt thư viện cần thiết
pip install django pandas openpyxl pillow pyodbc django-mssql-backend


#### 3.3. Cấu hình kết nối Database
Mở file library_project/settings.py, tìm mục DATABASES và cập nhật:
- HOST: Điền tên Server SQL của bạn (Ví dụ: localhost\SQLEXPRESS).
- NAME: LibraryGIS_DB.

##### 3.4. Khởi chạy ứng dụng
- Kiểm tra kết nối và cấu trúc: python manage.py migrate
- Chạy server: python manage.py runserver
