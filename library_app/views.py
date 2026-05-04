from .decorators import admin_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum, F
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied
import pandas as pd
import json, csv
from .forms import RegisterForm
from django.core.mail import send_mail
from .models import (
    Category,
    Book,
    Reader,
    BorrowRecord,
    FinePayment,
    BookReservation,
    Notification,
    LibraryLocation,
    LibraryBranch,
)


# ─── HELPERS ───


def _auto_flag_overdue():
    today = timezone.now().date()
    for br in BorrowRecord.objects.filter(status="borrowed", due_date__lt=today):
        br.status = "overdue"
        br.save(update_fields=["status"])
        Notification.objects.get_or_create(
            borrow_record=br,
            type="overdue",
            defaults={
                "reader": br.reader,
                "title": f"Sach qua han: {br.book.title}",
                "message": f'{br.reader.full_name} qua han tra "{br.book.title}" tu {br.due_date:%d/%m/%Y}.',
            },
        )
    for br in BorrowRecord.objects.filter(
        status="borrowed", due_date=today + timedelta(days=2)
    ):
        Notification.objects.get_or_create(
            borrow_record=br,
            type="due_soon",
            defaults={
                "reader": br.reader,
                "title": f"Sap den han: {br.book.title}",
                "message": f"Sach se den han tra ngay {br.due_date:%d/%m/%Y}.",
            },
        )


def _assign_preview_pages(book, files):
    preview_files = files.getlist('preview_pages')[:4]

    if not preview_files:
        return

    book.preview_page_1 = None
    book.preview_page_2 = None
    book.preview_page_3 = None
    book.preview_page_4 = None

    if len(preview_files) > 0:
        book.preview_page_1 = preview_files[0]
    if len(preview_files) > 1:
        book.preview_page_2 = preview_files[1]
    if len(preview_files) > 2:
        book.preview_page_3 = preview_files[2]
    if len(preview_files) > 3:
        book.preview_page_4 = preview_files[3]

# ─── DASHBOARD ───


@login_required
def dashboard(request):
    _auto_flag_overdue()
    today = timezone.now().date()
    this_month = today.replace(day=1)

    stats = {
        "total_books": Book.objects.count(),
        "total_readers": Reader.objects.filter(status="active").count(),
        "borrowed_today": BorrowRecord.objects.filter(borrow_date=today).count(),
        "overdue_count": BorrowRecord.objects.filter(status="overdue").count(),
        "returned_today": BorrowRecord.objects.filter(return_date=today).count(),
        "new_readers_month": Reader.objects.filter(
            card_issue_date__gte=this_month
        ).count(),
        "available_books": Book.objects.filter(available_copies__gt=0).count(),
        "total_fine_unpaid": BorrowRecord.objects.filter(status="overdue").aggregate(
            s=Sum("fine_amount")
        )["s"]
        or 0,
        "reservations_pending": BookReservation.objects.filter(
            status="pending"
        ).count(),
        "unread_notifications": Notification.objects.filter(is_read=False).count(),
        "books_borrowed_total": BorrowRecord.objects.count(),
    }

    monthly_data = []
    for i in range(11, -1, -1):
        d = today - timedelta(days=30 * i)
        ms = d.replace(day=1)
        me = (
            ms.replace(month=ms.month % 12 + 1, day=1)
            if ms.month < 12
            else ms.replace(year=ms.year + 1, month=1, day=1)
        ) - timedelta(days=1)
        monthly_data.append(
            {
                "month": ms.strftime("%m/%Y"),
                "borrowed": BorrowRecord.objects.filter(
                    borrow_date__range=[ms, me]
                ).count(),
                "returned": BorrowRecord.objects.filter(
                    return_date__range=[ms, me]
                ).count(),
            }
        )

    cat_data = list(
        Category.objects.annotate(cnt=Count("books"))
        .filter(cnt__gt=0)
        .values("name", "color", "cnt")
        .order_by("-cnt")
    )
    popular_books = Book.objects.annotate(
        borrow_count=Count("borrow_records")
    ).order_by("-borrow_count")[:8]
    recent_borrows = BorrowRecord.objects.select_related("reader", "book").order_by(
        "-created_at"
    )[:12]
    overdue_list = (
        BorrowRecord.objects.filter(status="overdue")
        .select_related("reader", "book")
        .order_by("due_date")[:10]
    )
    notifications = Notification.objects.filter(is_read=False).order_by("-created_at")[
        :8
    ]

    return render(
        request,
        "library_app/dashboard.html",
        {
            "stats": stats,
            "monthly_data": json.dumps(monthly_data),
            "cat_data": json.dumps(cat_data),
            "popular_books": popular_books,
            "recent_borrows": recent_borrows,
            "overdue_list": overdue_list,
            "notifications": notifications,
        },
    )


# ─── BOOKS ───


