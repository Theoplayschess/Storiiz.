# Storiiz

Storiiz is a Streamlit card feed for discovering WhatsApp Channels. Cards look like Stories or TikTok posts, with a handle, avatar, image, caption and tags. Creators can submit their own channel from inside the app, and new channels show up in the feed right away.

## Features
- Card feed with handle, avatar, image, caption and tags for each channel
- Like system: likes feed into the ranking
- Ranking by engagement (base score plus 3 points per like) with a fresh-channel boost that decays over 48 hours, so new submissions compete immediately
- Next button to move through cards; a new round starts after the last card
- Join WhatsApp Channel button on every card
- Submission form: handle, channel name, category, caption, image URL or upload, optional avatar URL, WhatsApp Channel link and tags
- Storage: Supabase when configured, otherwise a local SQLite database that needs no setup

## Project files
- app.py: Streamlit UI (feed and submission form)
- storage.py: storage backends (Supabase and SQLite), validation, ranking
- channels.json: sample channels, loaded into an empty local database on first run
- supabase_schema.sql: table definition for Supabase
- .streamlit/secrets.toml.example: template for Supabase secrets
- requirements.txt: Python dependencies
- .gitignore: keeps local data and secrets out of git

## Run locally (no database setup needed)
```
pip install -r requirements.txt
streamlit run app.py
```
Without Supabase settings, the app creates data/storiiz.db and seeds it from channels.json. The sidebar shows which storage is active.

## Set up Supabase (recommended for persistent storage)
1. Create a project at https://supabase.com.
2. Open the SQL editor and run the contents of supabase_schema.sql. This creates the channels table.
3. In Project Settings > API, copy the Project URL and the service_role key.
4. Add the secrets, using one of these options:
   - Local file: copy .streamlit/secrets.toml.example to .streamlit/secrets.toml and fill in SUPABASE_URL and SUPABASE_KEY.
   - Environment variables: export SUPABASE_URL and SUPABASE_KEY before running streamlit.
   - Streamlit Community Cloud: open the app settings, go to Secrets, and paste the same two lines.
5. Restart the app. The sidebar should show Storage: Supabase.

Keep the service_role key private. It must only live in secrets, never in the code. If you use the anon key instead, enable row level security on the channels table and add policies that allow select, insert and update.

If Supabase is configured but cannot be reached, the app falls back to the local SQLite database and shows a warning in the sidebar. It does not crash.

## Submitting a channel
Open the Submit a channel tab and fill in the form. Required fields are the handle (starting with @), a caption (up to 280 characters), an image (URL or upload of up to 2 MB) and a link that starts with https://whatsapp.com/channel/. The new channel is added to the feed immediately.

Uploaded images are stored inside the database as data URLs. This is simple and works everywhere, but a file-storage service is a better choice if you expect many large images.

## Adding channels manually
With SQLite, you can edit channels.json before the first run, or insert rows into the database. With Supabase, insert rows into the channels table in the Table Editor. Each channel needs: id, handle, name, category, avatar, image, caption, link, tags (comma separated text), base_engagement and likes.

## Hosting notes
- The sample links and images are placeholders. Replace the link values with real WhatsApp Channel invite links.
- On Streamlit Community Cloud, the local file system is reset when the app redeploys or restarts. Use Supabase there so submissions are kept.
- This repo does not include any deployment configuration. Hosting is up to you.
