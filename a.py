from elevenlabs import generate, voices, play, set_api_key
import os
from dotenv import load_dotenv
import shutil
print(shutil.which("ffplay"))

load_dotenv()

# Adding ffmpeg's bin path manually
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin"


# inbuilt elevenlabs function to load the apiKey
set_api_key(os.getenv("ELEVENLABS_API_KEY"))
print(voices())
audio = generate(
    text="Hello! 你好! Hola! नमस्ते! Bonjour! こんにちは! مرحبا! 안녕하세요! Ciao! Cześć! Привіт! வணக்கம்!",
    voice="Aria",
    model="eleven_multilingual_v2"
)

play(audio)