@login_required
def book_list(request):
    qs = Book.objects.select_related("category").all()
    search = request.GET.get("search", "").strip()
    cat_id = request.GET.get("category", "")
    available = request.GET.get("available", "")
    sort = request.GET.get("sort", "-created_at")
    
    if search:
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(author__icontains=search) |
            Q(isbn__icontains=search)
        )
    
    if cat_id:
        qs = qs.filter(category_id=cat_id)
    
    if available:
        qs = qs.filter(available_copies__gt=0)
    
    if sort in ["title", "-title", "-created_at", "publish_year", "-publish_year"]:
        qs = qs.order_by(sort)
    
    # Pagination logic
    page = request.GET.get("page", 1)
    paginator = Paginator(qs, 5)  
    try:
        books = paginator.page(page)
    except PageNotAnInteger:
        books = paginator.page(1)
    except EmptyPage:
        books = paginator.page(paginator.num_pages)

    return render(request, "library_app/book_list.html", {
        "books": books,
        "categories": Category.objects.all(),
        "search": search,
        "total_count": qs.count(),
        "sort": sort,
        "cat_id": cat_id,
    })


@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    history = (
        BorrowRecord.objects.filter(book=book)
        .select_related("reader")
        .order_by("-borrow_date")
    )
    return render(
        request,
        "library_app/book_detail.html",
        {
            "book": book,
            "borrow_history": history[:15],
            "active_borrows": history.filter(status__in=["borrowed", "overdue"]),
            "reservations": BookReservation.objects.filter(
                book=book, status__in=["pending", "ready"]
            ),
        },
    )


@login_required
def book_create(request):
    from .forms import BookForm

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            _assign_preview_pages(book, request.FILES)
            book.save()
            messages.success(request, f'Da them sach "{book.title}"!')
            return redirect('book_detail', pk=book.pk)
        else:
            print("BOOK CREATE ERRORS:", form.errors)
            messages.error(request, 'Form thêm sách đang lỗi.')
    else:
        form = BookForm()

    return render(request, 'library_app/book_form.html', {
        'form': form,
        'title': 'Them sach moi',
        'book': None,
    })


@admin_required
def book_edit(request, pk):
    from .forms import BookForm
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save(commit=False)
            _assign_preview_pages(book, request.FILES)
            book.save()
            messages.success(request, 'Cap nhat sach thanh cong!')
            return redirect('book_detail', pk=book.pk)
        else:
            print("BOOK EDIT ERRORS:", form.errors)
            messages.error(request, 'Form sửa sách đang lỗi.')
    else:
        form = BookForm(instance=book)

    return render(request, 'library_app/book_form.html', {
        'form': form,
        'title': 'Sua sach',
        'book': book,
    })


@admin_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        title = book.title
        book.delete()
        messages.success(request, f'Da xoa "{title}".')
        return redirect("book_list")
    return render(request, "library_app/confirm_delete.html", {"obj_name": book.title})


@admin_required
def book_bulk_import(request):
    return render(
        request,
        "library_app/book_bulk_import.html",
        {"categories": Category.objects.all()},
    )


