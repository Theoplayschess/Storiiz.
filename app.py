import html
import json

import streamlit as st

import auth
import storage

st.set_page_config(page_title='Storiiz', page_icon='💬', layout='centered')

PAGE_STEP = 8
GREEN = '#25D366'
DARK_BG = '#0B0F0C'
CARD_BG = '#141A16'
VERIFIED_BLUE = '#1D9BF0'

# Pill label -> category filter. Trending shows everything ranked.
PILLS = {
    '🔥 Trending': None,
    '💪 Fitness': 'Fitness',
    '📰 News': 'News',
    '🎮 Gaming': 'Entertainment',
    '🍳 Cooking': 'Food',
    '🐶 Pets': 'Animals',
    '💻 Tech': 'Tech',
}

CSS = f'''
<style>
.stApp {{ background: {DARK_BG}; color: #F2F5F3; }}
.block-container {{ max-width: 720px; padding-top: 1rem; padding-bottom: 4rem; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.brand {{ font-size: 2rem; font-weight: 900; letter-spacing: 0.5px; color: {GREEN}; }}
.brand span {{ color: #F2F5F3; }}
.card {{ background: {CARD_BG}; border: 1px solid #1F2A23; border-radius: 22px;
  padding: 1.1rem; margin-bottom: 1.6rem; box-shadow: 0 0 28px rgba(37,211,102,0.08); }}
.card-head {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.9rem; }}
.avatar {{ width: 56px; height: 56px; border-radius: 50%; object-fit: cover; border: 2px solid {GREEN}; }}
.handle {{ font-size: 1.25rem; font-weight: 800; }}
.tag {{ display: inline-block; background: #1E2B23; color: {GREEN}; border-radius: 999px;
  padding: 0.15rem 0.7rem; font-size: 0.9rem; font-weight: 700; margin-left: 0.4rem; }}
.verified {{ display: inline-block; background: {VERIFIED_BLUE}; color: #FFFFFF; border-radius: 999px;
  padding: 0.12rem 0.55rem; font-size: 0.8rem; font-weight: 800; margin-left: 0.45rem; vertical-align: middle; }}
.pinned {{ display: inline-block; background: #2B2412; color: #F5B301; border-radius: 999px;
  padding: 0.12rem 0.55rem; font-size: 0.8rem; font-weight: 800; margin-left: 0.4rem; vertical-align: middle; }}
.likes-badge {{ margin-left: auto; background: #1E2B23; border-radius: 999px; padding: 0.3rem 0.8rem;
  font-weight: 700; font-size: 1rem; white-space: nowrap; }}
.media {{ width: 100%; border-radius: 16px; display: block; max-height: 520px; object-fit: cover; }}
.title {{ font-size: 1.5rem; font-weight: 800; margin: 0.9rem 0 0.25rem 0; }}
.desc {{ font-size: 1.1rem; color: #B9C6BE; line-height: 1.5; margin-bottom: 0.9rem; }}
.hashtags {{ color: {GREEN}; font-weight: 600; margin-bottom: 0.9rem; }}
.owner {{ color: #8FA096; font-size: 0.95rem; margin-bottom: 0.6rem; }}
.badge-admin {{ display: inline-block; background: #F5B301; color: #1A1200; border-radius: 999px;
  padding: 0.1rem 0.6rem; font-size: 0.8rem; font-weight: 800; margin-left: 0.4rem; vertical-align: middle; }}
.userline {{ font-weight: 700; font-size: 1.05rem; padding-top: 0.5rem; }}
.maint-banner {{ background: #3A2A00; border: 1px solid #F5B301; color: #FFE08A; border-radius: 14px;
  padding: 0.6rem 0.9rem; font-weight: 700; margin-bottom: 0.8rem; }}
.barrier {{ text-align: center; padding: 4rem 1.2rem; background: {CARD_BG}; border: 1px solid #1F2A23;
  border-radius: 24px; margin: 2rem 0; }}
.barrier h1 {{ font-size: 2.2rem !important; color: {GREEN}; }}
.barrier p {{ font-size: 1.2rem; color: #B9C6BE; }}
.stButton button {{ border-radius: 14px !important; font-weight: 700 !important; font-size: 1.05rem !important;
  background: #1E2B23 !important; color: #F2F5F3 !important; border: 1px solid #2B3A31 !important; min-height: 3.1rem; }}
.stLinkButton a {{ border-radius: 14px !important; font-weight: 800 !important; font-size: 1.1rem !important;
  background: {GREEN} !important; color: #04130A !important; border: none !important; min-height: 3.1rem;
  display: flex; align-items: center; justify-content: center; text-decoration: none; }}
.stTextInput input {{ background: {CARD_BG} !important; color: #F2F5F3 !important; border-radius: 14px !important;
  border: 1px solid #1F2A23 !important; font-size: 1.05rem; }}
div[role="radiogroup"] {{ gap: 0.5rem; flex-wrap: wrap; }}
div[role="radiogroup"] label {{ background: {CARD_BG}; border: 1px solid #1F2A23; border-radius: 999px;
  padding: 0.35rem 0.9rem; }}
div[role="radiogroup"] label:has(input:checked) {{ background: {GREEN}; color: #04130A; border-color: {GREEN}; }}
div[role="radiogroup"] label p {{ font-weight: 700; font-size: 0.98rem; }}
</style>
'''


