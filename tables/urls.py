from django.urls import path
from . import views

app_name = 'tables'

urlpatterns = [
    path('select/', views.table_selection, name='table_selection'),
    path('lock/<int:table_id>/', views.lock_table, name='lock_table'),
]