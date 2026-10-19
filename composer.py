"""Post composer for the Poster (➕) tab. Channel owners and level 2+ users can publish text, image or video updates."""

import streamlit as st

import channel_posts

LEVEL_OWNER_MIN = 2  # level 2 and up may post (owners of a channel always may)


def can_post(user, owned_channels, level):
    """True when the user owns a channel or is at level 2 or above."""
    return bool(user) and (bool(owned_channels) or level >= LEVEL_OWNER_MIN)


def render(backend, user, owned_channels, level):
    if not can_post(user, owned_channels, level):
        return
    with st.expander('Publier une mise à jour'):
        if not owned_channels:
            st.caption('Ajoutez d’abord une chaîne pour publier des mises à jour.')
            return
        handles = {c['id']: c['handle'] for c in owned_channels}
        with st.form('channel_post_form', clear_on_submit=False, border=False):
            target = st.selectbox('Chaîne', list(handles), format_func=lambda cid: handles[cid])
            kind = st.selectbox('Type', list(channel_posts.CONTENT_TYPES),
                                format_func=lambda v: {'text': 'Texte', 'image': 'Photo', 'video': 'Vidéo'}[v])
            content = st.text_area('Message', max_chars=channel_posts.MAX_POST_CAPTION)
            media_url = st.text_input('Lien image ou vidéo (https://)', placeholder='https://...')
            submitted = st.form_submit_button('Publier')
        if not submitted:
            return
        try:
            channel_posts.create_channel_post(backend, target, user['username'], kind, content, media_url)
        except ValueError as exc:
            st.error(str(exc))
            return
        except Exception as exc:
            st.error(f'Impossible de publier : {exc}')
            return
        st.success('Votre publication est en ligne.')
