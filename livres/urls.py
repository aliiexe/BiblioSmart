from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), 
    path('add/', views.add_book, name='add_book'),
    path('delete/<int:book_id>/', views.delete_book, name='delete_book'),  
    path('edit/<int:book_id>/', views.edit_book, name='edit_book'),
    path('update/<int:book_id>/', views.update_book, name='update_book'),
    path('details/<int:book_id>/', views.details_book, name='details_book'),
]