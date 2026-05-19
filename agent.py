"""
Customer support voice agent — order lookup, returns, callbacks, transfers.

Opens an AssemblyAI Voice Agent API session, streams mic audio in, plays
audio out, and dispatches tool calls to your backend.

API surface: https://www.assemblyai.com/docs/voice-agents/voice-agent-api/events-reference
"""

import asyncio
import base64
import json
import os
import signal

import websockets
from dotenv import load_dotenv

from audio import MicStream, Speaker
from prompts import SYSTEM_PROMPT
from tools import TOOLS, dispatch_tool

load_dotenv()

ASSEMBLYAI_API_KEY = os.environ["ASSEMBLYAI_API_KEY"]
VOICE_AGENT_WS_URL = "wss://agents.assemblyai.com/v1/ws"
GREETING = "Thanks for calling. What can I help you with today?"


async def run_agent():
    mic = MicStream()
    speaker = Speaker()

    session_config = {
        "type": "session.update",
        "session": {
            "system_prompt": SYSTEM_PROMPT,
            "greeting": GREETING,
            "tools": TOOLS,
            "output": {"voice": "ivy"},
        },
    }

    async with websockets.connect(
        VOICE_AGENT_WS_URL,
        additional_headers={"Authorization": f"Bearer {ASSEMBLYAI_API_KEY}"},
    ) as ws:
        await ws.send(json.dumps(session_config))

        ready = asyncio.Event()
        pending_tools: list[dict] = []

        async def send_audio():
            await ready.wait()
            mic.start()
            async for chunk in mic.chunks():
                await ws.send(json.dumps({
                    "type": "input.audio",
                    "audio": base64.b64encode(chunk).decode(),
                }))

        async def receive_events():
            async for raw in ws:
                event = json.loads(raw)
                kind = event.get("type")

                if kind == "session.ready":
                    ready.set()
                    print(f"Session ready: {event.get('session_id')}")

                elif kind == "reply.audio":
                    speaker.play(base64.b64decode(event["data"]))

                elif kind == "tool.call":
                    result = await dispatch_tool(
                        event["name"], event.get("arguments", {})
                    )
                    # Accumulate — don't send until reply.done.
                    pending_tools.append({
                        "call_id": event["call_id"],
                        "result": result,
                    })

                elif kind == "reply.done":
                    if event.get("status") == "interrupted":
                        # User barged in — drop pending results and flush playback.
                        pending_tools.clear()
                        speaker.flush_and_restart()
                    elif pending_tools:
                        for tool in pending_tools:
                            value = tool["result"]
                            if not isinstance(value, str):
                                value = json.dumps(value)
                            await ws.send(json.dumps({
                                "type": "tool.result",
                                "call_id": tool["call_id"],
                                "result": value,
                            }))
                        pending_tools.clear()

                elif kind == "transcript.user":
                    print(f"User:  {event['text']}")

                elif kind == "transcript.agent":
                    print(f"Agent: {event['text']}")

                elif kind == "session.error":
                    print(
                        f"Session error [{event.get('code')}]: "
                        f"{event.get('message')}"
                    )

        try:
            await asyncio.gather(send_audio(), receive_events())
        finally:
            mic.stop()
            speaker.close()


def main():
    loop = asyncio.new_event_loop()

    def shutdown():
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    try:
        loop.run_until_complete(run_agent())
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    main()
