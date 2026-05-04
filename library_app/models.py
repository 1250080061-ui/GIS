from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#1e6fbf")
    icon = models.CharField(max_length=50, default="book")

    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục sách"

    def __str__(self):
        return self.name


class Book(models.Model):
    isbn = models.CharField(max_length=13, unique=True, verbose_name="ISBN")
    title = models.CharField(max_length=300, verbose_name="Tên sách")
    author = models.CharField(max_length=200, verbose_name="Tác giả")
    publisher = models.CharField(max_length=200, verbose_name="NXB")
    publish_year = models.IntegerField(verbose_name="Năm xuất bản")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    description = models.TextField(blank=True, verbose_name="Mô tả")
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    total_copies = models.PositiveIntegerField(default=1, verbose_name="Tổng số bản")
    available_copies = models.PositiveIntegerField(default=1, verbose_name="Sách có sẵn")
    language = models.CharField(max_length=50, default="Tiếng Việt")
    pages = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    preview_page_1 = models.ImageField(upload_to='book_previews/', blank=True, null=True, verbose_name="Trang xem trước 1")
    preview_page_2 = models.ImageField(upload_to='book_previews/', blank=True, null=True, verbose_name="Trang xem trước 2")
    preview_page_3 = models.ImageField(upload_to='book_previews/', blank=True, null=True, verbose_name="Trang xem trước 3")
    preview_page_4 = models.ImageField(upload_to='book_previews/', blank=True, null=True, verbose_name="Trang xem trước 4")

    class Meta:
        verbose_name = "Sách"
        verbose_name_plural = "Kho sách"

    def __str__(self):
        return f"{self.title} - {self.author}"

    @property
    def is_available(self):
        return self.available_copies > 0


class Reader(models.Model):
    GENDER_CHOICES = [('M', 'Nam'), ('F', 'Nữ'), ('O', 'Khác')]
    STATUS_CHOICES = [('active', 'Hoạt động'), ('suspended', 'Tạm Khóa'), ('expired', 'Hết hạn')]

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reader_profile')
    card_number = models.CharField(max_length=20, unique=True, verbose_name="Ma the")
    full_name = models.CharField(max_length=200, verbose_name="Ho ten")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    date_of_birth = models.DateField(verbose_name="Ngay sinh")
    phone = models.CharField(max_length=15, verbose_name="So dien thoai")
    email = models.EmailField(verbose_name="Email")
    address = models.TextField(verbose_name="Dia chi")
    card_issue_date = models.DateField(default=timezone.now)
    card_expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    photo = models.ImageField(upload_to='readers/', blank=True, null=True)
    home_latitude = models.FloatField(null=True, blank=True, verbose_name="Vĩ độ nhà")
    home_longitude = models.FloatField(null=True, blank=True, verbose_name="Kinh độ nhà")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Doc gia"
        verbose_name_plural = "Doc gia"

    def __str__(self):
        return f"{self.card_number} - {self.full_name}"

    @property
    def is_card_valid(self):
        return self.card_expiry_date >= timezone.now().date() and self.status == 'active'


class BorrowRecord(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Dang muon'),
        ('returned', 'Da tra'),
        ('overdue', 'Qua han'),
        ('lost', 'Mat sach'),
    ]

    borrow_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE, related_name='borrow_records')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    borrow_date = models.DateField(default=timezone.now, verbose_name="Ngay muon")
    due_date = models.DateField(verbose_name="Han tra")
    return_date = models.DateField(null=True, blank=True, verbose_name="Ngay tra")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
    librarian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_borrows')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Phieu muon"
        verbose_name_plural = "Phieu muon/tra"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reader.full_name} - {self.book.title}"

    @property
    def is_overdue(self):
        if self.status == 'borrowed':
            return timezone.now().date() > self.due_date
        return False

    def save(self, *args, **kwargs):
        if self.is_overdue:
            self.status = 'overdue'
        super().save(*args, **kwargs)


class FinePayment(models.Model):
    PAYMENT_METHOD = [
        ('cash', 'Tien mat'),
        ('transfer', 'Chuyen khoan'),
        ('card', 'The ngan hang'),
    ]
    borrow_record = models.OneToOneField(BorrowRecord, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='cash')
    paid_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = "Thanh toan phat"

    def __str__(self):
        return f"Phat {self.amount} - {self.borrow_record}"


class BookReservation(models.Model):
    STATUS = [
        ('pending', 'Cho sach'),
        ('ready', 'San sang lay'),
        ('cancelled', 'Da huy'),
        ('fulfilled', 'Hoan thanh'),
    ]
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations')
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = "Dat truoc sach"
        ordering = ['-reserved_at']

    def __str__(self):
        return f"{self.reader.full_name} - {self.book.title}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('overdue', 'Qua han tra'),
        ('due_soon', 'Sap den han'),
        ('fine', 'Phi phat'),
        ('system', 'He thong'),
    ]
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    borrow_record = models.ForeignKey(BorrowRecord, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Thong bao"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
class LibraryLocation(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tên thư viện")
    province = models.CharField(max_length=100, verbose_name="Tỉnh/Thành")
    address = models.TextField(verbose_name="Địa chỉ")
    LIBRARY_TYPE_CHOICES = [
        ('public', 'Công cộng'),
        ('university', 'Đại học'),
        ('national', 'Quốc gia'),
        ('provincial', 'Tỉnh/Thành phố'),
        ('specialized', 'Chuyên ngành'),
    ]
    
    library_type = models.CharField(
        max_length=20,
        choices=LIBRARY_TYPE_CHOICES,
        default='public',
        verbose_name='Loại thư viện'
    )
    latitude = models.FloatField(verbose_name="Vĩ độ")
    longitude = models.FloatField(verbose_name="Kinh độ")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")
    website = models.URLField(blank=True, verbose_name="Website")
    open_time = models.CharField(max_length=100, blank=True, verbose_name="Giờ mở cửa")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    image = models.ImageField(upload_to='libraries/', blank=True, null=True, verbose_name="Hình ảnh")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Thư viện"
        verbose_name_plural = "Thư viện toàn quốc"
        ordering = ['province', 'name']

    def __str__(self):
        return f"{self.name} - {self.province}"

class LibraryBranch(models.Model):
    library = models.ForeignKey(
        LibraryLocation,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name="Thư viện chính"
    )
    name = models.CharField(max_length=255, verbose_name="Tên chi nhánh")
    address = models.TextField(verbose_name="Địa chỉ chi nhánh")
    latitude = models.FloatField(verbose_name="Vĩ độ")
    longitude = models.FloatField(verbose_name="Kinh độ")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")
    open_time = models.CharField(max_length=100, blank=True, verbose_name="Giờ mở cửa")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chi nhánh thư viện"
        verbose_name_plural = "Chi nhánh thư viện"
        ordering = ['library__name', 'name']

    def __str__(self):
        return f"{self.library.name} - {self.name}"    