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
  is_verified boolean not null default false,
  is_banned boolean not null default false,
  created_at timestamptz default now()
);

-- Older setups had an email column. Accounts no longer use email.
alter table users drop column if exists email;
alter table users add column if not exists is_admin boolean not null default false;
alter table users add column if not exists is_verified boolean not null default false;
alter table users add column if not exists is_banned boolean not null default false;

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

-- The app talks to these tables with the key in secrets. Keep that key private.
-- The admin account (storiizadmin) is created by the app on first start if it is missing.
