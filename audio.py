"""Microphone capture and speaker playback using PyAudio.

For production phone-based use, replace this with Twilio Media Streams or
your telephony provider's audio bridge.
"""

import asyncio
import threading
from queue import Queue

import pyaudio

SAMPLE_RATE = 16000
CHUNK_SIZE = 3200  # 200ms at 16kHz, 16-bit


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
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            output=True,
        )

    def play(self, audio_bytes: bytes):
        self._stream.write(audio_bytes)

    def close(self):
        self._stream.stop_stream()
        self._stream.close()
        self._pa.terminate()
