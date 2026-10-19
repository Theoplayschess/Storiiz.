import html

import streamlit as st

import storage

st.set_page_config(page_title='Storiiz', page_icon='💬', layout='centered')

PAGE_STEP = 8
GREEN = '#25D366'
DARK_BG = '#0B0F0C'
CARD_BG = '#141A16'

# Pill label -> category filter. 'All' and 'Trending' show everything (Trending is ranked).
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
.likes-badge {{ margin-left: auto; background: #1E2B23; border-radius: 999px; padding: 0.3rem 0.8rem;
  font-weight: 700; font-size: 1rem; white-space: nowrap; }}
.media {{ width: 100%; border-radius: 16px; display: block; max-height: 520px; object-fit: cover; }}
.title {{ font-size: 1.5rem; font-weight: 800; margin: 0.9rem 0 0.25rem 0; }}
.desc {{ font-size: 1.1rem; color: #B9C6BE; line-height: 1.5; margin-bottom: 0.9rem; }}
.hashtags {{ color: {GREEN}; font-weight: 600; margin-bottom: 0.9rem; }}
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


def init_state():
    st.session_state.setdefault('liked_ids', set())
    st.session_state.setdefault('visible', PAGE_STEP)


def toggle_like(backend, channel_id):
    if channel_id in st.session_state.liked_ids:
        st.session_state.liked_ids.discard(channel_id)
        backend.add_like(channel_id, -1)
    else:
        st.session_state.liked_ids.add(channel_id)
        backend.add_like(channel_id, 1)


def image_src(value):
    source = storage.media_source(value)
    if isinstance(source, bytes):
        return None
    return source


def render_card(backend, channel):
    handle = html.escape(channel['handle'])
    title = html.escape(channel.get('name') or channel['handle'])
    desc = html.escape(channel.get('caption') or '')
    category = html.escape(channel.get('category') or '')
    avatar = image_src(channel.get('avatar') or channel.get('image')) or ''
    media = image_src(channel.get('image')) or ''
    likes = channel.get('likes') or 0
    tags = storage.parse_tags(channel.get('tags'))
    tags_html = f"<div class='hashtags'>{' '.join('#' + html.escape(t) for t in tags)}</div>" if tags else ''

    st.markdown(f"""
<div class='card'>
  <div class='card-head'>
    <img class='avatar' src='{html.escape(avatar)}' alt=''/>
    <div>
      <span class='handle'>{handle}</span><span class='tag'>{category}</span>
    </div>
    <div class='likes-badge'>❤ {likes}</div>
  </div>
  <img class='media' src='{html.escape(media)}' alt='{title}'/>
  <div class='title'>{title}</div>
  <div class='desc'>{desc}</div>
  {tags_html}
</div>
""", unsafe_allow_html=True)

    liked = channel['id'] in st.session_state.liked_ids
    cols = st.columns([1, 2])
    with cols[0]:
        st.button(
            ('❤️ Liked' if liked else '🤍 Like'),
            key=f"like_{channel['id']}",
            on_click=toggle_like,
            args=(backend, channel['id']),
            use_container_width=True,
        )
    with cols[1]:
        st.link_button('Join WhatsApp Channel  →', channel['link'], use_container_width=True)
    st.write('')


def matches(channel, query, category):
    if category and channel.get('category') != category:
        return False
    if not query:
        return True
    q = query.lower()
    haystack = ' '.join([
        channel.get('handle') or '', channel.get('name') or '',
        channel.get('caption') or '', channel.get('tags') or '',
    ]).lower()
    return q in haystack


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


def main():
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    backend = get_backend()
    st.sidebar.caption(f'Storage: {backend.name}')
    if backend.note:
        st.sidebar.warning(backend.note)

    st.markdown("<div class='brand'>STORIIZ<span>.</span></div>", unsafe_allow_html=True)
    feed_tab, submit_tab = st.tabs(['Feed', 'Submit a channel'])
    with feed_tab:
        query = st.text_input('Search', placeholder='Search channels...', label_visibility='collapsed')
        pill = st.radio('Category', list(PILLS.keys()), horizontal=True, label_visibility='collapsed')
        if query != st.session_state.get('last_query') or pill != st.session_state.get('last_pill'):
            st.session_state.visible = PAGE_STEP
            st.session_state.last_query = query
            st.session_state.last_pill = pill
        feed_view(backend, query.strip(), pill)
    with submit_tab:
        submit_view(backend)


main()
