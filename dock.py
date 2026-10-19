"""Bottom dock for Storiiz: a fixed, translucent tab bar with four icon buttons (video, photo, post, settings)."""

import streamlit as st

GREEN = '#25D366'
INK = '#EDF1EE'
LINE = '#1E2820'

# (view key, icon, tooltip)
DOCK_ITEMS = [
    ('video', '🎬', 'Vidéo'),
    ('photo', '📷', 'Photo'),
    ('post', '➕', 'Poster'),
    ('settings', '⚙️', 'Paramètres'),
]

DOCK_CSS = f'''
<style>
/* Bottom dock: a fixed translucent tab bar. Streamlit button chrome is removed with !important. */
div[data-testid="stHorizontalBlock"]:has(.dock-marker) {{ position: fixed !important; bottom: 0 !important; left: 0 !important; right: 0 !important; top: auto !important;
  width: 100% !important; max-width: 680px !important; margin: 0 auto !important; z-index: 99999 !important;
  background: rgba(18,18,18,0.85) !important; backdrop-filter: blur(16px) !important; -webkit-backdrop-filter: blur(16px) !important;
  border-top: 1px solid rgba(255,255,255,0.1) !important; border-radius: 0 !important;
  padding: 0.35rem 0.5rem calc(0.35rem + env(safe-area-inset-bottom)) 0.5rem !important; gap: 0 !important;
  flex-wrap: nowrap !important; align-items: center !important; }}
div[data-testid="stHorizontalBlock"]:has(.dock-marker) > div[data-testid="stColumn"] {{ min-width: 0 !important; flex: 1 1 0 !important;
  width: auto !important; display: flex !important; justify-content: center !important; }}
div[data-testid="stHorizontalBlock"]:has(.dock-marker) .stButton {{ width: 100% !important; display: flex !important; justify-content: center !important; }}
div[data-testid="stHorizontalBlock"]:has(.dock-marker) .stButton button {{ background: transparent !important; border: none !important;
  box-shadow: none !important; outline: none !important; min-height: 3rem !important; width: 100% !important;
  font-size: 1.35rem !important; line-height: 1 !important; padding: 0 !important; border-radius: 12px !important;
  color: {INK} !important; transition: transform 0.12s ease, background 0.15s ease !important; }}
div[data-testid="stHorizontalBlock"]:has(.dock-marker) .stButton button:hover {{ background: rgba(255,255,255,0.06) !important; }}
div[data-testid="stHorizontalBlock"]:has(.dock-marker) .stButton button:active {{ transform: scale(0.92) !important; }}
div[data-testid="stHorizontalBlock"]:has(.dock-marker) .stButton button[kind="primary"] {{ background: rgba(37,211,102,0.16) !important; color: {GREEN} !important; }}
div[data-testid="stHorizontalBlock"]:has(.dock-marker) .stButton button p {{ font-size: 1.35rem !important; margin: 0 !important; }}
.dock-marker {{ display: none; }}
</style>
'''


def inject_css():
    st.markdown(DOCK_CSS, unsafe_allow_html=True)


def active_view():
    return st.session_state.get('view', 'video')


def set_view(name):
    st.session_state.view = name


def render(on_select=set_view):
    """Render the four dock buttons. The active item is shown as a tinted primary button."""
    current = active_view()
    cols = st.columns(len(DOCK_ITEMS))
    for col, (name, icon, label) in zip(cols, DOCK_ITEMS):
        with col:
            if name == 'video':
                st.markdown("<span class='dock-marker'></span>", unsafe_allow_html=True)
            st.button(
                icon,
                key=f'nav_{name}',
                help=label,
                on_click=on_select,
                args=(name,),
                type='primary' if current == name else 'secondary',
                use_container_width=True,
            )
