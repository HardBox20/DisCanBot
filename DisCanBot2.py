import aiohttp
import asyncio
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
API_URL = os.getenv("API_URL")
PORT = int(os.environ.get("PORT", 10000))

MESSAGE_FILE = "message.json"


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()


def run_web():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()


threading.Thread(target=run_web, daemon=True).start()


def load_message_id():
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, "r") as f:
            return json.load(f).get("id")
    return None


def save_message_id(msg_id):
    with open(MESSAGE_FILE, "w") as f:
        json.dump({"id": msg_id}, f)


async def get_player_count():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            data = await response.json()
            return data['response']['numplayers'], data['response']['maxplayers']


async def send_or_edit(session, content, message_id):
    if message_id:
        # РЕДАКТИРОВАНИЕ
        url = f"{WEBHOOK_URL}/messages/{message_id}"
        async with session.patch(url, json={"content": content}) as r:
            if r.status == 200:
                return message_id
            else:
                print("Не удалось отредактировать, создаём новое")

    # СОЗДАНИЕ НОВОГО
    async with session.post(WEBHOOK_URL + "?wait=true", json={"content": content}) as r:
        data = await r.json()
        msg_id = data["id"]
        save_message_id(msg_id)
        return msg_id


async def loop():
    message_id = load_message_id()
    last_text = None

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                players, maxplayers = await get_player_count()
                text = f"🟢 Игроки: {players}/{maxplayers}"

                if text != last_text:
                    message_id = await send_or_edit(session, text, message_id)
                    last_text = text
                    print("Обновлено:", text)
                else:
                    print("Без изменений")

            except Exception as e:
                print("Ошибка:", e)

            await asyncio.sleep(120)


asyncio.run(loop())