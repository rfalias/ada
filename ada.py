import discord
from discord.ext import commands, tasks
import os
import psutil
from discord import app_commands
import requests
import satisfactory_api
import asyncio

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
    service_status = satisfactory_api.get_service_status()
    gameDurationHours = 0
    try:
        gameDurationHours = round(int(totalGameDuration) / 60 / 60, 1)
    except Exception as e:
        print(f"Failed to get game duration {e}")
    return f"Connected Players: {numConnectedPlayers}\nMilestone: {milestone}\nTier: {techTier}\nisPaused: {isGamePaused}\nRunning Hours: {gameDurationHours}\nService Active: {service_status}"

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

     # Slash command to stop and restart the Satisfactory server, restricted to SatisfactoryAdmin role
    @app_commands.command(name="restartserver", description="Stop and restart the Satisfactory server.")
    async def restartserver(self, interaction: discord.Interaction):
        # Check if the user has the required role
        if not has_required_role(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        # Stop the server
        await interaction.response.send_message("Stopping the Satisfactory server. This will take ~30s")
        os.system("systemctl stop satisfactory")

        # Wait for 30 seconds
        await asyncio.sleep(30)

        # Start the server again
        await interaction.followup.send("Starting up the satisfactory server.\nThis will check for updates and could take some time.")
        os.system("systemctl start satisfactory")



# A helper function to check if the user has the required role
def has_required_role(interaction: discord.Interaction):
    return any(role.name == "SatisfactoryAdmin" for role in interaction.user.roles)

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
    player_string = "pioneers"
    if player_count == 1:
        player_string = "pioneer"
    try:
        content = f"{player_count} {player_string} working on {satisfactory_api.get_current_milestone()}"
    except Exception as e:
        content = f"Unable to supervise players {e}"
        raise e

    await bot.change_presence(activity=discord.CustomActivity(name=content))
    print(f"Activity updated to: {content}")

# Register the Cog for the /serverstatus command
async def setup(bot):
    await bot.add_cog(ServerStatusCog(bot))

# Run the bot
bot.run(TOKEN)
