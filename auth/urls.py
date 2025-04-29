from django.urls import path
from . import views

urlpatterns = [
    path('', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
]