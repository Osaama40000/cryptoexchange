"""
Email Validator Service
=======================
Validates email format, domain, and handles email verification
"""

import re
import dns.resolver
import logging
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class EmailValidator:
    """
    Production-grade email validation
    """
    
    # Common disposable email domains to block
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'throwaway.email', 'guerrillamail.com',
        'mailinator.com', '10minutemail.com', 'fakeinbox.com',
        'temp-mail.org', 'disposablemail.com', 'yopmail.com',
        'trashmail.com', 'getnada.com', 'maildrop.cc',
    }
    
    # Common typos in popular domains
    DOMAIN_TYPOS = {
        'gmial.com': 'gmail.com',
        'gmal.com': 'gmail.com',
        'gamil.com': 'gmail.com',
        'gmail.co': 'gmail.com',
        'gmaill.com': 'gmail.com',
        'yahooo.com': 'yahoo.com',
        'yaho.com': 'yahoo.com',
        'hotmal.com': 'hotmail.com',
        'hotmai.com': 'hotmail.com',
        'outlok.com': 'outlook.com',
    }
    
    @classmethod
    def validate_format(cls, email):
        """
        Level 1: Validate email format
        Returns: (is_valid, error_message)
        """
        try:
            validate_email(email)
            return True, None
        except ValidationError:
            return False, "Invalid email format"
    
    @classmethod
    def check_domain_typo(cls, email):
        """
        Check for common domain typos and suggest correction
        Returns: (has_typo, suggested_email)
        """
        if '@' not in email:
            return False, None
        
        local, domain = email.rsplit('@', 1)
        domain_lower = domain.lower()
        
        if domain_lower in cls.DOMAIN_TYPOS:
            suggested = f"{local}@{cls.DOMAIN_TYPOS[domain_lower]}"
            return True, suggested
        
        return False, None
    
    @classmethod
    def is_disposable(cls, email):
        """
        Check if email is from a disposable email provider
        Returns: bool
        """
        if '@' not in email:
            return False
        
        domain = email.rsplit('@', 1)[1].lower()
        return domain in cls.DISPOSABLE_DOMAINS
    
    @classmethod
    def validate_domain(cls, email):
        """
        Level 2: Validate that email domain has MX records
        Returns: (is_valid, error_message)
        """
        if '@' not in email:
            return False, "Invalid email format"
        
        domain = email.rsplit('@', 1)[1]
        
        try:
            # Check for MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            if mx_records:
                return True, None
        except dns.resolver.NXDOMAIN:
            return False, f"Domain '{domain}' does not exist"
        except dns.resolver.NoAnswer:
            # No MX record, try A record as fallback
            try:
                dns.resolver.resolve(domain, 'A')
                return True, None
            except Exception:
                return False, f"Domain '{domain}' cannot receive emails"
        except Exception as e:
            logger.warning(f"DNS lookup failed for {domain}: {e}")
            # Don't block if DNS lookup fails, just warn
            return True, None
        
        return False, "Domain cannot receive emails"
    
    @classmethod
    def validate_full(cls, email):
        """
        Full validation: format + typo check + disposable check + domain
        Returns: {
            'is_valid': bool,
            'error': str or None,
            'warnings': list,
            'suggestion': str or None
        }
        """
        result = {
            'is_valid': True,
            'error': None,
            'warnings': [],
            'suggestion': None
        }
        
        # Normalize email
        email = email.strip().lower()
        
        # Level 1: Format validation
        is_valid, error = cls.validate_format(email)
        if not is_valid:
            result['is_valid'] = False
            result['error'] = error
            return result
        
        # Check for typos
        has_typo, suggestion = cls.check_domain_typo(email)
        if has_typo:
            result['warnings'].append(f"Did you mean {suggestion}?")
            result['suggestion'] = suggestion
        
        # Check for disposable email
        if cls.is_disposable(email):
            result['is_valid'] = False
            result['error'] = "Disposable email addresses are not allowed"
            return result
        
        # Level 2: Domain validation
        is_valid, error = cls.validate_domain(email)
        if not is_valid:
            result['is_valid'] = False
            result['error'] = error
            return result
        
        return result
