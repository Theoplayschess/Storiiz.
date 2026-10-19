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

-- Owner of a submitted channel (the username that submitted it).
alter table channels add column if not exists owner text;

-- User accounts. Passwords are stored only as PBKDF2 hashes, never in plain text.
create table if not exists users (
  username text primary key,
  email text,
  password_hash text not null,
  created_at timestamptz default now()
);

-- One row per user per liked channel. The primary key stops double likes.
create table if not exists channel_likes (
  username text not null,
  channel_id text not null,
  created_at timestamptz default now(),
  primary key (username, channel_id)
);

-- The app talks to these tables with the key in secrets. Keep that key private.
-- If you use the anon key instead, enable row level security and add matching policies.
