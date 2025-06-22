from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('options/', views.payment_options, name='payment_options'),
    path('generate-qr/<int:order_id>/', views.generate_qr, name='generate_qr'),
    path('success/<int:order_id>/', views.payment_success, name='payment_success'),
]