@admin_required
def book_import_single(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed"})
    try:
        isbn = request.POST.get("isbn", "").strip()
        title = request.POST.get("title", "").strip()
        author = request.POST.get("author", "").strip()
        publisher = request.POST.get("publisher", "").strip()
        description = request.POST.get("description", "").strip()
        language = request.POST.get("language", "Tieng Viet")
        cover_url = request.POST.get("cover_url", "").strip()
        category_id = request.POST.get("category", None)

        try:
            publish_year = int(request.POST.get("publish_year", 0))
        except:
            publish_year = 2024
        try:
            pages = int(request.POST.get("pages", 0)) or None
        except:
            pages = None
        try:
            total = int(request.POST.get("total_copies", 1))
            available = int(request.POST.get("available_copies", 1))
        except:
            total = available = 1

        if not isbn or not title:
            return JsonResponse({"ok": False, "error": "Thieu ISBN hoac ten sach"})

        if Book.objects.filter(isbn=isbn).exists():
            return JsonResponse({"ok": False, "error": f"ISBN {isbn} da ton tai"})

        book = Book(
            isbn=isbn,
            title=title,
            author=author,
            publisher=publisher,
            publish_year=publish_year,
            description=description,
            language=language,
            pages=pages,
            total_copies=total,
            available_copies=available,
        )

        if category_id:
            try:
                book.category_id = int(category_id)
            except:
                pass

        if cover_url:
            try:
                import urllib.request
                from django.core.files.base import ContentFile

                ext = cover_url.split(".")[-1].split("?")[0]
                ext = ext if ext in ["jpg", "jpeg", "png", "webp"] else "jpg"
                filename = f"{isbn}.{ext}"
                with urllib.request.urlopen(cover_url, timeout=5) as resp:
                    image_data = resp.read()
                book.cover_image.save(filename, ContentFile(image_data), save=False)
            except:
                pass

        book.save()
        return JsonResponse({"ok": True, "id": book.pk, "title": book.title})

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


# ─── READERS ───


@login_required
def reader_list(request):
    # Lấy tất cả độc giả và áp dụng các bộ lọc tìm kiếm và trạng thái
    qs = Reader.objects.all()
    search = request.GET.get("search", "").strip()  # Lấy từ khóa tìm kiếm từ URL
    status = request.GET.get("status", "")  # Lấy bộ lọc trạng thái từ URL

    # Áp dụng bộ lọc tìm kiếm nếu có
    if search:
        qs = qs.filter(
            Q(full_name__icontains=search) |
            Q(card_number__icontains=search) |
            Q(phone__icontains=search)
        )

    # Áp dụng bộ lọc trạng thái nếu có
    if status:
        qs = qs.filter(status=status)

    # Cấu hình phân trang: 25 bản ghi mỗi trang
    page_number = request.GET.get("page", 1)  # Lấy số trang hiện tại từ URL
    paginator = Paginator(qs, 2)  # Chia queryset thành các trang với 25 bản ghi mỗi trang
    page = paginator.get_page(page_number)  # Lấy dữ liệu của trang hiện tại

    # Truyền dữ liệu vào template
    return render(
        request,
        "library_app/reader_list.html",
        {
            "readers": page,  # Truyền đối tượng phân trang vào template
            "search": search,  # Truyền từ khóa tìm kiếm vào template
            "status": status,  # Truyền bộ lọc trạng thái vào template
            "total_count": qs.count(),  # Tổng số bản ghi (sử dụng trong phân trang)
        }
    )

@login_required
def reader_detail(request, pk):
    reader = get_object_or_404(Reader, pk=pk)
    records = (
        BorrowRecord.objects.filter(reader=reader)
        .select_related("book")
        .order_by("-borrow_date")
    )
    total_fine = records.aggregate(s=Sum("fine_amount"))["s"] or 0
    paid_fine = (
        FinePayment.objects.filter(borrow_record__reader=reader).aggregate(
            s=Sum("amount")
        )["s"]
        or 0
    )
    return render(
        request,
        "library_app/reader_detail.html",
        {
            "reader": reader,
            "borrow_records": records[:25],
            "active_borrows": records.filter(status__in=["borrowed", "overdue"]),
            "total_borrowed": records.count(),
            "total_fine": total_fine,
            "paid_fine": paid_fine,
            "unpaid_fine": total_fine - paid_fine,
            "notifications": Notification.objects.filter(reader=reader).order_by(
                "-created_at"
            )[:10],
        },
    )


@admin_required
def reader_create(request):
    from .forms import ReaderForm

    if request.method == "POST":
        form = ReaderForm(request.POST, request.FILES)
        if form.is_valid():
            r = form.save()
            messages.success(request, f"Cap the cho {r.full_name} ({r.card_number})!")
            return redirect("reader_detail", pk=r.pk)
    else:
        form = ReaderForm()
    return render(
        request, "library_app/reader_form.html", {"form": form, "title": "Cap the moi"}
    )


@admin_required
def reader_edit(request, pk):
    from .forms import ReaderForm

    reader = get_object_or_404(Reader, pk=pk)
    if request.method == "POST":
        form = ReaderForm(request.POST, request.FILES, instance=reader)
        if form.is_valid():
            form.save()
            messages.success(request, "Cap nhat thanh cong!")
            return redirect("reader_detail", pk=reader.pk)
    else:
        form = ReaderForm(instance=reader)
    return render(
        request,
        "library_app/reader_form.html",
        {"form": form, "title": "Sua doc gia", "reader": reader},
    )


# ─── BORROW / RETURN ───


@admin_required
def borrow_list(request):
    # Tạo truy vấn
    qs = BorrowRecord.objects.select_related("reader", "book")
    
    # Lọc theo trạng thái, tìm kiếm và ngày
    status = request.GET.get("status", "")
    search = request.GET.get("search", "").strip()
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    # Lọc theo trạng thái
    if status:
        qs = qs.filter(status=status)

    # Lọc theo tìm kiếm
    if search:
        qs = qs.filter(
            Q(reader__full_name__icontains=search) |
            Q(book__title__icontains=search) |
            Q(reader__card_number__icontains=search)
        )

    # Lọc theo ngày mượn
    if date_from:
        qs = qs.filter(borrow_date__gte=date_from)
    if date_to:
        qs = qs.filter(borrow_date__lte=date_to)

    # Phân trang
    page = Paginator(qs.order_by("-created_at"), 25).get_page(request.GET.get("page", 1))

    return render(
        request,
        "library_app/borrow_list.html",
        {
            "borrows": page,
            "overdue_count": BorrowRecord.objects.filter(status="overdue").count(),
            "status_filter": status,
            "search": search,
            "total_count": qs.count(),
            "branches": LibraryBranch.objects.filter(is_active=True),
        },
    )


@admin_required
def borrow_create(request):
    from .forms import BorrowForm

    initial = {k: request.GET.get(k, "") for k in ["book", "reader"]}
    if request.method == "POST":
        form = BorrowForm(request.POST)
        if form.is_valid():
            borrow = form.save(commit=False)
            borrow.librarian = request.user
            if not borrow.reader.is_card_valid:
                messages.error(request, "The doc gia khong hop le hoac da het han!")
            elif borrow.book.available_copies <= 0:
                messages.error(request, "Sach hien khong co san!")
            else:
                borrow.book.available_copies -= 1
                borrow.book.save(update_fields=["available_copies"])
                borrow.save()
                messages.success(request, "Tao phieu muon thanh cong!")
                return redirect("borrow_list")
    else:
        form = BorrowForm(initial=initial)
    return render(
        request,
        "library_app/borrow_form.html",
        {"form": form, "title": "Tao phieu muon moi"},
    )


@admin_required
def return_book(request, pk):
    borrow = get_object_or_404(BorrowRecord, pk=pk)
    today = timezone.now().date()
    if borrow.status == "returned":
        messages.warning(request, "Phieu nay da tra roi.")
        return redirect("borrow_list")

    overdue_days = (
        max(0, (today - borrow.due_date).days) if today > borrow.due_date else 0
    )
    fine = overdue_days * 5000

    if request.method == "POST":
        borrow.return_date = today
        borrow.status = "returned"
        borrow.fine_amount = fine
        borrow.save()
        borrow.book.available_copies = F("available_copies") + 1
        borrow.book.save(update_fields=["available_copies"])
        if fine > 0:
            Notification.objects.create(
                reader=borrow.reader,
                borrow_record=borrow,
                type="fine",
                title=f"Phi phat {fine:,}d - {borrow.book.title}",
                message=f"Qua han {overdue_days} ngay. Phi: {fine:,}d.",
            )
        messages.success(request, f"Da tra sach. Phi phat: {fine:,}d")
        return redirect("borrow_list")

    return render(
        request,
        "library_app/return_confirm.html",
        {
            "borrow": borrow,
            "overdue_days": overdue_days,
            "fine": fine,
        },
    )


# ─── FINES ───


@login_required
def fine_list(request):
    paid = request.GET.get("paid", "")
    search = request.GET.get("search", "").strip()
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    fines = BorrowRecord.objects.filter(fine_amount__gt=0).select_related("reader", "book")

    if paid == "1":
        fines = fines.filter(payment__isnull=False)  # Phí đã được thanh toán
    elif paid == "0":
        fines = fines.filter(payment__isnull=True)  # Phí chưa thanh toán

    if search:
        fines = fines.filter(
            Q(reader__full_name__icontains=search) |
            Q(reader__card_number__icontains=search) |
            Q(book__title__icontains=search)
        )

    if date_from:
        fines = fines.filter(due_date__gte=date_from)

    if date_to:
        fines = fines.filter(due_date__lte=date_to)

    # Phân trang: hiển thị 25 bản ghi trên mỗi trang
    page = Paginator(fines.order_by("-created_at"), 25).get_page(request.GET.get("page", 1))

    total_fine = fines.aggregate(s=Sum("fine_amount"))["s"] or 0
    total_paid = FinePayment.objects.aggregate(s=Sum("amount"))["s"] or 0
    total_records = fines.count()

    return render(
        request,
        "library_app/fine_list.html",
        {
            "fines": page,
            "paid_filter": paid,
            "search": search,
            "date_from": date_from,
            "date_to": date_to,
            "total_fine": total_fine,
            "total_paid": total_paid,
            "total_records": total_records,
        }
    )


@admin_required
def pay_fine(request, pk):
    from .forms import FinePaymentForm

    borrow = get_object_or_404(BorrowRecord, pk=pk)
    if hasattr(borrow, "payment"):
        messages.info(request, "Da thanh toan roi.")
        return redirect("fine_list")
    if request.method == "POST":
        form = FinePaymentForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.borrow_record = borrow
            p.amount = borrow.fine_amount
            p.received_by = request.user
            p.save()
            messages.success(request, f"Thanh toan {borrow.fine_amount:,}d thanh cong!")
            return redirect("fine_list")
    else:
        form = FinePaymentForm()
    return render(
        request, "library_app/pay_fine.html", {"borrow": borrow, "form": form}
    )


# ─── RESERVATIONS ───


from django.core.paginator import Paginator

@admin_required
def reservation_list(request):
    qs = BookReservation.objects.select_related("reader", "book")
    status = request.GET.get("status", "")

    if status:
        qs = qs.filter(status=status)

    # Phân trang: Lấy 25 kết quả mỗi trang
    page = Paginator(qs, 1).get_page(request.GET.get("page", 1))

    return render(
        request,
        "library_app/reservation_list.html",
        {
            "reservations": page,
            "status_filter": status,
        },
    )


@login_required
def reservation_create(request):
    from .forms import ReservationForm

    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            res = form.save()
            messages.success(request, f"Da dat truoc cho {res.reader.full_name}!")
            return redirect("reservation_list")
    else:
        form = ReservationForm(
            initial={k: request.GET.get(k) for k in ["book", "reader"]}
        )
    return render(
        request,
        "library_app/reservation_form.html",
        {"form": form, "title": "Dat truoc sach"},
    )


# ─── NOTIFICATIONS ───


@login_required
def notification_list(request):
    _auto_flag_overdue()

    if request.user.is_staff:
        notifs = Notification.objects.select_related("reader").order_by("-created_at")
        unread_count = Notification.objects.filter(is_read=False).count()
    else:
        reader = getattr(request.user, "reader_profile", None)
        if reader:
            notifs = (
                Notification.objects.filter(reader=reader)
                .select_related("reader")
                .order_by("-created_at")
            )
            unread_count = Notification.objects.filter(
                reader=reader, is_read=False
            ).count()
        else:
            notifs = Notification.objects.none()
            unread_count = 0

    page = Paginator(notifs, 30).get_page(request.GET.get("page", 1))
    return render(
        request,
        "library_app/notification_list.html",
        {
            "notifications": page,
            "unread_count": unread_count,
        },
    )


@login_required
def notification_mark_read(request, pk):
    Notification.objects.filter(pk=pk).update(is_read=True)
    return redirect("notification_list")


@admin_required
def notification_mark_all_read(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    messages.success(request, "Da danh dau tat ca la da doc.")
    return redirect("notification_list")


# ─── REPORTS ───


@admin_required
def report_overview(request):
    today = timezone.now().date()

    fine_monthly = []
    for i in range(5, -1, -1):
        d = today - timedelta(days=30 * i)
        ms = d.replace(day=1)
        me = (
            ms.replace(month=ms.month % 12 + 1, day=1)
            if ms.month < 12
            else ms.replace(year=ms.year + 1, month=1, day=1)
        ) - timedelta(days=1)
        total = (
            BorrowRecord.objects.filter(return_date__range=[ms, me]).aggregate(
                s=Sum("fine_amount")
            )["s"]
            or 0
        )
        fine_monthly.append({"month": ms.strftime("%m/%Y"), "total": int(total)})

    daily = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        daily.append(
            {
                "date": d.strftime("%d/%m"),
                "borrowed": BorrowRecord.objects.filter(borrow_date=d).count(),
                "returned": BorrowRecord.objects.filter(return_date=d).count(),
            }
        )

    aging = {
        "1-7 ngay": BorrowRecord.objects.filter(
            status="overdue", due_date__gte=today - timedelta(7)
        ).count(),
        "8-14 ngay": BorrowRecord.objects.filter(
            status="overdue",
            due_date__range=[today - timedelta(14), today - timedelta(8)],
        ).count(),
        "15-30 ngay": BorrowRecord.objects.filter(
            status="overdue",
            due_date__range=[today - timedelta(30), today - timedelta(15)],
        ).count(),
        "> 30 ngay": BorrowRecord.objects.filter(
            status="overdue", due_date__lt=today - timedelta(30)
        ).count(),
    }

    return render(
        request,
        "library_app/report_overview.html",
        {
            "fine_monthly": json.dumps(fine_monthly),
            "daily_data": json.dumps(daily),
            "aging": aging,
            "aging_json": json.dumps(list(aging.values())),
            "aging_labels": json.dumps(list(aging.keys())),
            "cat_borrows": Category.objects.annotate(
                cnt=Count("books__borrow_records")
            ).order_by("-cnt"),
            "top_readers": Reader.objects.annotate(
                cnt=Count("borrow_records")
            ).order_by("-cnt")[:10],
            "total_fine_collected": FinePayment.objects.aggregate(s=Sum("amount"))["s"]
            or 0,
            "total_fine_pending": BorrowRecord.objects.filter(
                status="overdue"
            ).aggregate(s=Sum("fine_amount"))["s"]
            or 0,
        },
    )


# ─── GIS: BAN DO PHAN BO NGUOI MUON SACH ───


@login_required
def borrow_map(request):
    readers_with_location = Reader.objects.filter(
        home_latitude__isnull=False, home_longitude__isnull=False
    ).annotate(borrow_count=Count("borrow_records"))

    return render(
        request,
        "library_app/borrow_map.html",
        {
            "total_readers": Reader.objects.count(),
            "total_borrows": BorrowRecord.objects.count(),
            "active_borrows": BorrowRecord.objects.filter(status="borrowed").count(),
            "overdue_borrows": BorrowRecord.objects.filter(status="overdue").count(),
        },
    )

def api_readers_geojson(request):
    readers = Reader.objects.filter(
        home_latitude__isnull=False,
        home_longitude__isnull=False,
    ).annotate(borrow_count=Count("borrow_records"))

    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [r.home_longitude, r.home_latitude],
            },
            "properties": {
                "name": r.full_name,
                "card": r.card_number,
                "borrow_count": r.borrow_count,
                "status": r.status,
                "address": r.address,
            },
        }
        for r in readers
    ]

    return JsonResponse({"type": "FeatureCollection", "features": features})

