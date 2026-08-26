from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import ollama
import whisper
from piper import PiperVoice
import wave


app = FastAPI()
voice_to_text = whisper.load_model(name="medium", device="cuda")
text_to_voice = PiperVoice.load(model_path="uk_UA-oleksa-high.onnx", config_path="uk_UA-oleksa-high.onnx.json", use_cuda=True)

async def generate_generator(text):
    ollama_resp = ollama.chat()

@app.post("/ai/generate/stream/voice", status_code=200)
async def generate(req: Request):
    audio = await req.body()

    with wave.open("temp.wav", "wb") as file:
        file.setframerate(16000)
        file.setsampwidth(2)
        file.setnchannels(1)
        file.writeframes(audio)

    whisper_resp = voice_to_text.transcribe(audio="temp.wav", language="uk")
    user_text = whisper_resp["text"]

    return StreamingResponse(
        generate_generator(user_text),
        media_type="application/octet-stream"
    )









