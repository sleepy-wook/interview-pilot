"""Step 6 Tests: Voice Input Integration.

Tests:
1. TranscribeStreamer connection + audio streaming
2. Custom Vocabulary creation from keywords
3. Voice metrics calculation (filler words, latency)
4. FastAPI server starts with all routes
"""

import sys
import os
import asyncio
import struct
import math
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("AWS_PROFILE", os.getenv("AWS_PROFILE", "interview-pilot"))
os.environ.setdefault("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))

from core.transcribe_client import (
    TranscribeStreamer,
    build_vocabulary_from_keywords,
    get_vocabulary_status,
    delete_vocabulary,
    FILLER_PATTERNS,
)


def _generate_tone_pcm(freq=440, duration=2.0, sample_rate=16000) -> bytes:
    samples = []
    for i in range(int(sample_rate * duration)):
        value = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / sample_rate))
        samples.append(struct.pack("<h", value))
    return b"".join(samples)


async def test_transcribe_streamer():
    """Test TranscribeStreamer class (connection + audio flow)."""
    print("=== Test 1: TranscribeStreamer ===")

    partials = []
    finals = []

    async def on_partial(text, is_partial=True):
        partials.append(text)

    async def on_final(text, is_partial=False):
        finals.append(text)

    streamer = TranscribeStreamer(on_partial=on_partial, on_final=on_final)
    await streamer.start()
    print("  [OK] Stream started")

    # Send 2 seconds of tone
    audio = _generate_tone_pcm(freq=440, duration=2.0)
    chunk_size = 16 * 1024
    for i in range(0, len(audio), chunk_size):
        await streamer.send_audio(audio[i : i + chunk_size])

    transcript = await streamer.stop()
    print(f"  Transcript: '{transcript}' (empty expected for tone)")
    print(f"  Partials received: {len(partials)}")

    # Get voice metrics
    metrics = streamer.get_voice_metrics(question_end_time=time.time() - 3.0)
    print(f"  Voice metrics: duration={metrics.get('answer_duration_s')}s, "
          f"fillers={metrics.get('filler_count')}")

    assert metrics.get("answer_duration_s", 0) > 0, "Duration should be > 0"
    print("[PASS] TranscribeStreamer works")


def test_custom_vocabulary():
    """Test Custom Vocabulary creation from research keywords."""
    print("\n=== Test 2: Custom Vocabulary from Keywords ===")

    keywords = ["Databricks", "Delta Lake", "Unity Catalog", "MLflow", "Spark Shuffle"]
    vocab_name = "interview-test-step6"

    # Clean up any existing test vocabulary
    delete_vocabulary(vocab_name)
    time.sleep(1)

    # Create via build function
    from core.transcribe_client import create_vocabulary
    result = create_vocabulary(vocab_name, keywords)

    print(f"  Vocabulary: {result.get('vocabulary_name')}")
    print(f"  Status: {result.get('status')}")
    print(f"  Phrases: {result.get('phrases_count')}")

    assert result.get("vocabulary_name") == vocab_name
    assert result.get("phrases_count") == len(keywords)

    # Check status
    status = get_vocabulary_status(vocab_name)
    print(f"  Current status: {status}")
    assert status in ("PENDING", "READY"), f"Unexpected status: {status}"

    # Wait for READY (up to 60s)
    print("  Waiting for READY (up to 60s)...")
    for _ in range(12):
        status = get_vocabulary_status(vocab_name)
        if status == "READY":
            break
        time.sleep(5)

    print(f"  Final status: {status}")

    # Clean up
    if status in ("READY", "FAILED"):
        delete_vocabulary(vocab_name)
        print("  [OK] Cleaned up")
    else:
        print("  [WARN] Could not delete (still PENDING)")

    print("[PASS] Custom Vocabulary creation works")


def test_voice_metrics_filler_detection():
    """Test filler word detection in transcripts."""
    print("\n=== Test 3: Voice Metrics - Filler Detection ===")

    # Test with filler-heavy text
    text_with_fillers = (
        "Um, so I worked with, like, Delta Lake and, you know, "
        "basically built a pipeline that, uh, processes data."
    )
    matches = FILLER_PATTERNS.findall(text_with_fillers)
    print(f"  Text: {text_with_fillers[:60]}...")
    print(f"  Fillers found: {matches}")

    assert len(matches) >= 4, f"Expected 4+ fillers, got {len(matches)}"

    # Test with clean text
    text_clean = (
        "I worked with Delta Lake to build a real-time data pipeline "
        "that processes over 100 terabytes of data per day."
    )
    matches_clean = FILLER_PATTERNS.findall(text_clean)
    print(f"  Clean text fillers: {len(matches_clean)}")
    assert len(matches_clean) <= 1, f"Too many fillers in clean text: {matches_clean}"

    print("[PASS] Filler detection works")


def test_server_routes():
    """Test FastAPI server has all expected routes."""
    print("\n=== Test 4: Server Routes ===")

    from main import app

    routes = [r.path for r in app.routes]
    print(f"  Total routes: {len(routes)}")

    expected = [
        "/health",
        "/api/interview/start",
        "/api/interview/{session_id}/next",
        "/api/interview/{session_id}/answer",
        "/api/interview/{session_id}/state",
        "/api/ws/voice",
    ]

    for route in expected:
        found = any(route in r for r in routes)
        status = "OK" if found else "MISSING"
        print(f"  {route}: {status}")
        assert found, f"Route {route} not found in {routes}"

    print("[PASS] All routes registered")


async def async_main():
    passed = 0
    failed = 0

    # Test 1: TranscribeStreamer
    try:
        await test_transcribe_streamer()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_transcribe_streamer: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # Test 2: Custom Vocabulary
    try:
        test_custom_vocabulary()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_custom_vocabulary: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # Test 3: Filler Detection
    try:
        test_voice_metrics_filler_detection()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_voice_metrics_filler_detection: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    # Test 4: Server Routes
    try:
        test_server_routes()
        passed += 1
    except Exception as e:
        print(f"[FAIL] test_server_routes: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    print(f"\n{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All Step 6 tests PASSED!")


if __name__ == "__main__":
    asyncio.run(async_main())
