from django.urls import path
from . import views

app_name = 'food'

urlpatterns = [
    path('select/', views.food_selection, name='food_selection'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
]