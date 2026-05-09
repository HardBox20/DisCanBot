import os
import json
import aiohttp
from aiohttp import web

# =========================
# ENV
# =========================

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
STATUS_WEBHOOK_URL = os.getenv("STATUS_WEBHOOK_URL")

SECRET = os.getenv("SECRET", "supersecret")

PORT = int(os.getenv("PORT", 10000))

MESSAGE_FILE = "message.json"

# =========================
# GLOBALS
# =========================

current_sub = "Неизвестно"
current_players = 0

status_message_id = None

# =========================
# MESSAGE ID
# =========================

def load_message_id():

    if os.path.exists(MESSAGE_FILE):

        with open(MESSAGE_FILE, "r", encoding="utf-8") as f:

            return json.load(f).get("id")

    return None


def save_message_id(msg_id):

    with open(MESSAGE_FILE, "w", encoding="utf-8") as f:

        json.dump({"id": msg_id}, f)

# =========================
# DISCORD
# =========================

async def send_discord(session, message):

    try:

        async with session.post(
            WEBHOOK_URL,
            json={"content": message}
        ) as r:

            print("→ Discord:", r.status)

    except Exception as e:

        print("❌ Discord error:", e)

# =========================
# STATUS MESSAGE
# =========================

async def update_status_message(session):

    global status_message_id

    content = (
        f"📡 Статус сервера\n"
        f"🚢 Корабль: {current_sub}\n"
        f"👥 Онлайн: {current_players}"
    )

    try:

        # =========================
        # UPDATE MESSAGE
        # =========================

        if status_message_id:

            url = (
                f"{STATUS_WEBHOOK_URL}"
                f"/messages/{status_message_id}"
            )

            async with session.patch(
                url,
                json={"content": content}
            ) as r:

                if r.status == 200:

                    print("🔄 статус обновлён")

                    return

                else:

                    print(
                        "⚠️ PATCH failed:",
                        r.status
                    )

        # =========================
        # CREATE NEW MESSAGE
        # =========================

        async with session.post(
            STATUS_WEBHOOK_URL + "?wait=true",
            json={"content": content}
        ) as r:

            data = await r.json()

            status_message_id = data["id"]

            save_message_id(status_message_id)

            print("✅ создано новое статус-сообщение")

    except Exception as e:

        print("❌ status update:", e)

# =========================
# EVENTS
# =========================

async def handle_event(request):

    global current_sub
    global current_players

    try:

        data = await request.json()

        print("EVENT:", data)

        # =========================
        # SECRET CHECK
        # =========================

        if data.get("key") != SECRET:

            return web.Response(
                text="forbidden",
                status=403
            )

        event = data.get("event")

        sub = data.get("sub")

        players = data.get("players")

        # =========================
        # UPDATE DATA
        # =========================

        if sub:

            current_sub = sub

        if players is not None:

            current_players = players

        async with aiohttp.ClientSession() as session:

            # =========================
            # STATUS UPDATE
            # =========================

            await update_status_message(session)

            # =========================
            # EVENTS
            # =========================

            if event == "start":

                await send_discord(
                    session,
                    (
                        f"🌊 Корабль "
                        f"{current_sub} "
                        f"отправился в поход"
                    )
                )

            elif event == "end_success":

                await send_discord(
                    session,
                    (
                        f"⚓ Корабль "
                        f"{current_sub} "
                        f"добрался до аванпоста"
                    )
                )

            elif event == "end_fail":

                await send_discord(
                    session,
                    (
                        f"⚠️ Корабль "
                        f"{current_sub} "
                        f"пропал без вести"
                    )
                )

        return web.Response(text="ok")

    except Exception as e:

        print("❌ handle_event:", e)

        return web.Response(
            text="error",
            status=500
        )

# =========================
# HEALTHCHECK
# =========================

async def health(request):

    return web.Response(text="ok")

# =========================
# APP
# =========================

app = web.Application()

app.router.add_post("/event", handle_event)

app.router.add_get("/", health)

# =========================
# START
# =========================

status_message_id = load_message_id()

print("🚀 Render app started")

web.run_app(
    app,
    host="0.0.0.0",
    port=PORT
)
