from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('auth.urls')),
    path('livres/', include('livres.urls')),
    path('utilisateurs/', include('utilisateurs.urls')),
     path('dashboard/', include('dashboard.urls')),
]