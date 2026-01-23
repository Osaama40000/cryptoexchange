from django.contrib import admin
from .models import KYCLevel, KYCProfile, KYCDocument, KYCVerificationRequest, KYCAuditLog


@admin.register(KYCLevel)
class KYCLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'daily_withdrawal_limit', 'can_trade', 'can_withdraw_crypto']
    list_filter = ['can_trade', 'can_withdraw_crypto', 'can_withdraw_fiat']


@admin.register(KYCProfile)
class KYCProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'current_level', 'created_at']
    list_filter = ['status', 'current_level']
    search_fields = ['user__email', 'first_name', 'last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ['kyc_profile', 'document_type', 'status', 'created_at']
    list_filter = ['document_type', 'status']
    search_fields = ['kyc_profile__user__email']


@admin.register(KYCVerificationRequest)
class KYCVerificationRequestAdmin(admin.ModelAdmin):
    list_display = ['kyc_profile', 'request_type', 'target_level', 'status', 'submitted_at']
    list_filter = ['request_type', 'status', 'target_level']
    search_fields = ['kyc_profile__user__email']


@admin.register(KYCAuditLog)
class KYCAuditLogAdmin(admin.ModelAdmin):
    list_display = ['kyc_profile', 'action', 'performed_by', 'created_at']
    list_filter = ['action']
    search_fields = ['kyc_profile__user__email']
    readonly_fields = ['id', 'created_at']