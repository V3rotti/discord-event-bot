import os
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get token from environment variable
TOKEN = os.getenv('DISCORD_TOKEN')

TIMEZONE = pytz.timezone('Europe/Berlin')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="create", description="Create a new event in #sessions and Discord")
@app_commands.describe(
    date="Event date (DD.MM.YYYY)",
    time="Event time (HH:MM)",
    title="Event title",
    description="Event description (optional)"
)
async def create_event(
    interaction: discord.Interaction, 
    date: str, 
    time: str, 
    title: str,
    description: str = "Event details to be announced."
):
    try:
        sessions_channel = discord.utils.get(interaction.guild.channels, name='sessions')
        voice_channel = discord.utils.get(interaction.guild.voice_channels, name='general-voice')
        
        if not all([sessions_channel, voice_channel]):
            await interaction.response.send_message(
                "Error: Required channels not found.", 
                ephemeral=True
            )
            return

        # Parse date and time with timezone
        event_date = datetime.strptime(date, "%d.%m.%Y")
        event_time = datetime.strptime(time, "%H:%M").time()
        event_datetime = datetime.combine(event_date, event_time)
        
        # Make datetime timezone aware
        local_dt = TIMEZONE.localize(event_datetime)
        utc_dt = local_dt.astimezone(pytz.UTC)
        
        embed = discord.Embed(
            title=f"{title}",
            description=f"**Date:** {event_date.strftime('%d %B %Y')}\n**Time:** {event_time.strftime('%H:%M')}\n\n{description}",
            color=discord.Color.blue()
        )
        
        await sessions_channel.send(embed=embed)
        
        try:
            await interaction.guild.create_scheduled_event(
                name=title,
                description=description,
                channel=voice_channel,
                start_time=utc_dt,
                end_time=utc_dt + timedelta(hours=2),
                privacy_level=discord.PrivacyLevel.guild_only,
                entity_type=discord.EntityType.voice
            )
            
            await interaction.response.send_message(
                f"Event '{title}' created successfully!", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Error creating server event: {str(e)}", 
                ephemeral=True
            )
    
    except Exception as e:
        await interaction.response.send_message(
            f"An error occurred: {str(e)}", 
            ephemeral=True
        )

bot.run(TOKEN)