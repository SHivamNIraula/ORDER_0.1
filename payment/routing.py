from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/payment/$', consumers.PaymentConsumer.as_asgi()),
    re_path(r'ws/payment/(?P<order_id>\d+)/$', consumers.PaymentConsumer.as_asgi()),
]