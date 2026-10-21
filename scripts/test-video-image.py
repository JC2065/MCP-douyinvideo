"""Offline image smoke test: exercises the decoder, VAD and loaded ASR model."""
import importlib.util
import tempfile
import wave
from pathlib import Path

spec = importlib.util.spec_from_file_location('video', Path(__file__).with_name('video-server.py'))
video = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video)
with tempfile.TemporaryDirectory() as folder:
    audio = Path(folder) / 'silence.wav'
    with wave.open(str(audio), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b'\0\0' * 32000)
    result = video._transcribe_reference(audio)
    assert result['status'] == 'silent', result
    assert video.ASR_MODEL is not None
    print('PASS: offline audio decode, VAD, model initialization and silent result')
