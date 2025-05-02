from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from notifications import views as notification_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('auth.urls')),
    path('livres/', include('livres.urls')),
    # path('auth/', include('auth.urls')),
    path('emprunt/', include('emprunt.urls')),
    path('utilisateurs/', include('utilisateurs.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('notifications/mark-all-read/', notification_views.mark_all_read, name='mark_all_read'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)