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

# Specific user ID for image forwarding
DUCKY_USER_ID = 1441164318711222353

def convert_link(link):
    """Convert instagram/tiktok links to add 'kk' prefix, removing any existing prefixes"""
    # Pattern matches optional 2-letter prefix (like vx, dd, kk, etc.) before instagram/tiktok
    # Replace with just 'kk' prefix to ensure there's only one prefix
    converted = re.sub(r'([a-z]{2})?(instagram)', r'kk\2', link, flags=re.IGNORECASE)
    converted = re.sub(r'([a-z]{2})?(tiktok)', r'kk\2', converted, flags=re.IGNORECASE)
    return converted

def is_image(attachment):
    """Check if an attachment is an image"""
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
    return any(attachment.filename.lower().endswith(ext) for ext in image_extensions)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    message_handled = False
    
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
                message_handled = True
                print(f"Forwarded {len(video_links)} link(s) from {message.author} to #videos and deleted original")
            except discord.Forbidden:
                print(f"Warning: Bot doesn't have permission to delete messages in {message.channel.name}")
            except discord.HTTPException as e:
                print(f"Error deleting message: {e}")
        else:
            print(f"Warning: 'videos' channel not found in {message.guild.name}")
    
    # Check if message is from the specific user and contains images
    if message.author.id == DUCKY_USER_ID and message.attachments and not message_handled:
        # Filter only image attachments
        images = [att for att in message.attachments if is_image(att)]
        
        if images:
            # Find the "ducky-images" channel
            ducky_channel = discord.utils.get(message.guild.channels, name='ducky-images')
            
            if ducky_channel:
                # Create embed with user info
                embed = discord.Embed(
                    color=discord.Color.purple(),
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
                await ducky_channel.send(embed=embed)
                
                # Forward each image
                for image in images:
                    await ducky_channel.send(image.url)
                
                # Delete the original message
                try:
                    await message.delete()
                    message_handled = True
                    print(f"Forwarded {len(images)} image(s) from {message.author} to #ducky-images and deleted original")
                except discord.Forbidden:
                    print(f"Warning: Bot doesn't have permission to delete messages in {message.channel.name}")
                except discord.HTTPException as e:
                    print(f"Error deleting message: {e}")
            else:
                print(f"Warning: 'ducky-images' channel not found in {message.guild.name}")
    
    # Check if message is from the specific user and is a text message (no links, no images)
    if message.author.id == DUCKY_USER_ID and not message_handled and message.content.strip():
        # Make sure there are no links and no attachments
        if not all_links and not message.attachments:
            # Find the "ducky-messages" channel
            ducky_messages_channel = discord.utils.get(message.guild.channels, name='ducky-messages')
            
            if ducky_messages_channel:
                # Create embed with user info
                embed = discord.Embed(
                    description=message.content,
                    color=discord.Color.green(),
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
                await ducky_messages_channel.send(embed=embed)
                
                # Delete the original message
                try:
                    await message.delete()
                    message_handled = True
                    print(f"Forwarded text message from {message.author} to #ducky-messages and deleted original")
                except discord.Forbidden:
                    print(f"Warning: Bot doesn't have permission to delete messages in {message.channel.name}")
                except discord.HTTPException as e:
                    print(f"Error deleting message: {e}")
            else:
                print(f"Warning: 'ducky-messages' channel not found in {message.guild.name}")
    
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

