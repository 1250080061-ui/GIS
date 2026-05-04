from django import forms
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import (
    Book,
    Reader,
    BorrowRecord,
    FinePayment,
    BookReservation,
    LibraryLocation,
    LibraryBranch,
)

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)

class BookForm(forms.ModelForm):
    preview_pages = MultipleFileField(
    required=False,
    widget=MultipleFileInput(attrs={
        'multiple': True,
        'accept': 'image/*'
    }),
    label='Trang xem trước'
)

    class Meta:
        model = Book
        fields = [
            "isbn",
            "title",
            "author",
            "publisher",
            "publish_year",
            "category",
            "description",
            "cover_image",
            "total_copies",
            "available_copies",
            "language",
            "pages",
            "preview_page_1",
            "preview_page_2",
            "preview_page_3",
            "preview_page_4",
        ]


class ReaderForm(forms.ModelForm):
    class Meta:
        model = Reader
        fields = [
            "card_number",
            "full_name",
            "gender",
            "date_of_birth",
            "phone",
            "email",
            "address",
            "card_issue_date",
            "card_expiry_date",
            "status",
            "photo",
        ]
        labels = {
            "card_number": "Mã thẻ",
            "full_name": "Họ tên",
            "gender": "Giới tính",
            "date_of_birth": "Ngày sinh",
            "phone": "Số điện thoại",
            "email": "Email",
            "address": "Địa chỉ",
            "card_issue_date": "Ngày cấp thẻ",
            "card_expiry_date": "Ngày hết hạn",
            "status": "Trạng thái",
            "photo": "Ảnh",
        }
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "card_issue_date": forms.DateInput(attrs={"type": "date"}),
            "card_expiry_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["card_issue_date"].initial = timezone.now().date()
            self.fields["card_expiry_date"].initial = timezone.now().date() + timedelta(
                days=365
            )


class BorrowForm(forms.ModelForm):
    class Meta:
        model = BorrowRecord
        fields = ["reader", "book", "borrow_date", "due_date", "notes"]
        labels = {
            "reader": "Người đọc",
            "book": "Sách",
            "borrow_date": "Ngày mượn",
            "due_date": "Hạn trả",
            "notes": "Ghi chú",
        }
        widgets = {
            "borrow_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["borrow_date"].initial = timezone.now().date()
            self.fields["due_date"].initial = timezone.now().date() + timedelta(days=14)
        self.fields["book"].queryset = Book.objects.filter(available_copies__gt=0)
        self.fields["reader"].queryset = Reader.objects.filter(status="active")


class FinePaymentForm(forms.ModelForm):
    class Meta:
        model = FinePayment
        fields = ["method", "note"]
        widgets = {"note": forms.Textarea(attrs={"rows": 2})}


class ReservationForm(forms.ModelForm):
    class Meta:
        model = BookReservation
        fields = ["reader", "book", "expires_at", "note"]
        labels = {
            "reader": "Người đọc",
            "book": "Sách",
            "expires_at": "Ngày đặt",
            "note": "Ghi chú",
        }
        widgets = {
            "expires_at": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["expires_at"].initial = timezone.now().date() + timedelta(
                days=7
            )
        self.fields["reader"].queryset = Reader.objects.filter(status="active")


class LibraryLocationForm(forms.ModelForm):
    class Meta:
        model = LibraryLocation
        fields = [
            "name",
            "province",
            "address",
            "latitude",
            "longitude",
            "library_type",
            "phone",
            "website",
            "open_time",
            "description",
            "is_active",
        ]
        labels = {
            "name": "Tên thư viện",
            "province": "Tỉnh/Thành",
            "address": "Địa chỉ",
            "latitude": "Vĩ độ",
            "longitude": "Kinh độ",
            "phone": "Số điện thoại",
            "website": "Website",
            "open_time": "Giờ mở cửa",
            "description": "Mô tả",
            "is_active": "Đang hoạt động",
            "library_type": "Loại thư viện",
        }
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "latitude": forms.NumberInput(
                attrs={"step": "any", "placeholder": "Ví dụ: 10.776889"}
            ),
            "longitude": forms.NumberInput(
                attrs={"step": "any", "placeholder": "Ví dụ: 106.700806"}
            ),
        }


class LibraryBranchForm(forms.ModelForm):
    class Meta:
        model = LibraryBranch
        fields = [
            "library",
            "name",
            "address",
            "latitude",
            "longitude",
            "phone",
            "open_time",
            "is_active",
        ]
        labels = {
            "library": "Thư viện chính",
            "name": "Tên chi nhánh",
            "address": "Địa chỉ chi nhánh",
            "latitude": "Vĩ độ",
            "longitude": "Kinh độ",
            "phone": "Số điện thoại",
            "open_time": "Giờ mở cửa",
            "is_active": "Đang hoạt động",
        }
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "latitude": forms.NumberInput(
                attrs={"step": "any", "placeholder": "Ví dụ: 10.776889"}
            ),
            "longitude": forms.NumberInput(
                attrs={"step": "any", "placeholder": "Ví dụ: 106.700806"}
            ),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=False, label="Email")
    first_name = forms.CharField(max_length=150, required=False, label="Họ")
    last_name = forms.CharField(max_length=150, required=False, label="Tên")
    is_staff = forms.BooleanField(required=False, label="Là thủ thư (Staff)")
    is_superuser = forms.BooleanField(required=False, label="Là quản trị viên")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2", "is_staff", "is_superuser"]


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "is_staff", "is_superuser"]
        labels = {
            "username": "Tên đăng nhập",
            "first_name": "Họ",
            "last_name": "Tên",
            "email": "Email",
            "is_active": "Kích hoạt",
            "is_staff": "Là thủ thư (Staff)",
            "is_superuser": "Là quản trị viên",
        }