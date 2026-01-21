# Discord Hello Bot

A simple Discord bot that responds with "Hello" when users type `!hello`.

## Setup Instructions

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" tab and click "Add Bot"
4. Under "Privileged Gateway Intents", enable "MESSAGE CONTENT INTENT"
5. Click "Reset Token" to get your bot token (save this securely!)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Bot Token

Create a `.env` file in the project root:

```
DISCORD_BOT_TOKEN=your_actual_bot_token_here
AI_KEY=your_gemini_api_key_here
TWITCH_CLIENT_ID=your_twitch_client_id_here
TWITCH_CLIENT_SECRET=your_twitch_client_secret_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

**Get your API keys:**
- Gemini API key: [Google AI Studio](https://aistudio.google.com/app/apikey)
- Twitch API credentials: [Twitch Developer Console](https://dev.twitch.tv/console/apps)
- YouTube API key: [Google Cloud Console](https://console.cloud.google.com/) → Enable YouTube Data API v3 → Create credentials

Or set it as an environment variable:

**Windows (PowerShell):**
```powershell
$env:DISCORD_BOT_TOKEN="your_actual_bot_token_here"
```

**Windows (CMD):**
```cmd
set DISCORD_BOT_TOKEN=your_actual_bot_token_here
```

**Linux/Mac:**
```bash
export DISCORD_BOT_TOKEN=your_actual_bot_token_here
```

### 4. Invite Bot to Your Server

1. In the Discord Developer Portal, go to "OAuth2" > "URL Generator"
2. Select scopes: `bot`
3. Select bot permissions: `Send Messages`, `Read Messages/View Channels`, `Manage Messages` (for deleting video links)
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

### 5. Create Required Channels

Make sure your Discord server has these channels:
- `#iron-mouse` - For Twitch/YouTube notifications
- `#videos` - For Instagram/TikTok link forwarding (optional)

### 6. Run the Bot

```bash
python bot.py
```

## Usage

Once the bot is running and in your server, you can use these commands:

### !hello
```
!hello
```
The bot will respond with a greeting!

### !ai
```
!ai What is the meaning of life?
!ai Explain quantum physics simply
!ai Write a haiku about coding
```
The bot will use Google's Gemini AI to respond to your message!

### !grigger
Reply to any message and use this command to fact-check or comment on it:
```
[Reply to a message]
!grigger fact check this
!grigger explain what this means
!grigger is this accurate?
!grigger analyze this claim
```
The bot will use AI to analyze the replied message and send a formatted embed with the analysis!

### !sendreply
Make the bot reply to any message by its ID:
```
!sendreply 1463108816001564806 This is my custom reply!
!sendreply 1463108816001564806 wah wah wah >:3
```
The bot will reply to the specified message. You can get a message ID by right-clicking a message and selecting "Copy Message ID" (requires Developer Mode enabled in Discord settings).

### !testtwitch (Testing Command)
Test if Twitch API is working and see the stream embed:
```
!testtwitch
```
Shows current stream status or confirms API is working if offline.

### !testyoutube (Testing Command)
Test if YouTube API is working and see the latest video embed:
```
!testyoutube
```
Shows the latest video/stream from Ironmouse's channel.

## Features

- **!hello** - Responds with a friendly greeting
- **!ai** - Chat with Google's Gemini AI
- **!grigger** - Fact-check or analyze any message by replying to it
- **!sendreply** - Make the bot reply to any message by ID (useful for remote control)
- **Random quirky AI responses** - Bot acts as Ironmouse with anime roleplay text (0.5% chance, max 10/hour - low to avoid API quota)
- **Twitch stream notifications** - Automatically notifies when Ironmouse goes live (checks every 2 minutes)
- **YouTube notifications** - Automatically posts when Ironmouse uploads a video or goes live (checks every 5 minutes)
- **Auto video forwarding** - Detects Instagram/TikTok links, converts them with 'kk' prefix, and forwards to #videos channel
- Beautiful Discord embeds for fact-checking, stream notifications, and video uploads
- Rate limiting to prevent spam
- Mentions the user who sent the command
- Handles long AI responses by splitting them into multiple messages
- Simple and easy to extend

## Requirements

- Python 3.8+
- discord.py 2.3.2+

