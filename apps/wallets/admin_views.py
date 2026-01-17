"""
Admin API Views for Wallets
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model

from .models import Currency, Withdrawal
from .services.ledger import LedgerService
from .serializers import WithdrawalSerializer

User = get_user_model()


class AdminBalanceAdjustmentView(APIView):
    """
    POST /api/v1/wallets/admin/adjust-balance/

    Admin endpoint to adjust user balances by email.
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        user_email = request.data.get('user_email')
        currency_symbol = request.data.get('currency_symbol')
        amount = request.data.get('amount')
        adjustment_type = request.data.get('adjustment_type')
        reason = request.data.get('reason')

        # Validation
        if not all([user_email, currency_symbol, amount, adjustment_type, reason]):
            return Response(
                {'error': 'All fields are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            currency = Currency.objects.get(symbol=currency_symbol.upper())
        except Currency.DoesNotExist:
            return Response(
                {'error': 'Currency not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            from decimal import Decimal
            amount = Decimal(str(amount))

            balance, ledger_entry = LedgerService.admin_adjust_balance(
                admin_user=request.user,
                target_user=target_user,
                currency=currency,
                amount=amount,
                adjustment_type=adjustment_type,
                reason=reason
            )

            return Response({
                'message': 'Balance adjusted successfully',
                'user_email': target_user.email,
                'currency': currency.symbol,
                'adjustment_type': adjustment_type,
                'amount': str(amount),
                'new_balance': str(balance.available),
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AdminWithdrawalListView(APIView):
    """
    GET /api/v1/wallets/admin/withdrawals/

    List all pending withdrawals.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        withdrawals = Withdrawal.objects.filter(
            status='pending'
        ).select_related('user', 'currency').order_by('-created_at')

        data = []
        for w in withdrawals:
            data.append({
                'id': str(w.id),
                'user_email': w.user.email,
                'currency_symbol': w.currency.symbol,
                'amount': str(w.amount),
                'fee': str(w.fee),
                'to_address': w.to_address,
                'status': w.status,
                'created_at': w.created_at.isoformat(),
            })

        return Response(data)


class AdminWithdrawalApproveView(APIView):
    """
    POST /api/v1/wallets/admin/withdrawals/<id>/approve/
    """
    permission_classes = [IsAdminUser]

    def post(self, request, withdrawal_id):
        try:
            withdrawal = Withdrawal.objects.get(id=withdrawal_id)
        except Withdrawal.DoesNotExist:
            return Response(
                {'error': 'Withdrawal not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if withdrawal.status != 'pending':
            return Response(
                {'error': 'Withdrawal is not pending'},
                status=status.HTTP_400_BAD_REQUEST
            )

        withdrawal.status = 'approved'
        withdrawal.approved_by = request.user
        withdrawal.save()

        return Response({'message': 'Withdrawal approved'})


class AdminWithdrawalRejectView(APIView):
    """
    POST /api/v1/wallets/admin/withdrawals/<id>/reject/
    """
    permission_classes = [IsAdminUser]

    def post(self, request, withdrawal_id):
        try:
            withdrawal = Withdrawal.objects.get(id=withdrawal_id)
        except Withdrawal.DoesNotExist:
            return Response(
                {'error': 'Withdrawal not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if withdrawal.status != 'pending':
            return Response(
                {'error': 'Withdrawal is not pending'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Refund the balance
        LedgerService.credit_balance(
            user=withdrawal.user,
            currency=withdrawal.currency,
            amount=withdrawal.amount + withdrawal.fee,
            entry_type='withdrawal',
            description='Withdrawal rejected - refund',
            reference_type='withdrawal',
            reference_id=str(withdrawal.id)
        )

        withdrawal.status = 'rejected'
        withdrawal.rejection_reason = request.data.get('reason', 'Rejected by admin')
        withdrawal.save()

        return Response({'message': 'Withdrawal rejected and funds refunded'})