from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from pydantic import BaseModel
import motor.motor_asyncio
import asyncio
from typing import List, Optional
from bson.objectid import ObjectId

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

# Structure for file responses without the binary content
class FileMetadata(BaseModel):
    id: str
    filename: str
    
# Structure for scores response
class ScoreResponse(BaseModel):
    id: str
    player_name: str
    score: int

@app.get("/")
async def root():
    return {"message": db.name}

@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...)):
    # Validate file type (optional security measure)
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # In a real application, the file should be saved to a storage service
    print(f"Filename: {file.filename} Content: {file.content_type}")
    content = await file.read()
    sprite_doc = {"filename": file.filename, "content": content, "content_type": file.content_type}
    result = await db.sprites.insert_one(sprite_doc)
    return {"message": "Sprite uploaded", "id": str(result.inserted_id)}

@app.get("/sprites", response_model=List[FileMetadata])
async def search_sprites(filename: Optional[str] = Query(None, description="Search sprites by filename")):
    """
    Search for sprites by filename. If no filename is provided, returns all sprites.
    """
    query = {}
    if filename:
        # Case-insensitive search using regex
        query = {"filename": {"$regex": filename, "$options": "i"}}
    
    sprites = []
    async for sprite in db.sprites.find(query, {"_id": 1, "filename": 1}):
        sprites.append({
            "id": str(sprite["_id"]),
            "filename": sprite["filename"]
        })
    
    return sprites

@app.get("/sprites/{sprite_id}")
async def get_sprite_by_id(sprite_id: str):
    """
    Get a specific sprite by its ID
    """
    try:
        sprite = await db.sprites.find_one({"_id": ObjectId(sprite_id)})
        if sprite:
            # Convert binary data to a response that can be rendered
            return {
                "id": str(sprite["_id"]),
                "filename": sprite["filename"],
                "content_type": sprite.get("content_type", "image/png")
                # Note: content is not returned directly as it's binary data
                # In a real application, you might return a URL to access the content
            }
        raise HTTPException(status_code=404, detail="Sprite not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid sprite ID: {str(e)}")

@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    # Validate file type (optional security measure)
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
        
    print(f"Filename: {file.filename} Content: {file.content_type}")
    content = await file.read()
    audio_doc = {"filename": file.filename, "content": content, "content_type": file.content_type}
    result = await db.audio.insert_one(audio_doc)
    return {"message": "Audio file uploaded", "id": str(result.inserted_id)}

@app.get("/audio", response_model=List[FileMetadata])
async def search_audio(filename: Optional[str] = Query(None, description="Search audio files by filename")):
    """
    Search for audio files by filename. If no filename is provided, returns all audio files.
    """
    query = {}
    if filename:
        # Case-insensitive search using regex
        query = {"filename": {"$regex": filename, "$options": "i"}}
    
    audio_files = []
    async for audio in db.audio.find(query, {"_id": 1, "filename": 1}):
        audio_files.append({
            "id": str(audio["_id"]),
            "filename": audio["filename"]
        })
    
    return audio_files

@app.get("/audio/{audio_id}")
async def get_audio_by_id(audio_id: str):
    """
    Get a specific audio file by its ID
    """
    try:
        audio = await db.audio.find_one({"_id": ObjectId(audio_id)})
        if audio:
            # Convert binary data to a response that can be rendered
            return {
                "id": str(audio["_id"]),
                "filename": audio["filename"],
                "content_type": audio.get("content_type", "audio/mpeg")
                # Note: content is not returned directly as it's binary data
                # In a real application, you might return a URL to access the content
            }
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid audio ID: {str(e)}")

@app.post("/player_score")
async def add_score(score: PlayerScore):
    score_doc = score.dict()
    result = await db.scores.insert_one(score_doc)
    return {"message": "Score recorded", "id": str(result.inserted_id)}

@app.get("/player_scores", response_model=List[ScoreResponse])
async def search_scores(player_name: Optional[str] = Query(None, description="Search scores by player name")):
    """
    Search for player scores by player name. If no name is provided, returns all scores.
    """
    query = {}
    if player_name:
        # Case-insensitive search using regex
        query = {"player_name": {"$regex": player_name, "$options": "i"}}
    
    scores = []
    async for score in db.scores.find(query):
        scores.append({
            "id": str(score["_id"]),
            "player_name": score["player_name"],
            "score": score["score"]
        })
    
    # Sort scores in descending order (highest first)
    scores.sort(key=lambda x: x["score"], reverse=True)
    
    return scores

@app.get("/player_scores/{score_id}", response_model=ScoreResponse)
async def get_score_by_id(score_id: str):
    """
    Get a specific score by its ID
    """
    try:
        score = await db.scores.find_one({"_id": ObjectId(score_id)})
        if score:
            return {
                "id": str(score["_id"]),
                "player_name": score["player_name"],
                "score": score["score"]
            }
        raise HTTPException(status_code=404, detail="Score not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid score ID: {str(e)}")

# Add a route to get the top scores
@app.get("/top_scores/{limit}", response_model=List[ScoreResponse])
async def get_top_scores(limit: int = 10):
    """
    Get the top scores, limited by the provided number
    """
    if limit <= 0:
        raise HTTPException(status_code=400, detail="Limit must be a positive integer")
    
    scores = []
    cursor = db.scores.find().sort("score", -1).limit(limit)
    async for score in cursor:
        scores.append({
            "id": str(score["_id"]),
            "player_name": score["player_name"],
            "score": score["score"]
        })
    
    return scores

# Add ability to delete files and scores
@app.delete("/sprites/{sprite_id}")
async def delete_sprite(sprite_id: str):
    """
    Delete a sprite by its ID
    """
    try:
        result = await db.sprites.delete_one({"_id": ObjectId(sprite_id)})
        if result.deleted_count:
            return {"message": "Sprite deleted successfully"}
        raise HTTPException(status_code=404, detail="Sprite not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid sprite ID: {str(e)}")

@app.delete("/audio/{audio_id}")
async def delete_audio(audio_id: str):
    """
    Delete an audio file by its ID
    """
    try:
        result = await db.audio.delete_one({"_id": ObjectId(audio_id)})
        if result.deleted_count:
            return {"message": "Audio file deleted successfully"}
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid audio ID: {str(e)}")

@app.delete("/player_scores/{score_id}")
async def delete_score(score_id: str):
    """
    Delete a player score by its ID
    """
    try:
        result = await db.scores.delete_one({"_id": ObjectId(score_id)})
        if result.deleted_count:
            return {"message": "Score deleted successfully"}
        raise HTTPException(status_code=404, detail="Score not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid score ID: {str(e)}")