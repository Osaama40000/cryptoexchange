from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('trading', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='stop_price',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True, help_text='Trigger price for stop orders'),
        ),
        migrations.AddField(
            model_name='order',
            name='take_profit_price',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True, help_text='Take profit trigger price'),
        ),
        migrations.AddField(
            model_name='order',
            name='stop_loss_price',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True, help_text='Stop loss trigger price'),
        ),
        migrations.AddField(
            model_name='order',
            name='trailing_stop_percent',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, help_text='Trailing stop percentage'),
        ),
        migrations.AddField(
            model_name='order',
            name='highest_price_seen',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True, help_text='Highest price seen for trailing stop'),
        ),
        migrations.AddField(
            model_name='order',
            name='lowest_price_seen',
            field=models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True, help_text='Lowest price seen for trailing stop'),
        ),
        migrations.AddField(
            model_name='order',
            name='triggered_at',
            field=models.DateTimeField(blank=True, null=True, help_text='When the stop order was triggered'),
        ),
        migrations.AddField(
            model_name='order',
            name='parent_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_orders', to='trading.order'),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_type',
            field=models.CharField(choices=[('market', 'Market'), ('limit', 'Limit'), ('stop_loss', 'Stop Loss'), ('stop_limit', 'Stop Limit'), ('take_profit', 'Take Profit'), ('take_profit_limit', 'Take Profit Limit'), ('trailing_stop', 'Trailing Stop'), ('oco', 'One Cancels Other')], default='limit', max_length=20),
        ),
    ]