def api_libraries_geojson(request):
    search = request.GET.get("search", "").strip()
    province = request.GET.get("province", "").strip()

    libraries = LibraryLocation.objects.filter(is_active=True)
    branches = LibraryBranch.objects.filter(is_active=True).select_related("library")

    if search:
        libraries = libraries.filter(
            Q(name__icontains=search)
            | Q(address__icontains=search)
            | Q(province__icontains=search)
        )
        branches = branches.filter(
            Q(name__icontains=search)
            | Q(address__icontains=search)
            | Q(library__name__icontains=search)
        )

    if province:
        libraries = libraries.filter(province=province)
        branches = branches.filter(library__province=province)

    features = []

    for lib in libraries:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lib.longitude, lib.latitude],
                },
                "properties": {
                    "id": lib.id,
                    "name": lib.name,
                    "province": lib.province,
                    "address": lib.address,
                    "phone": lib.phone,
                    "website": lib.website,
                    "open_time": lib.open_time,
                    "description": lib.description,
                    "item_type": "library",
                    "parent_library": "",
                    "latitude": lib.latitude,
                    "longitude": lib.longitude,
                },
            }
        )

    for branch in branches:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [branch.longitude, branch.latitude],
                },
                "properties": {
                    "id": branch.id,
                    "name": branch.name,
                    "province": branch.library.province,
                    "address": branch.address,
                    "phone": branch.phone,
                    "website": "",
                    "open_time": branch.open_time,
                    "description": f"Chi nhánh của {branch.library.name}",
                    "item_type": "branch",
                    "parent_library": branch.library.name,
                    "latitude": branch.latitude,
                    "longitude": branch.longitude,
                },
            }
        )

    return JsonResponse({"type": "FeatureCollection", "features": features})

@admin_required
def library_create(request):
    from .forms import LibraryLocationForm

    if request.method == 'POST':
        form = LibraryLocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm thư viện thành công!')
            return redirect('library_map')
    else:
        form = LibraryLocationForm()

    return render(request, 'library_app/library_form.html', {
        'form': form,
        'title': 'Thêm thư viện',
        'form_type': 'library',
    })


@admin_required
def branch_create(request):
    from .forms import LibraryBranchForm

    if request.method == 'POST':
        form = LibraryBranchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm chi nhánh thành công!')
            return redirect('library_map')
    else:
        form = LibraryBranchForm()

    return render(request, 'library_app/library_form.html', {
        'form': form,
        'title': 'Thêm chi nhánh',
        'form_type': 'branch',
    })


# ─── EXPORT CSV ───

@admin_required
def export_center(request):
    export_type = request.GET.get('type', 'borrows')

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    category_id = request.GET.get('category', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    availability = request.GET.get('availability', '').strip()

    borrow_qs = BorrowRecord.objects.select_related('reader', 'book').order_by('-borrow_date')
    reader_qs = Reader.objects.order_by('card_number')
    book_qs = Book.objects.select_related('category').order_by('title')

    if export_type == 'borrows':
        if q:
            borrow_qs = borrow_qs.filter(
                Q(reader__full_name__icontains=q) |
                Q(reader__card_number__icontains=q) |
                Q(book__title__icontains=q)
            )
        if status:
            borrow_qs = borrow_qs.filter(status=status)
        if from_date:
            borrow_qs = borrow_qs.filter(borrow_date__date__gte=from_date)
        if to_date:
            borrow_qs = borrow_qs.filter(borrow_date__date__lte=to_date)

    elif export_type == 'readers':
        if q:
            reader_qs = reader_qs.filter(
                Q(full_name__icontains=q) |
                Q(card_number__icontains=q) |
                Q(email__icontains=q) |
                Q(phone__icontains=q)
            )
        if status:
            reader_qs = reader_qs.filter(status=status)

    elif export_type == 'books':
        if q:
            book_qs = book_qs.filter(
                Q(title__icontains=q) |
                Q(author__icontains=q) |
                Q(isbn__icontains=q)
            )
        if category_id:
            book_qs = book_qs.filter(category_id=category_id)
        if availability == 'available':
            book_qs = book_qs.filter(available_copies__gt=0)
        elif availability == 'out':
            book_qs = book_qs.filter(available_copies__lte=0)

    context = {
        'export_type': export_type,
        'q': q,
        'status': status,
        'category_id': category_id,
        'from_date': from_date,
        'to_date': to_date,
        'availability': availability,

        'borrow_preview': borrow_qs[:20],
        'reader_preview': reader_qs[:20],
        'book_preview': book_qs[:20],

        'borrow_count': borrow_qs.count(),
        'reader_count': reader_qs.count(),
        'book_count': book_qs.count(),

        'categories': Category.objects.order_by('name'),
    }
    return render(request, 'library_app/export_center.html', context)

@admin_required
def export_borrows_csv(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    from_date = request.GET.get("from_date", "").strip()
    to_date = request.GET.get("to_date", "").strip()

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="phieu_muon.csv"'
    w = csv.writer(response)

    VI = {
        "borrowed": "Dang muon",
        "returned": "Da tra",
        "overdue": "Qua han",
        "lost": "Mat sach",
    }

    w.writerow([
        "Ma phieu",
        "Ho ten",
        "Ma the",
        "Ten sach",
        "ISBN",
        "Ngay muon",
        "Han tra",
        "Ngay tra",
        "Trang thai",
        "Phi phat",
    ])

    borrows = BorrowRecord.objects.select_related("reader", "book").order_by("-borrow_date")

    if q:
        borrows = borrows.filter(
            Q(reader__full_name__icontains=q) |
            Q(reader__card_number__icontains=q) |
            Q(book__title__icontains=q) |
            Q(book__isbn__icontains=q)
        )

    if status:
        borrows = borrows.filter(status=status)

    if from_date:
        borrows = borrows.filter(borrow_date__date__gte=from_date)

    if to_date:
        borrows = borrows.filter(borrow_date__date__lte=to_date)
    
    for b in borrows:
        w.writerow([
            str(b.borrow_code)[:8].upper(),
            b.reader.full_name,
            b.reader.card_number,
            b.book.title,
            b.book.isbn,
            b.borrow_date.strftime("%d/%m/%Y"),
            b.due_date.strftime("%d/%m/%Y"),
            b.return_date.strftime("%d/%m/%Y") if b.return_date else "",
            VI.get(b.status, b.status),
            int(b.fine_amount),
        ])

    return response


@admin_required
def export_readers_csv(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="doc_gia.csv"'
    w = csv.writer(response)

    VI = {
        "active": "Hoat dong",
        "suspended": "Tam Khoa",
        "expired": "Het han",
    }

    w.writerow([
        "Ma the",
        "Ho ten",
        "Email",
        "Dien thoai",
        "Dia chi",
        "Trang thai",
    ])

    readers = Reader.objects.order_by("card_number")

    if q:
        readers = readers.filter(
            Q(full_name__icontains=q) |
            Q(card_number__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )

    if status:
        readers = readers.filter(status=status)

    for r in readers:
        w.writerow([
            r.card_number,
            r.full_name,
            r.email,
            r.phone,
            r.address,
            VI.get(r.status, r.status),
        ])

    return response


@admin_required
def export_books_csv(request):
    q = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()
    availability = request.GET.get("availability", "").strip()

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="kho_sach.csv"'
    w = csv.writer(response)

    w.writerow([
        "ISBN",
        "Ten sach",
        "Tac gia",
        "Danh muc",
        "Nha xuat ban",
        "Nam xuat ban",
        "Ngon ngu",
        "So trang",
        "Tong so ban",
        "So ban co san",
        "Mo ta",
    ])

    books = Book.objects.select_related("category").order_by("title")

    if q:
        books = books.filter(
            Q(title__icontains=q) |
            Q(author__icontains=q) |
            Q(isbn__icontains=q)
        )

    if category_id:
        books = books.filter(category_id=category_id)

    if availability == "available":
        books = books.filter(available_copies__gt=0)
    elif availability == "out":
        books = books.filter(available_copies__lte=0)

    for b in books:
        w.writerow([
            b.isbn,
            b.title,
            b.author,
            b.category.name if b.category else "",
            b.publisher,
            b.publish_year,
            b.language,
            b.pages if b.pages else "",
            b.total_copies,
            b.available_copies,
            b.description,
        ])

    return response


@admin_required
def export_fines_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="phi_phat.csv"'

    w = csv.writer(response)
    w.writerow(
        [
            "Ma phieu",
            "Doc gia",
            "Ma the",
            "Ten sach",
            "Han tra",
            "Ngay tra",
            "Phi phat",
            "Trang thai",
        ]
    )

    fines = (
        BorrowRecord.objects.filter(fine_amount__gt=0)
        .select_related("reader", "book")
        .order_by("-created_at")
    )

    for item in fines:
        w.writerow(
            [
                str(item.borrow_code)[:8].upper(),
                item.reader.full_name,
                item.reader.card_number,
                item.book.title,
                item.due_date.strftime("%d/%m/%Y") if item.due_date else "",
                item.return_date.strftime("%d/%m/%Y") if item.return_date else "",
                int(item.fine_amount),
                "Da thu" if hasattr(item, "payment") else "Chua thu",
            ]
        )

    return response


# ─── API ───


def api_stats(request):
    today = timezone.now().date()
    return JsonResponse(
        {
            "total_books": Book.objects.count(),
            "available_books": Book.objects.filter(available_copies__gt=0).count(),
            "total_readers": Reader.objects.filter(status="active").count(),
            "borrowed_today": BorrowRecord.objects.filter(borrow_date=today).count(),
            "overdue": BorrowRecord.objects.filter(status="overdue").count(),
            "unread_notifs": Notification.objects.filter(is_read=False).count(),
        }
    )


# ---GIS----


@login_required
def library_map(request):
    provinces = (
        LibraryLocation.objects.filter(is_active=True)
        .values_list("province", flat=True)
        .distinct()
        .order_by("province")
    )
    total_libraries = LibraryLocation.objects.filter(is_active=True).count()

    return render(
        request,
        "library_app/library_map.html",
        {
            "provinces": provinces,
            "total_libraries": total_libraries,
        },
    )


@login_required
def api_libraries_geojson(request):
    search = request.GET.get("search", "").strip()
    province = request.GET.get("province", "").strip()

    qs = LibraryLocation.objects.filter(is_active=True)

    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(address__icontains=search)
            | Q(province__icontains=search)
        )

    if province:
        qs = qs.filter(province=province)

    features = []
    for lib in qs:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lib.longitude, lib.latitude],
                },
                "properties": {
                    "id": lib.id,
                    "name": lib.name,
                    "province": lib.province,
                    "address": lib.address,
                    "phone": lib.phone,
                    "website": lib.website,
                    "open_time": lib.open_time,
                    "description": lib.description,
                },
            }
        )

    return JsonResponse({"type": "FeatureCollection", "features": features})


