"""
KYC Serializers
"""
from rest_framework import serializers
from .models import KYCLevel, KYCProfile, KYCDocument, KYCVerificationRequest, KYCAuditLog


class KYCLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCLevel
        fields = [
            'level', 'name', 'description',
            'daily_withdrawal_limit', 'monthly_withdrawal_limit', 'daily_deposit_limit',
            'can_trade', 'can_withdraw_crypto', 'can_withdraw_fiat', 'can_use_p2p',
            'requires_email', 'requires_phone', 'requires_id_document',
            'requires_selfie', 'requires_proof_of_address', 'requires_source_of_funds'
        ]


class KYCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCDocument
        fields = [
            'id', 'document_type', 'status',
            'original_filename', 'file_size', 'mime_type',
            'document_number', 'issuing_country', 'issue_date', 'expiry_date',
            'rejection_reason', 'is_expired',
            'created_at', 'reviewed_at'
        ]
        read_only_fields = [
            'id', 'status', 'file_size', 'mime_type',
            'rejection_reason', 'is_expired', 'created_at', 'reviewed_at'
        ]


class KYCDocumentUploadSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(choices=KYCDocument.DocumentType.choices)
    file = serializers.FileField()
    document_number = serializers.CharField(required=False, allow_blank=True)
    issuing_country = serializers.CharField(required=False, allow_blank=True)
    issue_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)

    def validate_file(self, value):
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be under 10MB")

        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Invalid file type. Allowed: JPEG, PNG, GIF, PDF")

        return value


class KYCProfileSerializer(serializers.ModelSerializer):
    current_level = KYCLevelSerializer(read_only=True)
    documents = KYCDocumentSerializer(many=True, read_only=True)
    full_name = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    daily_withdrawal_limit = serializers.SerializerMethodField()
    monthly_withdrawal_limit = serializers.SerializerMethodField()

    class Meta:
        model = KYCProfile
        fields = [
            'id', 'status', 'current_level',
            'first_name', 'last_name', 'full_name', 'date_of_birth', 'nationality',
            'phone_number', 'phone_verified',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'email_verified_at', 'phone_verified_at', 'identity_verified_at', 'address_verified_at',
            'is_verified', 'risk_score',
            'daily_withdrawal_limit', 'monthly_withdrawal_limit',
            'documents', 'rejection_reason',
            'created_at', 'updated_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'status', 'current_level', 'phone_verified',
            'email_verified_at', 'phone_verified_at', 'identity_verified_at', 'address_verified_at',
            'is_verified', 'risk_score', 'rejection_reason',
            'created_at', 'updated_at', 'expires_at'
        ]

    def get_daily_withdrawal_limit(self, obj):
        return str(obj.get_withdrawal_limit('daily'))

    def get_monthly_withdrawal_limit(self, obj):
        return str(obj.get_withdrawal_limit('monthly'))


class KYCProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCProfile
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'nationality',
            'phone_number',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country'
        ]

    def validate_date_of_birth(self, value):
        from datetime import date
        if value:
            today = date.today()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            if age < 18:
                raise serializers.ValidationError("You must be at least 18 years old")
            if age > 120:
                raise serializers.ValidationError("Invalid date of birth")
        return value


class KYCVerificationRequestSerializer(serializers.ModelSerializer):
    target_level = KYCLevelSerializer(read_only=True)
    documents = KYCDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = KYCVerificationRequest
        fields = [
            'id', 'request_type', 'target_level', 'status',
            'documents', 'rejection_reason', 'additional_info_request',
            'submitted_at', 'reviewed_at'
        ]
        read_only_fields = [
            'id', 'status', 'rejection_reason', 'additional_info_request',
            'submitted_at', 'reviewed_at'
        ]


class SubmitVerificationSerializer(serializers.Serializer):
    target_level = serializers.ChoiceField(choices=KYCLevel.LevelType.choices)
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list
    )


class KYCAuditLogSerializer(serializers.ModelSerializer):
    performed_by_email = serializers.CharField(source='performed_by.email', read_only=True)

    class Meta:
        model = KYCAuditLog
        fields = [
            'id', 'action', 'performed_by_email',
            'description', 'old_value', 'new_value',
            'ip_address', 'created_at'
        ]


class AdminKYCProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    current_level = KYCLevelSerializer(read_only=True)
    documents = KYCDocumentSerializer(many=True, read_only=True)
    verification_requests = KYCVerificationRequestSerializer(many=True, read_only=True)

    class Meta:
        model = KYCProfile
        fields = '__all__'


class AdminDocumentReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    document_number = serializers.CharField(required=False, allow_blank=True)
    issuing_country = serializers.CharField(required=False, allow_blank=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting a document'
            })
        return data


class AdminVerificationReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject', 'request_more_info'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    additional_info_request = serializers.CharField(required=False, allow_blank=True)
    admin_notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required'
            })
        if data['action'] == 'request_more_info' and not data.get('additional_info_request'):
            raise serializers.ValidationError({
                'additional_info_request': 'Please specify what additional information is needed'
            })
        return data