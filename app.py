import streamlit as st

import storage

st.set_page_config(page_title='Storiiz', page_icon='💬', layout='centered')

PAGE_STEP = 8

CSS = '''
<style>
.block-container { max-width: 760px; padding-top: 1.5rem; padding-bottom: 4rem; }
h1 { font-size: 2.6rem !important; }
.feed-card { border-radius: 20px !important; padding: 1.2rem !important;
  box-shadow: 0 6px 24px rgba(0,0,0,0.12); margin-bottom: 1.8rem; min-height: 80vh; }
.feed-card img { border-radius: 16px; }
.feed-handle { font-size: 1.5rem; font-weight: 700; }
.feed-caption { font-size: 1.35rem; line-height: 1.5; margin: 0.8rem 0; }
.feed-tags { font-size: 1.05rem; color: #128C7E; font-weight: 600; }
.stButton button, .stLinkButton a { font-size: 1.15rem !important; padding: 0.7rem 1rem !important;
  border-radius: 14px !important; min-height: 3.2rem; }
.stLinkButton a { width: 100%; text-align: center; }
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


def show_image(value, width=None):
    source = storage.media_source(value)
    if source is None:
        return
    if width:
        st.image(source, width=width)
    else:
        st.image(source, use_container_width=True)


def render_card(backend, channel):
    with st.container(border=True):
        header = st.columns([1, 5])
        with header[0]:
            show_image(channel.get('avatar') or channel.get('image'), width=72)
        with header[1]:
            st.markdown(f"<div class='feed-handle'>{channel['handle']}</div>", unsafe_allow_html=True)
            st.caption(f"{channel.get('name') or ''} · {channel.get('category') or ''}")
        show_image(channel.get('image'))
        if channel.get('caption'):
            st.markdown(f"<div class='feed-caption'>{channel['caption']}</div>", unsafe_allow_html=True)
        tags = storage.parse_tags(channel.get('tags'))
        if tags:
            st.markdown(
                f"<div class='feed-tags'>{' '.join('#' + t for t in tags)}</div>",
                unsafe_allow_html=True,
            )

        likes = channel.get('likes') or 0
        liked = channel['id'] in st.session_state.liked_ids
        heart = '❤️' if liked else '🤍'
        cols = st.columns([1, 2])
        with cols[0]:
            st.button(
                f'{heart} {likes}',
                key=f"like_{channel['id']}",
                on_click=toggle_like,
                args=(backend, channel['id']),
                use_container_width=True,
            )
        with cols[1]:
            st.link_button('Join WhatsApp Channel', channel['link'], type='primary', use_container_width=True)


def feed_view(backend):
    channels = backend.list_channels()
    if not channels:
        st.info('No channels yet. Be the first to submit one in the Submit tab.')
        return
    queue = storage.ranked(channels)
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

    st.title('Storiiz')
    st.caption('Discover WhatsApp Channels. Scroll to explore.')
    feed_tab, submit_tab = st.tabs(['Feed', 'Submit a channel'])
    with feed_tab:
        feed_view(backend)
    with submit_tab:
        submit_view(backend)


main()
