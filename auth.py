"""Accounts for Storiiz: username and password only, PBKDF2-SHA256 hashing, and a seeded admin.

Passwords are never stored in plain text. Each hash has its own random salt and the format is
pbkdf2_sha256$iterations$salt_hex$hash_hex.

The admin account is created automatically the first time the app starts if it does not exist.
The admin password can be overridden with the STORIIZ_ADMIN_PASSWORD environment variable or secret.
"""

import hashlib
import hmac
import os
import secrets

ITERATIONS = 310_000
MIN_PASSWORD = 8
MAX_PASSWORD = 128
MIN_USERNAME = 3
MAX_USERNAME = 30

ADMIN_USERNAME = 'storiizadmin'
DEFAULT_ADMIN_PASSWORD = 'StorizzAdmin2026!?'
ADMIN_PASSWORD_ENV = 'STORIIZ_ADMIN_PASSWORD'


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'


def verify_password(password, stored):
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split('$')
        if algorithm != 'pbkdf2_sha256':
            return False
        digest = hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def normalize_username(username):
    return (username or '').strip().lower()


def _username_ok(username):
    return (
        MIN_USERNAME <= len(username) <= MAX_USERNAME
        and all(ch.isascii() and (ch.isalnum() or ch == '_') for ch in username)
    )


def validate_signup(username, password, confirm):
    errors = []
    name = normalize_username(username)
    if not _username_ok(name):
        errors.append('Username must be 3 to 30 characters: letters, numbers or underscores.')
    elif name == ADMIN_USERNAME:
        errors.append('That username is reserved.')
    if len(password or '') < MIN_PASSWORD:
        errors.append(f'Password must be at least {MIN_PASSWORD} characters.')
    elif len(password) > MAX_PASSWORD:
        errors.append(f'Password must be {MAX_PASSWORD} characters or fewer.')
    if password != confirm:
        errors.append('The passwords do not match.')
    return errors


def sign_up(backend, username, password):
    """Create a regular account and return the normalized username. Raises ValueError if taken."""
    name = normalize_username(username)
    if backend.get_user(name) is not None:
        raise ValueError('That username is already taken.')
    backend.create_user({
        'username': name,
        'password_hash': hash_password(password),
        'is_admin': False,
    })
    return name


def log_in(backend, username, password):
    """Return the user dict on success, or None if the credentials are wrong."""
    name = normalize_username(username)
    user = backend.get_user(name) if name else None
    if user is None or not verify_password(password or '', user['password_hash']):
        return None
    return {'username': user['username'], 'is_admin': bool(user.get('is_admin'))}


def admin_password():
    try:
        import streamlit as st
        if ADMIN_PASSWORD_ENV in st.secrets:
            return str(st.secrets[ADMIN_PASSWORD_ENV])
    except Exception:
        pass
    return os.environ.get(ADMIN_PASSWORD_ENV) or DEFAULT_ADMIN_PASSWORD


def ensure_admin(backend):
    """Create the admin account if missing, and make sure it has the admin flag."""
    user = backend.get_user(ADMIN_USERNAME)
    if user is None:
        backend.create_user({
            'username': ADMIN_USERNAME,
            'password_hash': hash_password(admin_password()),
            'is_admin': True,
        })
    elif not user.get('is_admin'):
        backend.set_admin(ADMIN_USERNAME, True)


def is_admin(user):
    return bool(user and user.get('is_admin'))