@st.cache_resource
def get_backend():
    return storage.get_backend()


# ---------- session and notices ----------

def init_state():
    st.session_state.setdefault('user', None)
    st.session_state.setdefault('liked_ids', set())
    st.session_state.setdefault('visible', PAGE_STEP)
    st.session_state.setdefault('dismissed', set())


def notify(kind, text):
    st.session_state.notice = (kind, text)


def current_user():
    return st.session_state.user


def is_admin_user():
    return auth.is_admin(current_user())


def refresh_user(backend):
    """Re-read the logged-in account so bans, role changes and verification apply immediately."""
    user = current_user()
    if not user:
        return
    fresh = backend.get_user(user['username'])
    if fresh is None or fresh.get('is_banned'):
        st.session_state.user = None
        st.session_state.liked_ids = set()
        notify('error', 'Your account is no longer active. You have been logged out.')
        return
    st.session_state.user = {
        'username': fresh['username'],
        'is_admin': bool(fresh.get('is_admin')),
        'is_verified': bool(fresh.get('is_verified')),
    }


def load_likes(backend):
    user = current_user()
    st.session_state.liked_ids = backend.liked_ids(user['username']) if user else set()


def log_out():
    st.session_state.user = None
    st.session_state.liked_ids = set()
    notify('info', 'You have logged out.')


# ---------- accounts ----------

def do_login(backend, username, password):
    user, message = auth.log_in(backend, username, password)
    if user is None:
        st.error(message)
        return False
    st.session_state.user = user
    load_likes(backend)
    return True


def login_form(backend):
    with st.form('login_form'):
        username = st.text_input('Username', key='login_username')
        password = st.text_input('Password', type='password', key='login_password')
        submitted = st.form_submit_button('Log in')
    if submitted and do_login(backend, username, password):
        st.rerun()


def signup_form(backend):
    with st.form('signup_form'):
        username = st.text_input('Username', help='3 to 30 characters: letters, numbers or underscores.',
                                 key='signup_username')
        password = st.text_input('Password', type='password', help='At least 8 characters.',
                                 key='signup_password')
        confirm = st.text_input('Confirm password', type='password', key='signup_confirm')
        submitted = st.form_submit_button('Create account')
    if not submitted:
        return
    errors = auth.validate_signup(username, password, confirm)
    if errors:
        for message in errors:
            st.error(message)
        return
    try:
        auth.sign_up(backend, username, password)
    except ValueError as exc:
        st.error(str(exc))
        return
    if do_login(backend, username, password):
        notify('success', 'Account created. Welcome to Storiiz!')
        st.rerun()


