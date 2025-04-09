from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv
import motor.motor_asyncio
import re
import asyncio
import os
from typing import List, Optional
from bson.objectid import ObjectId

app = FastAPI()

#get the .env file which provides the connection string with the read/write user access
load_dotenv()

# Connect to Mongo Atlas with read/write access
connectionString = os.environ.get("MONGODBSTRING")

# Connect to Mongo Atlas
client = motor.motor_asyncio.AsyncIOMotorClient(connectionString)

#for debug purposes
#client = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://quinqui8311:ppZDu0aowfnMxcnm@gamedatabse.egeonsl.mongodb.net/?retryWrites=true&w=majority&appName=GameDatabse")


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

#its job is to check the names and strings, and
#removes characters from the name to prevent unintended 
#queries from being executed in mongodb
def prevent_nosql_injection(data: any) -> any:
    # if the parameter is dictionary, get one of the items in the dicionary and call the funciton again
    if isinstance(data, dict):
        return {k: prevent_nosql_injection(v) for k, v in data.items()}
    
    # if the parameter is list, get one of the items in the list and call the funciton again
    elif isinstance(data, list):
        return [prevent_nosql_injection(item) for item in data]
    
    # if the parameter is string, remove characters that are vulnerable to sql injections
    # and return sanitzed name
    elif isinstance(data, str):
        # Remove MongoDB operators and special characters
        sanitized = re.sub(r'[${}()\[\]]', '', data)
        # Remove JavaScript execution patterns
        sanitized = re.sub(r'(javascript|exec|eval|function)', '', sanitized, flags=re.IGNORECASE)
        return sanitized
    
    # Don't check on other data types
    else:
        return data

#when initialized, return "message" + the database thats being used
@app.get("/")
async def root():
    return {"message": db.name}
    
# PUT Methods

@app.put("/player_score/update/{score_id}")
async def update_score(score_id: str, score: PlayerScore):
    try:
        # Check if the score exists with id
        existing_score = await db.scores.find_one({"_id": ObjectId(score_id)})
        if not existing_score:
            raise HTTPException(status_code=404, detail="Score not found")
        
        # Update the score
        result = await db.scores.update_one(
            {"_id": ObjectId(score_id)},
            {"$set": score.dict()}
        )
        
        #if the score is modified, then display this message
        if result.modified_count:
            return {"message": "Score updated successfully"}
        
        #if there is no changes, then display this message
        return {"message": "No changes applied"}
    #else, if there is trouble connecting to the database etc., then display message
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating score: {str(e)}")

