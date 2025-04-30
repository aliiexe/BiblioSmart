from django.contrib import admin
from django.urls import path, include


from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('auth.urls')),
    path('livres/', include('livres.urls')),
    # path('auth/', include('auth.urls')),
    path('emprunt/', include('emprunt.urls')),
    path('utilisateurs/', include('utilisateurs.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)