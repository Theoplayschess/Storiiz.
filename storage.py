"""Storage, validation and ranking for Storiiz.

Uses Supabase when SUPABASE_URL and SUPABASE_KEY are set (st.secrets or environment variables).
Otherwise uses a local SQLite database that is created automatically in data/storiiz.db.
"""

import base64
import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
SQLITE_PATH = BASE_DIR / 'data' / 'storiiz.db'
SEED_PATH = BASE_DIR / 'channels.json'

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {'image/png', 'image/jpeg', 'image/webp'}
CATEGORIES = ['General', 'Animals', 'Fitness', 'Food', 'News', 'Tech', 'Entertainment', 'Other']
WHATSAPP_PREFIXES = ('https://whatsapp.com/channel/', 'https://www.whatsapp.com/channel/')
MAX_CAPTION = 280

LIKE_WEIGHT = 3          # each like counts as 3 points of engagement
NEW_BOOST_MAX = 20.0     # newly added channels get up to 20 extra points...
NEW_BOOST_HOURS = 48.0   # ...decaying linearly to zero over 48 hours

COLUMNS = ['id', 'handle', 'name', 'category', 'avatar', 'image', 'caption', 'link',
           'tags', 'base_engagement', 'likes', 'created_at']

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
    created_at TEXT
)
'''


def _secret(name):
    try:
        import streamlit as st
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name)


class SQLiteBackend:
    name = 'SQLite (local file)'

    def __init__(self, path=SQLITE_PATH):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        self.note = ''
        with closing(self._connect()) as conn:
            conn.execute(CREATE_SQLITE_TABLE)
            conn.commit()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def list_channels(self):
        with closing(self._connect()) as conn:
            return [dict(row) for row in conn.execute('SELECT * FROM channels').fetchall()]

    def insert_channel(self, row):
        cols = ', '.join(row.keys())
        marks = ', '.join('?' for _ in row)
        with closing(self._connect()) as conn:
            conn.execute(f'INSERT INTO channels ({cols}) VALUES ({marks})', list(row.values()))
            conn.commit()

    def add_like(self, channel_id, delta):
        with closing(self._connect()) as conn:
            conn.execute('UPDATE channels SET likes = MAX(0, likes + ?) WHERE id = ?', (delta, channel_id))
            conn.commit()


class SupabaseBackend:
    name = 'Supabase'

    def __init__(self, url, key):
        from supabase import create_client
        self.client = create_client(url, key)
        self.note = ''

    def _table(self):
        return self.client.table('channels')

    def list_channels(self):
        return self._table().select('*').execute().data or []

    def insert_channel(self, row):
        self._table().insert(row).execute()

    def add_like(self, channel_id, delta):
        rows = self._table().select('likes').eq('id', channel_id).execute().data or []
        if not rows:
            return
        new_likes = max(0, (rows[0].get('likes') or 0) + delta)
        self._table().update({'likes': new_likes}).eq('id', channel_id).execute()


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
    return {
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
        'created_at': data.get('created_at') or datetime.now(timezone.utc).isoformat(),
    }


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
    if url and key:
        try:
            backend = SupabaseBackend(url, key)
            backend.list_channels()  # verifies connection and table
            return backend
        except Exception as exc:
            fallback = SQLiteBackend()
            fallback.note = (f'Supabase is configured but unavailable ({type(exc).__name__}). '
                             'Using local SQLite instead. Check the setup steps in the README.')
            seed_if_empty(fallback)
            return fallback
    backend = SQLiteBackend()
    seed_if_empty(backend)
    return backend


def _age_hours(created_at, now):
    if not created_at:
        return None
    try:
        created = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
    except ValueError:
        return None
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return (now - created).total_seconds() / 3600


def engagement_score(channel, now=None):
    now = now or datetime.now(timezone.utc)
    score = (channel.get('base_engagement') or 0) + LIKE_WEIGHT * (channel.get('likes') or 0)
    age = _age_hours(channel.get('created_at'), now)
    if age is not None and 0 <= age < NEW_BOOST_HOURS:
        score += NEW_BOOST_MAX * (1 - age / NEW_BOOST_HOURS)
    return score


def ranked(channels):
    now = datetime.now(timezone.utc)
    return sorted(channels, key=lambda c: engagement_score(c, now), reverse=True)


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
