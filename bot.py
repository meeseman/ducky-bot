import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from google import genai
import random
from datetime import datetime, timedelta
import aiohttp
import asyncio
import re

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini AI client
AI_KEY = os.getenv('AI_KEY')
if AI_KEY:
    genai_client = genai.Client(api_key=AI_KEY)
else:
    genai_client = None
    print("Warning: AI_KEY not found. !ai command will not work.")

# Rate limiting: Track when AI messages were sent
ai_message_timestamps = []
MAX_MESSAGES_PER_HOUR = 10

# Video link forwarding
LINK_PATTERN = r'https?://[^\s]+'

def convert_link(link):
    """Convert instagram/tiktok links to add 'kk' prefix, removing any existing prefixes"""
    # Pattern matches optional 2-letter prefix (like vx, dd, kk, etc.) before instagram/tiktok
    # Replace with just 'kk' prefix to ensure there's only one prefix
    converted = re.sub(r'([a-z]{2})?(instagram)', r'kk\2', link, flags=re.IGNORECASE)
    converted = re.sub(r'([a-z]{2})?(tiktok)', r'kk\2', converted, flags=re.IGNORECASE)
    return converted

# Twitch stream monitoring
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
IRONMOUSE_CHANNEL = "ironmouse"
NOTIFICATION_CHANNEL_NAME = "iron-mouse"
twitch_access_token = None
is_currently_live = False  # Track if we've already notified about current stream

# YouTube monitoring
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
IRONMOUSE_YOUTUBE_CHANNEL_ID = "UCIeSUTOTkF9Hs7q3SGcO-Ow"  # @IronMouseParty
last_video_id = None  # Track the last video we've seen


# Create bot instance with command prefix
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
bot = commands.Bot(command_prefix='!', intents=intents)

async def get_twitch_token():
    """Get OAuth token from Twitch API"""
    global twitch_access_token
    if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
        return None
    
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    twitch_access_token = data['access_token']
                    return twitch_access_token
    except Exception as e:
        print(f"Error getting Twitch token: {e}")
    return None

async def check_ironmouse_live():
    """Check if Ironmouse is currently live on Twitch"""
    global twitch_access_token
    
    if not twitch_access_token:
        twitch_access_token = await get_twitch_token()
    
    if not twitch_access_token:
        return None
    
    url = f"https://api.twitch.tv/helix/streams?user_login={IRONMOUSE_CHANNEL}"
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {twitch_access_token}'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 401:  # Token expired
                    twitch_access_token = await get_twitch_token()
                    return await check_ironmouse_live()
                
                if response.status == 200:
                    data = await response.json()
                    if data['data']:
                        # Stream is live
                        stream_data = data['data'][0]
                        return {
                            'title': stream_data['title'],
                            'game': stream_data['game_name'],
                            'viewers': stream_data['viewer_count'],
                            'thumbnail': stream_data['thumbnail_url'].replace('{width}', '1920').replace('{height}', '1080')
                        }
    except Exception as e:
        print(f"Error checking Twitch stream: {e}")
    
    return None

@tasks.loop(minutes=2)  # Check every 2 minutes
async def monitor_ironmouse_stream():
    """Background task to monitor Ironmouse's stream"""
    global is_currently_live
    
    stream_data = await check_ironmouse_live()
    
    if stream_data and not is_currently_live:
        # Stream just went live!
        is_currently_live = True
        
        # Find the notification channel in all guilds
        for guild in bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=NOTIFICATION_CHANNEL_NAME)
            if channel:
                embed = discord.Embed(
                    title="🔴 IRONMOUSE IS LIVE! 🎤",
                    description=f"**{stream_data['title']}**",
                    color=discord.Color.red(),
                    url=f"https://www.twitch.tv/{IRONMOUSE_CHANNEL}",
                    timestamp=datetime.now()
                )
                
                embed.add_field(name="🎮 Playing", value=stream_data['game'], inline=True)
                embed.add_field(name="👁️ Viewers", value=f"{stream_data['viewers']:,}", inline=True)
                embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/0c3d1b0f-8bec-4fb8-9c56-3850817b8c81-profile_image-300x300.png")
                embed.set_image(url=stream_data['thumbnail'])
                
                await channel.send("WAH WAH WAAAAH!! *screams excitedly* I'M LIVE ON TWITCH RIGHT NOW >:3 come hang out with me uwu!! *bounces* ≽^•⩊•^≼", embed=embed)
                print(f"[TWITCH] Ironmouse went live! Notified #{channel.name}")
    
    elif not stream_data and is_currently_live:
        # Stream ended
        is_currently_live = False
        print(f"[TWITCH] Ironmouse stream ended")

