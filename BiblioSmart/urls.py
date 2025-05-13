from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from notifications import views as notification_views

urlpatterns = [
    path('', include('pgAcc.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('auth.urls')),
    path('livres/', include('livres.urls')),
    # path('auth/', include('auth.urls')),
    path('emprunt/', include('emprunt.urls')),
    path('utilisateurs/', include('utilisateurs.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('notifications/mark-all-read/', notification_views.mark_all_read, name='mark_all_read'),
    path('rapports/', include('rapports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# ...existing code...
urlpatterns = [
    # ...existing URL patterns...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)