from django.urls import path
from . import views_transfer

urlpatterns = [
    path('transfer/', views_transfer.transfer_crypto, name='transfer-crypto'),
    path('transfer/qr/', views_transfer.get_transfer_qr_data, name='transfer-qr'),
    path('transfer/search/', views_transfer.search_users, name='transfer-search'),
]
