"""
Ledger Service
==============
Core service for managing internal balances.
All balance changes go through this service to ensure:
1. Atomic transactions
2. Complete audit trail
3. Proper balance validation
"""

import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.wallets.models import Currency, Balance, LedgerEntry, Deposit, Withdrawal
from apps.accounts.models import User

logger = logging.getLogger('apps.wallets')


class LedgerService:
    """
    Service for managing internal ledger operations.

    IMPORTANT: This is an INTERNAL ledger - it does NOT interact with
    the blockchain directly. All operations are off-chain database updates.
    """

    @staticmethod
    @transaction.atomic
    def get_or_create_balance(user: User, currency: Currency) -> Balance:
        """
        Get or create a balance record for a user and currency.

        Args:
            user: User object
            currency: Currency object

        Returns:
            Balance object
        """
        balance, created = Balance.objects.select_for_update().get_or_create(
            user=user,
            currency=currency,
            defaults={'available': Decimal('0'), 'locked': Decimal('0')}
        )

        if created:
            logger.info(f"Created new balance for {user.email} - {currency.symbol}")

        return balance

    @staticmethod
    @transaction.atomic
    def credit_balance(
            user: User,
            currency: Currency,
            amount: Decimal,
            entry_type: str,
            description: str = None,
            reference_type: str = None,
            reference_id: str = None,
            created_by: User = None
    ) -> tuple[Balance, LedgerEntry]:
        """
        Credit (add) amount to user's available balance.

        Args:
            user: User to credit
            currency: Currency to credit
            amount: Amount to credit (must be positive)
            entry_type: Type of ledger entry
            description: Optional description
            reference_type: Type of related object (deposit, trade, etc.)
            reference_id: ID of related object
            created_by: User who initiated this action (for admin actions)

        Returns:
            Tuple of (Balance, LedgerEntry)
        """
        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        # Get or create balance with lock
        balance = LedgerService.get_or_create_balance(user, currency)

        # Record before state
        balance_before = balance.available

        # Update balance
        balance.available += amount
        balance.version += 1
        balance.save()

        # Create ledger entry
        ledger_entry = LedgerEntry.objects.create(
            user=user,
            currency=currency,
            entry_type=entry_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance.available,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=created_by
        )

        logger.info(
            f"Credited {amount} {currency.symbol} to {user.email}. "
            f"Balance: {balance_before} -> {balance.available}"
        )

        return balance, ledger_entry

    @staticmethod
    @transaction.atomic
    def debit_balance(
            user: User,
            currency: Currency,
            amount: Decimal,
            entry_type: str,
            description: str = None,
            reference_type: str = None,
            reference_id: str = None,
            created_by: User = None
    ) -> tuple[Balance, LedgerEntry]:
        """
        Debit (subtract) amount from user's available balance.

        Args:
            user: User to debit
            currency: Currency to debit
            amount: Amount to debit (must be positive)
            entry_type: Type of ledger entry
            description: Optional description
            reference_type: Type of related object
            reference_id: ID of related object
            created_by: User who initiated this action

        Returns:
            Tuple of (Balance, LedgerEntry)

        Raises:
            ValueError: If insufficient balance
        """
        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError("Debit amount must be positive")

        # Get balance with lock
        balance = LedgerService.get_or_create_balance(user, currency)

        if balance.available < amount:
            raise ValueError(
                f"Insufficient balance. Available: {balance.available}, "
                f"Required: {amount}"
            )

        # Record before state
        balance_before = balance.available

        # Update balance
        balance.available -= amount
        balance.version += 1
        balance.save()

        # Create ledger entry (negative amount for debit)
        ledger_entry = LedgerEntry.objects.create(
            user=user,
            currency=currency,
            entry_type=entry_type,
            amount=-amount,
            balance_before=balance_before,
            balance_after=balance.available,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=created_by
        )

        logger.info(
            f"Debited {amount} {currency.symbol} from {user.email}. "
            f"Balance: {balance_before} -> {balance.available}"
        )

        return balance, ledger_entry

    @staticmethod
    @transaction.atomic
    def lock_balance(
            user: User,
            currency: Currency,
            amount: Decimal,
            reference_type: str = None,
            reference_id: str = None
    ) -> tuple[Balance, LedgerEntry]:
        """
        Lock amount for an order (move from available to locked).

        Args:
            user: User
            currency: Currency
            amount: Amount to lock
            reference_type: Usually 'order'
            reference_id: Order ID

        Returns:
            Tuple of (Balance, LedgerEntry)
        """
        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError("Lock amount must be positive")

        balance = LedgerService.get_or_create_balance(user, currency)

        if balance.available < amount:
            raise ValueError(
                f"Insufficient available balance. Available: {balance.available}, "
                f"Required: {amount}"
            )

        balance_before = balance.available

        balance.available -= amount
        balance.locked += amount
        balance.version += 1
        balance.save()

        ledger_entry = LedgerEntry.objects.create(
            user=user,
            currency=currency,
            entry_type='order_lock',
            amount=-amount,
            balance_before=balance_before,
            balance_after=balance.available,
            description=f"Locked for order",
            reference_type=reference_type,
            reference_id=reference_id
        )

        logger.info(
            f"Locked {amount} {currency.symbol} for {user.email}. "
            f"Available: {balance.available}, Locked: {balance.locked}"
        )

        return balance, ledger_entry

    @staticmethod
    @transaction.atomic
    def unlock_balance(
            user: User,
            currency: Currency,
            amount: Decimal,
            reference_type: str = None,
            reference_id: str = None
    ) -> tuple[Balance, LedgerEntry]:
        """
        Unlock amount (move from locked back to available).
        Used when orders are cancelled.

        Args:
            user: User
            currency: Currency
            amount: Amount to unlock
            reference_type: Usually 'order'
            reference_id: Order ID

        Returns:
            Tuple of (Balance, LedgerEntry)
        """
        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError("Unlock amount must be positive")

        balance = LedgerService.get_or_create_balance(user, currency)

        if balance.locked < amount:
            raise ValueError(
                f"Insufficient locked balance. Locked: {balance.locked}, "
                f"Required: {amount}"
            )

        balance_before = balance.available

        balance.locked -= amount
        balance.available += amount
        balance.version += 1
        balance.save()

        ledger_entry = LedgerEntry.objects.create(
            user=user,
            currency=currency,
            entry_type='order_unlock',
            amount=amount,
            balance_before=balance_before,
            balance_after=balance.available,
            description=f"Unlocked from cancelled order",
            reference_type=reference_type,
            reference_id=reference_id
        )

        logger.info(
            f"Unlocked {amount} {currency.symbol} for {user.email}. "
            f"Available: {balance.available}, Locked: {balance.locked}"
        )

        return balance, ledger_entry

    @staticmethod
    @transaction.atomic
    def deduct_locked(
            user: User,
            currency: Currency,
            amount: Decimal,
            entry_type: str,
            reference_type: str = None,
            reference_id: str = None
    ) -> tuple[Balance, LedgerEntry]:
        """
        Deduct from locked balance (when order is filled).

        Args:
            user: User
            currency: Currency
            amount: Amount to deduct from locked
            entry_type: Type of entry (trade_sell, fee, etc.)
            reference_type: Usually 'trade'
            reference_id: Trade ID

        Returns:
            Tuple of (Balance, LedgerEntry)
        """
        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError("Deduct amount must be positive")

        balance = LedgerService.get_or_create_balance(user, currency)

        if balance.locked < amount:
            raise ValueError(
                f"Insufficient locked balance. Locked: {balance.locked}, "
                f"Required: {amount}"
            )

        balance_before = balance.total

        balance.locked -= amount
        balance.version += 1
        balance.save()

        ledger_entry = LedgerEntry.objects.create(
            user=user,
            currency=currency,
            entry_type=entry_type,
            amount=-amount,
            balance_before=balance_before,
            balance_after=balance.total,
            description=f"Deducted from locked balance",
            reference_type=reference_type,
            reference_id=reference_id
        )

        logger.info(
            f"Deducted {amount} {currency.symbol} from locked for {user.email}. "
            f"Total: {balance.total}"
        )

        return balance, ledger_entry

    @staticmethod
    @transaction.atomic
    def process_deposit(deposit: Deposit) -> tuple[Balance, LedgerEntry]:
        """
        Process a confirmed deposit - credit user's balance.

        Args:
            deposit: Deposit object with status 'confirming' and enough confirmations

        Returns:
            Tuple of (Balance, LedgerEntry)
        """
        if deposit.status == 'completed':
            raise ValueError("Deposit already processed")

        if deposit.confirmations < deposit.required_confirmations:
            raise ValueError("Deposit does not have enough confirmations")

        # Credit balance
        balance, ledger_entry = LedgerService.credit_balance(
            user=deposit.user,
            currency=deposit.currency,
            amount=deposit.amount,
            entry_type='deposit',
            description=f"Deposit from {deposit.from_address[:10]}...",
            reference_type='deposit',
            reference_id=str(deposit.id)
        )

        # Update deposit status
        deposit.status = 'completed'
        deposit.credited_at = timezone.now()
        deposit.save()

        logger.info(
            f"Processed deposit {deposit.id}: {deposit.amount} {deposit.currency.symbol} "
            f"for {deposit.user.email}"
        )

        return balance, ledger_entry

    @staticmethod
    @transaction.atomic
    def create_withdrawal(
            user: User,
            currency: Currency,
            to_address: str,
            amount: Decimal
    ) -> Withdrawal:
        """
        Create a withdrawal request - debit user's balance.

        Args:
            user: User requesting withdrawal
            currency: Currency to withdraw
            to_address: Destination address
            amount: Amount to withdraw

        Returns:
            Withdrawal object
        """
        amount = Decimal(str(amount))
        fee = currency.withdrawal_fee
        total_debit = amount + fee

        # Check balance
        balance = LedgerService.get_or_create_balance(user, currency)

        if balance.available < total_debit:
            raise ValueError(
                f"Insufficient balance. Available: {balance.available}, "
                f"Required: {total_debit} (amount: {amount}, fee: {fee})"
            )

        # Debit balance
        LedgerService.debit_balance(
            user=user,
            currency=currency,
            amount=total_debit,
            entry_type='withdrawal',
            description=f"Withdrawal to {to_address[:10]}..."
        )

        # Create withdrawal record
        withdrawal = Withdrawal.objects.create(
            user=user,
            currency=currency,
            to_address=to_address,
            amount=amount,
            fee=fee,
            chain_id=currency.chain_id
        )

        logger.info(
            f"Created withdrawal {withdrawal.id}: {amount} {currency.symbol} "
            f"for {user.email} to {to_address[:10]}..."
        )

        return withdrawal

    @staticmethod
    @transaction.atomic
    def admin_adjust_balance(
            admin_user: User,
            target_user: User,
            currency: Currency,
            amount: Decimal,
            adjustment_type: str,
            reason: str
    ) -> tuple[Balance, LedgerEntry]:
        """
        Admin balance adjustment with full audit trail.

        Args:
            admin_user: Admin performing the adjustment
            target_user: User whose balance is being adjusted
            currency: Currency to adjust
            amount: Amount to adjust (always positive)
            adjustment_type: 'credit' or 'debit'
            reason: Reason for adjustment

        Returns:
            Tuple of (Balance, LedgerEntry)
        """
        amount = Decimal(str(amount))

        if amount <= 0:
            raise ValueError("Adjustment amount must be positive")

        if adjustment_type not in ['credit', 'debit']:
            raise ValueError("adjustment_type must be 'credit' or 'debit'")

        if adjustment_type == 'credit':
            balance, ledger_entry = LedgerService.credit_balance(
                user=target_user,
                currency=currency,
                amount=amount,
                entry_type='admin_credit',
                description=f"Admin credit: {reason}",
                created_by=admin_user
            )
        else:
            balance, ledger_entry = LedgerService.debit_balance(
                user=target_user,
                currency=currency,
                amount=amount,
                entry_type='admin_debit',
                description=f"Admin debit: {reason}",
                created_by=admin_user
            )

        logger.warning(
            f"ADMIN BALANCE ADJUSTMENT: {admin_user.email} {adjustment_type}ed "
            f"{amount} {currency.symbol} for {target_user.email}. Reason: {reason}"
        )

        return balance, ledger_entry