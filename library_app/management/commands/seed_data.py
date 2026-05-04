"""
python manage.py seed_data
Tạo toàn bộ dữ liệu mẫu cho LibraryGIS
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from library_app.models import (Branch, Category, Book, Reader,
                                 BorrowRecord, Notification, BookReservation)
import random

BRANCHES = [
    dict(name='Thư viện Trung tâm Q.1',    address='69 Lý Tự Trọng, Q.1, TP.HCM',           latitude=10.7769, longitude=106.7009, phone='028 3822 1023', opening_hours='7:30 - 21:00'),
    dict(name='Chi nhánh Gò Vấp',           address='45 Nguyễn Văn Nghi, Q.Gò Vấp, TP.HCM',  latitude=10.8380, longitude=106.6632, phone='028 3895 4412', opening_hours='8:00 - 20:00'),
    dict(name='Chi nhánh Bình Thạnh',       address='12 Đinh Tiên Hoàng, Q.Bình Thạnh, TP.HCM', latitude=10.8027, longitude=106.7117, phone='028 3840 2211', opening_hours='8:00 - 20:00'),
    dict(name='Chi nhánh Thủ Đức',          address='18 Võ Văn Ngân, TP.Thủ Đức, TP.HCM',    latitude=10.8509, longitude=106.7718, phone='028 3726 1180', opening_hours='8:00 - 19:30'),
    dict(name='Chi nhánh Tân Bình',         address='5 Hoàng Văn Thụ, Q.Tân Bình, TP.HCM',   latitude=10.7997, longitude=106.6529, phone='028 3849 3300', opening_hours='8:00 - 20:00'),
]

CATEGORIES = [
    ('Văn học',               'van-hoc',             '#f0c040'),
    ('Khoa học & Công nghệ',  'khoa-hoc-cong-nghe',  '#58a6ff'),
    ('Lịch sử & Địa lý',      'lich-su-dia-ly',       '#39d353'),
    ('Kinh tế & Tài chính',   'kinh-te-tai-chinh',   '#bc8cff'),
    ('Tâm lý & Kỹ năng',      'tam-ly-ky-nang',      '#ff7b72'),
    ('Thiếu nhi',              'thieu-nhi',            '#e3b341'),
    ('Triết học',              'triet-hoc',            '#79c0ff'),
    ('Y học & Sức khỏe',       'y-hoc-suc-khoe',      '#56d364'),
]

BOOKS = [
    ('9780062315007','Đắc Nhân Tâm','Dale Carnegie','NXB Tổng hợp TP.HCM',1936,4,4),
    ('9780062316097','Nhà Giả Kim','Paulo Coelho','NXB Hội Nhà Văn',1988,4,4),
    ('9781501156700','Tuổi Trẻ Đáng Giá Bao Nhiêu','Rosie Nguyễn','NXB Tổng hợp',2016,0,3),
    ('9780385490818','Lược Sử Thời Gian','Stephen Hawking','NXB Trẻ',1988,1,2),
    ('9780062457714','Sapiens: Lược Sử Loài Người','Yuval Noah Harari','NXB Tri Thức',2011,2,3),
    ('9781847941831','Khéo Ăn Nói Sẽ Có Được Thiên Hạ','Trác Nhã','NXB Lao Động',2018,1,3),
    ('9780735224292','Atomic Habits','James Clear','NXB Lao Động - Xã Hội',2018,2,2),
    ('9781250301697','Người Giàu Có Nhất Thành Babylon','George S. Clason','NXB Trẻ',1926,2,2),
    ('9780062641540','Nghĩ Giàu Làm Giàu','Napoleon Hill','NXB Tổng hợp',1937,1,2),
    ('9781501110368','Dám Bị Ghét','Kishimi Ichiro','NXB Lao Động',2013,3,3),
    ('9780307588364','Mỗi Ngày Một Điều Tốt','Neil Pasricha','NXB Trẻ',2010,2,2),
    ('9781442431027','Đừng Bao Giờ Đi Ăn Một Mình','Keith Ferrazzi','NXB Lao Động',2005,1,2),
    ('9780525559474','The Subtle Art of Not Giving a F*ck','Mark Manson','NXB Thế Giới',2016,2,3),
    ('9780062457608','Homo Deus','Yuval Noah Harari','NXB Tri Thức',2015,1,2),
    ('9780062301239','Zero to One','Peter Thiel','NXB Trẻ',2014,2,2),
]

READERS = [
    ('TDG2024001','Nguyễn Văn An','M','1995-03-15','0901234567','an.nguyen@gmail.com','12 Lý Thường Kiệt, Q.10',10.7714,106.6683,'Quận 10'),
    ('TDG2024002','Trần Thị Bình','F','1998-07-22','0912345678','binh.tran@gmail.com','55 Phan Xích Long, Q.Bình Thạnh',10.8014,106.7058,'Bình Thạnh'),
    ('TDG2024003','Lê Minh Châu','M','2000-01-10','0923456789','chau.le@gmail.com','8 Nguyễn Oanh, Q.Gò Vấp',10.8361,106.6663,'Gò Vấp'),
    ('TDG2024004','Phạm Thị Dung','F','1992-11-30','0934567890','dung.pham@gmail.com','100 Đinh Bộ Lĩnh, Q.Bình Thạnh',10.8070,106.7133,'Bình Thạnh'),
    ('TDG2024005','Hoàng Văn Em','M','1997-05-18','0945678901','em.hoang@gmail.com','33 Võ Văn Ngân, TP.Thủ Đức',10.8490,106.7695,'Thủ Đức'),
    ('TDG2024006','Võ Thị Phương','F','2001-08-05','0956789012','phuong.vo@gmail.com','22 Cộng Hòa, Q.Tân Bình',10.7982,106.6508,'Tân Bình'),
    ('TDG2024007','Đặng Quốc Hùng','M','1990-12-20','0967890123','hung.dang@gmail.com','15 Nguyễn Xí, Q.Bình Thạnh',10.8085,106.7090,'Bình Thạnh'),
    ('TDG2024008','Ngô Thị Lan','F','1999-04-14','0978901234','lan.ngo@gmail.com','78 Quang Trung, Q.Gò Vấp',10.8350,106.6710,'Gò Vấp'),
    ('TDG2024009','Bùi Thanh Minh','M','1993-09-28','0989012345','minh.bui@gmail.com','5 Trần Não, TP.Thủ Đức',10.7965,106.7524,'Thủ Đức'),
    ('TDG2024010','Trương Thị Nga','F','2002-02-17','0990123456','nga.truong@gmail.com','40 Lê Văn Sỹ, Q.3',10.7814,106.6880,'Quận 3'),
]


class Command(BaseCommand):
    help = 'Seed dữ liệu mẫu LibraryGIS'

    def handle(self, *args, **opts):
        out = self.stdout.write

        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@library.vn', 'admin123')
            out('✅ superuser: admin / admin123')

        # Branches
        branches = []
        for d in BRANCHES:
            b, _ = Branch.objects.get_or_create(name=d['name'], defaults=d)
            branches.append(b)
        out(f'✅ {len(branches)} chi nhánh')

        # Categories
        cats = []
        for name, slug, color in CATEGORIES:
            c, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'color': color})
            cats.append(c)
        out(f'✅ {len(cats)} danh mục')

        # Books
        books = []
        for i, (isbn, title, author, pub, yr, avail, total) in enumerate(BOOKS):
            bk, created = Book.objects.get_or_create(isbn=isbn, defaults={
                'title': title, 'author': author, 'publisher': pub, 'publish_year': yr,
                'category': cats[i % len(cats)], 'branch': branches[i % len(branches)],
                'total_copies': total, 'available_copies': avail,
                'language': 'Tiếng Việt', 'pages': random.randint(180, 500),
                'description': f'Cuốn sách "{title}" của tác giả {author}. Được xuất bản năm {yr}.',
            })
            books.append(bk)
        out(f'✅ {len(books)} đầu sách')

        # Readers
        today = timezone.now().date()
        readers = []
        for d in READERS:
            card, name, gender, dob, phone, email, addr, lat, lng, district = d
            r, _ = Reader.objects.get_or_create(card_number=card, defaults={
                'full_name': name, 'gender': gender,
                'date_of_birth': date.fromisoformat(dob),
                'phone': phone, 'email': email, 'address': addr,
                'home_latitude': lat, 'home_longitude': lng, 'district': district,
                'preferred_branch': branches[0],
                'card_issue_date': today - timedelta(days=random.randint(30, 365)),
                'card_expiry_date': today + timedelta(days=random.randint(30, 730)),
                'status': 'active',
            })
            readers.append(r)
        out(f'✅ {len(readers)} độc giả')

        # Borrow records — mix of borrowed/returned/overdue
        created_borrows = []
        for i in range(20):
            reader = readers[i % len(readers)]
            book   = books[i % len(books)]
            borrow_date = today - timedelta(days=random.randint(1, 60))
            due_date    = borrow_date + timedelta(days=14)
            if i < 6:
                status = 'borrowed'; return_date = None
            elif i < 10:
                status = 'overdue'; return_date = None
            else:
                status = 'returned'; return_date = due_date + timedelta(days=random.randint(-3, 5))

            br, created = BorrowRecord.objects.get_or_create(
                reader=reader, book=book,
                defaults={
                    'branch': book.branch, 'borrow_date': borrow_date,
                    'due_date': due_date, 'return_date': return_date, 'status': status,
                    'fine_amount': max(0, (return_date - due_date).days * 5000) if return_date and return_date > due_date else 0,
                }
            )
            if created and status == 'overdue':
                Notification.objects.get_or_create(
                    borrow_record=br, type='overdue',
                    defaults={
                        'reader': reader,
                        'title': f'Sách quá hạn: {book.title}',
                        'message': f'{reader.full_name} quá hạn trả "{book.title}" từ {due_date:%d/%m/%Y}.',
                    }
                )
            created_borrows.append(br)
        out(f'✅ {len(created_borrows)} phiếu mượn')

        # Reservations
        for i in range(3):
            reader = readers[i]
            book   = books[(i + 5) % len(books)]
            BookReservation.objects.get_or_create(
                reader=reader, book=book,
                defaults={
                    'branch': branches[0],
                    'expires_at': today + timedelta(days=7),
                    'status': 'pending',
                }
            )
        out('✅ 3 đặt trước mẫu')

        self.stdout.write(self.style.SUCCESS('\n🎉 Xong! http://127.0.0.1:8000 — admin/admin123'))

        # Librarian user
        from django.contrib.auth.models import User
        if not User.objects.filter(username='librarian').exists():
            User.objects.create_user('librarian', 'librarian@library.vn', 'lib2024',
                                     first_name='Nguyễn', last_name='Thủ thư')
            out('✅ librarian: librarian / lib2024')
