"""Storage, validation, ranking, moderation settings and backups for Storiiz.

Uses Supabase when SUPABASE_URL and SUPABASE_KEY are set (st.secrets or environment variables).
Otherwise uses a local SQLite database that is created automatically in data/storiiz.db.
The admin account is ensured on every backend start. Older SQLite files get new columns automatically.
"""

import base64
import json
import os
import re
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

import auth

BASE_DIR = Path(__file__).parent
SQLITE_PATH = BASE_DIR / 'data' / 'storiiz.db'
SEED_PATH = BASE_DIR / 'channels.json'

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {'image/png', 'image/jpeg', 'image/webp'}
CATEGORIES = ['General', 'Animals', 'Fitness', 'Food', 'News', 'Tech', 'Entertainment', 'Other']
WHATSAPP_PREFIXES = ('https://whatsapp.com/channel/', 'https://www.whatsapp.com/channel/')
MAX_CAPTION = 280
MAX_MAINTENANCE = 300
MAX_ANNOUNCEMENT = 200
MAX_LINK = 300
ANNOUNCEMENT_KINDS = ['Info', 'Warning', 'Success']
DEFAULT_MAINTENANCE_MESSAGE = "Storiiz is under maintenance. We'll be back shortly."
URL_PATTERN = re.compile(r'https?://[^\s<>"\']+')

LIKE_WEIGHT = 3          # each like counts as 3 points of engagement
NEW_BOOST_MAX = 20.0     # newly added channels get up to 20 extra points...
NEW_BOOST_HOURS = 48.0   # ...decaying linearly to zero over 48 hours

CREATE_SQLITE_TABLE = '''
CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY,
    handle TEXT NOT NULL,
    name TEXT,
    category TEXT,
    avatar TEXT,
    image TEXT,
    caption TEXT,
    link TEXT NOT NULL,
    tags TEXT DEFAULT '',
    base_engagement INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    created_at TEXT,
    owner TEXT,
    is_verified INTEGER NOT NULL DEFAULT 0,
    is_pinned INTEGER NOT NULL DEFAULT 0
)
'''

CREATE_USERS_TABLE = '''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    is_verified INTEGER NOT NULL DEFAULT 0,
    is_banned INTEGER NOT NULL DEFAULT 0,
    created_at TEXT
)
'''

CREATE_LIKES_TABLE = '''
CREATE TABLE IF NOT EXISTS channel_likes (
    username TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    created_at TEXT,
    PRIMARY KEY (username, channel_id)
)
'''

CREATE_SETTINGS_TABLE = '''
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
'''


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def parse_time(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _secret(name):
    try:
        import streamlit as st
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name)


def _add_missing_columns(conn, table, columns):
    existing = {row['name'] for row in conn.execute(f'PRAGMA table_info({table})')}
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f'ALTER TABLE {table} ADD COLUMN {name} {ddl}')


def _user_out(row):
    """Public view of a user. Never includes the password hash."""
    return {
        'username': row['username'],
        'is_admin': bool(row.get('is_admin')),
        'is_verified': bool(row.get('is_verified')),
        'is_banned': bool(row.get('is_banned')),
        'created_at': row.get('created_at'),
    }


def _sqlite_flags(fields):
    return {k: (int(v) if isinstance(v, bool) else v) for k, v in fields.items()}


