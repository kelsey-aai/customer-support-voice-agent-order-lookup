"""Microphone capture and speaker playback using PyAudio.

For production phone-based use, replace this with Twilio Media Streams or
your telephony provider's audio bridge.

Default Voice Agent API audio encoding is `audio/pcm`, which is 16-bit
signed little-endian PCM at 24 kHz. See:
https://www.assemblyai.com/docs/voice-agents/voice-agent-api/audio-format
"""

import asyncio
import threading
from queue import Queue

import pyaudio

SAMPLE_RATE = 24000
CHUNK_SIZE = 1200  # 50ms at 24kHz, 16-bit mono — per docs recommendation


class MicStream:
    def __init__(self):
        self._pa = pyaudio.PyAudio()
        self._stream = None
        self._queue: Queue = Queue()
        self._running = False

    def start(self):
        self._running = True
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )
        threading.Thread(target=self._capture, daemon=True).start()

    def _capture(self):
        while self._running:
            data = self._stream.read(CHUNK_SIZE, exception_on_overflow=False)
            self._queue.put(data)

    async def chunks(self):
        loop = asyncio.get_event_loop()
        while self._running:
            chunk = await loop.run_in_executor(None, self._queue.get)
            yield chunk

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        self._pa.terminate()


class Speaker:
    def __init__(self):
        self._pa = pyaudio.PyAudio()
        self._stream = self._open_stream()

    def _open_stream(self):
        return self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            output=True,
        )

    def play(self, audio_bytes: bytes):
        self._stream.write(audio_bytes)

    def flush_and_restart(self):
        """Discard any queued playback and reopen the stream.

        Called when the agent is interrupted (barge-in) so the caller doesn't
        keep hearing stale speech after they've started talking.
        """
        try:
            self._stream.stop_stream()
            self._stream.close()
        except Exception:
            pass
        self._stream = self._open_stream()

    def close(self):
        self._stream.stop_stream()
        self._stream.close()
        self._pa.terminate()