#update the sprite details on sprite collection
@app.put("/sprites/update/{sprite_id}")
async def update_sprite(sprite_id: str, file: UploadFile = File(...)):
    try:
        # Check if the sprite exists
        existing_sprite = await db.sprites.find_one({"_id": ObjectId(sprite_id)})

        #if the id does not exist, then it will display this messaage
        if not existing_sprite:
            raise HTTPException(status_code=404, detail="Sprite not found")
        
        # if the file is not image, then it will display this message
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read new file content
        content = await file.read()
        
        # Sanitize filename to remove characters vulnerable to sql injection
        safe_filename = prevent_nosql_injection(file.filename)
        
        # Create filter and update as separate variables
        filter_query = {"_id": ObjectId(sprite_id)}
        update_query = {
            "$set": {
                "filename": safe_filename,
                "content": content,
                "content_type": file.content_type
            }
        }
        
        # Pass both arguments separately to update_one
        result = await db.sprites.update_one(filter_query, update_query)
        
        #if the data is modified, then it will display this message
        if result.modified_count:
            return {"message": "Sprite updated successfully"}
        return {"message": "No changes applied"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating sprite: {str(e)}")

#update the audio details on audio collection
@app.put("/audio/update/{audio_id}")
async def update_audio(audio_id: str, file: UploadFile = File(...)):
    try:
        # Check if the audio file exists
        existing_audio = await db.audio.find_one({"_id": ObjectId(audio_id)})
        if not existing_audio:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # if the file is not an audio, then it will display this message
        # and not update the audio
        if not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read new file content
        content = await file.read()

        # Sanitize filename
        safe_filename = prevent_nosql_injection(file.filename)
        
        # Create filter and update as separate variables
        filter_query = {"_id": ObjectId(audio_id)}
        update_query = {
            "$set": {
                "filename": safe_filename,
                "content": content,
                "content_type": file.content_type
            }
        }
        
        # Update the selected audio (with id) with modified details
        result = await db.audio.update_one(filter_query, update_query)
        
        #if the audio is successfully updated, then it will display this message
        if result.modified_count:
            return {"message": "Audio file updated successfully"}
        return {"message": "No changes applied"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating audio file: {str(e)}")
    
# DELETE Methods

# Add ability to delete files and scores
@app.delete("/sprites/del/{sprite_id}")
async def delete_sprite(sprite_id: str):
    try:
        #find the id in the sprites collection and try to delete it
        result = await db.sprites.delete_one({"_id": ObjectId(sprite_id)})

        #if it is deleted, then display this message
        if result.deleted_count:
            return {"message": "Sprite deleted successfully"}
        #if the sprite is not found, then display this error message
        raise HTTPException(status_code=404, detail="Sprite not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid sprite ID: {str(e)}")

@app.delete("/audio/del/{audio_id}")
async def delete_audio(audio_id: str):
    try:
        # find the id in the audio collection and try to delete it
        result = await db.audio.delete_one({"_id": ObjectId(audio_id)})

        #if it is deleted, then display this message
        if result.deleted_count:
            return {"message": "Audio file deleted successfully"}
        #if it is not found, then display this error message
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid audio ID: {str(e)}")

@app.delete("/player_score/del/{score_id}")
async def delete_score(score_id: str):
    try:
        # find the id in the scores collection and try to delete it
        result = await db.scores.delete_one({"_id": ObjectId(score_id)})

        #if it is deleted, then display this message
        if result.deleted_count:
            return {"message": "Score deleted successfully"}
        #if it is not found, then display this error message
        raise HTTPException(status_code=404, detail="Score not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid score ID: {str(e)}")
    
# POST Methods

#uploading image file 
@app.post("/upload_sprite")
async def upload_sprite(file: UploadFile = File(...)):
    #if the file is not an image, return an error
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    #read the file contents, and insert the metadata (file name and content)
    print(f"Filename: {file.filename} Content: {file.content_type}")
    content = await file.read()
    sprite_doc = {"filename": file.filename, "content": content, "content_type": file.content_type}
    sprite_doc_sanatised = prevent_nosql_injection(sprite_doc)
    result = await db.sprites.insert_one(sprite_doc_sanatised)
    return {"message": "Sprite uploaded", "id": str(result.inserted_id)}

#upload audio in audio collection
@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    #if the file is not audio, then dont insert it and return error
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")

    #print data thats going to be inserted inside audio collection   
    print(f"Filename: {file.filename} Content: {file.content_type}")

    #read file to get metadata and insert it into audio collection 
    content = await file.read()

    #create the data document to be inserted inside collection
    audio_doc = {"filename": file.filename, "content": content, "content_type": file.content_type}

    audio_doc_sanatised = prevent_nosql_injection(audio_doc)

    #wait for it to be inserted inside collection
    result = await db.audio.insert_one(audio_doc_sanatised)

    #print its object id on postman
    return {"message": "Audio file uploaded", "id": str(result.inserted_id)}

#this will insert inputted user name and score in scores collections
@app.post("/player_score")
async def add_score(score: PlayerScore):
    #it will turn the inserted data into dictionary
    score_doc = score.dict()

    score_doc_sanatised = prevent_nosql_injection(score_doc)

    #it will insert a playerscore modal into dictionary
    result = await db.scores.insert_one(score_doc_sanatised)

    #it will return a object id for the inserted data
    return {"message": "Score recorded", "id": str(result.inserted_id)}
    
# GET Methods

#get sprite by object id
@app.get("/sprites/{sprite_id}")
async def get_sprite_by_id(sprite_id: str):
    try:
        #find the sprite with object id
        sprite = await db.sprites.find_one({"_id": ObjectId(sprite_id)})
        if sprite:
            
            return {
                "id": str(sprite["_id"]), # get the object id
                "filename": sprite["filename"], #get the file name 
                "content_type": sprite.get("content_type", "image/png") # this is to get the filetype
                # Note: content is not returned directly as it's binary data
                # In a real application, you might return a URL to access the content
            }
        #if it is not found, the display this error message
        raise HTTPException(status_code=404, detail="Sprite not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid sprite ID: {str(e)}")

@app.get("/player_score/{score_id}", response_model=ScoreResponse)
async def get_score_by_id(score_id: str):
    try:
        #find the scores with object id
        score = await db.scores.find_one({"_id": ObjectId(score_id)})
        if score:
            return {
                "id": str(score["_id"]), # get the object id
                "player_name": score["player_name"], #get the file name 
                "score": score["score"] # this is to get the score of the player
            }
        #if the id is not found in the scores collection, then it will display this error message
        raise HTTPException(status_code=404, detail="Score not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid score ID: {str(e)}")
    
#this will search audio by id in audio collections
@app.get("/audio/{audio_id}")
async def get_audio_by_id(audio_id: str):
    #try searching by its object od
    try:
        #find audio by its object id
        audio = await db.audio.find_one({"_id": ObjectId(audio_id)})

        #if its found then display details about the found data
        if audio:
            
            return {
                "id": str(audio["_id"]),
                "filename": audio["filename"], #convert it to base64 to be displayed
                "content_type": audio.get("content_type", "audio/mpeg") #display file type
            }
        #if id is not found, then it will display this message
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid audio ID: {str(e)}")