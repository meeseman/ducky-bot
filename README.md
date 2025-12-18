# Discord Video Link Bot

A simple Discord bot that automatically detects Instagram and TikTok links and forwards them to a dedicated "videos" channel.

## Features

- 🔍 Automatically detects any links containing "instagram" or "tiktok" in messages
- 📺 Forwards links to a channel named "videos"
- 👤 Shows who posted the link and from which channel
- 🔗 Converts links by adding "kk" prefix (e.g., `instagram.com` → `kkinstagram.com`)
- 📝 Sends plain text links (no embeds) for easy copying
- 🗑️ Automatically deletes the original message after forwarding

## Setup Instructions

### 1. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Under "Privileged Gateway Intents", enable:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT (optional)
5. Copy your bot token (you'll need this later)

### 2. Invite the Bot to Your Server

1. In the Developer Portal, go to "OAuth2" → "URL Generator"
2. Select scopes:
   - `bot`
3. Select bot permissions:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Read Message History
   - Manage Messages (to delete the original messages)
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Bot

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```
   (On Linux/Mac, use `cp .env.example .env`)

2. Edit `.env` and paste your bot token:
   ```
   DISCORD_TOKEN=your_actual_bot_token_here
   ```

### 5. Create a "videos" Channel

Make sure your Discord server has a text channel named exactly **"videos"** (lowercase). The bot will forward all detected links to this channel.

### 6. Run the Bot

```bash
python bot.py
```

You should see a message like:
```
YourBotName#1234 has connected to Discord!
Bot is in 1 guild(s)
```

## Usage

Simply send any message containing an Instagram or TikTok link in any channel, and the bot will automatically copy it to the #videos channel and delete the original message!

The bot will send **two messages** to #videos:
1. First message: An embed showing who sent the link and from which channel
2. Second message: The **converted link** with "kk" added (see examples below)

The original message will be **automatically deleted** from the source channel.

### Link Conversion Examples

The bot automatically adds "kk" before "instagram" or "tiktok" in the URLs:

- `https://www.instagram.com/reel/xyz/` → `https://www.kkinstagram.com/reel/xyz/`
- `https://instagram.com/p/abc/` → `https://kkinstagram.com/p/abc/`
- `https://www.tiktok.com/@user/video/123` → `https://www.kktiktok.com/@user/video/123`
- `https://vm.tiktok.com/xyz/` → `https://vm.kktiktok.com/xyz/`

This is useful for download services that use the "kk" prefix!

**Supported links:**
- Any link containing "instagram" in the URL (e.g., `https://www.instagram.com/...`, `https://ddinstagram.com/...`)
- Any link containing "tiktok" in the URL (e.g., `https://www.tiktok.com/...`, `https://vm.tiktok.com/...`, `https://vxtiktok.com/...`)

## Troubleshooting

### Bot doesn't respond to messages
- Make sure you enabled "MESSAGE CONTENT INTENT" in the Discord Developer Portal
- Verify the bot has permission to read messages in your channels

### "videos" channel not found warning
- Create a text channel named "videos" (all lowercase)
- Make sure the bot has permission to view and send messages in that channel

### Bot won't start
- Check that your `.env` file exists and contains a valid token
- Make sure you installed all dependencies with `pip install -r requirements.txt`

### Bot doesn't delete original messages
- Make sure the bot has "Manage Messages" permission in your server
- The bot needs this permission in all channels where you want it to delete messages

## License

Free to use and modify!

