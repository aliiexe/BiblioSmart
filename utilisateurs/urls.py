from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_management, name='user_management'),
    path('add/', views.add_user, name='add_user'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    path('users/lecteur/<int:user_id>/edit/', views.edit_lecteur, name='edit_lecteur'),
    path('users/bibliothecaire/<int:user_id>/edit/', views.edit_bibliothecaire, name='edit_bibliothecaire'),
]