"""
P2P Transfer API - Internal transfers between users
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal, InvalidOperation
import uuid

from .models import Balance, Currency

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_crypto(request):
    """
    Transfer crypto to another user on the platform
    """
    sender = request.user
    recipient_email = request.data.get('recipient_email', '').strip().lower()
    currency_symbol = request.data.get('currency', '').strip().upper()
    amount_str = request.data.get('amount', '')
    note = request.data.get('note', '')

    # Validate inputs
    if not recipient_email:
        return Response({'error': 'Recipient email is required'}, status=400)
    
    if not currency_symbol:
        return Response({'error': 'Currency is required'}, status=400)
    
    try:
        amount = Decimal(str(amount_str))
        if amount <= 0:
            return Response({'error': 'Amount must be positive'}, status=400)
    except (InvalidOperation, ValueError):
        return Response({'error': 'Invalid amount'}, status=400)

    # Cannot send to yourself
    if recipient_email == sender.email.lower():
        return Response({'error': 'Cannot transfer to yourself'}, status=400)

    # Find recipient
    try:
        recipient = User.objects.get(email__iexact=recipient_email)
    except User.DoesNotExist:
        return Response({'error': 'Recipient not found on this platform'}, status=404)

    # Find currency
    try:
        currency = Currency.objects.get(symbol=currency_symbol, is_active=True)
    except Currency.DoesNotExist:
        return Response({'error': f'Currency {currency_symbol} not found'}, status=404)

    # Perform transfer atomically
    with transaction.atomic():
        # Get or create sender balance
        sender_balance, _ = Balance.objects.get_or_create(
            user=sender,
            currency=currency,
            defaults={'available': Decimal('0'), 'locked': Decimal('0')}
        )

        # Check sufficient balance
        if sender_balance.available < amount:
            return Response({
                'error': f'Insufficient balance. You have {sender_balance.available} {currency_symbol}'
            }, status=400)

        # Get or create recipient balance
        recipient_balance, _ = Balance.objects.get_or_create(
            user=recipient,
            currency=currency,
            defaults={'available': Decimal('0'), 'locked': Decimal('0')}
        )

        # Deduct from sender
        sender_balance.available -= amount
        sender_balance.save()

        # Add to recipient
        recipient_balance.available += amount
        recipient_balance.save()

    return Response({
        'success': True,
        'message': f'Successfully transferred {amount} {currency_symbol} to {recipient.email}',
        'transaction': {
            'id': str(uuid.uuid4()),
            'from': sender.email,
            'to': recipient.email,
            'amount': str(amount),
            'currency': currency_symbol,
            'note': note,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transfer_qr_data(request):
    """
    Get data for generating QR code for receiving transfers
    """
    user = request.user
    return Response({
        'email': user.email,
        'user_id': str(user.id),
        'display_name': user.email.split('@')[0],
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    """
    Search for users to transfer to
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 3:
        return Response({'users': []})
    
    users = User.objects.filter(
        email__icontains=query,
        is_active=True
    ).exclude(
        id=request.user.id
    )[:10]
    
    return Response({
        'users': [
            {
                'email': u.email,
                'display_name': u.email.split('@')[0],
            }
            for u in users
        ]
    })