@login_required
def my_borrows(request):
    reader = getattr(request.user, "reader_profile", None)
    if not reader:
        messages.warning(request, "Tài khoản này chưa được liên kết với hồ sơ độc giả.")
        return redirect("book_list")

    borrows = (
        BorrowRecord.objects.filter(reader=reader)
        .select_related("book")
        .order_by("-created_at")
    )
    page = Paginator(borrows, 20).get_page(request.GET.get("page", 1))

    return render(
        request,
        "library_app/my_borrows.html",
        {
            "borrows": page,
        },
    )


@login_required
def my_reservations(request):
    reader = getattr(request.user, "reader_profile", None)
    if not reader:
        messages.warning(request, "Tài khoản này chưa được liên kết với hồ sơ độc giả.")
        return redirect("book_list")

    reservations = (
        BookReservation.objects.filter(reader=reader)
        .select_related("book")
        .order_by("-reserved_at")
    )
    page = Paginator(reservations, 20).get_page(request.GET.get("page", 1))

    return render(
        request,
        "library_app/my_reservations.html",
        {
            "reservations": page,
        },
    )


@login_required
def my_profile(request):
    reader = getattr(request.user, "reader_profile", None)
    return render(
        request,
        "library_app/my_profile.html",
        {
            "reader": reader,
        },
    )
    
