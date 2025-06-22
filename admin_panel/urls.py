from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tables/', views.manage_tables, name='manage_tables'),
    path('food/', views.manage_food, name='manage_food'),
    path('change-order-status/<int:order_id>/', views.change_order_status, name='change_order_status'),
]