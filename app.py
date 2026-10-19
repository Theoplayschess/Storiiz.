import html
import json

import streamlit as st

import auth
import custom_roles
import i18n
import role_ui
import storage
from i18n import t

st.set_page_config(page_title='Storiiz', page_icon='💬', layout='centered')

PAGE_STEP = 8
GREEN = '#25D366'
INK = '#EDF1EE'
MUTED = '#8C9A92'
SOFT = '#B7C3BB'
PAGE_BG = '#0B0F0C'
SURFACE = '#121813'
LINE = '#1E2820'
VERIFIED_BLUE = '#4DA3F5'

# Pill translation key -> stored category filter. Trending shows everything ranked.
PILLS = {
    'pill.trending': None,
    'pill.fitness': 'Fitness',
    'pill.news': 'News',
    'pill.gaming': 'Entertainment',
    'pill.cooking': 'Food',
    'pill.pets': 'Animals',
    'pill.tech': 'Tech',
}

# Level -> (CSS class, translation key) for the role badge.
LEVEL_BADGES = {
    auth.LEVEL_MAIN_ADMIN: ('lvl-main', 'lvl.main'),
    auth.LEVEL_SUPER_ADMIN: ('lvl-super', 'lvl.super'),
    auth.LEVEL_ADMIN: ('lvl-admin', 'lvl.admin'),
    auth.LEVEL_VERIFIED: ('lvl-verified', 'lvl.verified'),
    auth.LEVEL_OWNER: ('lvl-owner', 'lvl.owner'),
    auth.LEVEL_USER: ('lvl-user', 'lvl.user'),
    auth.LEVEL_GUEST: ('lvl-guest', 'lvl.guest'),
}