@admin_required
def branch_detail(request, pk):
    branch = get_object_or_404(LibraryBranch, pk=pk)
    return render(request, 'library_app/branch_detail.html', {
        'branch': branch,
    })
    
    
def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_403(request, exception):
    return render(request, '403.html', status=403)   

def test_403(request):
    raise PermissionDenied

def preview_404(request):
    return render(request, '404.html', status=200)

def preview_403(request):
    return render(request, '403.html', status=200)

# Gioi Thieu
def about_page(request):
    return render(request, 'library_app/about.html')

# ĐK
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tạo tài khoản thành công!')
            return redirect('login')  # redirect tới trang đăng nhập
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

def test_email(request):
    send_mail(
        "Test Resend",
        "Mail này gửi từ Django dùng Resend",
        None,
        ["phamhoang05042005@gmail.com"],
        fail_silently=False,
    )
    return HttpResponse("Đã gửi mail")

# ─── USER MANAGEMENT ───

@admin_required
def user_list(request):
    search = request.GET.get('search', '').strip()
    role = request.GET.get('role', '').strip()

    qs = User.objects.all().order_by('username')

    if search:
        qs = qs.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    if role == 'superuser':
        qs = qs.filter(is_superuser=True)
    elif role == 'staff':
        qs = qs.filter(is_staff=True, is_superuser=False)
    elif role == 'user':
        qs = qs.filter(is_staff=False, is_superuser=False)

    total_count = qs.count()
    page = Paginator(qs, 20).get_page(request.GET.get('page', 1))

    return render(request, 'library_app/user_list.html', {
        'users': page,
        'search': search,
        'role': role,
        'total_count': total_count,
    })


