# Storiiz

Storiiz is a Streamlit card feed for discovering WhatsApp Channels. Cards look like Stories or TikTok posts, with a handle, avatar, image, and caption.

## Features
- Card feed with avatar, image, and caption per channel
- Like system; likes raise a channel's engagement score
- Feed ranked by engagement (base engagement plus likes), with a Next button to move through cards
- Join WhatsApp Channel button linking to each channel

## Project files
- app.py: Streamlit app
- channels.json: sample channel data (replace with real channels)
- requirements.txt: Python dependencies

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Adding channels
Edit channels.json. Each entry needs: id, handle, name, category, avatar, image, caption, link, base_engagement.

The sample links and images are placeholders. Replace the link values with real WhatsApp Channel invite links and use your own images.

## Hosting
This repo does not include any deployment configuration. Hosting is up to you; Streamlit Community Cloud can deploy app.py directly from this repo if you choose.