CSS = f'''
<style>
.stApp {{ background: {PAGE_BG}; color: {INK}; }}
.block-container {{ max-width: 680px; padding-top: 2.2rem; padding-bottom: 5rem; }}
header[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{ display: none; }}

.brand {{ font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em; color: {INK};
  margin-bottom: 1.6rem; }}
.brand span {{ color: {GREEN}; }}

.card {{ background: {SURFACE}; border: 1px solid {LINE}; border-radius: 18px;
  padding: 1.25rem 1.3rem 1rem 1.3rem; margin-bottom: 1rem; }}
.card-head {{ display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.9rem; }}
.avatar {{ width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 1px solid {LINE}; }}
.handle {{ font-size: 1.05rem; font-weight: 600; color: {INK}; }}
.tag {{ display: inline-block; color: {MUTED}; font-size: 0.8rem; font-weight: 500;
  margin-left: 0.5rem; }}
.verified {{ display: inline-block; color: {VERIFIED_BLUE}; font-size: 0.8rem; font-weight: 600;
  margin-left: 0.5rem; }}
.pinned {{ display: inline-block; color: #D9A52B; font-size: 0.8rem; font-weight: 600;
  margin-left: 0.5rem; }}
.likes-badge {{ margin-left: auto; color: {MUTED}; font-size: 0.9rem; font-weight: 500; white-space: nowrap; }}
.media {{ width: 100%; border-radius: 12px; display: block; max-height: 480px; object-fit: cover; }}
.title {{ font-size: 1.25rem; font-weight: 600; letter-spacing: -0.01em; margin: 1rem 0 0.3rem 0; color: {INK}; }}
.desc {{ font-size: 1rem; color: {SOFT}; line-height: 1.6; margin-bottom: 0.8rem; }}
.hashtags {{ color: {MUTED}; font-size: 0.9rem; margin-bottom: 0.4rem; }}
.owner {{ color: {MUTED}; font-size: 0.85rem; margin-bottom: 0.5rem; }}

.lvl {{ display: inline-block; font-size: 0.75rem; font-weight: 600; margin-left: 0.5rem;
  vertical-align: middle; padding: 0.05rem 0.5rem; border-radius: 6px; border: 1px solid {LINE}; }}
.lvl-main {{ color: #FF7A7A; border-color: #4A2424; }}
.lvl-super {{ color: #C9A2FF; border-color: #3A2A4D; }}
.lvl-admin {{ color: #E8C36A; border-color: #4A3D1C; }}
.lvl-verified {{ color: {VERIFIED_BLUE}; border-color: #1E3550; }}
.lvl-owner {{ color: {GREEN}; border-color: #1E3A2A; }}
.lvl-user {{ color: {SOFT}; }}
.lvl-guest {{ color: {MUTED}; }}

.userline {{ font-weight: 600; font-size: 0.98rem; padding: 0.2rem 0 0.4rem 0; color: {INK}; }}
.maint-banner {{ color: #E8C36A; border-left: 2px solid #E8C36A; padding: 0.2rem 0 0.2rem 0.8rem;
  font-size: 0.92rem; margin-bottom: 1rem; }}
.barrier {{ padding: 3.5rem 0.5rem 2.5rem 0.5rem; margin: 1.5rem 0; border-top: 1px solid {LINE}; }}
.barrier h1 {{ font-size: 1.9rem !important; font-weight: 700 !important; letter-spacing: -0.02em;
  color: {INK} !important; margin-bottom: 0.6rem !important; }}
.barrier p {{ font-size: 1.05rem; color: {SOFT}; line-height: 1.6; }}

.announce-cta a {{ border-radius: 10px !important; font-weight: 600 !important; background: {GREEN} !important;
  color: #05130A !important; border: none !important; min-height: 2.5rem; display: flex; align-items: center;
  justify-content: center; text-decoration: none; }}

.stButton button {{ border-radius: 10px !important; font-weight: 500 !important; font-size: 0.95rem !important;
  background: transparent !important; color: {INK} !important; border: 1px solid {LINE} !important;
  min-height: 2.6rem; transition: border-color 0.15s ease, background 0.15s ease; }}
.stButton button:hover {{ border-color: #33413A !important; background: #161E18 !important; }}
.stButton button:disabled {{ color: {MUTED} !important; }}
.stLinkButton a {{ border-radius: 10px !important; font-weight: 600 !important; font-size: 0.95rem !important;
  background: {GREEN} !important; color: #05130A !important; border: none !important; min-height: 2.6rem;
  display: flex; align-items: center; justify-content: center; text-decoration: none; }}

.stTextInput input, .stTextArea textarea {{ background: {SURFACE} !important; color: {INK} !important;
  border-radius: 10px !important; border: 1px solid {LINE} !important; font-size: 0.98rem; }}
.stTextInput input:focus, .stTextArea textarea:focus {{ border-color: #2F4A39 !important; box-shadow: none !important; }}

div[role="radiogroup"] {{ gap: 0.4rem; flex-wrap: wrap; }}
div[role="radiogroup"] label {{ background: transparent; border: 1px solid {LINE}; border-radius: 999px;
  padding: 0.25rem 0.8rem; }}
div[role="radiogroup"] label:has(input:checked) {{ background: #16241B; border-color: #2F4A39; }}
div[role="radiogroup"] label p {{ font-weight: 500; font-size: 0.9rem; color: {SOFT}; }}
div[role="radiogroup"] label:has(input:checked) p {{ color: {INK}; }}

h2, h3 {{ font-weight: 600 !important; letter-spacing: -0.01em; }}
</style>
'''


@st.cache_resource
def get_backend():
    return storage.get_backend()


# ---------- labels ----------

def category_label(value):
    """Translated display label for a stored category or announcement kind."""
    return i18n.label_or(f'cat.{value}', value or '')


def kind_label(value):
    return i18n.label_or(f'kind.{value}', value or '')


# ---------- levels ----------

def level_badge(level):
    css, key = LEVEL_BADGES.get(level, LEVEL_BADGES[auth.LEVEL_GUEST])
    return f"<span class='lvl {css}'>{html.escape(t(key))}</span>"


def member_level(member, owners):
    return auth.level_of(member, owns_channel=member['username'] in owners)


def current_user():
    return st.session_state.user


def current_level():
    user = current_user()
    if not user:
        return auth.LEVEL_GUEST
    return auth.level_of(user, owns_channel=user.get('owns_channel', False))


def is_admin_user():
    return current_level() >= auth.LEVEL_ADMIN


def is_super_user():
    return current_level() >= auth.LEVEL_SUPER_ADMIN


# ---------- session and notices ----------

def init_state():
    st.session_state.setdefault('user', None)
    st.session_state.setdefault('liked_ids', set())
    st.session_state.setdefault('visible', PAGE_STEP)
    st.session_state.setdefault('dismissed', set())


def notify(kind, text):
    st.session_state.notice = (kind, text)


