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
    path('books/<int:book_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('books/<int:book_id>/return/', views.return_book, name='return_book'),
    
    # Book Management URLs
    path('management/books/', views.book_management, name='book_management'),
    path('management/books/add/', views.add_book, name='add_book'),
    path('management/books/<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('management/books/<int:book_id>/delete/', views.delete_book, name='delete_book'),

    path('logout/', views.logout, name='logout'),

    path('book/<int:book_id>/review/', views.review_book, name='review_book'),
    path('book/<int:book_id>/submit-review/', views.submit_review, name='submit_review'),
    path('books/bulk-delete/', views.bulk_delete_books, name='bulk_delete_books'),
    path('books/bulk-update-availability/', views.bulk_update_availability, name='bulk_update_availability'),

        
        # path('books/bulk-delete/', views.bulk_delete_books, name='bulk_delete_books'),
        # path('books/bulk-available/', views.bulk_mark_available, name='bulk_mark_available'),
        # path('books/bulk-borrowed/', views.bulk_mark_borrowed, name='bulk_mark_borrowed'),
    
]