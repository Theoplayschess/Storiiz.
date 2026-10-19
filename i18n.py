"""Translations for Storiiz. English is the default. French is chosen with the header toggle.

Each key maps to an (English, French) pair. Add a key here, then call t(key) in the UI.
Stored data (category values, announcement kinds) stays in English. Only the labels are translated.
"""

import streamlit as st

DEFAULT_LANG = 'en'
LANGUAGES = {'en': '🇬🇧 EN', 'fr': '🇫🇷 FR'}

STRINGS = {
    'lang.label': ('Language', 'Langue'),

    # navigation and search
    'tab.feed': ('Feed', 'Fil'),
    'tab.submit': ('Submit a channel', 'Ajouter un canal'),
    'tab.admin': ('Admin Panel', 'Panneau admin'),
    'search.label': ('Search', 'Recherche'),
    'search.placeholder': ('Search channels...', 'Rechercher des canaux...'),
    'category.label': ('Category', 'Catégorie'),
    'pill.trending': ('🔥 Trending', '🔥 Tendances'),
    'pill.fitness': ('💪 Fitness', '💪 Fitness'),
    'pill.news': ('📰 News', '📰 Actualités'),
    'pill.gaming': ('🎮 Gaming', '🎮 Jeux vidéo'),
    'pill.cooking': ('🍳 Cooking', '🍳 Cuisine'),
    'pill.pets': ('🐶 Pets', '🐶 Animaux'),
    'pill.tech': ('💻 Tech', '💻 Tech'),

    # stored category values
    'cat.Fitness': ('Fitness', 'Fitness'),
    'cat.News': ('News', 'Actualités'),
    'cat.Entertainment': ('Entertainment', 'Divertissement'),
    'cat.Food': ('Food', 'Cuisine'),
    'cat.Animals': ('Animals', 'Animaux'),
    'cat.Tech': ('Tech', 'Tech'),

    # channel cards
    'card.join': ('Join WhatsApp Channel  →', 'Rejoindre le canal WhatsApp  →'),
    'card.like': ('🤍 Like', "🤍 J'aime"),
    'card.liked': ('❤️ Liked', "❤️ Aimé"),
    'card.login_to_like': ('🤍 Log in to like', '🤍 Connectez-vous pour aimer'),
    'card.remove': ('🗑 Remove', '🗑 Retirer'),
    'card.submitted_by': ('Submitted by @{name}', 'Ajouté par @{name}'),
    'card.verified': ('✓ Verified', '✓ Vérifié'),
    'card.pinned': ('📌 Pinned', '📌 Épinglé'),
    'card.followers': ('{n} likes', "{n} j'aime"),

    # feed
    'feed.empty': ('No channels yet. Be the first to submit one in the Submit tab.',
                   "Aucun canal pour le moment. Soyez le premier à en ajouter un dans l'onglet Ajouter un canal."),
    'feed.no_match': ('No channels match your search or filter.',
                      'Aucun canal ne correspond à votre recherche ou à votre filtre.'),
    'feed.load_more': ('Load more ({n} left)', 'Charger plus ({n} restants)'),
    'feed.end': ('You have reached the end of the feed.', 'Vous êtes arrivé à la fin du fil.'),

    # submission form
    'submit.login_prompt': ('Log in or create an account above to submit a channel.',
                            'Connectez-vous ou créez un compte ci-dessus pour ajouter un canal.'),
    'submit.intro': ('Share your WhatsApp Channel with the Storiiz community. New channels appear in the feed right away.',
                     'Partagez votre canal WhatsApp avec la communauté Storiiz. Les nouveaux canaux apparaissent tout de suite dans le fil.'),
    'submit.handle': ('Handle', 'Identifiant'),
    'submit.name': ('Channel name', 'Nom du canal'),
    'submit.category': ('Category', 'Catégorie'),
    'submit.caption': ('Caption', 'Description'),
    'submit.image_url': ('Image URL', "URL de l'image"),
    'submit.upload': ('Or upload an image (PNG, JPEG, WebP, max 2 MB)',
                      "Ou importez une image (PNG, JPEG, WebP, 2 Mo maximum)"),
    'submit.avatar': ('Avatar URL (optional, defaults to the image)',
                      "URL de l'avatar (facultatif, par défaut l'image)"),
    'submit.link': ('WhatsApp Channel link', 'Lien du canal WhatsApp'),
    'submit.tags': ('Tags (comma separated)', 'Mots-clés (séparés par des virgules)'),
    'submit.button': ('Submit channel', 'Ajouter le canal'),
    'submit.error_save': ('Could not save your channel: {error}', "Impossible d'enregistrer votre canal : {error}"),
    'submit.success': ('Thanks! {handle} is now live in the feed (id: {id}).',
                       'Merci ! {handle} est maintenant visible dans le fil (id : {id}).'),

    # accounts and auth modals
    'auth.title': ('Log in or create an account', 'Se connecter ou créer un compte'),
    'auth.tab_login': ('Log in', 'Se connecter'),
    'auth.tab_signup': ('Create account', 'Créer un compte'),
    'auth.username': ('Username', "Nom d'utilisateur"),
    'auth.username_help': ('3 to 30 characters: letters, numbers or underscores.',
                           '3 à 30 caractères : lettres, chiffres ou tirets bas.'),
    'auth.password': ('Password', 'Mot de passe'),
    'auth.password_help': ('At least 8 characters.', 'Au moins 8 caractères.'),
    'auth.confirm': ('Confirm password', 'Confirmer le mot de passe'),
    'auth.login_button': ('Log in', 'Se connecter'),
    'auth.signup_button': ('Create account', 'Créer le compte'),
    'auth.logged_in_as': ('Logged in as @{name}', 'Connecté en tant que @{name}'),
    'auth.logout': ('Log out', 'Se déconnecter'),
    'auth.created': ('Account created. Welcome to Storiiz!', 'Compte créé. Bienvenue sur Storiiz !'),
    'auth.logged_out': ('You have logged out.', 'Vous êtes déconnecté.'),
    'auth.inactive': ('Your account is no longer active. You have been logged out.',
                      "Votre compte n'est plus actif. Vous avez été déconnecté."),

    # announcements and maintenance
    'announce.dismiss': ('Dismiss', 'Fermer'),
    'maint.banner': ('⚠ Maintenance mode is ON. Regular visitors see a maintenance screen. Admins can still use the full site.',
                     '⚠ Le mode maintenance est ACTIVÉ. Les visiteurs voient un écran de maintenance. Les admins peuvent toujours utiliser le site.'),
    'maint.title': ("We'll be right back", 'Nous revenons très vite'),

    # levels
    'lvl.main': ('Main Admin', 'Admin principal'),
    'lvl.super': ('Super Admin', 'Super Admin'),
    'lvl.admin': ('Admin', 'Admin'),
    'lvl.verified': ('Verified', 'Vérifié'),
    'lvl.owner': ('Channel Owner', 'Propriétaire de canal'),
    'lvl.user': ('Logged In', 'Connecté'),
    'lvl.guest': ('Unregistered', 'Non inscrit'),

    # admin panel
    'admin.your_role': ('Your role', 'Votre rôle'),
    'admin.permissions': ('{level} permissions apply to this account.',
                          'Les permissions {level} s\'appliquent à ce compte.'),
    'admin.stats': ('Stats', 'Statistiques'),
    'admin.users': ('Users', 'Utilisateurs'),
    'admin.admins': ('Admins', 'Admins'),
    'admin.verified_users': ('Verified users', 'Utilisateurs vérifiés'),
    'admin.banned_users': ('Banned users', 'Utilisateurs bannis'),
    'admin.channels': ('Channels', 'Canaux'),
    'admin.verified_channels': ('Verified channels', 'Canaux vérifiés'),
    'admin.pinned_channels': ('Pinned channels', 'Canaux épinglés'),
    'admin.total_likes': ('Total likes', "Total des j'aime"),
    'admin.maintenance': ('Maintenance mode', 'Mode maintenance'),
    'admin.maint_on': ('Maintenance mode is on', 'Mode maintenance activé'),
    'admin.maint_message': ('Message shown to visitors', 'Message affiché aux visiteurs'),
    'admin.maint_save': ('Save maintenance settings', 'Enregistrer le mode maintenance'),
    'admin.maint_note': ('Admins are not blocked. Regular visitors see the maintenance screen while this is on.',
                         "Les admins ne sont pas bloqués. Les visiteurs voient l'écran de maintenance tant que le mode est activé."),
    'admin.announcements': ('Announcements', 'Annonces'),
    'admin.ann_message': ('Message', 'Message'),
    'admin.ann_message_help': ('Any http or https link pasted here becomes the button link if the field below is empty.',
                               'Tout lien http ou https collé ici devient le lien du bouton si le champ ci-dessous est vide.'),
    'admin.ann_link': ('Button link (optional)', 'Lien du bouton (facultatif)'),
    'admin.ann_link_help': ('A WhatsApp channel URL, another https link, or a Storiiz @handle.',
                            'Un lien de canal WhatsApp, un autre lien https ou un identifiant Storiiz @.'),
    'admin.ann_style': ('Style', 'Style'),
    'admin.ann_lasts': ('Lasts for', 'Durée'),
    'admin.ann_unit': ('Unit', 'Unité'),
    'admin.ann_hours': ('Hours', 'Heures'),
    'admin.ann_days': ('Days', 'Jours'),
    'admin.ann_publish': ('Publish announcement', "Publier l'annonce"),
    'admin.ann_none': ('No announcements yet.', 'Aucune annonce pour le moment.'),
    'admin.ann_meta': ('{kind} | {status} | expires {when}', '{kind} | {status} | expire le {when}'),
    'admin.ann_link_note': (' | link: {link}', ' | lien : {link}'),
    'admin.ann_on': ('Turn on', 'Activer'),
    'admin.ann_off': ('Turn off', 'Désactiver'),
    'admin.ann_delete': ('Delete', 'Supprimer'),
    'admin.maint_only': ('Maintenance mode and announcements are managed by Super Admins and the Main Admin Account.',
                         'Le mode maintenance et les annonces sont gérés par les Super Admins et le compte principal.'),
    'admin.no_channels': ('No channels.', 'Aucun canal.'),
    'admin.channels_heading': ('Channels', 'Canaux'),
    'admin.badge_verified': ('✓ verified', '✓ vérifié'),
    'admin.badge_pinned': ('📌 pinned', '📌 épinglé'),
    'admin.by_owner': ('by @{owner}', 'par @{owner}'),
    'admin.verify': ('Verify', 'Vérifier'),
    'admin.unverify': ('Unverify', 'Retirer la vérification'),
    'admin.pin': ('Pin to top', 'Épingler'),
    'admin.unpin': ('Unpin', 'Désépingler'),
    'admin.remove': ('Remove', 'Retirer'),
    'admin.channel_stats': ('Channel stats', 'Statistiques des canaux'),
    'col.handle': ('handle', 'identifiant'),
    'col.category': ('category', 'catégorie'),
    'col.owner': ('owner', 'propriétaire'),
    'col.likes': ('likes', "j'aime"),
    'col.verified': ('verified', 'vérifié'),
    'col.pinned': ('pinned', 'épinglé'),
    'admin.users_note': ('You can only change accounts below your own level. The Main Admin Account cannot be changed.',
                         'Vous ne pouvez modifier que les comptes sous votre niveau. Le compte principal ne peut pas être modifié.'),
    'admin.joined': ('Joined {date}', 'Inscrit le {date}'),
    'admin.banned_note': (' | banned', ' | banni'),
    'admin.make_admin': ('Make admin', 'Nommer admin'),
    'admin.demote': ('Demote to user', 'Rétrograder en utilisateur'),
    'admin.make_super': ('Make Super Admin', 'Nommer Super Admin'),
    'admin.remove_super': ('Remove Super Admin', 'Retirer Super Admin'),
    'admin.verify_user': ('Verify', 'Vérifier'),
    'admin.unverify_user': ('Unverify', 'Retirer la vérification'),
    'admin.ban': ('Ban', 'Bannir'),
    'admin.unban': ('Unban', 'Débannir'),
    'admin.reset_expander': ('Reset password for @{name}', 'Réinitialiser le mot de passe de @{name}'),
    'admin.new_password': ('New password', 'Nouveau mot de passe'),
    'admin.set_password': ('Set new password', 'Définir le nouveau mot de passe'),
    'admin.custom_roles': ('Custom roles', 'Rôles personnalisés'),
    'admin.manage_roles': ('Manage roles (create, edit, delete)', 'Gérer les rôles (créer, modifier, supprimer)'),
    'admin.role_directory': ('Roles and their members', 'Rôles et leurs membres'),
    'admin.assign_roles': ('Assign custom roles', 'Attribuer des rôles personnalisés'),
    'admin.assign_note': ('Up to {max} roles per user. You can only change accounts below your own level.',
                          'Jusqu à {max} rôles par utilisateur. Vous ne pouvez modifier que les comptes sous votre niveau.'),
    'admin.roles_note': ("Roles are badges and perks only. They never change a user's level.",
                         "Les rôles sont uniquement des badges et des avantages. Ils ne modifient jamais le niveau d'un utilisateur."),
    'admin.backup': ('Backup', 'Sauvegarde'),
    'admin.download_backup': ('Download backup (JSON)', 'Télécharger la sauvegarde (JSON)'),
    'admin.backup_note': ('The backup includes channels, users (no password hashes), roles, maintenance and announcements.',
                          'La sauvegarde comprend les canaux, les utilisateurs (sans mots de passe), les rôles, le mode maintenance et les annonces.'),

    # announcement kinds
    'kind.Info': ('Info', 'Info'),
    'kind.Success': ('Success', 'Succès'),
    'kind.Warning': ('Warning', 'Avertissement'),

    # notices shown after an action
    'n.channel_removed': ('Channel removed from the feed.', 'Canal retiré du fil.'),
    'n.label_verification': ('verification', 'vérification'),
    'n.label_pin': ('pin', 'épinglage'),
    'n.channel_flag': ('Channel {label} updated.', 'Canal mis à jour ({label}).'),
    'n.now_admin': ('@{name} is now an admin.', '@{name} est maintenant admin.'),
    'n.now_user': ('@{name} is now a regular user.', '@{name} est maintenant utilisateur standard.'),
    'n.now_super': ('@{name} is now a Super Admin.', '@{name} est maintenant Super Admin.'),
    'n.now_std_admin': ('@{name} is now a standard Admin.', '@{name} est maintenant admin standard.'),
    'n.verified': ('@{name} verified.', '@{name} vérifié.'),
    'n.unverified': ('@{name} unverified.', "@{name} n'est plus vérifié."),
    'n.frozen': ('@{name} frozen (banned).', '@{name} suspendu (banni).'),
    'n.unfrozen': ('@{name} unfrozen.', '@{name} réactivé.'),
    'n.pw_reset': ('Password reset for @{name}.', 'Mot de passe réinitialisé pour @{name}.'),
    'n.on': ('ON', 'ACTIVÉ'),
    'n.off': ('OFF', 'DÉSACTIVÉ'),
    'n.maint_saved': ('Maintenance mode saved. It is now {state}.', 'Mode maintenance enregistré. Il est maintenant {state}.'),
    'n.maint_super_only': ('Only Super Admins and the Main Admin Account can change maintenance mode.',
                           'Seuls les Super Admins et le compte principal peuvent modifier le mode maintenance.'),
    'n.ann_super_only': ('Only Super Admins and the Main Admin Account can publish announcements.',
                         'Seuls les Super Admins et le compte principal peuvent publier des annonces.'),
    'n.ann_write': ('Write a message for the announcement.', "Écrivez un message pour l'annonce."),
    'n.ann_published': ('Announcement published.', 'Annonce publiée.'),
    'n.ann_updated': ('Announcement updated.', 'Annonce mise à jour.'),
    'n.ann_deleted': ('Announcement deleted.', 'Annonce supprimée.'),
}


def current_lang():
    lang = st.session_state.get('lang', DEFAULT_LANG)
    return lang if lang in LANGUAGES else DEFAULT_LANG


def t(key, **values):
    """Translate a key into the current language. Falls back to English, then to the key itself."""
    pair = STRINGS.get(key)
    if pair is None:
        return key
    text = pair[1] if current_lang() == 'fr' else pair[0]
    return text.format(**values) if values else text


def label_or(key, raw):
    """Translate a stored value when a key exists for it, otherwise show the raw value."""
    return t(key) if key in STRINGS else raw


def language_toggle():
    """One-click EN / FR switch. The choice is kept in session_state under 'lang'."""
    st.radio(
        t('lang.label'),
        list(LANGUAGES),
        format_func=lambda code: LANGUAGES[code],
        horizontal=True,
        key='lang',
        label_visibility='collapsed',
    )