def session_user(backend, fresh):
    """Build the session record from a stored account, including whether it owns a channel."""
    owns = fresh['username'] in {c.get('owner') for c in backend.list_channels() if c.get('owner')}
    return {
        'username': fresh['username'],
        'is_admin': bool(fresh.get('is_admin')),
        'is_super_admin': bool(fresh.get('is_super_admin')),
        'is_verified': bool(fresh.get('is_verified')),
        'owns_channel': owns,
    }


def refresh_user(backend):
    """Re-read the logged-in account so bans, role changes and verification apply immediately."""
    user = current_user()
    if not user:
        return
    fresh = backend.get_user(user['username'])
    if fresh is None or fresh.get('is_banned'):
        st.session_state.user = None
        st.session_state.liked_ids = set()
        notify('error', t('auth.inactive'))
        return
    st.session_state.user = session_user(backend, fresh)


def load_likes(backend):
    user = current_user()
    st.session_state.liked_ids = backend.liked_ids(user['username']) if user else set()


def log_out():
    st.session_state.user = None
    st.session_state.liked_ids = set()
    notify('info', t('auth.logged_out'))


# ---------- accounts ----------

def do_login(backend, username, password):
    user, message = auth.log_in(backend, username, password)
    if user is None:
        st.error(message)
        return False
    fresh = backend.get_user(user['username'])
    st.session_state.user = session_user(backend, fresh or user)
    load_likes(backend)
    return True


def login_form(backend):
    with st.form('login_form', border=False):
        username = st.text_input(t('auth.username'), key='login_username')
        password = st.text_input(t('auth.password'), type='password', key='login_password')
        submitted = st.form_submit_button(t('auth.login_button'))
    if submitted and do_login(backend, username, password):
        st.rerun()


def signup_form(backend):
    with st.form('signup_form', border=False):
        username = st.text_input(t('auth.username'), help=t('auth.username_help'), key='signup_username')
        password = st.text_input(t('auth.password'), type='password', help=t('auth.password_help'),
                                 key='signup_password')
        confirm = st.text_input(t('auth.confirm'), type='password', key='signup_confirm')
        submitted = st.form_submit_button(t('auth.signup_button'))
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
        notify('success', t('auth.created'))
        st.rerun()


