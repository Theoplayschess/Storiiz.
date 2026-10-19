-- Run this once in the Supabase SQL editor. Safe to re-run.
create table if not exists channels (
  id text primary key,
  handle text not null,
  name text,
  category text,
  avatar text,
  image text,
  caption text,
  link text not null,
  tags text default '',
  base_engagement integer default 0,
  likes integer default 0,
  created_at timestamptz default now()
);

-- Username of the account that submitted the channel.
alter table channels add column if not exists owner text;
-- Verified badge (blue check) and pinned-to-top flag, set by admins.
alter table channels add column if not exists is_verified boolean not null default false;
alter table channels add column if not exists is_pinned boolean not null default false;

-- Accounts use only a username and a password. Passwords are stored only as PBKDF2 hashes.
create table if not exists users (
  username text primary key,
  password_hash text not null,
  is_admin boolean not null default false,
  is_super_admin boolean not null default false,
  is_verified boolean not null default false,
  is_banned boolean not null default false,
  created_at timestamptz default now()
);

-- Older setups had an email column. Accounts no longer use email.
alter table users drop column if exists email;
alter table users add column if not exists is_admin boolean not null default false;
alter table users add column if not exists is_super_admin boolean not null default false;
alter table users add column if not exists is_verified boolean not null default false;
alter table users add column if not exists is_banned boolean not null default false;

-- Role levels (highest wins): storiizadmin = Main Admin Account (6), is_super_admin = Super Admin (5),
-- is_admin = Admin (4), is_verified = Verified (3), owns a channel = Channel Owner (2), any account = Logged In (1).
-- Only the storiizadmin account can set or remove is_super_admin. Admins cannot change Super Admins.

-- One row per user per liked channel. The primary key stops double likes.
create table if not exists channel_likes (
  username text not null,
  channel_id text not null,
  created_at timestamptz default now(),
  primary key (username, channel_id)
);

-- Key/value settings: maintenance mode and announcements are stored here as JSON.
create table if not exists settings (
  key text primary key,
  value text
);

-- Custom roles: coloured badges with an icon. Super Admins and the Main Admin Account create and edit them.
-- Roles are cosmetic and do not change permissions. icon holds an emoji, an https image link, or a data URL
-- (PNG, JPEG, WebP, SVG or ICO, at most 256 KB).
create table if not exists custom_roles (
  id text primary key,
  name text not null,
  color text not null check (color ~ '^#[0-9a-fA-F]{6}$'),
  icon text not null default '',
  description text not null default '',
  priority integer not null default 0,
  created_at timestamptz default now(),
  created_by text
);
create unique index if not exists custom_roles_name_lower on custom_roles (lower(name));

-- Role assignments. A user can hold several roles, at most 250 (enforced by the trigger below).
create table if not exists user_roles (
  username text not null references users(username) on delete cascade,
  role_id text not null references custom_roles(id) on delete cascade,
  assigned_at timestamptz default now(),
  assigned_by text,
  primary key (username, role_id)
);
create index if not exists user_roles_role_id on user_roles (role_id);

create or replace function enforce_user_role_cap() returns trigger language plpgsql as $$
begin
  if (select count(*) from user_roles where username = new.username) >= 250 then
    raise exception 'A user can hold at most 250 custom roles';
  end if;
  return new;
end;
$$;

drop trigger if exists user_roles_cap on user_roles;
create trigger user_roles_cap before insert on user_roles
  for each row execute function enforce_user_role_cap();

-- Posts published by channel owners (text, image or video) shown with their channel.
-- content_type is one of 'text', 'image', 'video'. likes_count is kept in step with post_likes.
create table if not exists channel_posts (
  id text primary key,
  channel_id text not null references channels(id) on delete cascade,
  author_id text not null,
  content_type text not null default 'text' check (content_type in ('text', 'image', 'video')),
  content text not null default '',
  media_url text not null default '',
  created_at timestamptz default now(),
  likes_count integer not null default 0
);
create index if not exists channel_posts_channel_id on channel_posts (channel_id, created_at desc);

-- The app talks to these tables with the key in secrets. Keep that key private.
-- The admin account (storiizadmin) is created by the app on first start if it is missing.
