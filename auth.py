"""Accounts and permissions for Storiiz: username and password only, PBKDF2-SHA256 hashing, roles.

Role levels, lowest to highest:
  0 Unregistered       visitor: browse the feed only
  1 Logged In          can like and submit channels
  2 Channel Owner      has submitted at least one channel
  3 Verified           verified account (is_verified)
  4 Admin              moderation: channels, pinning, bans and verification of lower-level accounts
  5 Super Admin        all admin powers, admin role changes, maintenance mode and announcements
  6 Main Admin Account storiizadmin and theo: root accounts. Neither can be demoted, banned or changed
                       by anyone else. Root accounts appoint and remove Super Admins.

Passwords are never stored in plain text. Each hash has its own random salt and the format is
pbkdf2_sha256$iterations$salt_hex$hash_hex.

The admin account is created automatically the first time the app starts if it does not exist.
The admin password can be overridden with the STORIIZ_ADMIN_PASSWORD environment variable or secret.
The theo account is created the same way, but only when STORIIZ_THEO_PASSWORD is set. No password is stored in the code.
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

THEO_USERNAME = 'theo'
THEO_PASSWORD_ENV = 'STORIIZ_THEO_PASSWORD'

# Root accounts: highest level, cannot be changed by anyone.
ROOT_USERNAMES = (ADMIN_USERNAME, THEO_USERNAME)

LEVEL_GUEST = 0
LEVEL_USER = 1
LEVEL_OWNER = 2
LEVEL_VERIFIED = 3
LEVEL_ADMIN = 4
LEVEL_SUPER_ADMIN = 5
LEVEL_MAIN_ADMIN = 6

LEVEL_NAMES = {
    LEVEL_GUEST: 'Unregistered',
    LEVEL_USER: 'Logged In',
    LEVEL_OWNER: 'Channel Owner',
    LEVEL_VERIFIED: 'Verified',
    LEVEL_ADMIN: 'Admin',
    LEVEL_SUPER_ADMIN: 'Super Admin',
    LEVEL_MAIN_ADMIN: 'Main Admin Account',
}

MODERATE_MESSAGE = ('You can only moderate accounts below your own level. '
                    'The Main Admin Account cannot be changed.')


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


# ---- Levels ----

def is_root_username(username):
    return normalize_username(username) in ROOT_USERNAMES


def is_main_admin(user):
    """True for the root accounts (storiizadmin and theo)."""
    return bool(user) and is_root_username(user.get('username'))


def same_user(a, b):
    return bool(a) and bool(b) and normalize_username(a.get('username')) == normalize_username(b.get('username'))


def level_of(user, owns_channel=False):
    """The highest level the account has. owns_channel is True when the account has submitted a channel."""
    if not user:
        return LEVEL_GUEST
    if is_main_admin(user):
        return LEVEL_MAIN_ADMIN
    if user.get('is_super_admin'):
        return LEVEL_SUPER_ADMIN
    if user.get('is_admin'):
        return LEVEL_ADMIN
    if user.get('is_verified'):
        return LEVEL_VERIFIED
    if owns_channel:
        return LEVEL_OWNER
    return LEVEL_USER


def level_name(level):
    return LEVEL_NAMES.get(level, LEVEL_NAMES[LEVEL_GUEST])


def is_admin(user):
    return level_of(user) >= LEVEL_ADMIN


def is_super_admin(user):
    return level_of(user) >= LEVEL_SUPER_ADMIN


# ---- Permission checks. Used by the UI to show buttons and by the actions below to enforce them. ----

def can_moderate_channels(actor):
    """Remove, verify and pin channels."""
    return is_admin(actor)


def can_manage_site(actor):
    """Maintenance mode and announcements."""
    return is_super_admin(actor)


def can_moderate_user(actor, target):
    """Ban, unban and verify accounts. Only accounts strictly below the actor's level, never a root account or oneself."""
    if target is None or not is_admin(actor) or same_user(actor, target) or is_main_admin(target):
        return False
    return level_of(actor) > level_of(target)


def can_change_admin_role(actor, target):
    """Make or remove a standard Admin. Super Admins can be changed only by a root account. Root accounts cannot be changed."""
    if target is None or not is_super_admin(actor) or same_user(actor, target) or is_main_admin(target):
        return False
    return not is_super_admin(target) or is_main_admin(actor)


def can_set_super_admin(actor, target):
    """Only a root account appoints or removes Super Admins. Root accounts cannot be changed."""
    return is_main_admin(actor) and target is not None and not is_main_admin(target)


def can_reset_password(actor, target):
    if target is None:
        return False
    if is_main_admin(target):
        return is_main_admin(actor) and same_user(actor, target)
    if same_user(actor, target):
        return is_admin(actor)
    return can_moderate_user(actor, target)


