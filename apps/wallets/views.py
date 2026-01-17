"""
Wallets Views
=============
API endpoints for balance management, deposits, and withdrawals.
"""

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.conf import settings

from .models import Currency, Balance, LedgerEntry, Deposit, Withdrawal
from .serializers import (
    CurrencySerializer,
    BalanceSerializer,
    BalanceSummarySerializer,
    LedgerEntrySerializer,
    DepositSerializer,
    WithdrawalSerializer,
    WithdrawalRequestSerializer,
    AdminBalanceAdjustmentSerializer,
)
from .services.ledger import LedgerService


# =============================================================================
# CURRENCY ENDPOINTS
# =============================================================================

class CurrencyListView(generics.ListAPIView):
    """
    GET /api/v1/wallets/currencies/

    List all active currencies.
    """
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Currency.objects.filter(is_active=True)


# =============================================================================
# BALANCE ENDPOINTS
# =============================================================================

class BalanceListView(APIView):
    """
    GET /api/v1/wallets/balances/

    Get all balances for the current user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        balances = Balance.objects.filter(
            user=request.user
        ).select_related('currency')

        existing_currencies = set(b.currency_id for b in balances)
        active_currencies = Currency.objects.filter(is_active=True)

        result = []

        for balance in balances:
            result.append({
                'currency_symbol': balance.currency.symbol,
                'currency_name': balance.currency.name,
                'available': balance.available,
                'locked': balance.locked,
                'total': balance.total,
            })

        for currency in active_currencies:
            if currency.id not in existing_currencies:
                result.append({
                    'currency_symbol': currency.symbol,
                    'currency_name': currency.name,
                    'available': '0',
                    'locked': '0',
                    'total': '0',
                })

        result.sort(key=lambda x: x['currency_symbol'])

        serializer = BalanceSummarySerializer(result, many=True)
        return Response(serializer.data)


class BalanceDetailView(APIView):
    """
    GET /api/v1/wallets/balances/<currency_symbol>/

    Get balance for a specific currency.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, currency_symbol):
        try:
            currency = Currency.objects.get(
                symbol=currency_symbol.upper(),
                is_active=True
            )
        except Currency.DoesNotExist:
            return Response(
                {'error': 'Currency not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        balance = LedgerService.get_or_create_balance(request.user, currency)

        return Response({
            'currency_symbol': currency.symbol,
            'currency_name': currency.name,
            'available': str(balance.available),
            'locked': str(balance.locked),
            'total': str(balance.total),
        })


# =============================================================================
# LEDGER ENDPOINTS
# =============================================================================

class LedgerHistoryView(generics.ListAPIView):
    """
    GET /api/v1/wallets/ledger/

    Get ledger history for the current user.
    """
    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = LedgerEntry.objects.filter(
            user=self.request.user
        ).select_related('currency')

        currency_symbol = self.request.query_params.get('currency')
        if currency_symbol:
            queryset = queryset.filter(currency__symbol=currency_symbol.upper())

        entry_type = self.request.query_params.get('type')
        if entry_type:
            queryset = queryset.filter(entry_type=entry_type)

        return queryset.order_by('-created_at')


# =============================================================================
# DEPOSIT ENDPOINTS
# =============================================================================

class DepositAddressView(APIView):
    """
    GET /api/v1/wallets/deposit-address/<currency_symbol>/

    Get deposit address for a currency.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, currency_symbol):
        try:
            currency = Currency.objects.get(
                symbol=currency_symbol.upper(),
                is_active=True
            )
        except Currency.DoesNotExist:
            return Response(
                {'error': 'Currency not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not currency.is_deposit_enabled:
            return Response(
                {'error': 'Deposits are disabled for this currency'},
                status=status.HTTP_400_BAD_REQUEST
            )

        network_info = settings.BLOCKCHAIN_CONFIG['NETWORKS'].get(currency.chain_id, {})

        deposit_address = "0xDEMO_DEPOSIT_ADDRESS_GENERATE_UNIQUE_PER_USER"

        wallet = request.user.wallet_connections.filter(is_primary=True).first()
        if wallet:
            note = "Your connected wallet: " + wallet.wallet_address
        else:
            note = "Connect a wallet to see your address"

        return Response({
            'currency_symbol': currency.symbol,
            'address': deposit_address,
            'chain_id': currency.chain_id,
            'network_name': network_info.get('name', 'Unknown Network'),
            'min_deposit': str(currency.min_deposit),
            'confirmations_required': settings.BLOCKCHAIN_CONFIG['MIN_CONFIRMATIONS'],
            'note': note,
            'warning': 'DEMO MODE: This is a test address. Do not send real funds!'
        })


class DepositListView(generics.ListAPIView):
    """
    GET /api/v1/wallets/deposits/

    List all deposits for the current user.
    """
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Deposit.objects.filter(
            user=self.request.user
        ).select_related('currency').order_by('-created_at')


# =============================================================================
# WITHDRAWAL ENDPOINTS
# =============================================================================

class WithdrawalListView(generics.ListAPIView):
    """
    GET /api/v1/wallets/withdrawals/

    List all withdrawals for the current user.
    """
    serializer_class = WithdrawalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Withdrawal.objects.filter(
            user=self.request.user
        ).select_related('currency').order_by('-created_at')


class WithdrawalCreateView(APIView):
    """
    POST /api/v1/wallets/withdrawals/create/

    Create a new withdrawal request.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            withdrawal = LedgerService.create_withdrawal(
                user=request.user,
                currency=serializer.validated_data['currency'],
                to_address=serializer.validated_data['to_address'],
                amount=serializer.validated_data['amount']
            )

            return Response({
                'message': 'Withdrawal request created successfully',
                'withdrawal': WithdrawalSerializer(withdrawal).data,
                'note': 'DEMO MODE: Withdrawals are not actually processed on-chain.'
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class WithdrawalCancelView(APIView):
    """
    POST /api/v1/wallets/withdrawals/<withdrawal_id>/cancel/

    Cancel a pending withdrawal.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, withdrawal_id):
        try:
            withdrawal = Withdrawal.objects.get(
                id=withdrawal_id,
                user=request.user
            )
        except Withdrawal.DoesNotExist:
            return Response(
                {'error': 'Withdrawal not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if withdrawal.status != 'pending':
            return Response(
                {'error': 'Cannot cancel withdrawal with status: ' + withdrawal.status},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_refund = withdrawal.amount + withdrawal.fee
        LedgerService.credit_balance(
            user=request.user,
            currency=withdrawal.currency,
            amount=total_refund,
            entry_type='withdrawal',
            description='Cancelled withdrawal refund',
            reference_type='withdrawal',
            reference_id=str(withdrawal.id)
        )

        withdrawal.status = 'rejected'
        withdrawal.rejection_reason = 'Cancelled by user'
        withdrawal.save()

        return Response({
            'message': 'Withdrawal cancelled successfully',
            'withdrawal': WithdrawalSerializer(withdrawal).data
        })


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

class AdminBalanceAdjustmentView(APIView):
    """
    POST /api/v1/wallets/admin/adjust-balance/

    Admin endpoint to adjust user balances.
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = AdminBalanceAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            balance, ledger_entry = LedgerService.admin_adjust_balance(
                admin_user=request.user,
                target_user=serializer.validated_data['user'],
                currency=serializer.validated_data['currency'],
                amount=serializer.validated_data['amount'],
                adjustment_type=serializer.validated_data['adjustment_type'],
                reason=serializer.validated_data['reason']
            )

            return Response({
                'message': 'Balance adjusted successfully',
                'user_email': serializer.validated_data['user'].email,
                'currency': serializer.validated_data['currency'].symbol,
                'adjustment_type': serializer.validated_data['adjustment_type'],
                'amount': str(serializer.validated_data['amount']),
                'new_balance': str(balance.available),
                'ledger_entry_id': str(ledger_entry.id)
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )