-- Run this once in the Supabase SQL editor.
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

-- The app is the only client, so it should use the service_role key kept in secrets.
-- If you use the anon key instead, enable row level security and add matching policies.
