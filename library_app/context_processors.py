from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(is_read=False).count()
        return {'unread_notif_count': count}
    return {'unread_notif_count': 0}
