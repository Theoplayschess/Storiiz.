"""User accounts for Storiiz: validation, password hashing (PBKDF2-SHA256) and sign up / log in.

Passwords are never stored in plain text. Each hash has its own random salt and the
format is pbkdf2_sha256$iterations$salt_hex$hash_hex.
"""

import hashlib
import hmac
import secrets

ITERATIONS = 310_000
MIN_PASSWORD = 8
MAX_PASSWORD = 128
MIN_USERNAME = 3
MAX_USERNAME = 30


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


def _email_ok(email):
    if not email:
        return True
    domain = email.split('@')[-1]
    return email.count('@') == 1 and ' ' not in email and '.' in domain and not domain.startswith('.')


def validate_signup(username, email, password, confirm):
    errors = []
    name = normalize_username(username)
    if not _username_ok(name):
        errors.append('Username must be 3 to 30 characters: letters, numbers or underscores.')
    email = (email or '').strip()
    if not _email_ok(email):
        errors.append('Enter a valid email or leave it empty.')
    if len(password or '') < MIN_PASSWORD:
        errors.append(f'Password must be at least {MIN_PASSWORD} characters.')
    elif len(password) > MAX_PASSWORD:
        errors.append(f'Password must be {MAX_PASSWORD} characters or fewer.')
    if password != confirm:
        errors.append('The passwords do not match.')
    return errors


def sign_up(backend, username, email, password):
    """Create an account and return the normalized username. Raises ValueError if it is taken."""
    name = normalize_username(username)
    if backend.get_user(name) is not None:
        raise ValueError('That username is already taken.')
    backend.create_user({
        'username': name,
        'email': (email or '').strip(),
        'password_hash': hash_password(password),
    })
    return name


def log_in(backend, username, password):
    """Return the normalized username on success, or None if the credentials are wrong."""
    name = normalize_username(username)
    user = backend.get_user(name) if name else None
    if user is None or not verify_password(password or '', user['password_hash']):
        return None
    return user['username']
