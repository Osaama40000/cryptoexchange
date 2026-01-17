"""
Wallets Serializers
===================
Serializers for balance, deposit, and withdrawal operations.
"""

from rest_framework import serializers
from decimal import Decimal
from web3 import Web3

from .models import Currency, Balance, LedgerEntry, Deposit, Withdrawal


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer for Currency model."""

    class Meta:
        model = Currency
        fields = [
            'id', 'symbol', 'name', 'currency_type', 'contract_address',
            'decimals', 'chain_id', 'is_active', 'is_deposit_enabled',
            'is_withdrawal_enabled', 'min_deposit', 'min_withdrawal',
            'withdrawal_fee', 'icon_url'
        ]


class BalanceSerializer(serializers.ModelSerializer):
    """Serializer for user balance."""

    currency = CurrencySerializer(read_only=True)
    currency_id = serializers.UUIDField(write_only=True)
    total = serializers.DecimalField(
        max_digits=36, decimal_places=18, read_only=True
    )

    class Meta:
        model = Balance
        fields = [
            'id', 'currency', 'currency_id', 'available',
            'locked', 'total', 'updated_at'
        ]
        read_only_fields = ['id', 'available', 'locked', 'updated_at']


class BalanceSummarySerializer(serializers.Serializer):
    """Simple balance summary for dashboard."""

    currency_symbol = serializers.CharField()
    currency_name = serializers.CharField()
    available = serializers.DecimalField(max_digits=36, decimal_places=18)
    locked = serializers.DecimalField(max_digits=36, decimal_places=18)
    total = serializers.DecimalField(max_digits=36, decimal_places=18)


class LedgerEntrySerializer(serializers.ModelSerializer):
    """Serializer for ledger entries."""

    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)

    class Meta:
        model = LedgerEntry
        fields = [
            'id', 'currency_symbol', 'entry_type', 'amount',
            'balance_before', 'balance_after', 'description',
            'reference_type', 'reference_id', 'created_at'
        ]


class DepositSerializer(serializers.ModelSerializer):
    """Serializer for deposits."""

    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)

    class Meta:
        model = Deposit
        fields = [
            'id', 'currency_symbol', 'tx_hash', 'from_address',
            'to_address', 'amount', 'confirmations', 'required_confirmations',
            'status', 'block_number', 'chain_id', 'credited_at', 'created_at'
        ]


class WithdrawalSerializer(serializers.ModelSerializer):
    """Serializer for withdrawals."""

    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    net_amount = serializers.DecimalField(
        max_digits=36, decimal_places=18, read_only=True
    )

    class Meta:
        model = Withdrawal
        fields = [
            'id', 'currency_symbol', 'to_address', 'amount', 'fee',
            'net_amount', 'tx_hash', 'status', 'rejection_reason',
            'chain_id', 'created_at', 'processed_at'
        ]


class WithdrawalRequestSerializer(serializers.Serializer):
    """Serializer for withdrawal requests."""

    currency_id = serializers.UUIDField()
    to_address = serializers.CharField(max_length=42)
    amount = serializers.DecimalField(max_digits=36, decimal_places=18)

    def validate_to_address(self, value):
        """Validate Ethereum address."""
        if not value.startswith('0x') or len(value) != 42:
            raise serializers.ValidationError('Invalid Ethereum address format.')

        try:
            return Web3.to_checksum_address(value)
        except Exception:
            raise serializers.ValidationError('Invalid Ethereum address.')

    def validate_amount(self, value):
        """Validate withdrawal amount."""
        if value <= Decimal('0'):
            raise serializers.ValidationError('Amount must be greater than 0.')
        return value

    def validate(self, attrs):
        """Validate withdrawal request."""
        try:
            currency = Currency.objects.get(id=attrs['currency_id'])
        except Currency.DoesNotExist:
            raise serializers.ValidationError({'currency_id': 'Currency not found.'})

        if not currency.is_active:
            raise serializers.ValidationError({'currency_id': 'Currency is not active.'})

        if not currency.is_withdrawal_enabled:
            raise serializers.ValidationError({
                'currency_id': 'Withdrawals are disabled for this currency.'
            })

        if attrs['amount'] < currency.min_withdrawal:
            raise serializers.ValidationError({
                'amount': f'Minimum withdrawal is {currency.min_withdrawal} {currency.symbol}.'
            })

        attrs['currency'] = currency
        return attrs


class DepositAddressSerializer(serializers.Serializer):
    """Serializer for deposit address response."""

    currency_symbol = serializers.CharField()
    address = serializers.CharField()
    chain_id = serializers.IntegerField()
    network_name = serializers.CharField()
    min_deposit = serializers.DecimalField(max_digits=36, decimal_places=18)
    confirmations_required = serializers.IntegerField()


# =============================================================================
# ADMIN SERIALIZERS
# =============================================================================

class AdminBalanceAdjustmentSerializer(serializers.Serializer):
    """Serializer for admin balance adjustments."""

    user_id = serializers.UUIDField()
    currency_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=36, decimal_places=18)
    adjustment_type = serializers.ChoiceField(choices=['credit', 'debit'])
    reason = serializers.CharField(max_length=500)

    def validate_amount(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Amount must be greater than 0.')
        return value

    def validate(self, attrs):
        from apps.accounts.models import User

        try:
            attrs['user'] = User.objects.get(id=attrs['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_id': 'User not found.'})

        try:
            attrs['currency'] = Currency.objects.get(id=attrs['currency_id'])
        except Currency.DoesNotExist:
            raise serializers.ValidationError({'currency_id': 'Currency not found.'})

        return attrs