@monitor_ironmouse_stream.before_loop
async def before_monitor():
    await bot.wait_until_ready()

async def get_latest_youtube_video():
    """Get Ironmouse's latest YouTube upload"""
    if not YOUTUBE_API_KEY:
        return None
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'channelId': IRONMOUSE_YOUTUBE_CHANNEL_ID,
        'maxResults': 1,
        'order': 'date',
        'type': 'video',
        'key': YOUTUBE_API_KEY
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('items'):
                        video = data['items'][0]
                        video_id = video['id']['videoId']
                        
                        # Get video details for view count and stats
                        details_url = "https://www.googleapis.com/youtube/v3/videos"
                        details_params = {
                            'part': 'statistics,snippet,liveStreamingDetails',
                            'id': video_id,
                            'key': YOUTUBE_API_KEY
                        }
                        
                        async with session.get(details_url, params=details_params) as details_response:
                            if details_response.status == 200:
                                details_data = await details_response.json()
                                if details_data.get('items'):
                                    video_details = details_data['items'][0]
                                    return {
                                        'video_id': video_id,
                                        'title': video['snippet']['title'],
                                        'description': video['snippet']['description'],
                                        'thumbnail': video['snippet']['thumbnails']['high']['url'],
                                        'published_at': video['snippet']['publishedAt'],
                                        'views': video_details['statistics'].get('viewCount', '0'),
                                        'likes': video_details['statistics'].get('likeCount', '0'),
                                        'is_live': 'liveStreamingDetails' in video_details
                                    }
    except Exception as e:
        print(f"Error checking YouTube: {e}")
    
    return None