# ---- Accounts ----

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
    elif is_root_username(name):
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
        'is_super_admin': False,
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
        'is_super_admin': bool(user.get('is_super_admin')),
        'is_verified': bool(user.get('is_verified')),
    }, None


def _secret_value(name, default=None):
    try:
        import streamlit as st
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name) or default


def admin_password():
    return _secret_value(ADMIN_PASSWORD_ENV, DEFAULT_ADMIN_PASSWORD)


def theo_password():
    """The theo password comes only from a secret or environment variable. None if not set."""
    return _secret_value(THEO_PASSWORD_ENV)


def _ensure_root_flags(backend, username):
    """Root accounts are admin, super admin, verified and never banned."""
    user = backend.get_user(username)
    fixes = {}
    if not user.get('is_admin'):
        fixes['is_admin'] = True
    if user.get('is_banned'):
        fixes['is_banned'] = False
    if fixes:
        backend.update_user(username, fixes)


def ensure_admin(backend):
    """Create the root accounts if missing and keep their flags correct."""
    user = backend.get_user(ADMIN_USERNAME)
    if user is None:
        backend.create_user({
            'username': ADMIN_USERNAME,
            'password_hash': hash_password(admin_password()),
            'is_admin': True,
            'is_super_admin': False,
        })
    else:
        fixes = {}
        if not user.get('is_admin'):
            fixes['is_admin'] = True
        if user.get('is_super_admin'):
            fixes['is_super_admin'] = False
        if user.get('is_banned'):
            fixes['is_banned'] = False
        if fixes:
            backend.update_user(ADMIN_USERNAME, fixes)

    password = theo_password()
    theo = backend.get_user(THEO_USERNAME)
    if theo is None:
        if password:
            backend.create_user({
                'username': THEO_USERNAME,
                'password_hash': hash_password(password),
                'is_admin': True,
                'is_super_admin': True,
                'is_verified': True,
            })
    else:
        fixes = {}
        if not theo.get('is_admin'):
            fixes['is_admin'] = True
        if not theo.get('is_super_admin'):
            fixes['is_super_admin'] = True
        if not theo.get('is_verified'):
            fixes['is_verified'] = True
        if theo.get('is_banned'):
            fixes['is_banned'] = False
        if fixes:
            backend.update_user(THEO_USERNAME, fixes)


# ---- Moderation actions. The actor is the logged-in user performing the action. ----

def _load_target(backend, username):
    name = normalize_username(username)
    user = backend.get_user(name) if name else None
    if user is None:
        raise ValueError('That user does not exist.')
    return name, user


def set_admin_role(backend, actor, username, make_admin):
    """Make or remove a standard Admin. Only Super Admins and root accounts can do this."""
    name, target = _load_target(backend, username)
    if is_main_admin(target):
        raise PermissionError('The Main Admin Account cannot be changed.')
    if same_user(actor, target):
        raise PermissionError('You cannot change your own role.')
    if not is_super_admin(actor):
        raise PermissionError('Only Super Admins and the Main Admin Account can change admin roles.')
    if not can_change_admin_role(actor, target):
        raise PermissionError('Only the Main Admin Account can change a Super Admin.')
    if make_admin:
        backend.update_user(name, {'is_admin': True})
    else:
        backend.update_user(name, {'is_admin': False, 'is_super_admin': False})


def set_super_admin(backend, actor, username, make_super):
    """Appoint or remove a Super Admin. Only a root account can do this.

    Removing Super Admin status leaves the account as a standard Admin.
    """
    name, target = _load_target(backend, username)
    if not can_set_super_admin(actor, target):
        raise PermissionError('Only the Main Admin Account can appoint or remove Super Admins.')
    if make_super:
        backend.update_user(name, {'is_super_admin': True, 'is_admin': True})
    else:
        backend.update_user(name, {'is_super_admin': False})


def set_verified(backend, actor, username, verified):
    name, target = _load_target(backend, username)
    if not can_moderate_user(actor, target):
        raise PermissionError(MODERATE_MESSAGE)
    backend.update_user(name, {'is_verified': bool(verified)})


def set_banned(backend, actor, username, banned):
    """Freeze or unfreeze an account. Only accounts below the actor's level can be changed."""
    name, target = _load_target(backend, username)
    if not can_moderate_user(actor, target):
        raise PermissionError(MODERATE_MESSAGE)
    backend.update_user(name, {'is_banned': bool(banned)})


def reset_password(backend, actor, username, new_password):
    name, target = _load_target(backend, username)
    if not can_reset_password(actor, target):
        raise PermissionError('You do not have permission to reset this password.')
    errors = _password_errors(new_password)
    if errors:
        raise ValueError(errors[0])
    backend.update_user(name, {'password_hash': hash_password(new_password)})