@admin_required
def user_create(request):
    from .forms import UserCreateForm
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã tạo tài khoản "{form.cleaned_data["username"]}" thành công!')
            return redirect('user_list')
    else:
        form = UserCreateForm()
    return render(request, 'library_app/user_form.html', {
        'form': form,
        'title': 'Thêm tài khoản mới',
    })


@admin_required
def user_edit(request, pk):
    from .forms import UserEditForm
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật tài khoản "{user_obj.username}"!')
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user_obj)
    return render(request, 'library_app/user_form.html', {
        'form': form,
        'title': f'Chỉnh sửa: {user_obj.username}',
        'user_obj': user_obj,
    })


@admin_required
def user_delete(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, 'Không thể xóa tài khoản đang đăng nhập.')
        return redirect('user_list')
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'Đã xóa tài khoản "{username}".')
        return redirect('user_list')
    return render(request, 'library_app/confirm_delete.html', {
        'obj_name': user_obj.username,
    })


from django.shortcuts import render

def intro_management(request):
    return render(request, 'library_app/intro_management.html')

def books_excel(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]

        df = pd.read_excel(file)

        for _, row in df.iterrows():
            Book.objects.create(
                title=row["Tên sách"],
                author=row["Tác giả"],
                isbn=row["ISBN"],
                publisher=row["NXB"],
                publish_year=row["Năm xuất bản"], 
                total_copies=row["Tổng số bản"],
                available_copies=row["Tổng số bản"],
            )

        return redirect("books_excel")

    return render(request, "library_app/books_excel.html")


def export_books_excel(request):
    books = Book.objects.all().values(
        "isbn", "title", "author", "publisher", "publish_year", "total_copies"
    )

    df = pd.DataFrame(list(books))

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename=books.xlsx'

    df.to_excel(response, index=False)

    return response