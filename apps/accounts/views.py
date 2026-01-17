"""
Accounts Views
==============
API endpoints for user authentication (email/password and wallet-based).
"""

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

            return Response({
                'message': 'Logout successful'
            })
        except Exception:
            return Response({
                'message': 'Logout successful'
            })


# =============================================================================
# WALLET AUTHENTICATION
# =============================================================================

class WalletNonceView(APIView):
    """
    POST /api/v1/auth/wallet/nonce/

    Request a nonce for wallet signature authentication.
    This is the first step in wallet-based login.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WalletNonceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wallet_address = serializer.validated_data['wallet_address']

        # Create nonce
        nonce = WalletAuthService.create_nonce(wallet_address)

        response_serializer = WalletNonceResponseSerializer({
            'nonce': nonce.nonce,
            'message': nonce.message,
            'expires_at': nonce.expires_at
        })

        return Response(response_serializer.data)


class WalletVerifyView(APIView):
    """
    POST /api/v1/auth/wallet/verify/

    Verify wallet signature and authenticate user.
    Creates a new user if the wallet is not connected to any account.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = WalletVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wallet_address = serializer.validated_data['wallet_address']
        signature = serializer.validated_data['signature']
        nonce = serializer.validated_data['nonce']

        # Verify signature
        is_valid = WalletAuthService.verify_signature(
            wallet_address=wallet_address,
            signature=signature,
            nonce=nonce
        )

        if not is_valid:
            return Response({
                'error': 'Invalid signature or expired nonce'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get or create user
        user, created = WalletAuthService.get_or_create_user_for_wallet(
            wallet_address=wallet_address
        )

        # Generate tokens
        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Wallet verified successfully',
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'is_new_user': created
        })


class WalletConnectView(APIView):
    """
    POST /api/v1/auth/wallet/connect/

    Connect a wallet to the currently authenticated user.
    Requires the user to be logged in.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WalletConnectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wallet_address = serializer.validated_data['wallet_address']
        signature = serializer.validated_data['signature']
        nonce = serializer.validated_data['nonce']
        wallet_type = serializer.validated_data['wallet_type']
        chain_id = serializer.validated_data['chain_id']

        # Verify signature
        is_valid = WalletAuthService.verify_signature(
            wallet_address=wallet_address,
            signature=signature,
            nonce=nonce
        )

        if not is_valid:
            return Response({
                'error': 'Invalid signature or expired nonce'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Connect wallet to user
            wallet_connection = WalletAuthService.connect_wallet_to_user(
                user=request.user,
                wallet_address=wallet_address,
                wallet_type=wallet_type,
                chain_id=chain_id
            )

            return Response({
                'message': 'Wallet connected successfully',
                'wallet': WalletConnectionSerializer(wallet_connection).data
            })

        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class WalletDisconnectView(APIView):
    """
    DELETE /api/v1/auth/wallet/<wallet_id>/disconnect/

    Disconnect a wallet from the current user.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, wallet_id):
        try:
            wallet = WalletConnection.objects.get(
                id=wallet_id,
                user=request.user
            )

            # Don't allow disconnecting the last wallet if user has no password
            if not request.user.has_usable_password():
                wallet_count = WalletConnection.objects.filter(
                    user=request.user
                ).count()
                if wallet_count <= 1:
                    return Response({
                        'error': 'Cannot disconnect the only wallet. Set a password first.'
                    }, status=status.HTTP_400_BAD_REQUEST)

            wallet.delete()

            return Response({
                'message': 'Wallet disconnected successfully'
            })

        except WalletConnection.DoesNotExist:
            return Response({
                'error': 'Wallet not found'
            }, status=status.HTTP_404_NOT_FOUND)


# =============================================================================
# USER PROFILE
# =============================================================================

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/auth/profile/
    PATCH /api/v1/auth/profile/

    Get or update the current user's profile.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserWalletsView(generics.ListAPIView):
    """
    GET /api/v1/auth/wallets/

    List all wallets connected to the current user.
    """
    serializer_class = WalletConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WalletConnection.objects.filter(user=self.request.user)


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/

    Change the current user's password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({
            'message': 'Password changed successfully'
        })


class SetPasswordView(APIView):
    """
    POST /api/v1/auth/set-password/

    Set password for wallet-only users who don't have a password yet.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.has_usable_password():
            return Response({
                'error': 'Password already set. Use change-password instead.'
            }, status=status.HTTP_400_BAD_REQUEST)

        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')

        if not password or len(password) < 10:
            return Response({
                'error': 'Password must be at least 10 characters'
            }, status=status.HTTP_400_BAD_REQUEST)

        if password != password_confirm:
            return Response({
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()

        return Response({
            'message': 'Password set successfully'
        })