def account_bar(backend):
    user = current_user()
    if user is None:
        with st.expander(t('auth.title')):
            login_tab, signup_tab = st.tabs([t('auth.tab_login'), t('auth.tab_signup')])
            with login_tab:
                login_form(backend)
            with signup_tab:
                signup_form(backend)
        return
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(
            f"<div class='userline'>{html.escape(t('auth.logged_in_as', name=user['username']))}"
            f"{level_badge(current_level())}</div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.button(t('auth.logout'), on_click=log_out, use_container_width=True)


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
    notify('success', t('n.channel_removed'))


def set_channel_flag(backend, channel_id, field, value):
    if not is_admin_user():
        return
    backend.update_channel(channel_id, {field: bool(value)})
    label = t('n.label_verification') if field == 'is_verified' else t('n.label_pin')
    notify('success', t('n.channel_flag', label=label))


def image_src(value):
    source = storage.media_source(value)
    return source if isinstance(source, str) else ''


def render_card(backend, channel, role_lookup=None):
    user = current_user()
    can_moderate = is_admin_user()
    handle = html.escape(channel['handle'])
    title = html.escape(channel.get('name') or channel['handle'])
    desc = html.escape(channel.get('caption') or '')
    category = html.escape(category_label(channel.get('category')))
    owner = channel.get('owner')
    owner_roles = (role_lookup or {}).get(owner, []) if owner else []
    role_html = role_ui.badges_html(owner_roles)
    owner_html = f"<div class='owner'>{html.escape(t('card.submitted_by', name=owner))}</div>" if owner else ''
    verified = f"<span class='verified'>{html.escape(t('card.verified'))}</span>" if channel.get('is_verified') else ''
    pinned = f"<span class='pinned'>{html.escape(t('card.pinned'))}</span>" if channel.get('is_pinned') else ''
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
      <span class='handle'>{handle}</span>{verified}{pinned}{role_html}<span class='tag'>{category}</span>
    </div>
    <div class='likes-badge'>{likes}</div>
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
    cols = st.columns([1, 2, 1]) if can_moderate else st.columns([1, 2])
    with cols[0]:
        if user:
            st.button(
                t('card.liked') if liked else t('card.like'),
                key=f'like_{channel_id}',
                on_click=toggle_like,
                args=(backend, channel_id),
                use_container_width=True,
            )
        else:
            st.button(t('card.login_to_like'), key=f'like_{channel_id}', disabled=True, use_container_width=True)
    with cols[1]:
        st.link_button(t('card.join'), channel['link'], use_container_width=True)
    if can_moderate:
        with cols[2]:
            st.button(
                t('card.remove'),
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
        st.info(t('feed.empty'))
        return
    category = PILLS[pill]
    queue = [c for c in storage.ranked(channels) if matches(c, query, category)]
    if not queue:
        st.info(t('feed.no_match'))
        return
    visible = st.session_state.visible
    role_lookup = storage.role_map(backend)
    for channel in queue[:visible]:
        render_card(backend, channel, role_lookup)
    if visible < len(queue):
        if st.button(t('feed.load_more', n=len(queue) - visible), use_container_width=True):
            st.session_state.visible = visible + PAGE_STEP
            st.rerun()
    else:
        st.caption(t('feed.end'))


def submit_view(backend):
    user = current_user()
    if not user:
        st.info(t('submit.login_prompt'))
        return
    st.write(t('submit.intro'))
    with st.form('submit_channel', clear_on_submit=True, border=False):
        handle = st.text_input(t('submit.handle'), placeholder='@yourchannel')
        name = st.text_input(t('submit.name'))
        category = st.selectbox(t('submit.category'), storage.CATEGORIES, format_func=category_label)
        caption = st.text_area(t('submit.caption'), max_chars=storage.MAX_CAPTION)
        image_url = st.text_input(t('submit.image_url'), placeholder='https://...')
        upload = st.file_uploader(
            t('submit.upload'),
            type=['png', 'jpg', 'jpeg', 'webp'],
        )
        avatar_url = st.text_input(t('submit.avatar'))
        link = st.text_input(t('submit.link'), placeholder='https://whatsapp.com/channel/...')
        tags = st.text_input(t('submit.tags'), placeholder='pets, funny')
        submitted = st.form_submit_button(t('submit.button'))

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
        st.error(t('submit.error_save', error=exc))
        return
    st.session_state.user['owns_channel'] = True
    st.success(t('submit.success', handle=data['handle'], id=channel_id))


# ---------- admin actions ----------

def act_role(backend, username, make_admin):
    try:
        auth.set_admin_role(backend, current_user(), username, make_admin)
        notify('success', t('n.now_admin' if make_admin else 'n.now_user', name=username))
    except (ValueError, PermissionError) as exc:
        notify('error', str(exc))


def act_super(backend, username, make_super):
    try:
        auth.set_super_admin(backend, current_user(), username, make_super)
        notify('success', t('n.now_super' if make_super else 'n.now_std_admin', name=username))
    except (ValueError, PermissionError) as exc:
        notify('error', str(exc))


def act_user_verify(backend, username, verified):
    try:
        auth.set_verified(backend, current_user(), username, verified)
        notify('success', t('n.verified' if verified else 'n.unverified', name=username))
    except (ValueError, PermissionError) as exc:
        notify('error', str(exc))


def act_ban(backend, username, banned):
    try:
        auth.set_banned(backend, current_user(), username, banned)
        notify('success', t('n.frozen' if banned else 'n.unfrozen', name=username))
    except (ValueError, PermissionError) as exc:
        notify('error', str(exc))


def act_reset_password(backend, username):
    new_password = st.session_state.get(f'reset_{username}', '')
    try:
        auth.reset_password(backend, current_user(), username, new_password)
        st.session_state[f'reset_{username}'] = ''
        notify('success', t('n.pw_reset', name=username))
    except (ValueError, PermissionError) as exc:
        notify('error', str(exc))


def act_save_maintenance(backend):
    if not is_super_user():
        notify('error', t('n.maint_super_only'))
        return
    storage.set_maintenance(
        backend,
        st.session_state.get('maint_enabled', False),
        st.session_state.get('maint_message', ''),
    )
    state = t('n.on') if st.session_state.get('maint_enabled') else t('n.off')
    notify('success', t('n.maint_saved', state=state))


def act_add_announcement(backend):
    if not is_super_user():
        notify('error', t('n.ann_super_only'))
        return
    message = st.session_state.get('ann_message', '').strip()
    if not message:
        notify('error', t('n.ann_write'))
        return
    amount = int(st.session_state.get('ann_amount', 24))
    hours = amount * (24 if st.session_state.get('ann_unit') == 'Days' else 1)
    try:
        storage.add_announcement(
            backend,
            message,
            st.session_state.get('ann_kind', 'Info'),
            hours,
            link=st.session_state.get('ann_link', ''),
        )
    except ValueError as exc:
        notify('error', str(exc))
        return
    st.session_state['ann_message'] = ''
    st.session_state['ann_link'] = ''
    notify('success', t('n.ann_published'))


def act_set_announcement(backend, announcement_id, active):
    if not is_super_user():
        return
    try:
        storage.update_announcement(backend, announcement_id, active)
        notify('success', t('n.ann_updated'))
    except ValueError as exc:
        notify('error', str(exc))


def act_delete_announcement(backend, announcement_id):
    if not is_super_user():
        return
    storage.delete_announcement(backend, announcement_id)
    notify('success', t('n.ann_deleted'))


# ---------- admin panel ----------

def unit_label(value):
    return t('admin.ann_days') if value == 'Days' else t('admin.ann_hours')


def admin_view(backend):
    user = current_user()
    channels = backend.list_channels()
    users = backend.list_users()
    owners = {c.get('owner') for c in channels if c.get('owner')}
    super_user = is_super_user()

    st.subheader(t('admin.your_role'))
    st.markdown(f"<div class='userline'>@{html.escape(user['username'])}{level_badge(current_level())}</div>",
                unsafe_allow_html=True)
    st.caption(t('admin.permissions', level=t(LEVEL_BADGES[current_level()][1])))

    st.subheader(t('admin.stats'))
    cols = st.columns(4)
    cols[0].metric(t('admin.users'), len(users))
    cols[1].metric(t('admin.admins'), sum(1 for u in users if u['is_admin']))
    cols[2].metric(t('admin.verified_users'), sum(1 for u in users if u['is_verified']))
    cols[3].metric(t('admin.banned_users'), sum(1 for u in users if u['is_banned']))
    cols = st.columns(4)
    cols[0].metric(t('admin.channels'), len(channels))
    cols[1].metric(t('admin.verified_channels'), sum(1 for c in channels if c.get('is_verified')))
    cols[2].metric(t('admin.pinned_channels'), sum(1 for c in channels if c.get('is_pinned')))
    cols[3].metric(t('admin.total_likes'), sum((c.get('likes') or 0) for c in channels))

    if super_user:
        st.subheader(t('admin.maintenance'))
        maint = storage.get_maintenance(backend)
        with st.form('maintenance_form', border=False):
            st.toggle(t('admin.maint_on'), value=maint['enabled'], key='maint_enabled')
            st.text_area(t('admin.maint_message'), value=maint['message'], max_chars=storage.MAX_MAINTENANCE,
                         key='maint_message')
            st.form_submit_button(t('admin.maint_save'), on_click=act_save_maintenance, args=(backend,))
        st.caption(t('admin.maint_note'))

        st.subheader(t('admin.announcements'))
        with st.form('announcement_form', clear_on_submit=False, border=False):
            st.text_input(t('admin.ann_message'), max_chars=storage.MAX_ANNOUNCEMENT, key='ann_message',
                          help=t('admin.ann_message_help'))
            st.text_input(t('admin.ann_link'), max_chars=storage.MAX_LINK, key='ann_link',
                          placeholder='https://whatsapp.com/channel/... or @channelhandle',
                          help=t('admin.ann_link_help'))
            cols = st.columns(3)
            with cols[0]:
                st.selectbox(t('admin.ann_style'), storage.ANNOUNCEMENT_KINDS, key='ann_kind', format_func=kind_label)
            with cols[1]:
                st.number_input(t('admin.ann_lasts'), min_value=1, max_value=365, value=24, key='ann_amount')
            with cols[2]:
                st.selectbox(t('admin.ann_unit'), ['Hours', 'Days'], key='ann_unit', format_func=unit_label)
            st.form_submit_button(t('admin.ann_publish'), on_click=act_add_announcement, args=(backend,))
        announcements = sorted(storage.list_announcements(backend), key=lambda a: a.get('created_at') or '',
                               reverse=True)
        now = storage.datetime.now(storage.timezone.utc)
        if not announcements:
            st.caption(t('admin.ann_none'))
        for item in announcements:
            status = storage.announcement_status(item, now)
            expires = storage.parse_time(item.get('expires_at'))
            when = expires.strftime('%A, %B %d, %Y %H:%M UTC') if expires else 'unknown'
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.markdown(f"**{html.escape(item.get('message', ''))}**")
                link_note = t('admin.ann_link_note', link=html.escape(item['link'])) if item.get('link') else ''
                meta = t('admin.ann_meta', kind=kind_label(item.get('kind')), status=status, when=when)
                st.caption(meta + link_note)
            with cols[1]:
                if item.get('active'):
                    st.button(t('admin.ann_off'), key=f"ann_off_{item['id']}", on_click=act_set_announcement,
                              args=(backend, item['id'], False), use_container_width=True)
                else:
                    st.button(t('admin.ann_on'), key=f"ann_on_{item['id']}", on_click=act_set_announcement,
                              args=(backend, item['id'], True), use_container_width=True)
            with cols[2]:
                st.button(t('admin.ann_delete'), key=f"ann_del_{item['id']}", on_click=act_delete_announcement,
                          args=(backend, item['id']), use_container_width=True)
    else:
        st.caption(t('admin.maint_only'))

    st.subheader(t('admin.channels_heading'))
    if not channels:
        st.info(t('admin.no_channels'))
    for channel in sorted(channels, key=lambda c: c.get('created_at') or '', reverse=True):
        badges = ''
        if channel.get('is_verified'):
            badges += '  ' + t('admin.badge_verified')
        if channel.get('is_pinned'):
            badges += '  ' + t('admin.badge_pinned')
        st.markdown(f"**{html.escape(channel['handle'])}**{html.escape(badges)}")
        owner_text = t('admin.by_owner', owner=channel.get('owner') or 'sample')
        st.caption(f"{channel.get('name') or ''} · {category_label(channel.get('category'))} · "
                   f"{owner_text} · {channel.get('likes') or 0}")
        cols = st.columns(3)
        with cols[0]:
            st.button(
                t('admin.unverify') if channel.get('is_verified') else t('admin.verify'),
                key=f"cv_{channel['id']}",
                on_click=set_channel_flag,
                args=(backend, channel['id'], 'is_verified', not channel.get('is_verified')),
                use_container_width=True,
            )
        with cols[1]:
            st.button(
                t('admin.unpin') if channel.get('is_pinned') else t('admin.pin'),
                key=f"cp_{channel['id']}",
                on_click=set_channel_flag,
                args=(backend, channel['id'], 'is_pinned', not channel.get('is_pinned')),
                use_container_width=True,
            )
        with cols[2]:
            st.button(t('admin.remove'), key=f"admin_remove_{channel['id']}", on_click=remove_channel,
                      args=(backend, channel['id']), use_container_width=True)

    st.subheader(t('admin.channel_stats'))
    ranked_channels = sorted(channels, key=lambda c: c.get('likes') or 0, reverse=True)
    st.dataframe(
        [{t('col.handle'): c['handle'],
          t('col.category'): category_label(c.get('category')),
          t('col.owner'): c.get('owner') or 'sample',
          t('col.likes'): c.get('likes') or 0,
          t('col.verified'): bool(c.get('is_verified')),
          t('col.pinned'): bool(c.get('is_pinned'))} for c in ranked_channels],
        use_container_width=True,
    )

    st.subheader(t('admin.custom_roles'))
    if custom_roles.can_manage_roles(user):
        with st.expander(t('admin.manage_roles')):
            role_ui.manage_roles(backend)
    st.caption(t('admin.roles_note'))
    with st.expander(t('admin.role_directory')):
        role_ui.role_directory(backend)

    st.subheader(t('admin.assign_roles'))
    st.caption(t('admin.assign_note', max=storage.MAX_ROLES_PER_USER))
    role_ui.assignment_section(backend, owners, users)

    role_lookup = storage.role_map(backend)
    st.subheader(t('admin.users'))
    st.caption(t('admin.users_note'))
    for member in users:
        name = member['username']
        level = member_level(member, owners)
        user_roles_html = role_ui.badges_html(role_lookup.get(name, []))
        st.markdown(f"**@{html.escape(name)}**{level_badge(level)}{user_roles_html}", unsafe_allow_html=True)
        st.caption(t('admin.joined', date=str(member.get('created_at') or '')[:10])
                   + (t('admin.banned_note') if member['is_banned'] else ''))
        actions = []
        if auth.can_change_admin_role(user, member):
            if member['is_admin']:
                actions.append((t('admin.demote'), 'role', [backend, name, False]))
            else:
                actions.append((t('admin.make_admin'), 'role', [backend, name, True]))
        if super_user and auth.can_set_super_admin(user, member):
            if member['is_super_admin']:
                actions.append((t('admin.remove_super'), 'super', [backend, name, False]))
            else:
                actions.append((t('admin.make_super'), 'super', [backend, name, True]))
        if auth.can_moderate_user(user, member):
            actions.append((t('admin.unverify_user') if member['is_verified'] else t('admin.verify_user'), 'verify',
                            [backend, name, not member['is_verified']]))
            actions.append((t('admin.unban') if member['is_banned'] else t('admin.ban'), 'ban',
                            [backend, name, not member['is_banned']]))
        if actions:
            cols = st.columns(len(actions))
            for col, (label, kind, args) in zip(cols, actions):
                handler = {'role': act_role, 'super': act_super, 'verify': act_user_verify, 'ban': act_ban}[kind]
                with col:
                    st.button(label, key=f'{kind}_{name}', on_click=handler, args=tuple(args),
                              use_container_width=True)
        if auth.can_reset_password(user, member):
            with st.expander(t('admin.reset_expander', name=name)):
                st.text_input(t('admin.new_password'), type='password', key=f'reset_{name}')
                st.button(t('admin.set_password'), key=f'resetbtn_{name}', on_click=act_reset_password,
                          args=(backend, name))

    st.subheader(t('admin.backup'))
    snapshot = storage.export_snapshot(backend)
    st.download_button(
        t('admin.download_backup'),
        data=json.dumps(snapshot, indent=2, default=str),
        file_name='storiiz-backup.json',
        mime='application/json',
        use_container_width=True,
    )
    st.caption(t('admin.backup_note'))


# ---------- page ----------

def maintenance_barrier(backend, message):
    st.markdown(
        f"<div class='barrier'><h1>{html.escape(t('maint.title'))}</h1><p>{html.escape(message)}</p></div>",
        unsafe_allow_html=True,
    )
    account_bar(backend)


def announcement_banners(backend):
    for item in storage.live_announcements(backend):
        if item['id'] in st.session_state.dismissed:
            continue
        text = html.escape(item.get('message', ''))
        kind = item.get('kind')
        cta = storage.announcement_cta(backend, item)
        cols = st.columns([6, 3, 1]) if cta else st.columns([9, 1])
        with cols[0]:
            if kind == 'Warning':
                st.warning(text)
            elif kind == 'Success':
                st.success(text)
            else:
                st.info(text)
        if cta:
            url, label = cta
            with cols[1]:
                st.markdown("<div class='announce-cta'>", unsafe_allow_html=True)
                st.link_button(label, url, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        with cols[-1]:
            if st.button('✕', key=f"dismiss_{item['id']}", help=t('announce.dismiss')):
                st.session_state.dismissed.add(item['id'])
                st.rerun()


def main():
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    role_ui.inject_css()
    backend = get_backend()
    refresh_user(backend)

    top = st.columns([3, 2])
    with top[0]:
        st.markdown("<div class='brand'>Storiiz<span>.</span></div>", unsafe_allow_html=True)
    with top[1]:
        i18n.language_toggle()

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
        st.markdown(f"<div class='maint-banner'>{html.escape(t('maint.banner'))}</div>", unsafe_allow_html=True)
    announcement_banners(backend)

    names = [t('tab.feed'), t('tab.submit')] + ([t('tab.admin')] if is_admin_user() else [])
    tabs = st.tabs(names)
    with tabs[0]:
        query = st.text_input(t('search.label'), placeholder=t('search.placeholder'), label_visibility='collapsed')
        pill = st.radio(t('category.label'), list(PILLS.keys()), horizontal=True, label_visibility='collapsed',
                        format_func=t)
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


main()
