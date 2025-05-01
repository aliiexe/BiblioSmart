
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from biblio_smart.models import Notification

@require_POST
def mark_all_read(request):
    if 'utilisateur_id' in request.session:
        utilisateur_id = request.session.get('utilisateur_id')
        Notification.objects.filter(user_id=utilisateur_id, read=False).update(read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})