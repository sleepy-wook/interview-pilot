"""WebSocket endpoint for voice streaming.

Browser → WebSocket → Backend → Transcribe Streaming → partial/final text → Browser

Protocol (JSON messages over WebSocket):
  Client → Server:
    {"type": "audio", "data": "<base64 PCM>"}
    {"type": "stop"}

  Server → Client:
    {"type": "partial", "text": "I worked with Delta..."}
    {"type": "final", "text": "I worked with Delta Lake to build..."}
    {"type": "done", "transcript": "full text", "voice_metrics": {...}}
    {"type": "error", "message": "..."}
"""

from __future__ import annotations

import asyncio
import base64
import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.transcribe_client import TranscribeStreamer

router = APIRouter()


@router.websocket("/ws/voice")
async def voice_websocket(ws: WebSocket):
    """WebSocket endpoint for real-time voice → text transcription."""
    await ws.accept()

    # Get optional vocabulary name from query params
    vocabulary_name = ws.query_params.get("vocabulary")
    question_end_time = time.time()  # Approximate question end = connection start

    streamer: TranscribeStreamer | None = None

    try:
        # Callbacks to relay partial/final results back to browser
        async def on_partial(text: str, is_partial: bool = True):
            await ws.send_json({"type": "partial", "text": text})

        async def on_final(text: str, is_partial: bool = False):
            await ws.send_json({"type": "final", "text": text})

        streamer = TranscribeStreamer(
            vocabulary_name=vocabulary_name,
            on_partial=on_partial,
            on_final=on_final,
        )
        await streamer.start()

        # Receive audio chunks from browser
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "audio":
                pcm_bytes = base64.b64decode(msg["data"])
                await streamer.send_audio(pcm_bytes)

            elif msg.get("type") == "stop":
                transcript = await streamer.stop()
                metrics = streamer.get_voice_metrics(question_end_time)
                await ws.send_json({
                    "type": "done",
                    "transcript": transcript,
                    "voice_metrics": metrics,
                })
                break

    except WebSocketDisconnect:
        if streamer:
            await streamer.stop()
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