class SQLiteBackend:
    name = 'SQLite (local file)'

    def __init__(self, path=SQLITE_PATH):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        self.note = ''
        with closing(self._connect()) as conn:
            conn.execute(CREATE_SQLITE_TABLE)
            conn.execute(CREATE_USERS_TABLE)
            conn.execute(CREATE_LIKES_TABLE)
            conn.execute(CREATE_SETTINGS_TABLE)
            _add_missing_columns(conn, 'channels', {
                'owner': 'TEXT',
                'is_verified': 'INTEGER NOT NULL DEFAULT 0',
                'is_pinned': 'INTEGER NOT NULL DEFAULT 0',
            })
            _add_missing_columns(conn, 'users', {
                'is_admin': 'INTEGER NOT NULL DEFAULT 0',
                'is_verified': 'INTEGER NOT NULL DEFAULT 0',
                'is_banned': 'INTEGER NOT NULL DEFAULT 0',
            })
            conn.commit()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def list_channels(self):
        with closing(self._connect()) as conn:
            return [dict(row) for row in conn.execute('SELECT * FROM channels').fetchall()]

    def insert_channel(self, row):
        row = _sqlite_flags(row)
        cols = ', '.join(row.keys())
        marks = ', '.join('?' for _ in row)
        with closing(self._connect()) as conn:
            conn.execute(f'INSERT INTO channels ({cols}) VALUES ({marks})', list(row.values()))
            conn.commit()

    def update_channel(self, channel_id, fields):
        fields = _sqlite_flags(fields)
        if not fields:
            return
        sets = ', '.join(f'{k} = ?' for k in fields)
        with closing(self._connect()) as conn:
            conn.execute(f'UPDATE channels SET {sets} WHERE id = ?', [*fields.values(), channel_id])
            conn.commit()

    def delete_channel(self, channel_id):
        with closing(self._connect()) as conn:
            conn.execute('DELETE FROM channel_likes WHERE channel_id = ?', (channel_id,))
            conn.execute('DELETE FROM channels WHERE id = ?', (channel_id,))
            conn.commit()

    def get_user(self, username):
        with closing(self._connect()) as conn:
            row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            return dict(row) if row else None

    def list_users(self):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                'SELECT username, is_admin, is_verified, is_banned, created_at FROM users ORDER BY created_at'
            ).fetchall()
        return [_user_out(dict(row)) for row in rows]

    def create_user(self, data):
        row = _sqlite_flags({
            'username': data['username'],
            'password_hash': data['password_hash'],
            'is_admin': bool(data.get('is_admin')),
            'is_verified': bool(data.get('is_verified')),
            'is_banned': bool(data.get('is_banned')),
            'created_at': now_iso(),
        })
        cols = ', '.join(row.keys())
        marks = ', '.join('?' for _ in row)
        with closing(self._connect()) as conn:
            conn.execute(f'INSERT INTO users ({cols}) VALUES ({marks})', list(row.values()))
            conn.commit()

    def update_user(self, username, fields):
        fields = _sqlite_flags(fields)
        if not fields:
            return
        sets = ', '.join(f'{k} = ?' for k in fields)
        with closing(self._connect()) as conn:
            conn.execute(f'UPDATE users SET {sets} WHERE username = ?', [*fields.values(), username])
            conn.commit()

    def set_admin(self, username, is_admin):
        self.update_user(username, {'is_admin': bool(is_admin)})

    def get_setting(self, key):
        with closing(self._connect()) as conn:
            row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
            return row['value'] if row else None

    def set_setting(self, key, value):
        with closing(self._connect()) as conn:
            conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
            conn.commit()

    def liked_ids(self, username):
        with closing(self._connect()) as conn:
            rows = conn.execute('SELECT channel_id FROM channel_likes WHERE username = ?', (username,))
            return {row['channel_id'] for row in rows.fetchall()}

    def set_like(self, username, channel_id, liked):
        """Like or unlike a channel for one user. Each user can like a channel only once."""
        with closing(self._connect()) as conn:
            exists = conn.execute(
                'SELECT 1 FROM channel_likes WHERE username = ? AND channel_id = ?',
                (username, channel_id),
            ).fetchone() is not None
            if liked and not exists:
                conn.execute(
                    'INSERT INTO channel_likes (username, channel_id, created_at) VALUES (?, ?, ?)',
                    (username, channel_id, now_iso()),
                )
                conn.execute('UPDATE channels SET likes = likes + 1 WHERE id = ?', (channel_id,))
            elif not liked and exists:
                conn.execute(
                    'DELETE FROM channel_likes WHERE username = ? AND channel_id = ?',
                    (username, channel_id),
                )
                conn.execute('UPDATE channels SET likes = MAX(0, likes - 1) WHERE id = ?', (channel_id,))
            conn.commit()


