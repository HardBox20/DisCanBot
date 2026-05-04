import discord
from discord.ext import tasks
import aiohttp
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

API_URL = os.getenv("API_URL")

PORT = int(os.environ.get("PORT", 10000))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_web():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()

threading.Thread(target=run_web).start()

async def get_player_count():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            data = await response.json()
            return data["numplayers"]
        
@client.event
async def om_ready():
    print(f"Бот запущен как {client.user}")
    update_channel.start()

@tasks.loop(seconds=60)
async def update_channel():
    channel = client.get_channel(CHANNEL_ID)

    try:
        numplayers = await get_player_count()
        new_name = f"Игроки: {numplayers}"

        await channel.edit(name=new_name)
        print(f"Обновлено: {new_name}")

    except Exception as e:
        print(f"Ошибка: {e}")

client.run(TOKEN)