"""
Firewall Interceptor Module
Intercepts and blocks/redacts sensitive data (PII, credit card numbers, unauthorized transactions)
before the Validator Agent receives it.
"""
import re
import requests
import json

GATEWAY_URL = "http://localhost:8000/api/validate"
BIFROST_URL = "http://localhost:8000/bifrost/v1/chat/completions"

CREDIT_CARD_PATTERN = r'\b(?:\d[ -]*?){13,16}\b'
SSN_PATTERN = r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
PHONE_PATTERN = r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
AMOUNT_PATTERN = r'\$[\d,]+(?:\.\d{2})?'
ACCOUNT_TRANSFER_PATTERN = r'(?:send|transfer|wire)\s+\$[\d,]+(?:\.\d{2})?\s+to\s+[A-Za-z0-9]+'

REDACTED_MARKER = "[REDACTED]"

class InterceptorResult:
    def __init__(self, allowed: bool, redacted_content: str = "", blocked_reason: str = "", detected_items: list = None):
        self.allowed = allowed
        self.redacted_content = redacted_content
        self.blocked_reason = blocked_reason
        self.detected_items = detected_items or []

def detect_sensitive_data(text: str) -> list:
    """Detect all sensitive data patterns in text."""
    detected = []
    
    cc_matches = re.findall(CREDIT_CARD_PATTERN, text)
    for match in cc_matches:
        digits_only = re.sub(r'[^0-9]', '', match)
        if len(digits_only) >= 13:
            detected.append({"type": "CREDIT_CARD", "value": match[:6] + "***" + match[-4:]})
    
    ssn_matches = re.findall(SSN_PATTERN, text)
    for match in ssn_matches:
        detected.append({"type": "SSN", "value": "***-**-" + match[-4:]})
    
    email_matches = re.findall(EMAIL_PATTERN, text)
    for match in email_matches:
        detected.append({"type": "EMAIL", "value": match[:2] + "***@" + match.split('@')[-1]})
    
    phone_matches = re.findall(PHONE_PATTERN, text)
    for match in phone_matches:
        detected.append({"type": "PHONE", "value": "***-***-" + match[-4:]})
    
    transfer_matches = re.findall(ACCOUNT_TRANSFER_PATTERN, text, re.IGNORECASE)
    for match in transfer_matches:
        detected.append({"type": "UNAUTHORIZED_TRANSFER", "value": match})
    
    return detected

def redact_sensitive_data(text: str) -> str:
    """Redact all sensitive data from text."""
    redacted = text
    
    redacted = re.sub(CREDIT_CARD_PATTERN, f"{REDACTED_MARKER}_CC", redacted)
    redacted = re.sub(SSN_PATTERN, f"{REDACTED_MARKER}_SSN", redacted)
    redacted = re.sub(EMAIL_PATTERN, f"{REDACTED_MARKER}_EMAIL", redacted)
    redacted = re.sub(PHONE_PATTERN, f"{REDACTED_MARKER}_PHONE", redacted)
    redacted = re.sub(ACCOUNT_TRANSFER_PATTERN, f"{REDACTED_MARKER}_TRANSFER", redacted, flags=re.IGNORECASE)
    
    return redacted

def intercept_and_clean(content: str) -> InterceptorResult:
    """
    Native interceptor function that:
    1. Detects sensitive data
    2. Redacts sensitive data
    3. Blocks if unauthorized transactions detected
    """
    print("[Gateway Interceptor] Scanning content for sensitive data...")
    
    detected = detect_sensitive_data(content)
    
    unauthorized_transfers = [d for d in detected if d['type'] == 'UNAUTHORIZED_TRANSFER']
    if unauthorized_transfers:
        print("[Gateway Interceptor] 🚨 BLOCKED: Unauthorized transfer requests detected!")
        return InterceptorResult(
            allowed=False,
            blocked_reason="Unauthorized transfer request detected",
            detected_items=detected
        )
    
    credit_cards = [d for d in detected if d['type'] == 'CREDIT_CARD']
    if credit_cards:
        print("[Gateway Interceptor] ⚠️ WARNING: Credit card numbers detected - will be redacted")
    
    ssn_data = [d for d in detected if d['type'] == 'SSN']
    if ssn_data:
        print("[Gateway Interceptor] ⚠️ WARNING: SSN detected - will be redacted")
    
    redacted_content = redact_sensitive_data(content)
    
    print("[Gateway Interceptor] ✅ Content passed PII scan")
    return InterceptorResult(
        allowed=True,
        redacted_content=redacted_content,
        detected_items=detected
    )
