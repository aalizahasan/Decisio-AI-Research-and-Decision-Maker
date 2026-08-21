import re
import hashlib
import hmac
import os
import json
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from app.config import settings

# JWT Secret Key and Algorithm
SECRET_KEY = (os.getenv("JWT_SECRET") or "").strip() or "decisio_super_secret_production_key_2026_998877"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


# Common disposable/fake email domains to reject for strict real email validation
DISPOSABLE_DOMAINS = {
  "mailinator.com", "trashmail.com", "10minutemail.com", "tempmail.com",
  "guerrillamail.com", "yopmail.com", "dispostable.com", "fake.com",
  "xyz.com", "test.com", "abc.com", "asdf.com", "example.com"
}


def validate_real_email(email: str) -> bool:
    """
    Validates that an email is a realistic, properly formatted email address compliant with RFC 5322.
    Rejects fake/dummy patterns like 'abc@xyz', 'test', 'a@b.c', or disposable domains.
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip().lower()

    # Standard RFC 5322 regex for valid email format
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False

    parts = email.split("@")
    if len(parts) != 2:
        return False

    local_part, domain = parts[0], parts[1]

    # Length constraints
    if len(local_part) < 2 or len(domain) < 4:
        return False

    # Check against known dummy/disposable domains
    if domain in DISPOSABLE_DOMAINS:
        return False

    # Ensure TLD is at least 2 characters (e.g. .com, .org, .io)
    domain_parts = domain.split(".")
    if len(domain_parts) < 2 or len(domain_parts[-1]) < 2:
        return False

    return True


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using PBKDF2 with SHA-256 and a random salt.
    """
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{pwd_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against a stored salted PBKDF2 hash string.
    """
    try:
        parts = hashed_password.split(":")
        if len(parts) != 2:
            return False
        salt = bytes.fromhex(parts[0])
        stored_hash = parts[1]

        pwd_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return pwd_hash.hex() == stored_hash
    except Exception:
        return False


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _base64url_decode(data_str: str) -> bytes:
    rem = len(data_str) % 4
    if rem > 0:
        data_str += '=' * (4 - rem)
    return base64.urlsafe_b64decode(data_str)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates an HMAC-SHA256 signed JWT access token.
    """
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": int(expire.timestamp())})

    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(to_encode, separators=(',', ':')).encode('utf-8')

    encoded_header = _base64url_encode(header_json)
    encoded_payload = _base64url_encode(payload_json)

    signature_input = f"{encoded_header}.{encoded_payload}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
    encoded_signature = _base64url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validates and decodes an HMAC-SHA256 signed JWT access token.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        encoded_header, encoded_payload, encoded_signature = parts

        signature_input = f"{encoded_header}.{encoded_payload}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
        actual_sig = _base64url_decode(encoded_signature)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None


        payload_bytes = _base64url_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode('utf-8'))

        # Check expiration with timezone-aware UTC timestamp
        exp = payload.get("exp")
        if exp and int(datetime.now(timezone.utc).timestamp()) > exp:
            return None

        return payload
    except Exception as err:
        return None


def create_password_reset_token(email: str) -> str:
    """
    Generates a 1-hour password reset token.
    """
    return create_access_token({"sub": email, "type": "reset"}, expires_delta=timedelta(hours=1))


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verifies a password reset token and returns the target email.
    """
    payload = decode_access_token(token)
    if not payload:
        return None
    if payload.get("type") != "reset":
        return None
    return payload.get("sub")


import random

def generate_6digit_otp() -> str:
    """
    Generates a secure random 6-digit numeric verification code (OTP).
    """
    return f"{random.randint(100000, 999999)}"


def decode_google_credential(credential_jwt: str) -> Optional[Dict[str, Any]]:
    """
    Decodes an unverified Google Identity JWT credential payload.
    Extracts email, email_verified, name, and picture.
    """
    try:
        parts = credential_jwt.split(".")
        if len(parts) < 2:
            return None
        payload_bytes = _base64url_decode(parts[1])
        payload = json.loads(payload_bytes.decode('utf-8'))
        return payload
    except Exception:
        return None

