"""
Accounts Serializers
====================
Serializers for user registration, login, and wallet authentication.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, WalletConnection, AuthNonce


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_email_verified', 'is_2fa_enabled', 'created_at'
        ]
        read_only_fields = ['id', 'is_email_verified', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        min_length=10,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for email/password login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError('Invalid email or password.')

        if not user.is_active:
            raise serializers.ValidationError('Account is disabled.')

        attrs['user'] = user
        return attrs


class WalletConnectionSerializer(serializers.ModelSerializer):
    """Serializer for Wallet Connection."""

    class Meta:
        model = WalletConnection
        fields = [
            'id', 'wallet_address', 'chain_id', 'wallet_type',
            'is_primary', 'is_verified', 'last_used_at', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'last_used_at', 'created_at']


class WalletNonceRequestSerializer(serializers.Serializer):
    """Request a nonce for wallet authentication."""

    wallet_address = serializers.CharField(max_length=42)

    def validate_wallet_address(self, value):
        # Basic Ethereum address validation
        if not value.startswith('0x') or len(value) != 42:
            raise serializers.ValidationError('Invalid Ethereum address format.')

        # Convert to checksum address
        from web3 import Web3
        try:
            return Web3.to_checksum_address(value)
        except Exception:
            raise serializers.ValidationError('Invalid Ethereum address.')


class WalletNonceResponseSerializer(serializers.Serializer):
    """Response with nonce for signing."""

    nonce = serializers.CharField()
    message = serializers.CharField()
    expires_at = serializers.DateTimeField()


class WalletVerifySerializer(serializers.Serializer):
    """Verify wallet signature."""

    wallet_address = serializers.CharField(max_length=42)
    signature = serializers.CharField()
    nonce = serializers.CharField()

    def validate_wallet_address(self, value):
        from web3 import Web3
        try:
            return Web3.to_checksum_address(value)
        except Exception:
            raise serializers.ValidationError('Invalid Ethereum address.')


class WalletConnectSerializer(serializers.Serializer):
    """Connect wallet to existing user account."""

    wallet_address = serializers.CharField(max_length=42)
    signature = serializers.CharField()
    nonce = serializers.CharField()
    wallet_type = serializers.ChoiceField(
        choices=['metamask', 'walletconnect'],
        default='metamask'
    )
    chain_id = serializers.IntegerField(default=1)

    def validate_wallet_address(self, value):
        from web3 import Web3
        try:
            return Web3.to_checksum_address(value)
        except Exception:
            raise serializers.ValidationError('Invalid Ethereum address.')


class ChangePasswordSerializer(serializers.Serializer):
    """Change user password."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        min_length=10,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs