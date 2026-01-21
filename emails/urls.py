from django.urls import path
from .views import (
    ValidateEmailView,
    SendVerificationEmailView,
    VerifyEmailView,
    ResendVerificationView,
)

urlpatterns = [
    path('validate/', ValidateEmailView.as_view(), name='validate-email'),
    path('send-verification/', SendVerificationEmailView.as_view(), name='send-verification'),
    path('verify/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
]