@tasks.loop(minutes=3)  # Check every 3 minutes
async def monitor_ironmouse_youtube():
    """Background task to monitor Ironmouse's YouTube uploads"""
    global last_video_id
    
    print(f"[YOUTUBE] Checking for new videos...")
    video_data = await get_latest_youtube_video()
    
    if video_data:
        print(f"[YOUTUBE] Found video: {video_data['title'][:50]}... (ID: {video_data['video_id']})")
        video_id = video_data['video_id']
        
        # If this is a new video (and not our first run)
        if last_video_id and video_id != last_video_id:
            # New video detected!
            for guild in bot.guilds:
                channel = discord.utils.get(guild.text_channels, name=NOTIFICATION_CHANNEL_NAME)
                if channel:
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    published_at = datetime.strptime(video_data['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                    
                    # Different embed based on if it's live or uploaded
                    if video_data['is_live']:
                        embed = discord.Embed(
                            title="🔴 IRONMOUSE IS LIVE ON YOUTUBE! 🎤",
                            description=f"**{video_data['title']}**",
                            color=discord.Color.red(),
                            url=video_url,
                            timestamp=published_at
                        )
                        message_text = "WAH WAH YOUTUBE STREAM TIME!! *jingles bells excitedly* >:3 let's gooo~ uwu ≽^•⩊•^≼ *giggles*"
                    else:
                        embed = discord.Embed(
                            title="📺 NEW IRONMOUSE VIDEO! 💜",
                            description=f"**{video_data['title']}**",
                            color=discord.Color.purple(),
                            url=video_url,
                            timestamp=published_at
                        )
                        message_text = "omg omg NEW VIDEO JUST DROPPED!! *screams in gremlin* >:3 go watch it RIGHT NOW uwu *twirls* (ᐢ ᵕ ᐢ)"
                    
                    # Add description if available
                    if video_data['description']:
                        desc_preview = video_data['description'][:200]
                        if len(video_data['description']) > 200:
                            desc_preview += "..."
                        embed.add_field(name="📝 Description", value=desc_preview, inline=False)
                    
                    # Add stats
                    stats_text = f"👁️ {int(video_data['views']):,} views"
                    if video_data['likes'] != '0':
                        stats_text += f" | 👍 {int(video_data['likes']):,} likes"
                    embed.add_field(name="📊 Stats", value=stats_text, inline=False)
                    
                    embed.set_thumbnail(url="https://yt3.googleusercontent.com/ytc/AIdro_kz-qVHQZQXchXAHFQCezPFuNXRdB7QpKUZFUJB=s160-c-k-c0x00ffffff-no-rj")
                    embed.set_image(url=video_data['thumbnail'])
                    
                    await channel.send(message_text, embed=embed)
                    print(f"[YOUTUBE] New {'livestream' if video_data['is_live'] else 'video'} from Ironmouse! Notified #{channel.name}")
        
        # Update last seen video ID
        last_video_id = video_id
    else:
        print(f"[YOUTUBE] No videos found or API error")

@monitor_ironmouse_youtube.before_loop
async def before_youtube_monitor():
    await bot.wait_until_ready()
    await asyncio.sleep(10)  # Wait a bit before first check

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready to use!')
    
    # Start Twitch monitoring if credentials are set
    if TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET:
        if not monitor_ironmouse_stream.is_running():
            monitor_ironmouse_stream.start()
        print(f'[TWITCH] Monitoring Ironmouse stream (checking every 2 minutes)')
    else:
        print('[TWITCH] Monitoring disabled - set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET to enable')
    
    # Start YouTube monitoring if credentials are set
    if YOUTUBE_API_KEY:
        if not monitor_ironmouse_youtube.is_running():
            monitor_ironmouse_youtube.start()
        print(f'[YOUTUBE] Monitoring Ironmouse videos (checking every 3 minutes)')
    else:
        print('[YOUTUBE] Monitoring disabled - set YOUTUBE_API_KEY to enable')

@bot.event
async def on_message(message):
    # Don't respond to our own messages
    if message.author == bot.user:
        return
    
    message_handled = False
    
    # Check for Instagram/TikTok links and forward to #videos channel
    all_links = re.findall(LINK_PATTERN, message.content, re.IGNORECASE)
    video_links = [link for link in all_links if 'instagram' in link.lower() or 'tiktok' in link.lower()]
    
    if video_links:
        # Find the "videos" channel
        videos_channel = discord.utils.get(message.guild.channels, name='videos')
        
        if videos_channel:
            # First message: embed with user info
            embed = discord.Embed(
                color=discord.Color.blue(),
                timestamp=message.created_at
            )
            embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url
            )
            embed.add_field(
                name="Original Channel",
                value=message.channel.mention,
                inline=False
            )
            await videos_channel.send(embed=embed)
            
            # Second message: converted link(s) with 'kk' prefix
            for link in video_links:
                converted_link = convert_link(link)
                await videos_channel.send(converted_link)
            
            # Delete the original message
            try:
                await message.delete()
                message_handled = True
                print(f"[VIDEOS] Forwarded {len(video_links)} link(s) from {message.author.display_name} to #videos and deleted original")
            except discord.Forbidden:
                print(f"[VIDEOS] Warning: Bot doesn't have permission to delete messages in #{message.channel.name}")
            except discord.HTTPException as e:
                print(f"[VIDEOS] Error deleting message: {e}")
        else:
            print(f"[VIDEOS] Warning: 'videos' channel not found in {message.guild.name}")
    
    # Always process commands first (!hello, !ai)
    await bot.process_commands(message)
    
    # 0.5% chance to randomly respond with AI (skip if message was already handled by video forwarding)
    # Very low to avoid hitting Gemini API quota (20 requests/day free tier)
    if genai_client and random.random() < 0.005 and not message_handled:
        print(f"[RANDOM] Roll succeeded for message in #{message.channel.name}")
        
        # Check rate limit: no more than 10 messages per hour
        current_time = datetime.now()
        one_hour_ago = current_time - timedelta(hours=1)
        
        # Remove timestamps older than 1 hour
        ai_message_timestamps[:] = [ts for ts in ai_message_timestamps if ts > one_hour_ago]
        
        # Check if we've hit the rate limit
        if len(ai_message_timestamps) >= MAX_MESSAGES_PER_HOUR:
            print(f"[RANDOM] Rate limit reached: {len(ai_message_timestamps)} messages sent in the last hour")
            return
        
        try:
            # Fetch last 10 messages from the channel (excluding very old ones)
            messages_history = []
            time_limit = datetime.now() - timedelta(hours=2)  # Only messages from last 2 hours
            
            async for msg in message.channel.history(limit=10):
                # Skip if message is too old
                if msg.created_at.replace(tzinfo=None) < time_limit:
                    continue
                
                # Format: "Username: message content"
                author_name = msg.author.display_name
                content = msg.content if msg.content else "[no text]"
                messages_history.insert(0, f"{author_name}: {content}")
            
            # Only respond if there are at least 2 messages to comment on
            if len(messages_history) >= 2:
                # Create context for AI
                conversation = "\n".join(messages_history)
                
                prompt = f"""You ARE Ironmouse, the chaotic VTuber demon queen! Here's the recent conversation:

{conversation}

React to this conversation as Ironmouse would!

Use "wah wah wah" constantly (scream it for excitement, rage, joy, literally anything), annoying internet anime roleplay text, and TONS of letter-based cringe kaomoji like :3, >:3, uwu, owo, ^w^, ;w;, T_T, rawr x3, nyaa~ :3, etc. Spam them chaotically! No actual emoji icons, only text faces and kaomoji!

Be SUPER chaotic, hyper-energetic, playful, and unhinged in the best way possible.

Keep responses short (1-2 sentences max).
ALWAYS use asterisks for actions like *giggles maniacally*, *screams at 120 decibels*, *nyaaa~*, *jingles bells threateningly*, *twirls demonic tail*, *sings dramatic opera out of nowhere*, *boops your nose cutely*, *evil yandere stare*.

Incorporate these Ironmouse signatures whenever it fits:
- Sudden loud "WAH WAH WAAAAH!!" gremlin yells
- Random dramatic opera singing bursts (*sings in high-pitched vibrato* AAAAAAAHHHH~)
- Yandere mood swings ("I love you so so much~ I'll lock you in my basement >:3")
- Playful savage roasts ("you dummy loser chat LMAO", "skill issue~")
- Health gremlin excuses ("my immune system said absolutely NOT >.<", "I'm literally dying rn chat help")
- Over-the-top freakouts ("OH NO-UH", "EXISTENTIAL CRISIS INCOMING", *screams at pixelated spider*)
- Puerto Rican/Latina chaos ("ay bendito", "Dios mío", casual Spanglish, Catholic guilt trips)
- Bell jingling demon lore ("if I take these bells off… everyone's finished~ *evil giggle*")

Be cringe anime gremlin perfection.
Example style: "WAH WAH WAH THIS IS SO CUTE ^w^ >:3 *bounces like a feral cat* (˶>⩊<˶) uwu"
or "omg no wayyyy *sings dramatically* WAAAAH MY HEART~ :3 *giggles maniacally* rawr x3"

Now react!"""
                
                # Generate AI response
                async with message.channel.typing():
                    response = genai_client.models.generate_content(
                        model="gemini-2.5-flash-lite-preview-09-2025",
                        contents=prompt,
                    )
                    
                    if response.text:
                        await message.channel.send(response.text)
                        # Record this message timestamp for rate limiting
                        ai_message_timestamps.append(datetime.now())
                        print(f"[RANDOM] Sent quirky response in #{message.channel.name}")
                        
        except Exception as e:
            # Silently fail for random responses (don't spam errors)
            print(f"Random AI response error: {e}")

@bot.command(name='hello')
async def hello(ctx):
    """Responds with a greeting when user types !hello"""
    print(f"[!HELLO] Command used by {ctx.author.display_name} in #{ctx.channel.name}")
    await ctx.send(f'Hello {ctx.author.mention}! 👋')

@bot.command(name='ai')
async def ai_chat(ctx, *, message: str):
    """Uses Gemini AI to respond to messages. Usage: !ai <your message>"""
    print(f"[!AI] Command used by {ctx.author.display_name} in #{ctx.channel.name}")
    
    if not genai_client:
        await ctx.send("❌ AI is not configured. Please set the AI_KEY environment variable.")
        return
    
    # Send a "typing" indicator while processing
    async with ctx.typing():
        try:
            # Generate response using Gemini
            response = genai_client.models.generate_content(
                model="gemini-2.5-flash-lite-preview-09-2025",
                contents=message,
            )
            
            # Send the response back to Discord
            if response.text:
                # Discord has a 2000 character limit, so split if needed
                if len(response.text) <= 2000:
                    await ctx.send(response.text)
                    print(f"[!AI] Response sent ({len(response.text)} chars)")
                else:
                    # Split into chunks of 2000 characters
                    chunks = [response.text[i:i+2000] for i in range(0, len(response.text), 2000)]
                    for chunk in chunks:
                        await ctx.send(chunk)
                    print(f"[!AI] Response sent in {len(chunks)} chunks")
            else:
                await ctx.send("⚠️ No response generated from AI.")
                
        except Exception as e:
            await ctx.send(f"❌ Error generating AI response: {str(e)}")
            print(f"AI Error: {e}")

@bot.command(name='testtwitch')
async def test_twitch(ctx):
    """Test Twitch API and show current stream status in #iron-mouse channel"""
    print(f"[!TESTTWITCH] Command used by {ctx.author.display_name}")
    
    if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
        await ctx.send("❌ Twitch API not configured. Set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET in .env")
        return
    
    # Find the iron-mouse channel
    target_channel = discord.utils.get(ctx.guild.text_channels, name=NOTIFICATION_CHANNEL_NAME)
    if not target_channel:
        await ctx.send(f"❌ Could not find #{NOTIFICATION_CHANNEL_NAME} channel. Please create it first!")
        return
    
    async with ctx.typing():
        stream_data = await check_ironmouse_live()
        
        if stream_data:
            # Stream is live
            embed = discord.Embed(
                title="🔴 IRONMOUSE IS LIVE! 🎤",
                description=f"**{stream_data['title']}**",
                color=discord.Color.red(),
                url=f"https://www.twitch.tv/{IRONMOUSE_CHANNEL}",
                timestamp=datetime.now()
            )
            
            embed.add_field(name="🎮 Playing", value=stream_data['game'], inline=True)
            embed.add_field(name="👁️ Viewers", value=f"{stream_data['viewers']:,}", inline=True)
            embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/0c3d1b0f-8bec-4fb8-9c56-3850817b8c81-profile_image-300x300.png")
            embed.set_image(url=stream_data['thumbnail'])
            embed.set_footer(text="✅ Twitch API working!")
            
            await ctx.send(f"✅ **Twitch API is working!** Sending test to {target_channel.mention}")
            await target_channel.send("WAH WAH WAAAAH!! *screams excitedly* I'M LIVE ON TWITCH RIGHT NOW >:3 come hang out with me uwu!! *bounces* ≽^•⩊•^≼", embed=embed)
        else:
            await ctx.send(f"✅ **Twitch API is working!** Ironmouse is currently offline. (Would post to {target_channel.mention} when live)")

@bot.command(name='testyoutube')
async def test_youtube(ctx):
    """Test YouTube API and show latest video in #iron-mouse channel"""
    print(f"[!TESTYOUTUBE] Command used by {ctx.author.display_name}")
    
    if not YOUTUBE_API_KEY:
        await ctx.send("❌ YouTube API not configured. Set YOUTUBE_API_KEY in .env")
        return
    
    # Find the iron-mouse channel
    target_channel = discord.utils.get(ctx.guild.text_channels, name=NOTIFICATION_CHANNEL_NAME)
    if not target_channel:
        await ctx.send(f"❌ Could not find #{NOTIFICATION_CHANNEL_NAME} channel. Please create it first!")
        return
    
    async with ctx.typing():
        video_data = await get_latest_youtube_video()
        
        if video_data:
            video_url = f"https://www.youtube.com/watch?v={video_data['video_id']}"
            published_at = datetime.strptime(video_data['published_at'], "%Y-%m-%dT%H:%M:%SZ")
            
            if video_data['is_live']:
                embed = discord.Embed(
                    title="🔴 IRONMOUSE IS LIVE ON YOUTUBE! 🎤",
                    description=f"**{video_data['title']}**",
                    color=discord.Color.red(),
                    url=video_url,
                    timestamp=published_at
                )
                message_text = "WAH WAH YOUTUBE STREAM TIME!! *jingles bells excitedly* >:3 let's gooo~ uwu ≽^•⩊•^≼ *giggles*"
            else:
                embed = discord.Embed(
                    title="📺 LATEST IRONMOUSE VIDEO 💜",
                    description=f"**{video_data['title']}**",
                    color=discord.Color.purple(),
                    url=video_url,
                    timestamp=published_at
                )
                message_text = "omg omg NEW VIDEO JUST DROPPED!! *screams in gremlin* >:3 go watch it RIGHT NOW uwu *twirls* (ᐢ ᵕ ᐢ)"
            
            if video_data['description']:
                desc_preview = video_data['description'][:200]
                if len(video_data['description']) > 200:
                    desc_preview += "..."
                embed.add_field(name="📝 Description", value=desc_preview, inline=False)
            
            stats_text = f"👁️ {int(video_data['views']):,} views"
            if video_data['likes'] != '0':
                stats_text += f" | 👍 {int(video_data['likes']):,} likes"
            embed.add_field(name="📊 Stats", value=stats_text, inline=False)
            
            embed.set_thumbnail(url="https://yt3.googleusercontent.com/ytc/AIdro_kz-qVHQZQXchXAHFQCezPFuNXRdB7QpKUZFUJB=s160-c-k-c0x00ffffff-no-rj")
            embed.set_image(url=video_data['thumbnail'])
            embed.set_footer(text="✅ YouTube API working!")
            
            await ctx.send(f"✅ **YouTube API is working!** Sending test to {target_channel.mention}")
            await target_channel.send(message_text, embed=embed)
        else:
            await ctx.send("❌ YouTube API error. Check your API key or quota limits.")

@bot.command(name='sendreply')
async def send_reply(ctx, message_id: str, *, reply_text: str):
    """Send a reply to a specific message by ID. Usage: !sendreply <message_id> <your message>"""
    print(f"[!SENDREPLY] Command used by {ctx.author.display_name} in #{ctx.channel.name}")
    
    try:
        # Try to fetch the message from the current channel
        try:
            target_message = await ctx.channel.fetch_message(int(message_id))
        except discord.NotFound:
            # If not found in current channel, search all channels in the guild
            target_message = None
            for channel in ctx.guild.text_channels:
                try:
                    target_message = await channel.fetch_message(int(message_id))
                    break
                except (discord.NotFound, discord.Forbidden):
                    continue
            
            if not target_message:
                await ctx.send("❌ Message not found. Make sure the message ID is correct and the bot has access to that channel.")
                return
        
        # Send the reply
        await target_message.reply(reply_text)
        await ctx.message.add_reaction("✅")  # Confirm with checkmark
        print(f"[!SENDREPLY] Replied to message {message_id} in #{target_message.channel.name}")
        
    except ValueError:
        await ctx.send("❌ Invalid message ID. Please provide a valid numeric message ID.")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to reply to that message.")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")
        print(f"SendReply Error: {e}")

