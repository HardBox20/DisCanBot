import discord
from discord.ext import tasks
import aiohttp
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

API_URL = os.getenv("API_URL")

PORT = int(os.environ.get("PORT", 10000))

intents = discord.Intents.all()
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
            print("API RESPONSE:", data)
            return data["numplayers"]
        
@client.event
async def setup_hook():
    update_channel.start()

@client.event
async def on_ready():
    print(f"Бот запущен как {client.user}")

last_name = None

@tasks.loop(seconds=60)
async def update_channel():
    global last_name

    print("Запуск update_channel")

    try:
        channel = await client.fetch_channel(CHANNEL_ID)

        numplayers = await get_player_count()
        new_name = f"Игроки: {numplayers}"

        if new_name != last_name:
            await channel.edit(name=new_name)
            last_name = new_name
            print(f"Обновлено: {new_name}")
        else:
            print("Без изменений")

    except Exception as e:
        print(f"Ошибка: {e}")


@update_channel.before_loop
async def before_update():
    await client.wait_until_ready()

client.run(TOKEN)