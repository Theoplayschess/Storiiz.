"""Custom role UI for Storiiz: badges, the role manager, assignments and the role directory.

Custom roles are cosmetic. Permission rules come from custom_roles.py and auth.py.
"""

import html

import streamlit as st

import custom_roles
import storage

ROLE_CSS = '''
<style>
.role-badge { display: inline-flex; align-items: center; gap: 0.3rem; border: 1px solid; border-radius: 999px;
  padding: 0.1rem 0.6rem; font-size: 0.8rem; font-weight: 800; margin-left: 0.35rem; vertical-align: middle; }
.role-icon { width: 14px; height: 14px; object-fit: contain; vertical-align: middle; }
.role-emoji { line-height: 1; }
</style>
'''

ROLE_ICON_TYPES = ['png', 'jpg', 'jpeg', 'webp', 'svg', 'ico']


def inject_css():
    st.markdown(ROLE_CSS, unsafe_allow_html=True)


# ---------- rendering ----------

def icon_html(icon):
    if not icon:
        return ''
    if icon.startswith(('http://', 'https://', 'data:image/')):
        return f"<img class='role-icon' src='{html.escape(icon, quote=True)}' alt=''/>"
    return f"<span class='role-emoji'>{html.escape(icon)}</span>"


def badge_html(role):
    """Icon, name and a pill in the role's colour. The colour is a validated #RRGGBB value."""
    color = role['color']
    return (f"<span class='role-badge' style='color:{color};border-color:{color};"
            f"background:{color}22;'>{icon_html(role.get('icon'))}{html.escape(role['name'])}</span>")


def badges_html(roles):
    return ''.join(badge_html(role) for role in roles)


# ---------- handlers (run as button callbacks) ----------

def _notify(kind, text):
    st.session_state.notice = (kind, text)


def _actor():
    return st.session_state.user


def _role_data(prefix, fallback_icon=''):
    upload = st.session_state.get(f'{prefix}_upload')
    if upload is not None:
        icon = storage.encode_role_icon(upload)
    else:
        icon = (st.session_state.get(f'{prefix}_icon') or '').strip() or fallback_icon
    return {
        'name': st.session_state.get(f'{prefix}_name', ''),
        'color': st.session_state.get(f'{prefix}_color', '#7C3AED'),
        'icon': icon,
        'description': st.session_state.get(f'{prefix}_description', ''),
        'priority': st.session_state.get(f'{prefix}_priority', 0),
    }


def _create_role(backend):
    try:
        custom_roles.create_role(backend, _actor(), _role_data('role_new'))
    except (ValueError, PermissionError) as exc:
        _notify('error', str(exc))
        return
    for key in ('role_new_name', 'role_new_icon', 'role_new_description'):
        st.session_state[key] = ''
    st.session_state['role_new_priority'] = 0
    _notify('success', 'Custom role created.')


def _save_role(backend, role_id, fallback_icon):
    try:
        custom_roles.update_role(backend, _actor(), role_id, _role_data(f'role_edit_{role_id}', fallback_icon))
        _notify('success', 'Custom role saved.')
    except (ValueError, PermissionError) as exc:
        _notify('error', str(exc))


def _delete_role(backend, role_id):
    try:
        custom_roles.delete_role(backend, _actor(), role_id)
        _notify('success', 'Custom role deleted and removed from every user.')
    except (ValueError, PermissionError) as exc:
        _notify('error', str(exc))


def _save_assignment(backend, username):
    picked = st.session_state.get(f'assign_roles_{username}', [])
    try:
        custom_roles.set_user_roles(backend, _actor(), username, list(picked))
        _notify('success', f'Custom roles saved for @{username} ({len(picked)} total).')
    except (ValueError, PermissionError) as exc:
        _notify('error', str(exc))


# ---------- role manager (Super Admin and Main Admin Account) ----------

