"""
Matching Engine
===============
Core trading engine that matches buy and sell orders.
Implements price-time priority matching.
"""

import logging
from decimal import Decimal
from typing import List, Optional, Tuple
from django.db import transaction
from django.utils import timezone

from apps.trading.models import TradingPair, Order, Trade
from apps.wallets.models import Currency
from apps.wallets.services.ledger import LedgerService
from apps.accounts.models import User
from .order_book import OrderBookService

logger = logging.getLogger('apps.trading')


class MatchingEngine:
    """
    Matching engine for order execution.

    Implements:
    - Price-time priority matching
    - Limit and market orders
    - Maker/taker fee calculation
    - Atomic balance updates
    """

    @staticmethod
    @transaction.atomic
    def create_order(
            user: User,
            trading_pair: TradingPair,
            order_type: str,
            side: str,
            quantity: Decimal,
            price: Decimal = None,
            time_in_force: str = 'GTC',
            client_order_id: str = None
    ) -> Tuple[Order, List[Trade]]:
        """
        Create a new order and attempt to match it.

        Args:
            user: User placing the order
            trading_pair: Trading pair
            order_type: 'limit' or 'market'
            side: 'buy' or 'sell'
            quantity: Order quantity
            price: Limit price (required for limit orders)
            time_in_force: GTC, IOC, or FOK
            client_order_id: Optional client reference

        Returns:
            Tuple of (Order, List of Trades)
        """
        quantity = Decimal(str(quantity))
        if price:
            price = Decimal(str(price))

        # Validate and lock funds
        MatchingEngine._lock_funds_for_order(
            user=user,
            trading_pair=trading_pair,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type
        )

        # Create the order
        order = Order.objects.create(
            user=user,
            trading_pair=trading_pair,
            order_type=order_type,
            side=side,
            price=price,
            quantity=quantity,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
            status='open'
        )

        logger.info(
            f"Created order {order.id}: {side.upper()} {quantity} "
            f"{trading_pair.symbol} @ {price or 'MARKET'}"
        )

        # Try to match the order
        trades = MatchingEngine._match_order(order)

        # Handle time-in-force
        if time_in_force == 'IOC' and order.status == 'open':
            # Immediate or Cancel - cancel unfilled portion
            MatchingEngine.cancel_order(order)
        elif time_in_force == 'FOK' and order.status != 'filled':
            # Fill or Kill - cancel if not fully filled
            # Note: In a real implementation, FOK should check before execution
            MatchingEngine.cancel_order(order)

        # Invalidate order book cache
        OrderBookService.invalidate_cache(trading_pair.symbol)

        return order, trades

    @staticmethod
    def _lock_funds_for_order(
            user: User,
            trading_pair: TradingPair,
            side: str,
            quantity: Decimal,
            price: Decimal,
            order_type: str
    ):
        """Lock the required funds for an order."""

        if side == 'buy':
            # Buy order: lock quote currency
            currency = trading_pair.quote_currency
            if order_type == 'market':
                # For market orders, estimate based on best ask or use a buffer
                best_ask = OrderBookService.get_best_ask(trading_pair)
                if best_ask:
                    estimated_price = best_ask.price * Decimal('1.05')  # 5% buffer
                else:
                    raise ValueError("No sell orders available for market buy")
                lock_amount = quantity * estimated_price
            else:
                lock_amount = quantity * price
        else:
            # Sell order: lock base currency
            currency = trading_pair.base_currency
            lock_amount = quantity

        # Lock the funds
        try:
            LedgerService.lock_balance(
                user=user,
                currency=currency,
                amount=lock_amount,
                reference_type='order',
                reference_id=None  # Will be updated after order creation
            )
        except ValueError as e:
            raise ValueError(f"Insufficient balance: {str(e)}")

    @staticmethod
    @transaction.atomic
    def _match_order(order: Order) -> List[Trade]:
        """
        Match an order against the order book.

        Returns:
            List of executed trades
        """
        trades = []

        if order.remaining_quantity <= 0:
            return trades

        # Get matching orders
        is_market = order.order_type == 'market'
        matching_orders = OrderBookService.get_matching_orders(
            trading_pair=order.trading_pair,
            side=order.side,
            price=order.price,
            is_market_order=is_market
        )

        for counter_order in matching_orders:
            if order.remaining_quantity <= 0:
                break

            # Skip self-matching
            if counter_order.user_id == order.user_id:
                continue

            # Determine trade quantity
            trade_quantity = min(order.remaining_quantity, counter_order.remaining_quantity)

            # Determine trade price (maker's price)
            trade_price = counter_order.price

            # Execute the trade
            trade = MatchingEngine._execute_trade(
                taker_order=order,
                maker_order=counter_order,
                quantity=trade_quantity,
                price=trade_price
            )

            trades.append(trade)

            # Refresh order from database
            order.refresh_from_db()

        return trades

    @staticmethod
    @transaction.atomic
    def _execute_trade(
            taker_order: Order,
            maker_order: Order,
            quantity: Decimal,
            price: Decimal
    ) -> Trade:
        """
        Execute a trade between two orders.

        Updates:
        - Order filled quantities and statuses
        - User balances
        - Trading pair last price
        """
        trading_pair = taker_order.trading_pair
        quote_quantity = quantity * price

        # Determine buyer and seller
        if taker_order.side == 'buy':
            buyer = taker_order.user
            seller = maker_order.user
            buy_order = taker_order
            sell_order = maker_order
            buyer_is_maker = False
        else:
            buyer = maker_order.user
            seller = taker_order.user
            buy_order = maker_order
            sell_order = taker_order
            buyer_is_maker = True

        # Calculate fees
        maker_fee_rate = trading_pair.maker_fee
        taker_fee_rate = trading_pair.taker_fee

        if buyer_is_maker:
            buyer_fee = quantity * maker_fee_rate  # Fee in base currency
            seller_fee = quote_quantity * taker_fee_rate  # Fee in quote currency
        else:
            buyer_fee = quantity * taker_fee_rate
            seller_fee = quote_quantity * maker_fee_rate

        # Create trade record
        trade = Trade.objects.create(
            trading_pair=trading_pair,
            buy_order=buy_order,
            sell_order=sell_order,
            buyer=buyer,
            seller=seller,
            price=price,
            quantity=quantity,
            quote_quantity=quote_quantity,
            buyer_fee=buyer_fee,
            seller_fee=seller_fee,
            buyer_is_maker=buyer_is_maker
        )

        logger.info(
            f"Trade executed: {quantity} {trading_pair.base_currency.symbol} "
            f"@ {price} {trading_pair.quote_currency.symbol}"
        )

        # Update balances
        MatchingEngine._settle_trade(
            trade=trade,
            trading_pair=trading_pair,
            buyer=buyer,
            seller=seller,
            quantity=quantity,
            quote_quantity=quote_quantity,
            buyer_fee=buyer_fee,
            seller_fee=seller_fee
        )

        # Update order statuses
        MatchingEngine._update_order_after_trade(taker_order, quantity)
        MatchingEngine._update_order_after_trade(maker_order, quantity)

        # Update trading pair last price
        trading_pair.last_price = price
        trading_pair.save(update_fields=['last_price', 'updated_at'])

        return trade

    @staticmethod
    def _settle_trade(
            trade: Trade,
            trading_pair: TradingPair,
            buyer: User,
            seller: User,
            quantity: Decimal,
            quote_quantity: Decimal,
            buyer_fee: Decimal,
            seller_fee: Decimal
    ):
        """Settle balances after a trade."""

        base_currency = trading_pair.base_currency
        quote_currency = trading_pair.quote_currency

        # Buyer:
        # - Deduct quote currency from locked (paid for the purchase)
        # - Credit base currency minus fee (received)
        LedgerService.deduct_locked(
            user=buyer,
            currency=quote_currency,
            amount=quote_quantity,
            entry_type='trade_buy',
            reference_type='trade',
            reference_id=str(trade.id)
        )

        LedgerService.credit_balance(
            user=buyer,
            currency=base_currency,
            amount=quantity - buyer_fee,
            entry_type='trade_buy',
            reference_type='trade',
            reference_id=str(trade.id)
        )

        # Seller:
        # - Deduct base currency from locked (sold)
        # - Credit quote currency minus fee (received)
        LedgerService.deduct_locked(
            user=seller,
            currency=base_currency,
            amount=quantity,
            entry_type='trade_sell',
            reference_type='trade',
            reference_id=str(trade.id)
        )

        LedgerService.credit_balance(
            user=seller,
            currency=quote_currency,
            amount=quote_quantity - seller_fee,
            entry_type='trade_sell',
            reference_type='trade',
            reference_id=str(trade.id)
        )

    @staticmethod
    def _update_order_after_trade(order: Order, filled_quantity: Decimal):
        """Update order after partial or full fill."""
        order.filled_quantity += filled_quantity

        if order.filled_quantity >= order.quantity:
            order.status = 'filled'
            order.filled_at = timezone.now()
        elif order.filled_quantity > 0:
            order.status = 'partial'

        order.save()

    @staticmethod
    @transaction.atomic
    def cancel_order(order: Order) -> Order:
        """
        Cancel an open or partially filled order.

        Unlocks remaining funds and updates order status.
        """
        if order.status not in ['open', 'partial']:
            raise ValueError(f"Cannot cancel order with status: {order.status}")

        # Calculate amount to unlock
        remaining_quantity = order.remaining_quantity

        if remaining_quantity > 0:
            if order.side == 'buy':
                # Unlock quote currency
                unlock_amount = remaining_quantity * order.price
                currency = order.trading_pair.quote_currency
            else:
                # Unlock base currency
                unlock_amount = remaining_quantity
                currency = order.trading_pair.base_currency

            # Unlock the funds
            LedgerService.unlock_balance(
                user=order.user,
                currency=currency,
                amount=unlock_amount,
                reference_type='order',
                reference_id=str(order.id)
            )

        # Update order status
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.save()

        # Invalidate order book cache
        OrderBookService.invalidate_cache(order.trading_pair.symbol)

        logger.info(f"Cancelled order {order.id}")

        return order