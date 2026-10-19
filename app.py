import streamlit as st

import storage

st.set_page_config(page_title='Storiiz', page_icon='💬', layout='centered')


@st.cache_resource
def get_backend():
    return storage.get_backend()


def init_state():
    st.session_state.setdefault('liked_ids', set())
    st.session_state.setdefault('seen_ids', [])


def toggle_like(backend, channel_id):
    if channel_id in st.session_state.liked_ids:
        st.session_state.liked_ids.discard(channel_id)
        backend.add_like(channel_id, -1)
    else:
        st.session_state.liked_ids.add(channel_id)
        backend.add_like(channel_id, 1)


def next_card(queue):
    seen = st.session_state.seen_ids
    for channel in queue:
        if channel['id'] not in seen:
            return channel
    # Every card has been seen: start a new round.
    st.session_state.seen_ids = []
    return queue[0] if queue else None


def mark_seen(channel_id):
    if channel_id not in st.session_state.seen_ids:
        st.session_state.seen_ids.append(channel_id)


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
        header = st.columns([1, 6])
        with header[0]:
            show_image(channel.get('avatar') or channel.get('image'), width=56)
        with header[1]:
            st.markdown(f"**{channel['handle']}**")
            st.caption(f"{channel.get('name') or ''} · {channel.get('category') or ''}")
        show_image(channel.get('image'))
        if channel.get('caption'):
            st.write(channel['caption'])
        tags = storage.parse_tags(channel.get('tags'))
        if tags:
            st.caption(' '.join(f'#{t}' for t in tags))

        likes = channel.get('likes') or 0
        liked = channel['id'] in st.session_state.liked_ids
        heart = '❤️' if liked else '🤍'
        cols = st.columns(3)
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
        with cols[2]:
            if st.button('Next →', key=f"next_{channel['id']}", use_container_width=True):
                mark_seen(channel['id'])
                st.rerun()


def feed_view(backend):
    channels = backend.list_channels()
    if not channels:
        st.info('No channels yet. Be the first to submit one in the Submit tab.')
        return
    queue = storage.ranked(channels)
    card = next_card(queue)
    if card is None:
        return
    render_card(backend, card)

    remaining = sum(1 for c in channels if c['id'] not in st.session_state.seen_ids)
    st.caption(f'{remaining} card(s) left in this round, ranked by engagement and freshness.')

    liked = [c for c in channels if c['id'] in st.session_state.liked_ids]
    if liked:
        with st.expander('Channels you liked'):
            for c in liked:
                st.markdown(f"- {c['handle']} ([Join]({c['link']}))")


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
    backend = get_backend()
    st.sidebar.caption(f'Storage: {backend.name}')
    if backend.note:
        st.sidebar.warning(backend.note)

    st.title('Storiiz')
    st.caption('Discover WhatsApp Channels, one card at a time.')
    feed_tab, submit_tab = st.tabs(['Feed', 'Submit a channel'])
    with feed_tab:
        feed_view(backend)
    with submit_tab:
        submit_view(backend)


main()
