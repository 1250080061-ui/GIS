from django.contrib import admin
from .models import Category, Book, Reader, BorrowRecord, FinePayment, BookReservation, Notification, LibraryLocation, LibraryBranch


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'isbn', 'category', 'available_copies', 'total_copies']
    list_filter = ['category', 'language']
    search_fields = ['title', 'author', 'isbn']
    list_editable = ['available_copies']

@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    list_display = ['card_number', 'full_name', 'phone', 'status', 'card_expiry_date']
    list_filter = ['status', 'gender']
    search_fields = ['full_name', 'card_number', 'phone', 'email']

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ['reader', 'book', 'borrow_date', 'due_date', 'return_date', 'status', 'fine_amount']
    list_filter = ['status']
    search_fields = ['reader__full_name', 'book__title']
    date_hierarchy = 'borrow_date'

@admin.register(FinePayment)
class FinePaymentAdmin(admin.ModelAdmin):
    list_display = ['borrow_record', 'amount', 'method', 'paid_at', 'received_by']
    list_filter = ['method']

@admin.register(BookReservation)
class BookReservationAdmin(admin.ModelAdmin):
    list_display = ['reader', 'book', 'reserved_at', 'expires_at', 'status']
    list_filter = ['status']
    search_fields = ['reader__full_name', 'book__title']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'reader', 'is_read', 'created_at']
    list_filter = ['type', 'is_read']
    search_fields = ['title', 'reader__full_name']

@admin.register(LibraryLocation)
class LibraryLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'province', 'phone', 'is_active')
    search_fields = ('name', 'province', 'address')
    list_filter = ('province', 'is_active')
    
@admin.register(LibraryBranch)
class LibraryBranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'library', 'phone', 'is_active')
    search_fields = ('name', 'library__name', 'address')
    list_filter = ('library', 'is_active')