# from django.urls import path
# from . import views

# urlpatterns = [
#     path('', views.index, name='index'), 
#     path('add/', views.add_book, name='add_book'),
#     path('delete/<int:book_id>/', views.delete_book, name='delete_book'),  
#     path('edit/<int:book_id>/', views.edit_book, name='edit_book'),
#     path('update/<int:book_id>/', views.update_book, name='update_book'),
#     path('details/<int:book_id>/', views.details_book, name='details_book'),  
# ]

from django.urls import path
from . import views

urlpatterns = [
    # path('', views.index, name='index'), 
    # path('add/', views.add_book, name='add_book'),
    path('', views.home, name='home'),
    path('books/', views.books, name='books'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('books/<int:book_id>/borrow/', views.borrow_book, name='borrow_book'),
    path('books/<int:book_id>/waitlist/', views.join_waitlist, name='join_waitlist'),
    
    # Book Management URLs
    path('management/books/', views.book_management, name='book_management'),
    path('management/books/add/', views.add_book, name='add_book'),
    path('management/books/<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('management/books/<int:book_id>/delete/', views.delete_book, name='delete_book'),
]