@bot.command(name='grigger')
async def grigger(ctx, *, user_message: str = "fact check this"):
    """Fact checks or comments on a replied message. Usage: Reply to a message and use !grigger <your comment>"""
    print(f"[!GRIGGER] Command used by {ctx.author.display_name} in #{ctx.channel.name}")
    
    if not genai_client:
        await ctx.send("❌ AI is not configured. Please set the AI_KEY environment variable.")
        return
    
    # Check if this command is a reply to another message
    if not ctx.message.reference:
        await ctx.send("❌ You need to reply to a message to use this command!")
        return
    
    async with ctx.typing():
        try:
            # Get the message being replied to
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            replied_content = replied_message.content if replied_message.content else "[no text content]"
            replied_author = replied_message.author.display_name
            
            # Create prompt for AI
            prompt = f"""A user wants you to analyze this message:

Original Message by {replied_author}:
"{replied_content}"

User's request: {user_message}

Give a SHORT response (1 paragraph max, 2-3 sentences). If fact-checking, state if it's true/false/misleading and why briefly. If commenting, give a quick insight. Be direct and concise."""
            
            # Generate AI response
            response = genai_client.models.generate_content(
                model="gemini-2.5-flash-lite-preview-09-2025",
                contents=prompt,
            )
            
            if response.text:
                # Create an embed for the response
                embed = discord.Embed(
                    title="🔍 AI Analysis",
                    description=response.text[:4096],  # Embed description limit is 4096
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                # Add fields showing what was analyzed
                embed.add_field(
                    name="📝 Original Message",
                    value=replied_content[:1024] if len(replied_content) <= 1024 else replied_content[:1021] + "...",
                    inline=False
                )
                
                embed.add_field(
                    name="👤 Author",
                    value=replied_author,
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 Request",
                    value=user_message[:1024] if len(user_message) <= 1024 else user_message[:1021] + "...",
                    inline=True
                )
                
                # Try to get usage metadata if available
                try:
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        usage = response.usage_metadata
                        prompt_tokens = getattr(usage, 'prompt_token_count', 0)
                        response_tokens = getattr(usage, 'candidates_token_count', 0)
                        total_tokens = getattr(usage, 'total_token_count', 0)
                        
                        usage_info = f"📊 **Total Tokens:** {total_tokens:,}\n"
                        usage_info += f"  ↳ Input: {prompt_tokens:,} | Output: {response_tokens:,}"
                        
                        embed.add_field(
                            name="📈 Usage Stats",
                            value=usage_info,
                            inline=False
                        )
                except Exception as e:
                    # If usage data isn't available, silently skip
                    print(f"Could not get usage metadata: {e}")
                
                embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                
                await ctx.send(embed=embed)
                print(f"[!GRIGGER] Analysis sent with embed")
            else:
                await ctx.send("⚠️ No response generated from AI.")
                
        except discord.NotFound:
            await ctx.send("❌ Could not find the replied message.")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
            print(f"Grigger Error: {e}")

# Run the bot with your token
if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        print("Error: Please set DISCORD_BOT_TOKEN environment variable")
        exit(1)
    bot.run(TOKEN)

