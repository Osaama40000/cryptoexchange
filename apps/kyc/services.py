"""
KYC Service - Business logic for KYC operations
"""
import hashlib
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import KYCLevel, KYCProfile, KYCDocument, KYCVerificationRequest, KYCAuditLog


class KYCService:
    """Service class for KYC operations"""

    @staticmethod
    def get_or_create_profile(user):
        """Get or create KYC profile for user"""
        profile, created = KYCProfile.objects.get_or_create(
            user=user,
            defaults={
                'current_level': KYCLevel.objects.filter(
                    level=KYCLevel.LevelType.UNVERIFIED
                ).first()
            }
        )

        if created:
            KYCAuditLog.objects.create(
                kyc_profile=profile,
                action=KYCAuditLog.Action.PROFILE_CREATED,
                performed_by=user,
                description=f"KYC profile created for {user.email}"
            )

        return profile

    @staticmethod
    def update_profile(profile, data, request=None):
        """Update KYC profile with personal information"""
        for field, value in data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)

        profile.save()

        KYCAuditLog.objects.create(
            kyc_profile=profile,
            action=KYCAuditLog.Action.PROFILE_CREATED,
            performed_by=profile.user,
            description="Profile information updated",
            new_value=data,
            ip_address=request.META.get('REMOTE_ADDR') if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
        )

        return profile

    @staticmethod
    def upload_document(profile, document_type, file, **kwargs):
        """Upload a KYC document"""
        file_hash = hashlib.sha256()
        for chunk in file.chunks():
            file_hash.update(chunk)

        document = KYCDocument.objects.create(
            kyc_profile=profile,
            document_type=document_type,
            file=file,
            file_hash=file_hash.hexdigest(),
            original_filename=file.name,
            file_size=file.size,
            mime_type=file.content_type,
            document_number=kwargs.get('document_number', ''),
            issuing_country=kwargs.get('issuing_country', ''),
            issue_date=kwargs.get('issue_date'),
            expiry_date=kwargs.get('expiry_date')
        )

        KYCAuditLog.objects.create(
            kyc_profile=profile,
            action=KYCAuditLog.Action.DOCUMENT_UPLOADED,
            performed_by=profile.user,
            description=f"Document uploaded: {document_type}",
            new_value={
                'document_id': str(document.id),
                'document_type': document_type,
                'filename': file.name
            }
        )

        return document

    @staticmethod
    @transaction.atomic
    def submit_verification(profile, target_level_type, document_ids=None):
        """Submit a verification request"""
        target_level = KYCLevel.objects.get(level=target_level_type)

        if profile.status == KYCProfile.Status.REJECTED:
            request_type = KYCVerificationRequest.RequestType.RESUBMISSION
        else:
            request_type = target_level_type

        verification_request = KYCVerificationRequest.objects.create(
            kyc_profile=profile,
            request_type=request_type,
            target_level=target_level,
            status=KYCVerificationRequest.Status.PENDING
        )

        if document_ids:
            documents = KYCDocument.objects.filter(
                id__in=document_ids,
                kyc_profile=profile
            )
            verification_request.documents.set(documents)
        else:
            pending_docs = profile.documents.filter(status=KYCDocument.Status.PENDING)
            verification_request.documents.set(pending_docs)

        profile.status = KYCProfile.Status.PENDING
        profile.save()

        KYCAuditLog.objects.create(
            kyc_profile=profile,
            action=KYCAuditLog.Action.VERIFICATION_SUBMITTED,
            performed_by=profile.user,
            description=f"Verification request submitted for {target_level.name}",
            new_value={
                'request_id': str(verification_request.id),
                'target_level': target_level_type
            }
        )

        return verification_request

    @staticmethod
    @transaction.atomic
    def approve_document(document, admin_user, **kwargs):
        """Approve a KYC document"""
        old_status = document.status

        document.status = KYCDocument.Status.APPROVED
        document.reviewed_by = admin_user
        document.reviewed_at = timezone.now()

        if kwargs.get('document_number'):
            document.document_number = kwargs['document_number']
        if kwargs.get('issuing_country'):
            document.issuing_country = kwargs['issuing_country']
        if kwargs.get('expiry_date'):
            document.expiry_date = kwargs['expiry_date']

        document.save()

        KYCAuditLog.objects.create(
            kyc_profile=document.kyc_profile,
            action=KYCAuditLog.Action.DOCUMENT_APPROVED,
            performed_by=admin_user,
            description=f"Document approved: {document.document_type}",
            old_value={'status': old_status},
            new_value={'status': document.status}
        )

        return document

    @staticmethod
    @transaction.atomic
    def reject_document(document, admin_user, reason):
        """Reject a KYC document"""
        old_status = document.status

        document.status = KYCDocument.Status.REJECTED
        document.reviewed_by = admin_user
        document.reviewed_at = timezone.now()
        document.rejection_reason = reason
        document.save()

        KYCAuditLog.objects.create(
            kyc_profile=document.kyc_profile,
            action=KYCAuditLog.Action.DOCUMENT_REJECTED,
            performed_by=admin_user,
            description=f"Document rejected: {document.document_type}",
            old_value={'status': old_status},
            new_value={'status': document.status, 'reason': reason}
        )

        return document

    @staticmethod
    @transaction.atomic
    def approve_verification(verification_request, admin_user, notes=''):
        """Approve a verification request and upgrade user level"""
        profile = verification_request.kyc_profile
        old_level = profile.current_level

        verification_request.status = KYCVerificationRequest.Status.APPROVED
        verification_request.reviewed_by = admin_user
        verification_request.reviewed_at = timezone.now()
        verification_request.admin_notes = notes
        verification_request.save()

        profile.current_level = verification_request.target_level
        profile.status = KYCProfile.Status.APPROVED
        profile.reviewed_by = admin_user
        profile.reviewed_at = timezone.now()

        now = timezone.now()
        if verification_request.target_level.requires_id_document:
            profile.identity_verified_at = now
        if verification_request.target_level.requires_proof_of_address:
            profile.address_verified_at = now

        from datetime import timedelta
        profile.expires_at = now + timedelta(days=365)

        profile.save()

        verification_request.documents.filter(
            status=KYCDocument.Status.PENDING
        ).update(
            status=KYCDocument.Status.APPROVED,
            reviewed_by=admin_user,
            reviewed_at=now
        )

        KYCAuditLog.objects.create(
            kyc_profile=profile,
            action=KYCAuditLog.Action.VERIFICATION_APPROVED,
            performed_by=admin_user,
            description=f"Verification approved - Level upgraded to {verification_request.target_level.name}",
            old_value={'level': old_level.level if old_level else None},
            new_value={'level': verification_request.target_level.level}
        )

        return verification_request

    @staticmethod
    @transaction.atomic
    def reject_verification(verification_request, admin_user, reason, notes=''):
        """Reject a verification request"""
        profile = verification_request.kyc_profile

        verification_request.status = KYCVerificationRequest.Status.REJECTED
        verification_request.reviewed_by = admin_user
        verification_request.reviewed_at = timezone.now()
        verification_request.rejection_reason = reason
        verification_request.admin_notes = notes
        verification_request.save()

        profile.status = KYCProfile.Status.REJECTED
        profile.rejection_reason = reason
        profile.save()

        KYCAuditLog.objects.create(
            kyc_profile=profile,
            action=KYCAuditLog.Action.VERIFICATION_REJECTED,
            performed_by=admin_user,
            description=f"Verification rejected: {reason}",
            new_value={'reason': reason}
        )

        return verification_request

    @staticmethod
    def request_more_info(verification_request, admin_user, info_request, notes=''):
        """Request additional information for verification"""
        verification_request.status = KYCVerificationRequest.Status.MORE_INFO
        verification_request.additional_info_request = info_request
        verification_request.admin_notes = notes
        verification_request.save()

        profile = verification_request.kyc_profile
        profile.status = KYCProfile.Status.NOT_STARTED
        profile.save()

        return verification_request

    @staticmethod
    def check_withdrawal_limit(user, amount_usd):
        """Check if withdrawal is within user's KYC limits"""
        try:
            profile = user.kyc_profile
            if not profile.current_level:
                return False, "KYC verification required"

            daily_limit = profile.get_withdrawal_limit('daily')
            if amount_usd > daily_limit:
                return False, f"Amount exceeds daily limit of ${daily_limit}"

            return True, None
        except KYCProfile.DoesNotExist:
            return False, "KYC profile not found"

    @staticmethod
    def get_user_limits(user):
        """Get user's current limits based on KYC level"""
        try:
            profile = user.kyc_profile
            level = profile.current_level

            if not level:
                return {
                    'daily_withdrawal': Decimal('0'),
                    'monthly_withdrawal': Decimal('0'),
                    'daily_deposit': Decimal('0'),
                    'can_trade': False,
                    'can_withdraw_crypto': False,
                    'can_withdraw_fiat': False
                }

            return {
                'daily_withdrawal': level.daily_withdrawal_limit,
                'monthly_withdrawal': level.monthly_withdrawal_limit,
                'daily_deposit': level.daily_deposit_limit,
                'can_trade': level.can_trade,
                'can_withdraw_crypto': level.can_withdraw_crypto,
                'can_withdraw_fiat': level.can_withdraw_fiat
            }
        except KYCProfile.DoesNotExist:
            return {
                'daily_withdrawal': Decimal('0'),
                'monthly_withdrawal': Decimal('0'),
                'daily_deposit': Decimal('0'),
                'can_trade': False,
                'can_withdraw_crypto': False,
                'can_withdraw_fiat': False
            }