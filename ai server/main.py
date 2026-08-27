from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import ollama
import whisper
from piper import PiperVoice
import wave
import base64
import json


app = FastAPI()
voice_to_text = whisper.load_model(name="medium", device="cuda")
text_to_voice = PiperVoice.load(model_path="uk_UA-oleksa-high.onnx", config_path="uk_UA-oleksa-high.onnx.json", use_cuda=True)
ratings = {
    "friendly": {
        "description": "Дуже дружнє спілкування з використанням компліментів",
        "value": 10,
    },
    "interesting": {
        "description": "Спілкування на цікаві/незвичні теми",
        "value": 5,
    },
    "normal": {
        "description": "Звичайне, буденне спілкування",
        "value": 1,
    },
    "sad": {
        "description": "Спілкування на сумні теми, легкі підколи",
        "value": -3,
    },
    "rude": {
        "description": "Жорстоке спілкування, можливо, з використанням нецензурних слів",
        "value": -10,
    },
}
deviders = [".", "?", "!"]


async def generate_generator(reputation, messages):
    ollama_resp = ollama.chat(model="gemma4:e2b", messages=messages, stream=True, think=False)
    text = ""
    for chunk in ollama_resp:
        text += chunk.message.content
        if any(devider in text for devider in deviders):
            voice_bytes = bytearray()
            for voice_part in text_to_voice.synthesize(text):
                voice_bytes.extend(voice_part.audio_int16_bytes)
            yield json.dumps({"reputation": reputation, "ai_resp_text": text, "ai_resp_voice": base64.b64encode(voice_bytes).decode("ascii"), "user_req": messages[len(messages)-1]})+"\n"
            print(text)
            text = ""

@app.post("/ai/generate/stream/voice", status_code=200)
async def generate(req: Request):
    print("start")
    data = await req.json()
    reputation = data["reputation"]
    messages = data["messages"]
    user_audio = base64.b64decode(data["user_audio"])

    with wave.open("temp.wav", "wb") as file:
        file.setframerate(16000)
        file.setsampwidth(2)
        file.setnchannels(1)
        file.writeframes(user_audio)

    whisper_resp = voice_to_text.transcribe(audio="temp.wav", language="uk")
    user_text = whisper_resp["text"]
    messages.append({"role": "user", "content": user_text})

    rating = ""
    for i in range(3):
        ollama_rep = ollama.generate(model="gemma4:e2b", system=f'Обери в залежності від настрою цього повідомлення оцінку для нього серед: {", ".join(ratings.keys())}. Не пиши нічного окрім одного з наданих тобі слів, інакше код зламається. При цьому, {", ".join(f'{key} - {value["description"]}' for key, value in ratings.items())}. Також не пиши ніякого форматування, навіть Markdown. Приклад №1: користувач: "Привіт, як справи?", ти: "normal". Приклад №2: користувач: "Привіт, розкажи будь-ласка, як працює штучний інтелект?", ти: "interesting"', prompt=messages[len(messages) - 1]["content"], think=False)
        rating = ollama_rep.response
        if rating in ratings.keys():
            break
        if rating not in ratings.keys() and i == 2:
            rating = "normal"

    reputation += ratings[rating]["value"]
    if reputation < 0:
        reputation = 0
    elif reputation > 100:
        reputation = 100

    system = ""
    if reputation in range(50, 70 + 1):
        system = "Ти дружня нейромережа-хлопчик. Тебе звати Квен. Ти відповідаєш на запитання користувача, не використовуєш ніякого форматування і навіть Markdown. "
    elif reputation in range(70, 90 + 1):
        system = "Ти дружня нейромережа-хлопчик. Тебе звати Квен. Ти відповідаєш на запитання користувача вічливо, з зацікавленістю, не використовуєш ніякого форматування і навіть Markdown. "
    elif reputation in range(90, 100 + 1):
        system = "Ти надзвичайно дружня нейромережа-хлопчик. Тебе звати Квен. Ти відповідаєш на запитання користувача вічливо, з зацікавленістю, задаєш зустрічні запитання, не використовуєш ніякого форматування і навіть Markdown. "
    elif reputation in range(40, 50 + 1):
        system = "Ти нейромережа-хлопчик. Тебе звати Квен. Ти відповідаєш на запитання користувача трохи прохолодно, не використовуєш ніякого форматування і навіть Markdown. "
    elif reputation in range(0, 40 + 1):
        system = "Ти нейромережа-хлопчик. Тебе звати Квен. Ти відповідаєш на запитання користувача дуже холодно, коротко, ти ображений на користувача, не використовуєш ніякого форматування і навіть Markdown. "
    system += f'Використовуй лише ці роздільники тексту: {", ".join(deviders)}'

    messages.insert(0, {"role": "system", "content": system})

    return StreamingResponse(
        generate_generator(reputation, messages),
        media_type="application/x-ndjson"
    )









