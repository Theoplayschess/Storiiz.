import json
from pathlib import Path

import streamlit as st

DATA_PATH = Path(__file__).parent / "channels.json"

st.set_page_config(page_title="Storiiz", page_icon="\U0001F4AC", layout="centered")


def load_channels():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)["channels"]


def engagement_score(channel, likes):
    # Ranking: base engagement from the channel data plus live likes (likes weigh more).
    return channel.get("base_engagement", 0) + 3 * likes.get(channel["id"], 0)


def init_state():
    st.session_state.setdefault("likes", {})
    st.session_state.setdefault("liked_ids", set())
    st.session_state.setdefault("seen_ids", [])


def ranked_queue(channels):
    likes = st.session_state.likes
    return sorted(channels, key=lambda c: engagement_score(c, likes), reverse=True)


def toggle_like(channel_id):
    likes = st.session_state.likes
    if channel_id in st.session_state.liked_ids:
        st.session_state.liked_ids.discard(channel_id)
        likes[channel_id] = max(0, likes.get(channel_id, 0) - 1)
    else:
        st.session_state.liked_ids.add(channel_id)
        likes[channel_id] = likes.get(channel_id, 0) + 1


def next_card(queue):
    seen = st.session_state.seen_ids
    for c in queue:
        if c["id"] not in seen:
            return c
    # Everything seen: start a new pass.
    st.session_state.seen_ids = []
    return queue[0] if queue else None


def mark_seen(channel_id):
    if channel_id not in st.session_state.seen_ids:
        st.session_state.seen_ids.append(channel_id)


def render_card(channel):
    with st.container(border=True):
        header_cols = st.columns([1, 6])
        with header_cols[0]:
            st.image(channel["avatar"], width=56)
        with header_cols[1]:
            st.markdown(f"**{channel['handle']}**")
            st.caption(f"{channel['name']} \u00b7 {channel.get('category', '')}")
        st.image(channel["image"], use_container_width=True)
        st.write(channel["caption"])

        likes_count = st.session_state.likes.get(channel["id"], 0)
        liked = channel["id"] in st.session_state.liked_ids
        heart = "\u2764\ufe0f" if liked else "\U0001F90D"
        cols = st.columns(3)
        with cols[0]:
            st.button(
                f"{heart} {likes_count}",
                key=f"like_{channel['id']}",
                on_click=toggle_like,
                args=(channel["id"],),
                use_container_width=True,
            )
        with cols[1]:
            st.link_button(
                "Join WhatsApp Channel",
                channel["link"],
                type="primary",
                use_container_width=True,
            )
        with cols[2]:
            if st.button("Next \u2192", key=f"next_{channel['id']}", use_container_width=True):
                mark_seen(channel["id"])
                st.rerun()


def main():
    init_state()
    st.title("Storiiz")
    st.caption("Discover WhatsApp Channels, one card at a time.")

    channels = load_channels()
    queue = ranked_queue(channels)

    card = next_card(queue)
    if card is None:
        st.info("No channels available yet. Add entries to channels.json.")
        return

    render_card(card)

    remaining = len([c for c in channels if c["id"] not in st.session_state.seen_ids])
    st.caption(f"{remaining} card(s) left in this round, ranked by engagement.")

    if st.session_state.liked_ids:
        with st.expander("Channels you liked"):
            for c in channels:
                if c["id"] in st.session_state.liked_ids:
                    st.markdown(f"- {c['handle']} ([Join]({c['link']}))")


main()
