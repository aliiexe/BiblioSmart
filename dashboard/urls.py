from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reader/', views.reader_dashboard, name='reader_dashboard'),
    path('librarian/', views.librarian_dashboard, name='librarian_dashboard'),
]