class SupabaseBackend:
    name = 'Supabase'

    def __init__(self, url, key):
        from supabase import create_client
        self.client = create_client(url, key)
        self.note = ''

    def _table(self, name='channels'):
        return self.client.table(name)

    def list_channels(self):
        return self._table().select('*').execute().data or []

    def insert_channel(self, row):
        self._table().insert(row).execute()

    def update_channel(self, channel_id, fields):
        if fields:
            self._table().update(fields).eq('id', channel_id).execute()

    def delete_channel(self, channel_id):
        self._table('channel_likes').delete().eq('channel_id', channel_id).execute()
        self._table().delete().eq('id', channel_id).execute()

    def get_user(self, username):
        rows = self._table('users').select('*').eq('username', username).execute().data or []
        return rows[0] if rows else None

    def list_users(self):
        rows = self._table('users').select('username,is_admin,is_verified,is_banned,created_at').execute().data or []
        return [_user_out(row) for row in rows]

    def create_user(self, data):
        row = {
            'username': data['username'],
            'password_hash': data['password_hash'],
            'is_admin': bool(data.get('is_admin')),
            'is_verified': bool(data.get('is_verified')),
            'is_banned': bool(data.get('is_banned')),
            'created_at': now_iso(),
        }
        self._table('users').insert(row).execute()

    def update_user(self, username, fields):
        if fields:
            self._table('users').update(fields).eq('username', username).execute()

    def set_admin(self, username, is_admin):
        self.update_user(username, {'is_admin': bool(is_admin)})

    def get_setting(self, key):
        rows = self._table('settings').select('value').eq('key', key).execute().data or []
        return rows[0]['value'] if rows else None

    def set_setting(self, key, value):
        self._table('settings').upsert({'key': key, 'value': value}).execute()

    def liked_ids(self, username):
        rows = self._table('channel_likes').select('channel_id').eq('username', username).execute().data or []
        return {row['channel_id'] for row in rows}

    def set_like(self, username, channel_id, liked):
        existing = (self._table('channel_likes').select('channel_id')
                    .eq('username', username).eq('channel_id', channel_id).execute().data or [])
        channel = self._table().select('likes').eq('id', channel_id).execute().data or []
        if not channel:
            return
        current = channel[0].get('likes') or 0
        if liked and not existing:
            self._table('channel_likes').insert(
                {'username': username, 'channel_id': channel_id, 'created_at': now_iso()}
            ).execute()
            self._table().update({'likes': current + 1}).eq('id', channel_id).execute()
        elif not liked and existing:
            self._table('channel_likes').delete().eq('username', username).eq('channel_id', channel_id).execute()
            self._table().update({'likes': max(0, current - 1)}).eq('id', channel_id).execute()


def parse_tags(value):
    if not value:
        return []
    items = value if isinstance(value, list) else str(value).split(',')
    tags = []
    for item in items:
        tag = str(item).strip().lstrip('#').lower()
        if tag and tag not in tags:
            tags.append(tag)
    return tags[:10]


def build_row(data):
    handle = data['handle']
    slug = ''.join(ch if ch.isalnum() else '_' for ch in handle.lower().lstrip('@'))
    row = {
        'id': data.get('id') or f'{slug}_{uuid.uuid4().hex[:6]}',
        'handle': handle,
        'name': data.get('name') or handle,
        'category': data.get('category') or 'General',
        'avatar': data.get('avatar') or '',
        'image': data['image'],
        'caption': data.get('caption') or '',
        'link': data['link'],
        'tags': ','.join(parse_tags(data.get('tags'))),
        'base_engagement': int(data.get('base_engagement') or 0),
        'likes': int(data.get('likes') or 0),
        'created_at': data.get('created_at') or now_iso(),
        'is_verified': bool(data.get('is_verified')),
        'is_pinned': bool(data.get('is_pinned')),
    }
    if data.get('owner'):
        row['owner'] = data['owner']
    return row


