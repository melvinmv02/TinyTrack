from .models import Notification, ChatMessage


def notification_count(request):
    """
    Injects unread_notif_count and unread_chat_count into every template context.
    """
    if request.user.is_authenticated and hasattr(request.user, 'role'):
        if request.user.role == 'parent':
            notif_count = Notification.objects.filter(
                recipient=request.user, is_read=False
            ).count()
        else:
            notif_count = 0

        chat_count = ChatMessage.objects.filter(
            recipient=request.user, is_read=False
        ).count()
    else:
        notif_count = 0
        chat_count = 0

    return {
        'unread_notif_count': notif_count,
        'unread_chat_count': chat_count,
    }
