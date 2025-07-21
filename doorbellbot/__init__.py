import asyncio

import uvicorn
from dotenv import dotenv_values
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from telegram.ext import Application
from uiprotect import ProtectApiClient

config = dotenv_values()

PORT = 9091


async def callback(a, b, c):
    print(a, b, c)


async def unifi(request: Request) -> Response:
    protect: ProtectApiClient = request.app.state.PROTECT
    tg = request.app.state.TG_APP
    json = await request.json()

    for trigger in json["triggers"]:
        if trigger["key"] != "ring":
            continue

        event_id = trigger["eventId"]
        print(f"event {event_id}")
        event = await protect.get_event(event_id)

        print("downloadin video")
        video = await event.get_video()

        print("uploadin video")
        await tg.bot.send_video(chat_id=config["TELEGRAM_CHANNEL"], video=video)

    return Response()


async def main() -> None:
    telegram_app = Application.builder().token(config["TELEGRAM_TOKEN"]).build()

    protect = ProtectApiClient(
        config["UNIFI_IP"],
        443,
        config["UNIFI_USER"],
        config["UNIFI_PASS"],
        verify_ssl=False,
    )
    await protect.update()

    starlette_app = Starlette(
        routes=[
            Route("/unifi", unifi, methods=["POST"]),
        ]
    )
    starlette_app.state.TG_APP = telegram_app
    starlette_app.state.PROTECT = protect

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=starlette_app,
            port=PORT,
            use_colors=False,
            host="127.0.0.1",
        )
    )

    async with telegram_app:
        await telegram_app.start()
        await webserver.serve()
        await telegram_app.stop()


if __name__ == "__main__":
    asyncio.run(main())
