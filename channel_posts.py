"""Channel posts for Storiiz: text, image or video updates published by channel owners.

Works with the existing storage backends (SQLite file or Supabase client) without changing storage.py.
Tables: channel_posts and channel_post_likes. Each user can like a post once.
"""

import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone

CONTENT_TYPES = ('text', 'image', 'video')
MAX_POST_CAPTION = 500

SQLITE_POSTS = '''
CREATE TABLE IF NOT EXISTS channel_posts (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'text',
    content TEXT NOT NULL DEFAULT '',
    media_url TEXT NOT NULL DEFAULT '',
    created_at TEXT,
    likes_count INTEGER NOT NULL DEFAULT 0
)
'''

SQLITE_POST_LIKES = '''
CREATE TABLE IF NOT EXISTS channel_post_likes (
    username TEXT NOT NULL,
    post_id TEXT NOT NULL,
    created_at TEXT,
    PRIMARY KEY (username, post_id)
)
'''


def _now():
    return datetime.now(timezone.utc).isoformat()


def _is_sqlite(backend):
    return hasattr(backend, 'path') and not hasattr(backend, 'client')


def _sqlite_conn(backend):
    conn = sqlite3.connect(backend.path)
    conn.row_factory = sqlite3.Row
    conn.execute(SQLITE_POSTS)
    conn.execute(SQLITE_POST_LIKES)
    return conn


def _validate(content_type, content, media_url):
    if content_type not in CONTENT_TYPES:
        raise ValueError('Post type must be text, image or video.')
    content = (content or '').strip()
    media_url = (media_url or '').strip()
    if len(content) > MAX_POST_CAPTION:
        raise ValueError(f'Post caption must be {MAX_POST_CAPTION} characters or fewer.')
    if content_type == 'text' and not content:
        raise ValueError('Write something for your post.')
    if content_type != 'text' and not media_url:
        raise ValueError('Add an image or video link to your post.')
    if media_url and not media_url.startswith(('http://', 'https://')):
        raise ValueError('Media link must start with http:// or https://.')
    return content, media_url


def create_channel_post(backend, channel_id, author_id, content_type, content, media_url=''):
    """Publish a post. Returns the new post id."""
    content, media_url = _validate(content_type, content, media_url)
    row = {
        'id': uuid.uuid4().hex,
        'channel_id': channel_id,
        'author_id': author_id,
        'content_type': content_type,
        'content': content,
        'media_url': media_url,
        'created_at': _now(),
        'likes_count': 0,
    }
    if _is_sqlite(backend):
        with closing(_sqlite_conn(backend)) as conn:
            cols = ', '.join(row)
            marks = ', '.join('?' for _ in row)
            conn.execute(f'INSERT INTO channel_posts ({cols}) VALUES ({marks})', list(row.values()))
            conn.commit()
    else:
        backend.client.table('channel_posts').insert(row).execute()
    return row['id']


def get_channel_posts(backend, channel_id, limit=50):
    """Newest first posts for one channel."""
    if _is_sqlite(backend):
        with closing(_sqlite_conn(backend)) as conn:
            rows = conn.execute(
                'SELECT * FROM channel_posts WHERE channel_id = ? ORDER BY created_at DESC LIMIT ?',
                (channel_id, int(limit)),
            ).fetchall()
        return [dict(row) for row in rows]
    rows = (backend.client.table('channel_posts').select('*').eq('channel_id', channel_id)
            .order('created_at', desc=True).limit(int(limit)).execute().data or [])
    return rows


def liked_post_ids(backend, username):
    """Ids of posts this user has liked."""
    if _is_sqlite(backend):
        with closing(_sqlite_conn(backend)) as conn:
            rows = conn.execute('SELECT post_id FROM channel_post_likes WHERE username = ?', (username,)).fetchall()
        return {row['post_id'] for row in rows}
    rows = backend.client.table('channel_post_likes').select('post_id').eq('username', username).execute().data or []
    return {row['post_id'] for row in rows}


def like_channel_post(backend, username, post_id, liked):
    """Like or unlike a post. Each user counts once."""
    liked = bool(liked)
    if _is_sqlite(backend):
        with closing(_sqlite_conn(backend)) as conn:
            exists = conn.execute(
                'SELECT 1 FROM channel_post_likes WHERE username = ? AND post_id = ?', (username, post_id)
            ).fetchone() is not None
            if liked and not exists:
                conn.execute(
                    'INSERT INTO channel_post_likes (username, post_id, created_at) VALUES (?, ?, ?)',
                    (username, post_id, _now()),
                )
                conn.execute('UPDATE channel_posts SET likes_count = likes_count + 1 WHERE id = ?', (post_id,))
            elif not liked and exists:
                conn.execute('DELETE FROM channel_post_likes WHERE username = ? AND post_id = ?', (username, post_id))
                conn.execute('UPDATE channel_posts SET likes_count = MAX(0, likes_count - 1) WHERE id = ?', (post_id,))
            conn.commit()
        return
    client = backend.client
    existing = (client.table('channel_post_likes').select('post_id')
                .eq('username', username).eq('post_id', post_id).execute().data or [])
    post = client.table('channel_posts').select('likes_count').eq('id', post_id).execute().data or []
    if not post:
        return
    current = post[0].get('likes_count') or 0
    if liked and not existing:
        client.table('channel_post_likes').insert(
            {'username': username, 'post_id': post_id, 'created_at': _now()}).execute()
        client.table('channel_posts').update({'likes_count': current + 1}).eq('id', post_id).execute()
    elif not liked and existing:
        client.table('channel_post_likes').delete().eq('username', username).eq('post_id', post_id).execute()
        client.table('channel_posts').update({'likes_count': max(0, current - 1)}).eq('id', post_id).execute()


def delete_channel_post(backend, post_id):
    """Remove a post and its likes."""
    if _is_sqlite(backend):
        with closing(_sqlite_conn(backend)) as conn:
            conn.execute('DELETE FROM channel_post_likes WHERE post_id = ?', (post_id,))
            conn.execute('DELETE FROM channel_posts WHERE id = ?', (post_id,))
            conn.commit()
        return
    backend.client.table('channel_post_likes').delete().eq('post_id', post_id).execute()
    backend.client.table('channel_posts').delete().eq('id', post_id).execute()
