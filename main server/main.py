from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from psycopg.errors import UniqueViolation
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
import httpx
import base64
import json


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(base_url="http://192.168.0.103:8001", timeout=60) as http:
        app.state.http = http

        await pool.open()
        yield
        await pool.close()

app = FastAPI(lifespan=lifespan)
pool = AsyncConnectionPool(
    conninfo="dbname=postgres user=postgres password=111222035",
    max_size=10,
    min_size=2,
    open=False
)


audios = {}


def get_user_id(req: Request):
    user_id = req.headers.get("id", False)
    if user_id == False:
        raise HTTPException(status_code=400, detail="incorrect usage of endpoint")
    return user_id

async def is_valid_id(req: Request):
    user_id = req.headers.get("id", False)
    if user_id == False:
        raise HTTPException(status_code=400, detail="incorrect usage of endpoint")
    if user_id not in audios.keys():
        raise HTTPException(status_code=403, detail="unknown id")
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT EXISTS(SELECT id from users WHERE id=%s)", (user_id,))
            is_exists = (await cur.fetchone())[0]
            print(is_exists)
            if not is_exists:
                raise HTTPException(status_code=403, detail="unknown id")
    return user_id

async def get_conn():
    async with pool.connection() as conn:
        yield conn

@app.get("/user/register", status_code=201)
async def register_user(user_id=Depends(get_user_id), conn=Depends(get_conn)):
    async with conn.cursor() as cur:
        try:
            await cur.execute("INSERT INTO users(id, reputation) VALUES(%s, %s)", (user_id, 50))
        except UniqueViolation:
            raise HTTPException(status_code=409, detail="user already exists")

@app.get("/audio/start", status_code=201)
def start(user_id=Depends(get_user_id)):
    audios[user_id] = bytearray()

@app.post("/audio/record", status_code=200)
async def record(req: Request, user_id=Depends(is_valid_id)):
    audios[user_id].extend(await req.body())

async def ai_response(user_data, audio, messages, user_id):
    async with app.state.http.stream("POST", "/ai/generate/stream/voice", json={"reputation": user_data["reputation"], "user_audio": base64.b64encode(audio).decode("ascii"), "messages": [item for message in sorted(messages, key=lambda msg: msg["id"]) for item in ({"role": "user", "content": message["user_req"]}, {"role": "assistant", "content": message["ai_resp_text"]})]}) as resp:

        if resp.status_code not in range(200, 300):
            raise HTTPException(status_code=500, detail="server`s error")

        ai_resp_text = ""
        user_req = ""
        reputation = ""
        async for data in resp.aiter_lines():

            if not data:
                continue

            data_json = json.loads(data)
            ai_resp_text += data_json["ai_resp_text"]
            user_req += data_json["user_req"]["content"]
            reputation = data_json["reputation"]
            yield base64.b64decode(data_json["ai_resp_voice"])

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO messages(user_id, user_req, ai_resp_text) VALUES(%s, %s, %s)", (user_id, user_req, ai_resp_text))
                await cur.execute("UPDATE users SET reputation=%s WHERE id=%s", (reputation, user_id))

@app.get("/audio/stop", status_code=200)
async def stop(user_id=Depends(is_valid_id)):
    audio = audios.pop(user_id)

    messages = []
    user_data = []
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, user_req, ai_resp_text FROM messages WHERE user_id=%s ORDER BY id DESC LIMIT 100",
                (user_id,))
            messages = await cur.fetchall()

            await cur.execute("SELECT reputation FROM users WHERE id=%s", (user_id,))
            user_data = await cur.fetchone()

    return StreamingResponse(
        ai_response(user_data, audio, messages, user_id),
        media_type="application/octet-stream"
    )