def account_bar(backend):
    user = current_user()
    if user is None:
        with st.expander('Log in or create an account'):
            login_tab, signup_tab = st.tabs(['Log in', 'Create account'])
            with login_tab:
                login_form(backend)
            with signup_tab:
                signup_form(backend)
        return
    badge = "<span class='badge-admin'>ADMIN</span>" if user['is_admin'] else ''
    verified = "<span class='verified'>✓ Verified</span>" if user.get('is_verified') else ''
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(
            f"<div class='userline'>Logged in as @{html.escape(user['username'])}{badge}{verified}</div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.button('Log out', on_click=log_out, use_container_width=True)


# ---------- feed ----------

def toggle_like(backend, channel_id):
    user = current_user()
    if not user:
        return
    liked = channel_id not in st.session_state.liked_ids
    backend.set_like(user['username'], channel_id, liked)
    if liked:
        st.session_state.liked_ids.add(channel_id)
    else:
        st.session_state.liked_ids.discard(channel_id)


def remove_channel(backend, channel_id):
    if not is_admin_user():
        return
    backend.delete_channel(channel_id)
    notify('success', 'Channel removed from the feed.')


def set_channel_flag(backend, channel_id, field, value):
    if not is_admin_user():
        return
    backend.update_channel(channel_id, {field: bool(value)})
    label = {'is_verified': 'verification', 'is_pinned': 'pin'}.get(field, field)
    notify('success', f"Channel {label} updated.")


def image_src(value):
    source = storage.media_source(value)
    return source if isinstance(source, str) else ''


def render_card(backend, channel):
    user = current_user()
    is_admin = auth.is_admin(user)
    handle = html.escape(channel['handle'])
    title = html.escape(channel.get('name') or channel['handle'])
    desc = html.escape(channel.get('caption') or '')
    category = html.escape(channel.get('category') or '')
    owner = channel.get('owner')
    owner_html = f"<div class='owner'>Submitted by @{html.escape(owner)}</div>" if owner else ''
    verified = "<span class='verified'>✓ Verified</span>" if channel.get('is_verified') else ''
    pinned = "<span class='pinned'>📌 Pinned</span>" if channel.get('is_pinned') else ''
    avatar_src = html.escape(image_src(channel.get('avatar') or channel.get('image')))
    media_src = html.escape(image_src(channel.get('image')))
    likes = channel.get('likes') or 0
    tags = storage.parse_tags(channel.get('tags'))
    tags_html = f"<div class='hashtags'>{' '.join('#' + html.escape(t) for t in tags)}</div>" if tags else ''

    st.markdown(f"""
<div class='card'>
  <div class='card-head'>
    <img class='avatar' src='{avatar_src}' alt=''/>
    <div>
      <span class='handle'>{handle}</span>{verified}{pinned}<span class='tag'>{category}</span>
    </div>
    <div class='likes-badge'>❤ {likes}</div>
  </div>
  {owner_html}
  <img class='media' src='{media_src}' alt='{title}'/>
  <div class='title'>{title}</div>
  <div class='desc'>{desc}</div>
  {tags_html}
</div>
""", unsafe_allow_html=True)

    channel_id = channel['id']
    liked = channel_id in st.session_state.liked_ids
    cols = st.columns([1, 2, 1]) if is_admin else st.columns([1, 2])
    with cols[0]:
        if user:
            st.button(
                '❤️ Liked' if liked else '🤍 Like',
                key=f'like_{channel_id}',
                on_click=toggle_like,
                args=(backend, channel_id),
                use_container_width=True,
            )
        else:
            st.button('🤍 Log in to like', key=f'like_{channel_id}', disabled=True, use_container_width=True)
    with cols[1]:
        st.link_button('Join WhatsApp Channel  →', channel['link'], use_container_width=True)
    if is_admin:
        with cols[2]:
            st.button(
                '🗑 Remove',
                key=f'remove_{channel_id}',
                on_click=remove_channel,
                args=(backend, channel_id),
                use_container_width=True,
            )
    st.write('')


def matches(channel, query, category):
    if category and channel.get('category') != category:
        return False
    if not query:
        return True
    haystack = ' '.join([
        channel.get('handle') or '', channel.get('name') or '',
        channel.get('caption') or '', channel.get('tags') or '',
    ]).lower()
    return query.lower() in haystack


def feed_view(backend, query, pill):
    channels = backend.list_channels()
    if not channels:
        st.info('No channels yet. Be the first to submit one in the Submit tab.')
        return
    category = PILLS[pill]
    queue = [c for c in storage.ranked(channels) if matches(c, query, category)]
    if not queue:
        st.info('No channels match your search or filter.')
        return
    visible = st.session_state.visible
    for channel in queue[:visible]:
        render_card(backend, channel)
    if visible < len(queue):
        if st.button(f'Load more ({len(queue) - visible} left)', use_container_width=True):
            st.session_state.visible = visible + PAGE_STEP
            st.rerun()
    else:
        st.caption('You have reached the end of the feed.')


def submit_view(backend):
    user = current_user()
    if not user:
        st.info('Log in or create an account above to submit a channel.')
        return
    st.write('Share your WhatsApp Channel with the Storiiz community. New channels appear in the feed right away.')
    with st.form('submit_channel', clear_on_submit=True):
        handle = st.text_input('Handle', placeholder='@yourchannel')
        name = st.text_input('Channel name')
        category = st.selectbox('Category', storage.CATEGORIES)
        caption = st.text_area('Caption', max_chars=storage.MAX_CAPTION)
        image_url = st.text_input('Image URL', placeholder='https://...')
        upload = st.file_uploader(
            'Or upload an image (PNG, JPEG, WebP, max 2 MB)',
            type=['png', 'jpg', 'jpeg', 'webp'],
        )
        avatar_url = st.text_input('Avatar URL (optional, defaults to the image)')
        link = st.text_input('WhatsApp Channel link', placeholder='https://whatsapp.com/channel/...')
        tags = st.text_input('Tags (comma separated)', placeholder='pets, funny')
        submitted = st.form_submit_button('Submit channel')

    if not submitted:
        return

    errors = []
    image = image_url.strip()
    if upload is not None:
        try:
            image = storage.encode_upload(upload)
        except ValueError as exc:
            errors.append(str(exc))

    data = {
        'handle': handle.strip(),
        'name': name.strip(),
        'category': category,
        'caption': caption.strip(),
        'image': image,
        'avatar': avatar_url.strip(),
        'link': link.strip(),
        'tags': tags,
        'owner': user['username'],
    }
    errors += storage.validate_submission(data)
    if errors:
        for message in errors:
            st.error(message)
        return

    try:
        channel_id = storage.create_channel(backend, data)
    except Exception as exc:
        st.error(f'Could not save your channel: {exc}')
        return
    st.success(f"Thanks! {data['handle']} is now live in the feed (id: {channel_id}).")


# ---------- admin actions ----------

def act_role(backend, username, make_admin):
    try:
        auth.set_admin_role(backend, current_user(), username, make_admin)
        notify('success', f"@{username} is now {'an admin' if make_admin else 'a regular user'}.")
    except (ValueError, PermissionError) as exc:
        notify('error', str(exc))


def act_user_verify(backend, username, verified):
    try:
        auth.set_verified(backend, current_user(), username, verified)
        notify('success', f"@{username} {'verified' if verified else 'unverified'}.")
    except (ValueError, PermissionError) as exc:
        notify('error', str(exc))


def act_ban(backend, username, banned):
    try:
        auth.set_banned(backend, current_user(), username, banned)
        notify('success', f"@{username} {'frozen (banned)' if banned else 'unfrozen'}.")
    except (ValueError, PermissionError) as exc:
        notify('error', str(exc))


def act_reset_password(backend, username):
    new_password = st.session_state.get(f'reset_{username}', '')
    try:
        auth.reset_password(backend, current_user(), username, new_password)
        st.session_state[f'reset_{username}'] = ''
        notify('success', f'Password reset for @{username}.')
    except (ValueError, PermissionError) as exc:
        notify('error', str(exc))


def act_save_maintenance(backend):
    storage.set_maintenance(
        backend,
        st.session_state.get('maint_enabled', False),
        st.session_state.get('maint_message', ''),
    )
    state = 'ON' if st.session_state.get('maint_enabled') else 'OFF'
    notify('success', f'Maintenance mode saved. It is now {state}.')


def act_add_announcement(backend):
    message = st.session_state.get('ann_message', '').strip()
    if not message:
        notify('error', 'Write a message for the announcement.')
        return
    amount = int(st.session_state.get('ann_amount', 24))
    hours = amount * (24 if st.session_state.get('ann_unit') == 'Days' else 1)
    storage.add_announcement(backend, message, st.session_state.get('ann_kind', 'Info'), hours)
    st.session_state['ann_message'] = ''
    notify('success', 'Announcement published.')


def act_set_announcement(backend, announcement_id, active):
    try:
        storage.update_announcement(backend, announcement_id, active)
        notify('success', 'Announcement updated.')
    except ValueError as exc:
        notify('error', str(exc))


def act_delete_announcement(backend, announcement_id):
    storage.delete_announcement(backend, announcement_id)
    notify('success', 'Announcement deleted.')


# ---------- admin panel ----------

def admin_view(backend):
    user = current_user()
    channels = backend.list_channels()
    users = backend.list_users()

    st.subheader('Stats')
    cols = st.columns(4)
    cols[0].metric('Users', len(users))
    cols[1].metric('Admins', sum(1 for u in users if u['is_admin']))
    cols[2].metric('Verified users', sum(1 for u in users if u['is_verified']))
    cols[3].metric('Banned users', sum(1 for u in users if u['is_banned']))
    cols = st.columns(4)
    cols[0].metric('Channels', len(channels))
    cols[1].metric('Verified channels', sum(1 for c in channels if c.get('is_verified')))
    cols[2].metric('Pinned channels', sum(1 for c in channels if c.get('is_pinned')))
    cols[3].metric('Total likes', sum((c.get('likes') or 0) for c in channels))

    st.subheader('Maintenance mode')
    maint = storage.get_maintenance(backend)
    with st.form('maintenance_form'):
        st.toggle('Maintenance mode is on', value=maint['enabled'], key='maint_enabled')
        st.text_area('Message shown to visitors', value=maint['message'], max_chars=storage.MAX_MAINTENANCE,
                     key='maint_message')
        st.form_submit_button('Save maintenance settings', on_click=act_save_maintenance, args=(backend,))
    st.caption('Admins are not blocked. Regular visitors see the maintenance screen while this is on.')

    st.subheader('Announcements')
    with st.form('announcement_form', clear_on_submit=False):
        st.text_input('Message', max_chars=storage.MAX_ANNOUNCEMENT, key='ann_message')
        cols = st.columns(3)
        with cols[0]:
            st.selectbox('Style', storage.ANNOUNCEMENT_KINDS, key='ann_kind')
        with cols[1]:
            st.number_input('Lasts for', min_value=1, max_value=365, value=24, key='ann_amount')
        with cols[2]:
            st.selectbox('Unit', ['Hours', 'Days'], key='ann_unit')
        st.form_submit_button('Publish announcement', on_click=act_add_announcement, args=(backend,))
    announcements = sorted(storage.list_announcements(backend), key=lambda a: a.get('created_at') or '',
                           reverse=True)
    now = storage.datetime.now(storage.timezone.utc)
    if not announcements:
        st.caption('No announcements yet.')
    for item in announcements:
        status = storage.announcement_status(item, now)
        expires = storage.parse_time(item.get('expires_at'))
        when = expires.strftime('%A, %B %d, %Y %H:%M UTC') if expires else 'unknown'
        cols = st.columns([4, 1, 1])
        with cols[0]:
            st.markdown(f"**{html.escape(item.get('message', ''))}**")
            st.caption(f"{item.get('kind')} | {status} | expires {when}")
        with cols[1]:
            if item.get('active'):
                st.button('Turn off', key=f"ann_off_{item['id']}", on_click=act_set_announcement,
                          args=(backend, item['id'], False), use_container_width=True)
            else:
                st.button('Turn on', key=f"ann_on_{item['id']}", on_click=act_set_announcement,
                          args=(backend, item['id'], True), use_container_width=True)
        with cols[2]:
            st.button('Delete', key=f"ann_del_{item['id']}", on_click=act_delete_announcement,
                      args=(backend, item['id']), use_container_width=True)

    st.subheader('Channels')
    if not channels:
        st.info('No channels.')
    for channel in sorted(channels, key=lambda c: c.get('created_at') or '', reverse=True):
        badges = ''
        if channel.get('is_verified'):
            badges += ' ✓ verified'
        if channel.get('is_pinned'):
            badges += ' 📌 pinned'
        st.markdown(f"**{html.escape(channel['handle'])}**{html.escape(badges)}")
        st.caption(f"{channel.get('name') or ''} | {channel.get('category') or ''} | "
                   f"by @{channel.get('owner') or 'sample'} | ❤ {channel.get('likes') or 0}")
        cols = st.columns(3)
        with cols[0]:
            st.button(
                'Unverify' if channel.get('is_verified') else 'Verify',
                key=f"cv_{channel['id']}",
                on_click=set_channel_flag,
                args=(backend, channel['id'], 'is_verified', not channel.get('is_verified')),
                use_container_width=True,
            )
        with cols[1]:
            st.button(
                'Unpin' if channel.get('is_pinned') else 'Pin to top',
                key=f"cp_{channel['id']}",
                on_click=set_channel_flag,
                args=(backend, channel['id'], 'is_pinned', not channel.get('is_pinned')),
                use_container_width=True,
            )
        with cols[2]:
            st.button('Remove', key=f"admin_remove_{channel['id']}", on_click=remove_channel,
                      args=(backend, channel['id']), use_container_width=True)

    st.subheader('Channel stats')
    ranked_channels = sorted(channels, key=lambda c: c.get('likes') or 0, reverse=True)
    st.dataframe(
        [{'handle': c['handle'], 'category': c.get('category') or '', 'owner': c.get('owner') or 'sample',
          'likes': c.get('likes') or 0, 'verified': bool(c.get('is_verified')),
          'pinned': bool(c.get('is_pinned'))} for c in ranked_channels],
        use_container_width=True,
    )

    st.subheader('Users')
    for member in users:
        name = member['username']
        badges = ''
        if member['is_admin']:
            badges += ' ADMIN'
        if member['is_verified']:
            badges += ' ✓ verified'
        if member['is_banned']:
            badges += ' BANNED'
        st.markdown(f"**@{html.escape(name)}**{html.escape(badges)}")
        st.caption(f"Joined {str(member.get('created_at') or '')[:10]}")
        cols = st.columns(3)
        with cols[0]:
            st.button(
                'Demote' if member['is_admin'] else 'Make admin',
                key=f'role_{name}',
                on_click=act_role,
                args=(backend, name, not member['is_admin']),
                use_container_width=True,
                disabled=(name == user['username'] and member['is_admin']),
            )
        with cols[1]:
            st.button(
                'Unverify' if member['is_verified'] else 'Verify',
                key=f'uv_{name}',
                on_click=act_user_verify,
                args=(backend, name, not member['is_verified']),
                use_container_width=True,
            )
        with cols[2]:
            st.button(
                'Unban' if member['is_banned'] else 'Ban',
                key=f'ban_{name}',
                on_click=act_ban,
                args=(backend, name, not member['is_banned']),
                use_container_width=True,
                disabled=(name == user['username']),
            )
        with st.expander(f'Reset password for @{name}'):
            st.text_input('New password', type='password', key=f'reset_{name}')
            st.button('Set new password', key=f'resetbtn_{name}', on_click=act_reset_password,
                      args=(backend, name))

    st.subheader('Backup')
    snapshot = storage.export_snapshot(backend)
    st.download_button(
        'Download backup (JSON)',
        data=json.dumps(snapshot, indent=2, default=str),
        file_name='storiiz-backup.json',
        mime='application/json',
        use_container_width=True,
    )
    st.caption('The backup includes channels, users (no password hashes), maintenance and announcements.')


# ---------- page ----------

def maintenance_barrier(backend, message):
    st.markdown(
        f"<div class='barrier'><h1>We'll be right back</h1><p>{html.escape(message)}</p></div>",
        unsafe_allow_html=True,
    )
    account_bar(backend)


def announcement_banners(backend):
    for item in storage.live_announcements(backend):
        if item['id'] in st.session_state.dismissed:
            continue
        text = html.escape(item.get('message', ''))
        kind = item.get('kind')
        cols = st.columns([9, 1])
        with cols[0]:
            if kind == 'Warning':
                st.warning(text)
            elif kind == 'Success':
                st.success(text)
            else:
                st.info(text)
        with cols[1]:
            if st.button('✕', key=f"dismiss_{item['id']}", help='Dismiss'):
                st.session_state.dismissed.add(item['id'])
                st.rerun()


def main():
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    backend = get_backend()
    st.sidebar.caption(f'Storage: {backend.name}')
    if backend.note:
        st.sidebar.warning(backend.note)

    refresh_user(backend)
    st.markdown("<div class='brand'>STORIIZ<span>.</span></div>", unsafe_allow_html=True)
    notice = st.session_state.pop('notice', None)
    if notice:
        kind, text = notice
        getattr(st, kind)(text)

    maint = storage.get_maintenance(backend)
    if maint['enabled'] and not is_admin_user():
        maintenance_barrier(backend, maint['message'])
        st.stop()

    account_bar(backend)
    if maint['enabled']:
        st.markdown(
            "<div class='maint-banner'>⚠ Maintenance mode is ON. Regular visitors see a maintenance screen. "
            "Admins can still use the full site.</div>",
            unsafe_allow_html=True,
        )
    announcement_banners(backend)

    user = current_user()
    names = ['Feed', 'Submit a channel'] + (['Admin Panel'] if auth.is_admin(user) else [])
    tabs = st.tabs(names)
    with tabs[0]:
        query = st.text_input('Search', placeholder='Search channels...', label_visibility='collapsed')
        pill = st.radio('Category', list(PILLS.keys()), horizontal=True, label_visibility='collapsed')
        if query != st.session_state.get('last_query') or pill != st.session_state.get('last_pill'):
            st.session_state.visible = PAGE_STEP
            st.session_state.last_query = query
            st.session_state.last_pill = pill
        feed_view(backend, query.strip(), pill)
    with tabs[1]:
        submit_view(backend)
    if len(tabs) > 2:
        with tabs[2]:
            admin_view(backend)


st.markdown(CSS, unsafe_allow_html=True)
main()
