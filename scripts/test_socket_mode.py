import os, sys, asyncio, json, time, signal

SLACK_BOT = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP = os.environ.get("SLACK_APP_TOKEN", "")

if not SLACK_BOT or not SLACK_APP:
    print("Tokens não encontrados")
    sys.exit(1)

from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

app = AsyncApp(token=SLACK_BOT)
events_received = []

@app.event("message")
async def handle_message(event, say, logger):
    events_received.append(event)
    print(f"\n🎯 EVENTO RECEBIDO: channel={event.get('channel')}, user={event.get('user')}, text={event.get('text','')[:80]}", flush=True)

@app.event("app_mention")
async def handle_mention(event, say):
    events_received.append(event)
    print(f"\n🎯 APP_MENTION: {event.get('text','')[:80]}", flush=True)

async def main():
    print("🔌 Conectando Socket Mode... (30s timeout)", flush=True)
    handler = AsyncSocketModeHandler(app, SLACK_APP)
    try:
        task = asyncio.create_task(handler.start_async())
        for i in range(30):
            await asyncio.sleep(1)
            if events_received:
                print(f"\n✅ Sucesso! {len(events_received)} evento(s) recebido(s)", flush=True)
                break
        else:
            print("\n⏰ 30 segundos sem eventos — Socket Mode conecta mas não recebe nada", flush=True)
        task.cancel()
        try:
            await task
        except:
            pass
    except Exception as e:
        print(f"\n❌ Erro: {e}", flush=True)

asyncio.run(main())