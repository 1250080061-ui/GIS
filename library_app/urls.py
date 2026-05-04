from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Books
    path('books/', views.book_list, name='book_list'),
    path('books/create/', views.book_create, name='book_create'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_edit, name='book_edit'),
    path('books/<int:pk>/delete/', views.book_delete, name='book_delete'),
    path('books/bulk-import/', views.book_bulk_import, name='book_bulk_import'),
    path('books/import-single/', views.book_import_single, name='book_import_single'),

    # Readers
    path('readers/', views.reader_list, name='reader_list'),
    path('readers/create/', views.reader_create, name='reader_create'),
    path('readers/<int:pk>/', views.reader_detail, name='reader_detail'),
    path('readers/<int:pk>/edit/', views.reader_edit, name='reader_edit'),

    # Borrows
    path('borrows/', views.borrow_list, name='borrow_list'),
    path('borrows/create/', views.borrow_create, name='borrow_create'),
    path('borrows/<int:pk>/return/', views.return_book, name='return_book'),

    # Fines
    path('fines/', views.fine_list, name='fine_list'),
    path('fines/<int:pk>/pay/', views.pay_fine, name='pay_fine'),
    path('fines/export/csv/', views.export_fines_csv, name='export_fines_csv'),

    # Reservations
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/create/', views.reservation_create, name='reservation_create'),

    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),

    # Reports
    path('reports/', views.report_overview, name='report_overview'),

    # Export CSV
    path('export/borrows/', views.export_borrows_csv, name='export_borrows'),
    path('export/readers/', views.export_readers_csv, name='export_readers'),
    path('export/books/', views.export_books_csv, name='export_books'),
    path('export/', views.export_center, name='export_center'),

    # Export Excel
    path('books-excel/', views.books_excel, name='books_excel'),
    path('export-books-excel/', views.export_books_excel, name='export_books_excel'),

    # API
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/readers/geojson/', views.api_readers_geojson, name='api_readers_geojson'),
    path('api/libraries-geojson/', views.api_libraries_geojson, name='api_libraries_geojson'),

    # GIS / Map
    path('map/', views.borrow_map, name='borrow_map'),
    path('libraries/map/', views.library_map, name='library_map'),
    path('libraries/create/', views.library_create, name='library_create'),
    path('branches/create/', views.branch_create, name='branch_create'),
    path('branches/<int:pk>/', views.branch_detail, name='branch_detail'),

    # Personal (non-staff)
    path('my-borrows/', views.my_borrows, name='my_borrows'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('my-profile/', views.my_profile, name='my_profile'),

    # Users management
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    # Auth
    path('accounts/register/', views.register_view, name='register'),

    # Info pages
    path('gioi-thieu/', views.about_page, name='about_page'),

    # Misc / Dev preview
    path('test-403/', views.test_403, name='test_403'),
    path('test-email/', views.test_email),
    path('preview/404/', views.preview_404, name='preview_404'),
    path('preview/403/', views.preview_403, name='preview_403'),
]
