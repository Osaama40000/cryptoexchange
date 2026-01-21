"""
Accounts Views
==============
API endpoints for user authentication (email/password and wallet-based).
"""
import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout

from .models import User, WalletConnection, AuthNonce
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    WalletConnectionSerializer,
    WalletNonceRequestSerializer,
    WalletNonceResponseSerializer,
    WalletVerifySerializer,
    WalletConnectSerializer,
    ChangePasswordSerializer,
)
from .services.wallet_auth import WalletAuthService

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    """Generate JWT tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# =============================================================================
# EMAIL/PASSWORD AUTHENTICATION
# =============================================================================

class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Register a new user with email and password.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send welcome email notification
        try:
            from emails.services import EmailService
            EmailService.send_welcome_email(user)
            logger.info(f"Welcome email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {e}")
        
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Registration successful',
            'user': UserSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Login with email and password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Send login alert email notification
        try:
            from emails.notifications import notify_login
            notify_login(user, request)
            logger.info(f"Login alert sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send login alert to {user.email}: {e}")
        
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': tokens
        })


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Logout and blacklist the refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            logout(request)
            return Response({
                'message': 'Logout successful'
            })
        except Exception as e:
            return Response({
                'message': 'Logout successful'
            })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/auth/profile/
    PUT /api/v1/auth/profile/
    Get or update user profile.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    Change user password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Send password changed notification
        try:
            from emails.notifications import notify_password_changed
            notify_password_changed(user)
            logger.info(f"Password changed email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password changed email to {user.email}: {e}")
        
        return Response({
            'message': 'Password changed successfully'
        })


# =============================================================================
# WALLET-BASED AUTHENTICATION
# =============================================================================

class WalletNonceView(APIView):
    """
    POST /api/v1/auth/wallet/nonce/
    Request a nonce for wallet signature verification.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WalletNonceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet_address = serializer.validated_data['wallet_address']
        nonce_data = WalletAuthService.generate_nonce(wallet_address)
        
        return Response(WalletNonceResponseSerializer(nonce_data).data)


class WalletVerifyView(APIView):
    """
    POST /api/v1/auth/wallet/verify/
    Verify wallet signature and authenticate user.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WalletVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet_address = serializer.validated_data['wallet_address']
        signature = serializer.validated_data['signature']
        
        result = WalletAuthService.verify_signature(wallet_address, signature)
        
        if result['success']:
            user = result['user']
            is_new_user = result.get('created', False)
            
            # Send welcome email for new wallet users
            if is_new_user:
                try:
                    from emails.services import EmailService
                    if user.email:
                        EmailService.send_welcome_email(user)
                        logger.info(f"Welcome email sent to new wallet user {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send welcome email: {e}")
            
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Wallet verified successfully',
                'user': UserSerializer(user).data,
                'tokens': tokens,
                'created': is_new_user
            })
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)


class WalletConnectView(APIView):
    """
    POST /api/v1/auth/wallet/connect/
    Connect a wallet to an existing authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WalletConnectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet_address = serializer.validated_data['wallet_address']
        signature = serializer.validated_data['signature']
        
        result = WalletAuthService.connect_wallet(
            request.user,
            wallet_address,
            signature
        )
        
        if result['success']:
            return Response({
                'message': 'Wallet connected successfully',
                'wallet': WalletConnectionSerializer(result['wallet']).data
            })
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)


class WalletDisconnectView(APIView):
    """
    POST /api/v1/auth/wallet/disconnect/
    Disconnect a wallet from the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        wallet_address = request.data.get('wallet_address')
        
        if not wallet_address:
            return Response({
                'error': 'Wallet address is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = WalletAuthService.disconnect_wallet(
            request.user,
            wallet_address
        )
        
        if result['success']:
            return Response({
                'message': 'Wallet disconnected successfully'
            })
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)


class UserWalletsView(generics.ListAPIView):
    """
    GET /api/v1/auth/wallets/
    List all wallets connected to the authenticated user.
    """
    serializer_class = WalletConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WalletConnection.objects.filter(user=self.request.user)
