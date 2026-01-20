"""
Security Views
==============
API views for security features
"""

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models import TwoFactorAuth, APIKey, IPWhitelist, LoginAttempt
from .serializers import (
    TwoFactorSetupSerializer, TwoFactorVerifySerializer,
    TwoFactorDisableSerializer, TwoFactorStatusSerializer,
    BackupCodeVerifySerializer, APIKeyCreateSerializer,
    APIKeyResponseSerializer, APIKeyListSerializer,
    AuditLogSerializer, IPWhitelistSerializer,
    SecuritySettingsSerializer
)
from .utils import generate_qr_code, get_client_ip_address

# Try to import existing AuditLog from audit app
try:
    from apps.audit.models import AuditLog
    HAS_AUDIT_LOG = True
except ImportError:
    HAS_AUDIT_LOG = False

def log_action(action, user=None, request=None, details=None, success=True, severity='info'):
    """Helper to log actions using existing audit system"""
    if HAS_AUDIT_LOG:
        try:
            ip_address = get_client_ip_address(request) if request else None
            AuditLog.objects.create(
                user=user,
                action=action,
                ip_address=ip_address,
                details=details or {},
                success=success
            )
        except Exception as e:
            print(f"Audit log error: {e}")


# ============== Two-Factor Authentication ==============

