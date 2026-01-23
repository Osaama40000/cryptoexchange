"""
KYC/AML Models for Identity Verification
"""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class KYCLevel(models.Model):
    """KYC verification levels with associated limits"""

    class LevelType(models.TextChoices):
        UNVERIFIED = 'unverified', 'Unverified'
        BASIC = 'basic', 'Basic'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    level = models.CharField(max_length=20, choices=LevelType.choices, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    daily_withdrawal_limit = models.DecimalField(max_digits=20, decimal_places=2)
    monthly_withdrawal_limit = models.DecimalField(max_digits=20, decimal_places=2)
    daily_deposit_limit = models.DecimalField(max_digits=20, decimal_places=2)

    can_trade = models.BooleanField(default=True)
    can_withdraw_crypto = models.BooleanField(default=False)
    can_withdraw_fiat = models.BooleanField(default=False)
    can_use_p2p = models.BooleanField(default=False)

    requires_email = models.BooleanField(default=True)
    requires_phone = models.BooleanField(default=False)
    requires_id_document = models.BooleanField(default=False)
    requires_selfie = models.BooleanField(default=False)
    requires_proof_of_address = models.BooleanField(default=False)
    requires_source_of_funds = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kyc_levels'
        ordering = ['daily_withdrawal_limit']

    def __str__(self):
        return f"{self.name} - ${self.daily_withdrawal_limit}/day"


class KYCProfile(models.Model):
    """User's KYC profile and verification status"""

    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not Started'
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        EXPIRED = 'expired', 'Expired'
        SUSPENDED = 'suspended', 'Suspended'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='kyc_profile'
    )

    current_level = models.ForeignKey(
        KYCLevel, on_delete=models.PROTECT,
        related_name='profiles', null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)

    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)

    phone_number = models.CharField(max_length=20, blank=True)
    phone_verified = models.BooleanField(default=False)

    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    identity_verified_at = models.DateTimeField(null=True, blank=True)
    address_verified_at = models.DateTimeField(null=True, blank=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='kyc_reviews'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    risk_score = models.IntegerField(default=0)
    is_pep = models.BooleanField(default=False)
    is_sanctioned = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'kyc_profiles'

    def __str__(self):
        return f"KYC: {self.user.email} - {self.status}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_verified(self):
        return self.status == self.Status.APPROVED

    def get_withdrawal_limit(self, period='daily'):
        if not self.current_level:
            return Decimal('0')
        if period == 'monthly':
            return self.current_level.monthly_withdrawal_limit
        return self.current_level.daily_withdrawal_limit


class KYCDocument(models.Model):
    """Uploaded KYC documents"""

    class DocumentType(models.TextChoices):
        PASSPORT = 'passport', 'Passport'
        NATIONAL_ID = 'national_id', 'National ID'
        DRIVERS_LICENSE = 'drivers_license', "Driver's License"
        SELFIE = 'selfie', 'Selfie with ID'
        PROOF_OF_ADDRESS = 'proof_of_address', 'Proof of Address'
        BANK_STATEMENT = 'bank_statement', 'Bank Statement'
        UTILITY_BILL = 'utility_bill', 'Utility Bill'
        SOURCE_OF_FUNDS = 'source_of_funds', 'Source of Funds'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        EXPIRED = 'expired', 'Expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc_profile = models.ForeignKey(KYCProfile, on_delete=models.CASCADE, related_name='documents')

    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    file = models.FileField(upload_to='kyc_documents/%Y/%m/')
    file_hash = models.CharField(max_length=64, blank=True)
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)

    document_number = models.CharField(max_length=100, blank=True)
    issuing_country = models.CharField(max_length=100, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_documents'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    extracted_data = models.JSONField(default=dict, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kyc_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document_type} - {self.kyc_profile.user.email}"

    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False


class KYCVerificationRequest(models.Model):
    """Track verification requests"""

    class RequestType(models.TextChoices):
        BASIC = 'basic', 'Basic Verification'
        INTERMEDIATE = 'intermediate', 'Intermediate Verification'
        ADVANCED = 'advanced', 'Advanced Verification'
        RESUBMISSION = 'resubmission', 'Resubmission'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_REVIEW = 'in_review', 'In Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        MORE_INFO = 'more_info', 'More Info Required'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc_profile = models.ForeignKey(KYCProfile, on_delete=models.CASCADE, related_name='verification_requests')

    request_type = models.CharField(max_length=20, choices=RequestType.choices)
    target_level = models.ForeignKey(KYCLevel, on_delete=models.PROTECT, related_name='verification_requests')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    documents = models.ManyToManyField(KYCDocument, related_name='verification_requests')

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_kyc_requests'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='completed_kyc_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    additional_info_request = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'kyc_verification_requests'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.request_type} - {self.kyc_profile.user.email} - {self.status}"


class KYCAuditLog(models.Model):
    """Audit log for KYC actions"""

    class Action(models.TextChoices):
        PROFILE_CREATED = 'profile_created', 'Profile Created'
        DOCUMENT_UPLOADED = 'document_uploaded', 'Document Uploaded'
        DOCUMENT_APPROVED = 'document_approved', 'Document Approved'
        DOCUMENT_REJECTED = 'document_rejected', 'Document Rejected'
        VERIFICATION_SUBMITTED = 'verification_submitted', 'Verification Submitted'
        VERIFICATION_APPROVED = 'verification_approved', 'Verification Approved'
        VERIFICATION_REJECTED = 'verification_rejected', 'Verification Rejected'
        LEVEL_UPGRADED = 'level_upgraded', 'Level Upgraded'
        LEVEL_DOWNGRADED = 'level_downgraded', 'Level Downgraded'
        PROFILE_SUSPENDED = 'profile_suspended', 'Profile Suspended'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc_profile = models.ForeignKey(KYCProfile, on_delete=models.CASCADE, related_name='audit_logs')

    action = models.CharField(max_length=30, choices=Action.choices)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='kyc_actions'
    )

    description = models.TextField()
    old_value = models.JSONField(default=dict, blank=True)
    new_value = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kyc_audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} - {self.kyc_profile.user.email}"