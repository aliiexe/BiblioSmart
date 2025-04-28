from django.urls import path
from . import views

urlpatterns = [
    path('emprunter/<int:livre_id>/', views.emprunt_livre, name='emprunter'), 
   
]