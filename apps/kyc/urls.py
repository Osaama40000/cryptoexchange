"""
KYC URL Configuration
"""
from django.urls import path
from .views import (
    KYCLevelListView,
    KYCProfileView,
    KYCDocumentUploadView,
    KYCDocumentListView,
    KYCDocumentDeleteView,
    SubmitVerificationView,
    VerificationStatusView,
    KYCLimitsView,
    AdminKYCProfileListView,
    AdminKYCProfileDetailView,
    AdminPendingVerificationsView,
    AdminDocumentReviewView,
    AdminVerificationReviewView,
    AdminKYCAuditLogView,
)

app_name = 'kyc'

urlpatterns = [
    # User endpoints
    path('levels/', KYCLevelListView.as_view(), name='levels'),
    path('profile/', KYCProfileView.as_view(), name='profile'),
    path('documents/', KYCDocumentListView.as_view(), name='document-list'),
    path('documents/upload/', KYCDocumentUploadView.as_view(), name='document-upload'),
    path('documents/<uuid:document_id>/delete/', KYCDocumentDeleteView.as_view(), name='document-delete'),
    path('verify/', SubmitVerificationView.as_view(), name='submit-verification'),
    path('verify/status/', VerificationStatusView.as_view(), name='verification-status'),
    path('limits/', KYCLimitsView.as_view(), name='limits'),

    # Admin endpoints
    path('admin/profiles/', AdminKYCProfileListView.as_view(), name='admin-profiles'),
    path('admin/profiles/<uuid:profile_id>/', AdminKYCProfileDetailView.as_view(), name='admin-profile-detail'),
    path('admin/pending/', AdminPendingVerificationsView.as_view(), name='admin-pending'),
    path('admin/documents/<uuid:document_id>/review/', AdminDocumentReviewView.as_view(), name='admin-document-review'),
    path('admin/verify/<uuid:request_id>/review/', AdminVerificationReviewView.as_view(),
         name='admin-verification-review'),
    path('admin/audit/', AdminKYCAuditLogView.as_view(), name='admin-audit-logs'),
    path('admin/audit/<uuid:profile_id>/', AdminKYCAuditLogView.as_view(), name='admin-profile-audit-logs'),
]