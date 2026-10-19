"""Accounts for Storiiz: username and password only, PBKDF2-SHA256 hashing, roles and moderation.

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


def is_admin(user):
    return bool(user and user.get('is_admin'))


def _username_ok(username):
    return (
        MIN_USERNAME <= len(username) <= MAX_USERNAME
        and all(ch.isascii() and (ch.isalnum() or ch == '_') for ch in username)
    )


def _password_errors(password):
    if len(password or '') < MIN_PASSWORD:
        return [f'Password must be at least {MIN_PASSWORD} characters.']
    if len(password) > MAX_PASSWORD:
        return [f'Password must be {MAX_PASSWORD} characters or fewer.']
    return []


def validate_signup(username, password, confirm):
    errors = []
    name = normalize_username(username)
    if not _username_ok(name):
        errors.append('Username must be 3 to 30 characters: letters, numbers or underscores.')
    elif name == ADMIN_USERNAME:
        errors.append('That username is reserved.')
    errors += _password_errors(password)
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
    """Return (user, None) on success or (None, message) on failure."""
    name = normalize_username(username)
    user = backend.get_user(name) if name else None
    if user is None or not verify_password(password or '', user['password_hash']):
        return None, 'Wrong username or password.'
    if user.get('is_banned'):
        return None, 'This account has been suspended. Contact the Storiiz admins.'
    return {
        'username': user['username'],
        'is_admin': bool(user.get('is_admin')),
        'is_verified': bool(user.get('is_verified')),
    }, None


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
        backend.update_user(ADMIN_USERNAME, {'is_admin': True})


# ---- Moderation actions. The actor is the logged-in user performing the action. ----

def _require_admin(actor):
    if not is_admin(actor):
        raise PermissionError('Admin rights are required for that.')


def _target(backend, username):
    name = normalize_username(username)
    user = backend.get_user(name)
    if user is None:
        raise ValueError('That user does not exist.')
    return name, user


def set_admin_role(backend, actor, username, make_admin):
    """Promote or demote a user. storiizadmin cannot be demoted and no one can demote themselves."""
    _require_admin(actor)
    name, _ = _target(backend, username)
    if not make_admin:
        if name == ADMIN_USERNAME:
            raise ValueError('The storiizadmin account cannot be demoted.')
        if name == actor['username']:
            raise ValueError('You cannot demote your own account.')
    backend.update_user(name, {'is_admin': bool(make_admin)})


def set_verified(backend, actor, username, verified):
    _require_admin(actor)
    name, _ = _target(backend, username)
    backend.update_user(name, {'is_verified': bool(verified)})


def set_banned(backend, actor, username, banned):
    """Freeze or unfreeze an account. Admins cannot be banned, and nobody can ban themselves."""
    _require_admin(actor)
    name, user = _target(backend, username)
    if banned:
        if name == actor['username']:
            raise ValueError('You cannot ban your own account.')
        if user.get('is_admin'):
            raise ValueError('Demote this admin before banning the account.')
    backend.update_user(name, {'is_banned': bool(banned)})


def reset_password(backend, actor, username, new_password):
    _require_admin(actor)
    name, _ = _target(backend, username)
    if name == ADMIN_USERNAME and actor['username'] != ADMIN_USERNAME:
        raise ValueError('Only storiizadmin can reset its own password.')
    errors = _password_errors(new_password)
    if errors:
        raise ValueError(errors[0])
    backend.update_user(name, {'password_hash': hash_password(new_password)})
