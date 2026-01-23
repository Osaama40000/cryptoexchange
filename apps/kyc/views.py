"""
KYC Views
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from .models import KYCLevel, KYCProfile, KYCDocument, KYCVerificationRequest, KYCAuditLog
from .serializers import (
    KYCLevelSerializer, KYCProfileSerializer, KYCProfileUpdateSerializer,
    KYCDocumentSerializer, KYCDocumentUploadSerializer,
    KYCVerificationRequestSerializer, SubmitVerificationSerializer,
    KYCAuditLogSerializer,
    AdminKYCProfileSerializer, AdminDocumentReviewSerializer, AdminVerificationReviewSerializer
)
from .services import KYCService


class KYCLevelListView(APIView):
    """List all KYC levels and their requirements"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        levels = KYCLevel.objects.all().order_by('daily_withdrawal_limit')
        serializer = KYCLevelSerializer(levels, many=True)
        return Response(serializer.data)


class KYCProfileView(APIView):
    """Get or update user's KYC profile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = KYCService.get_or_create_profile(request.user)
        serializer = KYCProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile = KYCService.get_or_create_profile(request.user)

        if profile.status == KYCProfile.Status.PENDING:
            return Response(
                {'error': 'Cannot update profile while verification is pending'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = KYCProfileUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            KYCService.update_profile(profile, serializer.validated_data, request)
            return Response(KYCProfileSerializer(profile).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KYCDocumentUploadView(APIView):
    """Upload KYC documents"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = KYCDocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        profile = KYCService.get_or_create_profile(request.user)

        document = KYCService.upload_document(
            profile=profile,
            document_type=serializer.validated_data['document_type'],
            file=serializer.validated_data['file'],
            document_number=serializer.validated_data.get('document_number', ''),
            issuing_country=serializer.validated_data.get('issuing_country', ''),
            issue_date=serializer.validated_data.get('issue_date'),
            expiry_date=serializer.validated_data.get('expiry_date')
        )

        return Response(
            KYCDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )


class KYCDocumentListView(APIView):
    """List user's KYC documents"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = KYCService.get_or_create_profile(request.user)
        documents = profile.documents.all()
        serializer = KYCDocumentSerializer(documents, many=True)
        return Response(serializer.data)


class KYCDocumentDeleteView(APIView):
    """Delete a pending KYC document"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, document_id):
        profile = KYCService.get_or_create_profile(request.user)
        document = get_object_or_404(
            KYCDocument,
            id=document_id,
            kyc_profile=profile,
            status=KYCDocument.Status.PENDING
        )

        document.file.delete()
        document.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class SubmitVerificationView(APIView):
    """Submit verification request"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubmitVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        profile = KYCService.get_or_create_profile(request.user)

        if profile.status == KYCProfile.Status.PENDING:
            return Response(
                {'error': 'You already have a pending verification request'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            verification_request = KYCService.submit_verification(
                profile=profile,
                target_level_type=serializer.validated_data['target_level'],
                document_ids=serializer.validated_data.get('document_ids')
            )

            return Response(
                KYCVerificationRequestSerializer(verification_request).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class VerificationStatusView(APIView):
    """Get verification request status"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = KYCService.get_or_create_profile(request.user)
        requests = profile.verification_requests.all()[:10]
        serializer = KYCVerificationRequestSerializer(requests, many=True)
        return Response(serializer.data)


class KYCLimitsView(APIView):
    """Get user's current KYC limits"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limits = KYCService.get_user_limits(request.user)
        return Response({
            'daily_withdrawal_limit': str(limits['daily_withdrawal']),
            'monthly_withdrawal_limit': str(limits['monthly_withdrawal']),
            'daily_deposit_limit': str(limits['daily_deposit']),
            'can_trade': limits['can_trade'],
            'can_withdraw_crypto': limits['can_withdraw_crypto'],
            'can_withdraw_fiat': limits['can_withdraw_fiat']
        })


# Admin Views

class AdminKYCProfileListView(APIView):
    """Admin: List all KYC profiles"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        status_filter = request.query_params.get('status')
        level_filter = request.query_params.get('level')

        profiles = KYCProfile.objects.select_related('user', 'current_level').all()

        if status_filter:
            profiles = profiles.filter(status=status_filter)
        if level_filter:
            profiles = profiles.filter(current_level__level=level_filter)

        profiles = profiles.order_by('-updated_at')[:100]
        serializer = AdminKYCProfileSerializer(profiles, many=True)
        return Response(serializer.data)


class AdminKYCProfileDetailView(APIView):
    """Admin: Get KYC profile details"""
    permission_classes = [IsAdminUser]

    def get(self, request, profile_id):
        profile = get_object_or_404(KYCProfile, id=profile_id)
        serializer = AdminKYCProfileSerializer(profile)
        return Response(serializer.data)


class AdminPendingVerificationsView(APIView):
    """Admin: List pending verification requests"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        pending = KYCVerificationRequest.objects.filter(
            status__in=[
                KYCVerificationRequest.Status.PENDING,
                KYCVerificationRequest.Status.IN_REVIEW
            ]
        ).select_related('kyc_profile__user', 'target_level').order_by('submitted_at')

        serializer = KYCVerificationRequestSerializer(pending, many=True)
        return Response(serializer.data)


class AdminDocumentReviewView(APIView):
    """Admin: Review a KYC document"""
    permission_classes = [IsAdminUser]

    def post(self, request, document_id):
        document = get_object_or_404(KYCDocument, id=document_id)
        serializer = AdminDocumentReviewSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data['action']

        if action == 'approve':
            document = KYCService.approve_document(
                document=document,
                admin_user=request.user,
                document_number=serializer.validated_data.get('document_number'),
                issuing_country=serializer.validated_data.get('issuing_country'),
                expiry_date=serializer.validated_data.get('expiry_date')
            )
        else:
            document = KYCService.reject_document(
                document=document,
                admin_user=request.user,
                reason=serializer.validated_data['rejection_reason']
            )

        return Response(KYCDocumentSerializer(document).data)


class AdminVerificationReviewView(APIView):
    """Admin: Review a verification request"""
    permission_classes = [IsAdminUser]

    def post(self, request, request_id):
        verification_request = get_object_or_404(KYCVerificationRequest, id=request_id)
        serializer = AdminVerificationReviewSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('admin_notes', '')

        if action == 'approve':
            verification_request = KYCService.approve_verification(
                verification_request=verification_request,
                admin_user=request.user,
                notes=notes
            )
        elif action == 'reject':
            verification_request = KYCService.reject_verification(
                verification_request=verification_request,
                admin_user=request.user,
                reason=serializer.validated_data['rejection_reason'],
                notes=notes
            )
        else:
            verification_request = KYCService.request_more_info(
                verification_request=verification_request,
                admin_user=request.user,
                info_request=serializer.validated_data['additional_info_request'],
                notes=notes
            )

        return Response(KYCVerificationRequestSerializer(verification_request).data)


class AdminKYCAuditLogView(APIView):
    """Admin: View KYC audit logs"""
    permission_classes = [IsAdminUser]

    def get(self, request, profile_id=None):
        if profile_id:
            logs = KYCAuditLog.objects.filter(kyc_profile_id=profile_id)
        else:
            logs = KYCAuditLog.objects.all()

        logs = logs.select_related('performed_by').order_by('-created_at')[:100]
        serializer = KYCAuditLogSerializer(logs, many=True)
        return Response(serializer.data)