class TwoFactorSetupView(APIView):
    """Setup 2FA for user account"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get 2FA setup information (QR code)"""
        user = request.user
        
        # Check if already enabled
        two_factor, created = TwoFactorAuth.objects.get_or_create(
            user=user,
            defaults={'secret_key': TwoFactorAuth.generate_secret()}
        )
        
        if two_factor.is_enabled:
            return Response(
                {'error': '2FA is already enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate new secret if not enabled
        if not created:
            two_factor.secret_key = TwoFactorAuth.generate_secret()
            two_factor.save()
        
        provisioning_uri = two_factor.get_provisioning_uri()
        qr_code = generate_qr_code(provisioning_uri)
        
        return Response({
            'secret_key': two_factor.secret_key,
            'qr_code': f"data:image/png;base64,{qr_code}",
            'provisioning_uri': provisioning_uri
        })
    
    def post(self, request):
        """Verify and enable 2FA"""
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        code = serializer.validated_data['code']
        
        try:
            two_factor = TwoFactorAuth.objects.get(user=user)
        except TwoFactorAuth.DoesNotExist:
            return Response(
                {'error': 'Please setup 2FA first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if two_factor.is_enabled:
            return Response(
                {'error': '2FA is already enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not two_factor.verify_code(code):
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enable 2FA and generate backup codes
        two_factor.is_enabled = True
        two_factor.save()
        backup_codes = two_factor.generate_backup_codes()
        
        # Log the action
        log_action('2fa_enable', user=user, request=request, details={'method': 'totp'})
        
        return Response({
            'message': '2FA enabled successfully',
            'backup_codes': backup_codes,
            'warning': 'Save these backup codes securely. They will not be shown again!'
        })


class TwoFactorDisableView(APIView):
    """Disable 2FA for user account"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        code = serializer.validated_data['code']
        password = serializer.validated_data['password']
        
        # Verify password
        if not user.check_password(password):
            return Response(
                {'error': 'Invalid password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            two_factor = TwoFactorAuth.objects.get(user=user, is_enabled=True)
        except TwoFactorAuth.DoesNotExist:
            return Response(
                {'error': '2FA is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify code
        if not two_factor.verify_code(code):
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Disable 2FA
        two_factor.is_enabled = False
        two_factor.backup_codes = []
        two_factor.save()
        
        # Log the action
        log_action('2fa_disable', user=user, request=request, severity='warning')
        
        return Response({'message': '2FA disabled successfully'})


class TwoFactorStatusView(APIView):
    """Get 2FA status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            two_factor = TwoFactorAuth.objects.get(user=request.user)
            serializer = TwoFactorStatusSerializer(two_factor)
            return Response(serializer.data)
        except TwoFactorAuth.DoesNotExist:
            return Response({
                'is_enabled': False,
                'backup_codes_remaining': 0
            })


class TwoFactorRegenerateBackupCodesView(APIView):
    """Regenerate backup codes"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        code = serializer.validated_data['code']
        
        try:
            two_factor = TwoFactorAuth.objects.get(user=user, is_enabled=True)
        except TwoFactorAuth.DoesNotExist:
            return Response(
                {'error': '2FA is not enabled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not two_factor.verify_code(code):
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        backup_codes = two_factor.generate_backup_codes()
        
        return Response({
            'backup_codes': backup_codes,
            'warning': 'Save these backup codes securely. They will not be shown again!'
        })


# ============== API Key Management ==============

class APIKeyListCreateView(APIView):
    """List and create API keys"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List user's API keys"""
        api_keys = APIKey.objects.filter(user=request.user)
        serializer = APIKeyListSerializer(api_keys, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create new API key"""
        serializer = APIKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        data = serializer.validated_data
        
        # Check limit (max 10 keys per user)
        if APIKey.objects.filter(user=user).count() >= 10:
            return Response(
                {'error': 'Maximum 10 API keys allowed per user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate key pair
        api_key, api_secret, secret_hash = APIKey.generate_key_pair()
        
        # Calculate expiry
        expires_at = None
        if data.get('expires_in_days'):
            expires_at = timezone.now() + timedelta(days=data['expires_in_days'])
        
        # Create API key
        key_obj = APIKey.objects.create(
            user=user,
            name=data['name'],
            key=api_key,
            secret_hash=secret_hash,
            permissions=data['permissions'],
            ip_whitelist=data.get('ip_whitelist', []),
            expires_at=expires_at
        )
        
        # Log the action
        log_action('api_key_create', user=user, request=request, 
                   details={'key_name': data['name'], 'permissions': data['permissions']})
        
        return Response({
            'id': key_obj.id,
            'name': key_obj.name,
            'key': api_key,
            'secret': api_secret,  # Only shown once!
            'permissions': key_obj.permissions,
            'created_at': key_obj.created_at,
            'expires_at': key_obj.expires_at,
            'message': 'Save your API secret now. It will not be shown again!'
        }, status=status.HTTP_201_CREATED)


class APIKeyDetailView(APIView):
    """Get, update, or delete API key"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        try:
            return APIKey.objects.get(pk=pk, user=user)
        except APIKey.DoesNotExist:
            return None
    
    def get(self, request, pk):
        api_key = self.get_object(pk, request.user)
        if not api_key:
            return Response(
                {'error': 'API key not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = APIKeyListSerializer(api_key)
        return Response(serializer.data)
    
    def patch(self, request, pk):
        """Update API key (name, permissions, ip_whitelist, is_active)"""
        api_key = self.get_object(pk, request.user)
        if not api_key:
            return Response(
                {'error': 'API key not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only allow updating certain fields
        allowed_fields = ['name', 'permissions', 'ip_whitelist', 'is_active']
        for field in allowed_fields:
            if field in request.data:
                setattr(api_key, field, request.data[field])
        
        api_key.save()
        serializer = APIKeyListSerializer(api_key)
        return Response(serializer.data)
    
    def delete(self, request, pk):
        api_key = self.get_object(pk, request.user)
        if not api_key:
            return Response(
                {'error': 'API key not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        key_name = api_key.name
        api_key.delete()
        
        # Log the action
        log_action('api_key_delete', user=request.user, request=request, details={'key_name': key_name})
        
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============== Audit Logs ==============

class AuditLogListView(APIView):
    """List audit logs for user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not HAS_AUDIT_LOG:
            return Response({'error': 'Audit logging not available'}, status=status.HTTP_404_NOT_FOUND)
        
        queryset = AuditLog.objects.filter(user=request.user).order_by('-created_at')[:100]
        serializer = AuditLogSerializer(queryset, many=True)
        return Response(serializer.data)


# ============== IP Whitelist ==============

class IPWhitelistView(APIView):
    """Manage IP whitelist for withdrawals"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        ips = IPWhitelist.objects.filter(user=request.user)
        serializer = IPWhitelistSerializer(ips, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = IPWhitelistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check limit
        if IPWhitelist.objects.filter(user=request.user).count() >= 10:
            return Response(
                {'error': 'Maximum 10 IPs allowed in whitelist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ip_entry = serializer.save(user=request.user)
        
        # Log the action
        log_action('ip_whitelist_change', user=request.user, request=request,
                   details={'action': 'add', 'ip': ip_entry.ip_address})
        
        return Response(
            IPWhitelistSerializer(ip_entry).data,
            status=status.HTTP_201_CREATED
        )


class IPWhitelistDeleteView(APIView):
    """Delete IP from whitelist"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            ip_entry = IPWhitelist.objects.get(pk=pk, user=request.user)
            ip_address = ip_entry.ip_address
            ip_entry.delete()
            
            # Log the action
            log_action('ip_whitelist_change', user=request.user, request=request,
                       details={'action': 'remove', 'ip': ip_address})
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except IPWhitelist.DoesNotExist:
            return Response(
                {'error': 'IP not found in whitelist'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============== Security Overview ==============

class SecurityOverviewView(APIView):
    """Get security settings overview"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # 2FA status
        try:
            two_factor = TwoFactorAuth.objects.get(user=user)
            two_factor_enabled = two_factor.is_enabled
        except TwoFactorAuth.DoesNotExist:
            two_factor_enabled = False
        
        # API keys count
        api_keys_count = APIKey.objects.filter(user=user, is_active=True).count()
        
        # Whitelisted IPs
        whitelisted_ips_count = IPWhitelist.objects.filter(user=user, is_active=True).count()
        
        # Recent login attempts
        recent_attempts = LoginAttempt.objects.filter(
            email=user.email,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return Response({
            'two_factor_enabled': two_factor_enabled,
            'api_keys_count': api_keys_count,
            'whitelisted_ips_count': whitelisted_ips_count,
            'recent_login_attempts': recent_attempts,
            'last_login': user.last_login,
            'last_password_change': None
        })

# Add this import at the top of the file
# from emails.services import EmailService

# Then in TwoFactorSetupView.post() after enabling 2FA:
# EmailService.send_2fa_enabled(user)

# In TwoFactorDisableView.post() after disabling 2FA:
# EmailService.send_2fa_disabled(user)

# In APIKeyListCreateView.post() after creating key:
# EmailService.send_api_key_created(user, key_name)
