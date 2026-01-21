"""
Email Views
===========
API endpoints for email verification
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone

from .models import EmailVerificationToken
from .services import EmailService
from .validators import EmailValidator


class ValidateEmailView(APIView):
    """
    Validate email format and domain before registration
    POST /api/v1/email/validate/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        
        if not email:
            return Response({
                'is_valid': False,
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = EmailValidator.validate_full(email)
        return Response(result)


class SendVerificationEmailView(APIView):
    """
    Send verification email to user
    POST /api/v1/email/send-verification/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Check if already verified
        if getattr(user, 'email_verified', False):
            return Response({
                'message': 'Email already verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Invalidate old tokens
        EmailVerificationToken.objects.filter(
            user=user,
            verified_at__isnull=True
        ).delete()
        
        # Create new token
        token = EmailVerificationToken.objects.create(
            user=user,
            email=user.email
        )
        
        # Send verification email
        sent = EmailService.send_verification_email(user, token)
        
        if sent:
            return Response({
                'message': 'Verification email sent',
                'email': user.email
            })
        else:
            return Response({
                'error': 'Failed to send verification email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyEmailView(APIView):
    """
    Verify email with token
    POST /api/v1/email/verify/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        token_str = request.data.get('token', '')
        
        if not token_str:
            return Response({
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = EmailVerificationToken.objects.get(token=token_str)
        except EmailVerificationToken.DoesNotExist:
            return Response({
                'error': 'Invalid verification token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if token.is_expired:
            return Response({
                'error': 'Token has expired. Please request a new verification email.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if token.is_verified:
            return Response({
                'message': 'Email already verified'
            })
        
        # Verify the token
        if token.verify():
            return Response({
                'message': 'Email verified successfully',
                'email': token.email
            })
        else:
            return Response({
                'error': 'Verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    """
    Resend verification email
    POST /api/v1/email/resend-verification/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return SendVerificationEmailView().post(request)
