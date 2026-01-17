"""
Blockchain Models
=================
Models for blockchain network configuration and transaction tracking.
"""

import uuid
from django.db import models


class Network(models.Model):
    """
    Supported blockchain networks.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    chain_id = models.IntegerField(unique=True)
    rpc_url = models.URLField()
    explorer_url = models.URLField(blank=True, null=True)
    native_currency = models.CharField(max_length=10, default='ETH')

    is_active = models.BooleanField(default=True)
    is_testnet = models.BooleanField(default=False)

    block_time = models.IntegerField(default=12, help_text='Average block time in seconds')
    confirmations_required = models.IntegerField(default=12)

    # Last synced block
    last_synced_block = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Network'
        verbose_name_plural = 'Networks'
        ordering = ['chain_id']

    def __str__(self):
        return f"{self.name} (Chain ID: {self.chain_id})"


class MonitoredAddress(models.Model):
    """
    Addresses being monitored for incoming deposits.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=42, db_index=True)
    network = models.ForeignKey(
        Network,
        on_delete=models.CASCADE,
        related_name='monitored_addresses'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='monitored_addresses'
    )

    is_active = models.BooleanField(default=True)
    label = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Monitored Address'
        verbose_name_plural = 'Monitored Addresses'
        unique_together = ['address', 'network']

    def __str__(self):
        return f"{self.address[:10]}... on {self.network.name}"