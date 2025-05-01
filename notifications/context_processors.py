# notifications/context_processors.py
from biblio_smart.models import Notification

def notification_processor(request):
    if 'utilisateur_id' in request.session:
        utilisateur_id = request.session.get('utilisateur_id')
        notifications = Notification.objects.filter(user_id=utilisateur_id, read=False)[:5]
        return {
            'notifications': notifications,
        }
    return {'notifications': []}