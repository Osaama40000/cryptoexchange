"""
Wallets Views
=============
API endpoints for balance management, deposits, and withdrawals.
"""

import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Balance, Currency, LedgerEntry

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

logger = logging.getLogger(__name__)


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


class DepositHistoryView(generics.ListAPIView):
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

            # Send withdrawal requested email notification
            try:
                from emails.notifications import notify_withdrawal_requested
                notify_withdrawal_requested(request.user, withdrawal)
                logger.info(f"Withdrawal requested email sent to {request.user.email}")
            except Exception as e:
                logger.error(f"Failed to send withdrawal requested email: {e}")

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


User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def p2p_transfer(request):
    """
    Transfer crypto from one user to another within the platform.

    Request body:
    {
        "currency_symbol": "BTC",
        "recipient_email": "user@example.com",  # OR
        "recipient_username": "username",
        "amount": "0.001",
        "note": "Optional message"
    }
    """
    try:
        currency_symbol = request.data.get('currency_symbol')
        recipient_email = request.data.get('recipient_email')
        recipient_username = request.data.get('recipient_username')
        amount = Decimal(str(request.data.get('amount', 0)))
        note = request.data.get('note', '')

        # Validate required fields
        if not currency_symbol:
            return Response(
                {'error': 'Currency is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not recipient_email and not recipient_username:
            return Response(
                {'error': 'Recipient email or username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount <= 0:
            return Response(
                {'error': 'Amount must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get currency
        try:
            currency = Currency.objects.get(symbol=currency_symbol)
        except Currency.DoesNotExist:
            return Response(
                {'error': f'Currency {currency_symbol} not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find recipient
        recipient = None
        if recipient_email:
            try:
                recipient = User.objects.get(email=recipient_email)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Recipient not found with this email'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif recipient_username:
            try:
                recipient = User.objects.get(username=recipient_username)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Recipient not found with this username'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check if sender is trying to send to themselves
        if recipient == request.user:
            return Response(
                {'error': 'Cannot transfer to yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create sender's balance
        sender_balance, _ = Balance.objects.get_or_create(
            user=request.user,
            currency=currency,
            defaults={'available': Decimal('0'), 'locked': Decimal('0')}
        )

        # Check sender has sufficient balance
        if sender_balance.available < amount:
            return Response(
                {'error': 'Insufficient balance'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create recipient's balance
        recipient_balance, _ = Balance.objects.get_or_create(
            user=recipient,
            currency=currency,
            defaults={'available': Decimal('0'), 'locked': Decimal('0')}
        )

        # Perform transfer atomically
        with transaction.atomic():
            # Deduct from sender
            sender_balance.available -= amount
            sender_balance.save()

            # Add to recipient
            recipient_balance.available += amount
            recipient_balance.save()

            # Create transfer record
            transfer = P2PTransfer.objects.create(
                sender=request.user,
                recipient=recipient,
                currency=currency,
                amount=amount,
                note=note,
                status='completed'
            )

            # Create ledger entries for audit trail
            LedgerEntry.objects.create(
                user=request.user,
                currency=currency,
                entry_type='p2p_send',
                amount=-amount,
                balance_after=sender_balance.available,
                reference_id=str(transfer.id),
                description=f'P2P transfer to {recipient.email or recipient.username}'
            )

            LedgerEntry.objects.create(
                user=recipient,
                currency=currency,
                entry_type='p2p_receive',
                amount=amount,
                balance_after=recipient_balance.available,
                reference_id=str(transfer.id),
                description=f'P2P transfer from {request.user.email or request.user.username}'
            )

        return Response({
            'success': True,
            'message': f'Successfully sent {amount} {currency_symbol} to {recipient.email or recipient.username}',
            'transfer': {
                'id': transfer.id,
                'amount': str(amount),
                'currency': currency_symbol,
                'recipient': recipient.email or recipient.username,
                'status': 'completed',
                'created_at': transfer.created_at.isoformat()
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transfers(request):
    """
    Get user's P2P transfer history (both sent and received).
    """
    try:
        # Get transfers where user is sender or recipient
        sent = P2PTransfer.objects.filter(sender=request.user).select_related('recipient', 'currency')
        received = P2PTransfer.objects.filter(recipient=request.user).select_related('sender', 'currency')

        transfers = []

        for t in sent:
            transfers.append({
                'id': t.id,
                'type': 'sent',
                'currency_symbol': t.currency.symbol,
                'amount': str(t.amount),
                'recipient': t.recipient.email or t.recipient.username,
                'note': t.note,
                'status': t.status,
                'created_at': t.created_at.isoformat()
            })

        for t in received:
            transfers.append({
                'id': t.id,
                'type': 'received',
                'currency_symbol': t.currency.symbol,
                'amount': str(t.amount),
                'sender': t.sender.email or t.sender.username,
                'note': t.note,
                'status': t.status,
                'created_at': t.created_at.isoformat()
            })

        # Sort by date descending
        transfers.sort(key=lambda x: x['created_at'], reverse=True)

        return Response(transfers, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )