"""Amazon Transcribe Streaming client for real-time STT.

Provides:
- Real-time streaming transcription via WebSocket
- Custom Vocabulary management (create, status, delete)
- Voice metrics collection (filler words, latency)
"""

from __future__ import annotations

import asyncio
import os
import re
import time
from typing import Callable

import boto3
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

from core.config import get_settings

# Filler word patterns for voice metrics
FILLER_PATTERNS = re.compile(
    r"\b(um|uh|like|you know|so|basically|actually|right|I mean|well)\b",
    re.IGNORECASE,
)


class TranscriptHandler(TranscriptResultStreamHandler):
    """Collects partial and final transcription results."""

    def __init__(self, stream, on_partial: Callable | None = None, on_final: Callable | None = None):
        super().__init__(stream)
        self.on_partial = on_partial
        self.on_final = on_final
        self.final_transcript = ""
        self.partial_transcript = ""
        self.first_utterance_time: float | None = None
        self._start_time = time.time()

    async def handle_transcript_event(self, event: TranscriptEvent):
        for result in event.transcript.results:
            if not result.alternatives:
                continue
            text = result.alternatives[0].transcript

            if result.is_partial:
                self.partial_transcript = text
                if self.first_utterance_time is None and text.strip():
                    self.first_utterance_time = time.time()
                if self.on_partial:
                    await _maybe_await(self.on_partial(text, is_partial=True))
            else:
                self.final_transcript += text + " "
                if self.on_final:
                    await _maybe_await(self.on_final(text, is_partial=False))

    def get_voice_metrics(self, question_end_time: float | None = None) -> dict:
        """Calculate voice metrics from the completed transcription."""
        text = self.final_transcript.strip()
        filler_matches = FILLER_PATTERNS.findall(text)
        word_count = len(text.split()) if text else 0
        duration = time.time() - self._start_time

        latency = None
        if question_end_time and self.first_utterance_time:
            latency = self.first_utterance_time - question_end_time

        return {
            "response_latency_s": round(latency, 2) if latency else None,
            "answer_duration_s": round(duration, 2),
            "filler_count": len(filler_matches),
            "filler_words": filler_matches,
            "word_count": word_count,
            "filler_rate_per_min": round(len(filler_matches) / (duration / 60), 2) if duration > 0 else 0,
        }


class TranscribeStreamer:
    """Manages a single Transcribe Streaming session.

    Usage:
        streamer = TranscribeStreamer(vocabulary_name="interview-databricks-se")
        await streamer.start()
        await streamer.send_audio(chunk)   # repeat for each chunk
        transcript = await streamer.stop()  # returns final text
    """

    def __init__(
        self,
        vocabulary_name: str | None = None,
        on_partial: Callable | None = None,
        on_final: Callable | None = None,
    ):
        settings = get_settings()
        self.region = settings.aws_region
        self.language_code = settings.transcribe_language_code
        self.vocabulary_name = vocabulary_name
        self.on_partial = on_partial
        self.on_final = on_final

        self._stream = None
        self._handler: TranscriptHandler | None = None
        self._handler_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start a Transcribe Streaming session."""
        os.environ.setdefault("AWS_PROFILE", get_settings().aws_profile)
        os.environ.setdefault("AWS_DEFAULT_REGION", self.region)

        client = TranscribeStreamingClient(region=self.region)

        kwargs = {
            "language_code": self.language_code,
            "media_sample_rate_hz": 16000,
            "media_encoding": "pcm",
            "enable_partial_results_stabilization": True,
            "partial_results_stability": "medium",
        }
        if self.vocabulary_name:
            kwargs["vocabulary_name"] = self.vocabulary_name

        self._stream = await client.start_stream_transcription(**kwargs)
        self._handler = TranscriptHandler(
            self._stream.output_stream,
            on_partial=self.on_partial,
            on_final=self.on_final,
        )
        self._handler_task = asyncio.create_task(self._handler.handle_events())

    async def send_audio(self, chunk: bytes) -> None:
        """Send an audio chunk (16kHz 16-bit PCM mono)."""
        if self._stream:
            await self._stream.input_stream.send_audio_event(audio_chunk=chunk)

    async def stop(self) -> str:
        """End the stream and return the final transcript."""
        if self._stream:
            await self._stream.input_stream.end_stream()
        if self._handler_task:
            await self._handler_task
        return self._handler.final_transcript.strip() if self._handler else ""

    def get_voice_metrics(self, question_end_time: float | None = None) -> dict:
        """Get voice metrics from the completed session."""
        if self._handler:
            return self._handler.get_voice_metrics(question_end_time)
        return {}


# ── Custom Vocabulary Management ──


def _get_transcribe_client():
    """Get a boto3 Transcribe client with the configured profile."""
    settings = get_settings()
    session = boto3.Session(
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
    )
    return session.client("transcribe")


def create_vocabulary(name: str, phrases: list[str]) -> dict:
    """Create a Custom Vocabulary for improved tech term recognition."""
    client = _get_transcribe_client()

    # Delete existing vocabulary with same name if READY/FAILED
    try:
        existing = client.get_vocabulary(VocabularyName=name)
        if existing.get("VocabularyState") in ("READY", "FAILED"):
            client.delete_vocabulary(VocabularyName=name)
            import time as _time
            _time.sleep(2)
    except client.exceptions.BadRequestException:
        pass  # Doesn't exist

    clean_phrases = list({p.strip() for p in phrases if p.strip()})

    client.create_vocabulary(
        VocabularyName=name,
        LanguageCode="en-US",
        Phrases=clean_phrases,
    )
    return {"vocabulary_name": name, "status": "PENDING", "phrases_count": len(clean_phrases)}


def get_vocabulary_status(name: str) -> str:
    """Get vocabulary status: PENDING, READY, FAILED, or NOT_FOUND."""
    client = _get_transcribe_client()
    try:
        response = client.get_vocabulary(VocabularyName=name)
        return response.get("VocabularyState", "UNKNOWN")
    except Exception:
        return "NOT_FOUND"


def delete_vocabulary(name: str) -> bool:
    """Delete a Custom Vocabulary."""
    client = _get_transcribe_client()
    try:
        client.delete_vocabulary(VocabularyName=name)
        return True
    except Exception:
        return False


def build_vocabulary_from_keywords(company: str, role: str, keywords: list[str]) -> dict:
    """Build a Custom Vocabulary from Research Brief keywords.

    Called at the end of Phase 0 to optimize STT for the interview.
    """
    name = f"interview-{company.lower().replace(' ', '-')}-{role.lower().replace(' ', '-')}"
    name = name[:200]
    return create_vocabulary(name, keywords)


async def _maybe_await(result):
    """Await a result if it's a coroutine."""
    if asyncio.iscoroutine(result):
        return await result
    return result
