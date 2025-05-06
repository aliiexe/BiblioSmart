from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index_rapports'),
    path('livres/', views.rapport_livres, name='rapport_livres'),
    path('adherents/', views.rapport_adherents, name='rapport_adherents'),
    path('activite/', views.rapport_activite, name='rapport_activite'),
    path('financier/', views.rapport_financier, name='rapport_financier'),
]