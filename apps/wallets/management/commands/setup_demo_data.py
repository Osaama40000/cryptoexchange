"""
Management command to set up demo data.

Usage:
    python manage.py setup_demo_data
"""

from django.core.management.base import BaseCommand
from decimal import Decimal

from apps.wallets.models import Currency
from apps.trading.models import TradingPair


class Command(BaseCommand):
    help = 'Set up demo currencies and trading pairs'

    def handle(self, *args, **options):
        self.stdout.write('Setting up demo data...\n')

        # Create currencies
        currencies_data = [
            {
                'symbol': 'ETH',
                'name': 'Ethereum',
                'currency_type': 'native',
                'decimals': 18,
                'min_deposit': Decimal('0.001'),
                'min_withdrawal': Decimal('0.01'),
                'withdrawal_fee': Decimal('0.005'),
            },
            {
                'symbol': 'USDT',
                'name': 'Tether USD',
                'currency_type': 'erc20',
                'contract_address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
                'decimals': 6,
                'min_deposit': Decimal('1'),
                'min_withdrawal': Decimal('10'),
                'withdrawal_fee': Decimal('5'),
            },
            {
                'symbol': 'USDC',
                'name': 'USD Coin',
                'currency_type': 'erc20',
                'contract_address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
                'decimals': 6,
                'min_deposit': Decimal('1'),
                'min_withdrawal': Decimal('10'),
                'withdrawal_fee': Decimal('5'),
            },
            {
                'symbol': 'BTC',
                'name': 'Wrapped Bitcoin',
                'currency_type': 'erc20',
                'contract_address': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
                'decimals': 8,
                'min_deposit': Decimal('0.0001'),
                'min_withdrawal': Decimal('0.001'),
                'withdrawal_fee': Decimal('0.0005'),
            },
        ]

        currencies = {}
        for data in currencies_data:
            currency, created = Currency.objects.update_or_create(
                symbol=data['symbol'],
                defaults=data
            )
            currencies[data['symbol']] = currency
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status} currency: {currency.symbol}')

        # Create trading pairs
        pairs_data = [
            {
                'base': 'ETH',
                'quote': 'USDT',
                'last_price': Decimal('2500.00'),
            },
            {
                'base': 'BTC',
                'quote': 'USDT',
                'last_price': Decimal('45000.00'),
            },
            {
                'base': 'ETH',
                'quote': 'USDC',
                'last_price': Decimal('2500.00'),
            },
        ]

        for data in pairs_data:
            base = currencies[data['base']]
            quote = currencies[data['quote']]
            symbol = f"{data['base']}_{data['quote']}"

            pair, created = TradingPair.objects.update_or_create(
                symbol=symbol,
                defaults={
                    'base_currency': base,
                    'quote_currency': quote,
                    'is_active': True,
                    'last_price': data['last_price'],
                    'min_order_size': Decimal('0.001'),
                    'max_order_size': Decimal('1000'),
                }
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status} trading pair: {pair.symbol}')

        self.stdout.write(self.style.SUCCESS('\n✅ Demo data setup complete!'))
        self.stdout.write('\nCurrencies: ' + ', '.join(currencies.keys()))
        self.stdout.write('Trading Pairs: ' + ', '.join([f"{p['base']}_{p['quote']}" for p in pairs_data]))