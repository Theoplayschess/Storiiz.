"""Permission-checked custom role actions for Storiiz.

The data rules (validation, storage, the 250-role cap) live in storage.py. This module decides who may
call them. Custom roles are cosmetic badges: they never change a user's level or permissions.

Who can do what:
  Super Admin and Main Admin Account: create, edit and delete custom roles.
  Admin and above: assign or remove custom roles, but only for accounts strictly below their own level.
  Nobody: change their own roles, or the Main Admin Account's roles.
"""

import auth
import storage


def can_manage_roles(actor):
    return auth.is_super_admin(actor)


def _require_manage(actor):
    if not can_manage_roles(actor):
        raise PermissionError('Only Super Admins and the Main Admin Account can create, edit or delete custom roles.')


def create_role(backend, actor, data):
    _require_manage(actor)
    return storage.create_role(backend, actor['username'], data)


def update_role(backend, actor, role_id, data):
    _require_manage(actor)
    storage.update_role(backend, role_id, data)


def delete_role(backend, actor, role_id):
    _require_manage(actor)
    storage.delete_role(backend, role_id)


def assign_block_reason(actor, target, target_owns):
    """None if the actor may change the target's custom roles, otherwise the reason why not."""
    if target is None:
        return 'That user does not exist.'
    if not auth.is_admin(actor):
        return 'Only Admins and above can assign custom roles.'
    if auth.same_user(actor, target):
        return 'You cannot change your own custom roles.'
    if auth.is_main_admin(target):
        return 'The Main Admin Account cannot be changed.'
    actor_level = auth.level_of(actor, owns_channel=actor.get('owns_channel', False))
    target_level = auth.level_of(target, owns_channel=target_owns)
    if actor_level <= target_level:
        return 'You can only change custom roles for accounts below your own level.'
    return None


def can_assign(actor, target, target_owns):
    return assign_block_reason(actor, target, target_owns) is None


def set_user_roles(backend, actor, username, role_ids):
    """Replace the user's custom roles with role_ids. Raises PermissionError or ValueError."""
    name = auth.normalize_username(username)
    target = backend.get_user(name)
    owners = {c.get('owner') for c in backend.list_channels() if c.get('owner')}
    reason = assign_block_reason(actor, target, name in owners)
    if reason:
        raise PermissionError(reason)
    storage.set_user_roles(backend, name, role_ids, actor['username'])