def seed_if_empty(backend):
    """Load the sample channels from channels.json into an empty local database."""
    if backend.list_channels() or not SEED_PATH.exists():
        return
    seeds = json.loads(SEED_PATH.read_text(encoding='utf-8')).get('channels', [])
    for seed in seeds:
        backend.insert_channel(build_row({'created_at': '2026-01-01T00:00:00+00:00', **seed}))


def get_backend():
    url = _secret('SUPABASE_URL')
    key = _secret('SUPABASE_KEY')
    backend = None
    if url and key:
        try:
            backend = SupabaseBackend(url, key)
            backend.list_channels()  # verifies connection and table
        except Exception as exc:
            backend = SQLiteBackend()
            backend.note = (f'Supabase is configured but unavailable ({type(exc).__name__}). '
                            'Using local SQLite instead. Check the setup steps in the README.')
            seed_if_empty(backend)
    else:
        backend = SQLiteBackend()
        seed_if_empty(backend)
    auth.ensure_admin(backend)
    return backend


def _age_hours(created_at, now):
    created = parse_time(created_at)
    if created is None:
        return None
    return (now - created).total_seconds() / 3600


def engagement_score(channel, now=None):
    now = now or datetime.now(timezone.utc)
    score = (channel.get('base_engagement') or 0) + LIKE_WEIGHT * (channel.get('likes') or 0)
    age = _age_hours(channel.get('created_at'), now)
    if age is not None and 0 <= age < NEW_BOOST_HOURS:
        score += NEW_BOOST_MAX * (1 - age / NEW_BOOST_HOURS)
    return score


def ranked(channels):
    """Pinned channels come first, then everything by engagement score."""
    now = datetime.now(timezone.utc)
    return sorted(
        channels,
        key=lambda c: (bool(c.get('is_pinned')), engagement_score(c, now)),
        reverse=True,
    )


def encode_upload(upload):
    if upload.size > MAX_UPLOAD_BYTES:
        raise ValueError('Uploaded image must be 2 MB or smaller.')
    if upload.type not in ALLOWED_IMAGE_TYPES:
        raise ValueError('Upload a PNG, JPEG, or WebP image.')
    encoded = base64.b64encode(upload.getvalue()).decode('ascii')
    return f'data:{upload.type};base64,{encoded}'


def media_source(value):
    """Return bytes for uploaded (data URL) images, the URL string otherwise, or None."""
    if not value:
        return None
    if value.startswith('data:'):
        _, _, payload = value.partition(',')
        return base64.b64decode(payload)
    return value


def validate_submission(data):
    errors = []
    handle = (data.get('handle') or '').strip()
    if not handle.startswith('@') or len(handle) < 2 or ' ' in handle:
        errors.append('Handle must start with @ and contain no spaces, for example @yourchannel.')
    caption = (data.get('caption') or '').strip()
    if not caption:
        errors.append('Please add a caption.')
    elif len(caption) > MAX_CAPTION:
        errors.append(f'Caption must be {MAX_CAPTION} characters or fewer.')
    image = (data.get('image') or '').strip()
    if not image:
        errors.append('Add an image URL or upload an image.')
    elif not image.startswith('data:') and not image.startswith(('http://', 'https://')):
        errors.append('Image URL must start with http:// or https://.')
    avatar = (data.get('avatar') or '').strip()
    if avatar and not avatar.startswith(('http://', 'https://')):
        errors.append('Avatar URL must start with http:// or https:// (or leave it empty).')
    link = (data.get('link') or '').strip()
    if not link.startswith(WHATSAPP_PREFIXES):
        errors.append('WhatsApp Channel link must start with https://whatsapp.com/channel/')
    return errors


def create_channel(backend, data):
    row = build_row(data)
    backend.insert_channel(row)
    return row['id']


# ---- Maintenance mode ----

def get_maintenance(backend):
    raw = backend.get_setting('maintenance')
    try:
        data = json.loads(raw) if raw else {}
    except ValueError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return {
        'enabled': bool(data.get('enabled')),
        'message': data.get('message') or DEFAULT_MAINTENANCE_MESSAGE,
    }


