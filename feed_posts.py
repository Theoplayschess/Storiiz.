"""Latest channel posts shown in the Vidéo and Photo feeds, with like counters and admin removal."""

import html

import streamlit as st

import channel_posts

MAX_POSTS = 8


def _media_html(post):
    media = html.escape(post.get('media_url') or '', quote=True)
    if not media:
        return ''
    if post.get('content_type') == 'video':
        return f"<video class='media' src='{media}' controls playsinline></video>"
    if post.get('content_type') == 'image':
        return f"<img class='media' src='{media}' alt=''/>"
    return ''


def _toggle_like(backend, user, post_id, currently_liked):
    if not user:
        return
    channel_posts.like_channel_post(backend, user['username'], post_id, not currently_liked)


def _remove(backend, post_id):
    channel_posts.delete_channel_post(backend, post_id)


def render(backend, queue, user, is_admin):
    """Show up to MAX_POSTS posts from the channels in this feed, newest first."""
    pairs = []
    for channel in queue[:MAX_POSTS]:
        for post in channel_posts.get_channel_posts(backend, channel['id'], limit=5):
            pairs.append((channel, post))
    if not pairs:
        return
    pairs.sort(key=lambda pair: pair[1].get('created_at') or '', reverse=True)
    liked_ids = channel_posts.liked_post_ids(backend, user['username']) if user else set()
    st.subheader('Dernières publications')
    for channel, post in pairs[:MAX_POSTS]:
        post_id = post['id']
        is_liked = post_id in liked_ids
        handle = html.escape(channel.get('handle') or '')
        content = html.escape(post.get('content') or '')
        st.markdown(
            f"<div class='card'><div class='card-head'><div><span class='handle'>{handle}</span></div></div>"
            f"{_media_html(post)}<div class='desc'>{content}</div></div>",
            unsafe_allow_html=True,
        )
        count = post.get('likes_count') or 0
        cols = st.columns([1, 1]) if is_admin else st.columns([1])
        with cols[0]:
            if user:
                st.button(
                    f"{'♥' if is_liked else '♡'} {count}",
                    key=f'postlike_{post_id}',
                    on_click=_toggle_like,
                    args=(backend, user, post_id, is_liked),
                    use_container_width=True,
                )
            else:
                st.caption(f'♡ {count}')
        if is_admin:
            with cols[1]:
                st.button('Retirer', key=f'postdel_{post_id}', on_click=_remove,
                          args=(backend, post_id), use_container_width=True)
