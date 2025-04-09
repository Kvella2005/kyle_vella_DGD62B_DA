from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import motor.motor_asyncio
import asyncio

app = FastAPI()

# Connect to Mongo Atlas
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://quinqui8311:ppZDu0aowfnMxcnm@gamedatabse.egeonsl.mongodb.net/?retryWrites=true&w=majority&appName=GameDatabse")
db = client.game_assets_db #get the database you want to insert into

#get the available database names in the cluster for debug purposes
# async def debug_db_names():
#     names = await client.list_database_names()
#     print("Available databases:", names)

# asyncio.create_task(debug_db_names())

#structure of the player score inside the scores collection
class PlayerScore(BaseModel):
    player_name: str
    score: int

@app.get("/")
async def root():
    return {"message": db.name}

@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...)):
    # In a real application, the file should be saved to a storage service
    print(f"Filename: {file.filename} Content: {file.content_type}")
    content = await file.read()
    sprite_doc = {"filename": file.filename, "content": content}
    result = await db.sprites.insert_one(sprite_doc)
    return {"message": "Sprite uploaded", "id": str(result.inserted_id)}

@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    print(f"Filename: {file.filename} Content: {file.content_type}")
    content = await file.read()
    audio_doc = {"filename": file.filename, "content": content}
    result = await db.audio.insert_one(audio_doc)
    return {"message": "Audio file uploaded", "id": str(result.inserted_id)}

@app.post("/player_score")
async def add_score(score: PlayerScore):
    try:
        # Create score document
        score_doc = {
            "player_name": score.player_name,
            "score": score.score
        }
        
        # Insert with timeout
        result = await asyncio.wait_for(
            db.scores.insert_one(score_doc),
            timeout=30.0  # 30 second timeout
        )
        
        return {"message": "Score recorded", "id": str(result.inserted_id)}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Database operation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))