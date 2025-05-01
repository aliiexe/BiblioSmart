from django.urls import path
from . import views

urlpatterns = [
    path('', views.loans_dashboard, name='loans_dashboard'),
    path('user/<int:user_id>/', views.user_loans, name='user_loans'),
    path('all/', views.all_loans, name='all_loans'),
    path('detail/<int:loan_id>/', views.loan_detail, name='loan_detail'),
]