import discord
from discord.ext import commands, tasks
import os
import psutil
from discord import app_commands
import requests
import satisfactory_api

# Function to find the PID of the server process by name
def find_pid_by_name():
    matching_pids = []
    name = "FactoryServer-Linux-Shipping"
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name.lower() in proc.info['name'].lower():
                matching_pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return matching_pids[0] if matching_pids else None

def get_token():
    with open("bot_token", 'r') as f:
        return f.read()

# Function to count the number of players connected by reading network connections
def get_player_count():
    status_raw = satisfactory_api.query_server_state()
    if not status_raw:
        return "Unable to query API"
    if "data" not in status_raw.keys():
        return "No data returned from API"
    if "serverGameState" not in status_raw['data'].keys():
        return "No server game state returned from API"

    numConnectedPlayers = status_raw['data']['serverGameState']['numConnectedPlayers']
    return numConnectedPlayers

def get_server_status_string():
    status_raw = satisfactory_api.query_server_state()
    if not status_raw:
        return "Unable to query API"
    if "data" not in status_raw.keys():
        return "No data returned from API"
    if "serverGameState" not in status_raw['data'].keys():
        return "No server game state returned from API"

    numConnectedPlayers = status_raw['data']['serverGameState']['numConnectedPlayers']
    techTier = status_raw['data']['serverGameState']['techTier']
    isGamePaused = status_raw['data']['serverGameState']['isGamePaused']
    totalGameDuration = status_raw['data']['serverGameState']['totalGameDuration']
    milestone = satisfactory_api.get_current_milestone()
    gameDurationHours = 0
    try:
        gameDurationHours = round(int(totalGameDuration) / 60 / 60, 1)
    except Exception as e:
        print(f"Failed to get game duration {e}")
    return f"Connected Players: {numConnectedPlayers}\nMilestone: {milestone}\nTier: {techTier}\nisPaused: {isGamePaused}\nRunning Hours: {gameDurationHours}"

TOKEN = get_token()

# Set up intents (default intents + message content for commands)
intents = discord.Intents.default()
intents.message_content = True  # Needed to read message content

# Create the bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Define the Cog for handling the /serverstatus slash command
class ServerStatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command to check the server status
    @app_commands.command(name="serverstatus", description="Check the current server status")
    async def serverstatus(self, interaction: discord.Interaction):
        status_message = get_server_status_string()
        await interaction.response.send_message(status_message)

# Event that runs when the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await setup(bot)
    try:
        synced = await bot.tree.sync()  # Sync the slash commands with Discord
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    # Start the task to update the bot's presence with player count
    update_activity_task.start()

# Task that runs every 30 seconds to update the bot's presence with player count
@tasks.loop(seconds=30)
async def update_activity_task():
    player_count = get_player_count()
    try:
        content = f"{player_count} players working on {satisfactory_api.get_current_milestone()}"
    except:
        content = "Unable to supervise players"

    await bot.change_presence(activity=discord.CustomActivity(name=content))
    print(f"Activity updated to: {content}")

# Register the Cog for the /serverstatus command
async def setup(bot):
    await bot.add_cog(ServerStatusCog(bot))

# Run the bot
bot.run(TOKEN)