def set_maintenance(backend, enabled, message):
    message = (message or '').strip()[:MAX_MAINTENANCE] or DEFAULT_MAINTENANCE_MESSAGE
    backend.set_setting('maintenance', json.dumps({'enabled': bool(enabled), 'message': message}))


# ---- Announcements (stored as a JSON list in the settings table) ----

def list_announcements(backend):
    raw = backend.get_setting('announcements')
    try:
        items = json.loads(raw) if raw else []
    except ValueError:
        items = []
    return items if isinstance(items, list) else []


def _save_announcements(backend, items):
    backend.set_setting('announcements', json.dumps(items))


def announcement_status(item, now=None):
    """'Live', 'Off' (switched off) or 'Expired'."""
    now = now or datetime.now(timezone.utc)
    if not item.get('active'):
        return 'Off'
    expires = parse_time(item.get('expires_at'))
    if expires is None or expires <= now:
        return 'Expired'
    return 'Live'


def live_announcements(backend):
    now = datetime.now(timezone.utc)
    return [a for a in list_announcements(backend) if announcement_status(a, now) == 'Live']


def find_link_in_text(text):
    """Return the first http(s) URL found in the text, without trailing punctuation."""
    match = URL_PATTERN.search(text or '')
    if not match:
        return ''
    return match.group(0).rstrip('.,;:!?)]}')


def clean_announcement_link(raw):
    """Accept an https/http link or a Storiiz @handle. Returns '' when empty, raises ValueError otherwise."""
    value = (raw or '').strip()
    if not value:
        return ''
    if len(value) > MAX_LINK:
        raise ValueError(f'Link must be {MAX_LINK} characters or fewer.')
    if value.startswith('@'):
        if len(value) < 2 or ' ' in value:
            raise ValueError('A channel handle must start with @ and contain no spaces.')
        return value
    if value.startswith(('https://', 'http://')) and ' ' not in value:
        return value
    raise ValueError('The link must start with https:// or be a @channel handle.')


def announcement_cta(backend, item):
    """Return (url, label) for the banner button, or None if there is no link.

    Priority: the link field (a URL, or a @handle looked up among channels), then a URL in the message.
    """
    url = ''
    raw = (item.get('link') or '').strip()
    if raw.startswith('@'):
        wanted = raw.lower()
        for channel in backend.list_channels():
            if (channel.get('handle') or '').lower() == wanted:
                url = channel.get('link') or ''
                break
    elif raw.startswith(('https://', 'http://')):
        url = raw
    if not url:
        url = find_link_in_text(item.get('message'))
    if not url.startswith(('https://', 'http://')):
        return None
    label = 'Join Channel →' if url.startswith(WHATSAPP_PREFIXES) else 'View Channel →'
    return url, label


def add_announcement(backend, message, kind, hours, link=''):
    cleaned_link = clean_announcement_link(link)
    items = list_announcements(backend)
    now = datetime.now(timezone.utc)
    items.append({
        'id': uuid.uuid4().hex[:10],
        'message': (message or '').strip()[:MAX_ANNOUNCEMENT],
        'kind': kind if kind in ANNOUNCEMENT_KINDS else 'Info',
        'link': cleaned_link,
        'active': True,
        'created_at': now.isoformat(),
        'expires_at': (now + timedelta(hours=max(1, int(hours)))).isoformat(),
    })
    _save_announcements(backend, items)


def update_announcement(backend, announcement_id, active):
    items = list_announcements(backend)
    for item in items:
        if item.get('id') == announcement_id:
            item['active'] = bool(active)
            _save_announcements(backend, items)
            return
    raise ValueError('That announcement no longer exists.')


def delete_announcement(backend, announcement_id):
    items = [a for a in list_announcements(backend) if a.get('id') != announcement_id]
    _save_announcements(backend, items)


# ---- Backup ----

def export_snapshot(backend):
    """Everything an admin needs for a backup. Password hashes are never included."""
    return {
        'exported_at': now_iso(),
        'channels': backend.list_channels(),
        'users': backend.list_users(),
        'maintenance': get_maintenance(backend),
        'announcements': list_announcements(backend),
    }