def _role_fields(prefix, role=None):
    extra = {}
    if role is not None:
        extra = {'value': role['name']}
    st.text_input('Name', max_chars=storage.MAX_ROLE_NAME, key=f'{prefix}_name', **extra)
    color_extra = {'value': role['color']} if role is not None else {}
    st.color_picker('Colour', key=f'{prefix}_color', **color_extra)
    icon_extra = {}
    if role is None:
        icon_extra = {}
    st.text_input('Icon: an emoji or an https image link', key=f'{prefix}_icon',
                  help='Leave empty to use the uploaded icon, or to keep the current icon when editing.', **icon_extra)
    st.file_uploader('Or upload an icon (PNG, JPG, WebP, SVG or ICO, max 256 KB)', type=ROLE_ICON_TYPES,
                     key=f'{prefix}_upload')
    desc_extra = {'value': role['description']} if role is not None else {}
    st.text_input('Description (optional)', max_chars=storage.MAX_ROLE_DESCRIPTION, key=f'{prefix}_description',
                  **desc_extra)
    prio_extra = {'value': role['priority']} if role is not None else {'value': 0}
    st.number_input('Priority (higher appears first)', min_value=-storage.ROLE_PRIORITY_LIMIT,
                    max_value=storage.ROLE_PRIORITY_LIMIT, step=1, key=f'{prefix}_priority', **prio_extra)


def manage_roles(backend):
    """Create, edit and delete custom roles. Callers must check custom_roles.can_manage_roles first."""
    roles = storage.list_roles(backend)
    members_by_role = {}
    for username, rid in backend.all_user_roles():
        members_by_role.setdefault(rid, []).append(username)

    st.markdown('**Create a role**')
    _role_fields('role_new')
    st.button('Create role', key='create_role_btn', on_click=_create_role, args=(backend,))

    st.markdown('**Existing roles**')
    if not roles:
        st.caption('No custom roles yet.')
    for role in roles:
        count = len(members_by_role.get(role['id'], []))
        with st.expander(f"{role['name']}  |  {count} member(s)"):
            st.markdown(badge_html(role), unsafe_allow_html=True)
            _role_fields(f"role_edit_{role['id']}", role)
            st.caption('Leave the icon empty to keep the current icon. Deleting a role removes it from all users.')
            cols = st.columns(2)
            with cols[0]:
                st.button('Save role', key=f"save_role_{role['id']}", on_click=_save_role,
                          args=(backend, role['id'], role['icon']), use_container_width=True)
            with cols[1]:
                st.button('Delete role', key=f"del_role_{role['id']}", on_click=_delete_role,
                          args=(backend, role['id']), use_container_width=True)


# ---------- assignments (Admin and above) ----------

def assignment_section(backend, owners, users):
    actor = _actor()
    roles = storage.list_roles(backend)
    if not roles:
        st.caption('Create a custom role first, then assign it here.')
        return
    options = [m for m in users if custom_roles.can_assign(actor, m, m['username'] in owners)]
    if not options:
        st.caption('You have no accounts below your level to assign roles to.')
        return
    names = [m['username'] for m in options]
    labels = {r['id']: r['name'] for r in roles}
    pick = st.selectbox('User', names, key='assign_user')
    current = [r['id'] for r in storage.roles_for_user(backend, pick)]
    st.multiselect(
        f'Custom roles (up to {storage.MAX_ROLES_PER_USER})',
        options=[r['id'] for r in roles],
        default=current,
        format_func=lambda rid: labels.get(rid, rid),
        max_selections=storage.MAX_ROLES_PER_USER,
        key=f'assign_roles_{pick}',
    )
    st.button('Save roles for this user', key=f'save_assign_{pick}', on_click=_save_assignment,
              args=(backend, pick), use_container_width=True)


# ---------- role directory (Admin and above) ----------

def role_directory(backend):
    roles = storage.list_roles(backend)
    if not roles:
        st.info('No custom roles yet.')
        return
    members_by_role = {}
    for username, rid in backend.all_user_roles():
        members_by_role.setdefault(rid, []).append(username)

    st.dataframe(
        [{'role': r['name'], 'members': len(members_by_role.get(r['id'], [])), 'priority': r['priority'],
          'colour': r['color'], 'description': r['description']} for r in roles],
        use_container_width=True,
    )

    labels = {r['id']: r['name'] for r in roles}
    chosen = st.selectbox('Inspect a role', [r['id'] for r in roles],
                          format_func=lambda rid: labels.get(rid, rid), key='role_inspect')
    role = next(r for r in roles if r['id'] == chosen)
    st.markdown(badge_html(role), unsafe_allow_html=True)
    if role['description']:
        st.caption(role['description'])
    st.caption(f"Priority {role['priority']} | Created {str(role.get('created_at') or '')[:10]} "
               f"by @{role.get('created_by') or 'unknown'}")
    members = sorted(members_by_role.get(chosen, []))
    st.markdown(f"**{len(members)} user(s) hold this role**")
    if members:
        st.dataframe([{'username': name} for name in members], use_container_width=True)
    else:
        st.caption('No users have this role yet.')
