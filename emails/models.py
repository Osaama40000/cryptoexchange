"""
Email Models
============
Models for email verification tokens
"""

import uuid
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone


class EmailVerificationToken(models.Model):
    """
    Token for verifying user email addresses
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_verification_tokens'
    )
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 24 hours
            self.expires_at = timezone.now() + timedelta(hours=24)
        if not self.token:
            self.token = uuid.uuid4().hex
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_verified(self):
        return self.verified_at is not None
    
    def verify(self):
        """Mark token as verified"""
        if self.is_expired:
            return False
        if self.is_verified:
            return False
        
        self.verified_at = timezone.now()
        self.save()
        
        # Update user's email_verified status
        self.user.email_verified = True
        self.user.save(update_fields=['email_verified'])
        
        return True
    
    def __str__(self):
        return f"Verification for {self.email}"
