import discord
from discord.ext import commands
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Regex pattern to detect any link containing instagram or tiktok
LINK_PATTERN = r'https?://[^\s]+'

def convert_link(link):
    """Convert instagram/tiktok links to add 'kk' prefix"""
    # Replace instagram with kkinstagram (case-insensitive)
    converted = re.sub(r'instagram', 'kkinstagram', link, flags=re.IGNORECASE)
    # Replace tiktok with kktiktok (case-insensitive)
    converted = re.sub(r'tiktok', 'kktiktok', converted, flags=re.IGNORECASE)
    return converted

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Find all links in the message
    all_links = re.findall(LINK_PATTERN, message.content, re.IGNORECASE)
    
    # Filter links that contain "instagram" or "tiktok"
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
                print(f"Forwarded {len(video_links)} link(s) from {message.author} to #videos and deleted original")
            except discord.Forbidden:
                print(f"Warning: Bot doesn't have permission to delete messages in {message.channel.name}")
            except discord.HTTPException as e:
                print(f"Error deleting message: {e}")
        else:
            print(f"Warning: 'videos' channel not found in {message.guild.name}")
    
    # Process commands if any
    await bot.process_commands(message)

# Run the bot
if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
        exit(1)
    
    bot.run(TOKEN)

