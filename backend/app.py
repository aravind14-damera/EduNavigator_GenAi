import os
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, StreamingResponse
import io
from backend.database import users_collection, documents_collection, chunks_collection, query_logs_collection, chats_collection, fs
from backend.auth import get_password_hash, verify_password, create_access_token, get_current_user, check_admin
from backend.processor import process_document, query_system, generate_ai_response
from bson import ObjectId
import shutil
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

load_dotenv()

app = FastAPI()

# Permissive CORS to allow separate frontend and backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# --- AUTH ---
@app.post("/register")
async def register(user: dict):
    if users_collection.find_one({"email": user['email']}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user['password'])
    users_collection.insert_one({"email": user['email'], "password": hashed_password, "role": user.get('role', 'student')})
    return {"message": "User registered successfully"}

@app.post("/login")
async def login(user: dict):
    try:
        if not user.get('email') or not user.get('password'):
            raise HTTPException(status_code=400, detail="Email and password required")
        
        db_user = users_collection.find_one({"email": user['email']})
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not db_user.get('password'):
            raise HTTPException(status_code=401, detail="Invalid user data - no password found")
        
        if not verify_password(user['password'], db_user['password']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = create_access_token(data={"sub": user['email'], "role": db_user.get('role', 'user')})
        return {"access_token": access_token, "token_type": "bearer", "role": db_user.get('role', 'user')}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

# --- CHATS ---
@app.post("/chats")
async def create_chat(data: dict, user = Depends(get_current_user)):
    chat_entry = {
        "user_email": user['email'],
        "title": data.get("title", "New Academic Chat"),
        "messages": [],
        "created_at": datetime.utcnow()
    }
    chat_id = chats_collection.insert_one(chat_entry).inserted_id
    return {"chat_id": str(chat_id)}

@app.get("/chats")
async def get_user_chats(user = Depends(get_current_user)):
    chats = list(chats_collection.find({"user_email": user['email']}).sort("created_at", -1))
    for chat in chats:
        chat["_id"] = str(chat["_id"])
        if "created_at" in chat and chat["created_at"]:
            chat["created_at"] = chat["created_at"].isoformat()
    return chats

@app.get("/chat/{chat_id}")
async def get_chat_history(chat_id: str, user = Depends(get_current_user)):
    chat = chats_collection.find_one({"_id": ObjectId(chat_id), "user_email": user['email']})
    if not chat: raise HTTPException(status_code=404, detail="Chat not found")
    chat["_id"] = str(chat["_id"])
    return chat

@app.delete("/chat/{chat_id}")
async def delete_chat(chat_id: str, user = Depends(get_current_user)):
    chats_collection.delete_one({"_id": ObjectId(chat_id), "user_email": user['email']})
    return {"message": "Chat deleted"}

# --- MESSAGING ---
@app.post("/chat/{chat_id}/message")
async def send_chat_message(
    chat_id: str,
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
    user = Depends(get_current_user)
):
    chat = chats_collection.find_one({"_id": ObjectId(chat_id), "user_email": user['email']})
    if not chat: raise HTTPException(status_code=404, detail="Chat not found")

    if file:
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file.filename)
        with open(temp_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        
        # Process and get ID
        doc_id = process_document(temp_path, file.filename, "Session Upload", user['email'], chat_id=chat_id)
        
        if doc_id:
            # Save original file to GridFS
            try:
                with open(temp_path, "rb") as f:
                    file_id = fs.put(f, filename=file.filename)
                    documents_collection.update_one({"_id": doc_id}, {"$set": {"file_id": file_id}})
                print(f"Stored {file.filename} in GridFS with ID: {file_id}")
            except Exception as e:
                print(f"GridFS Upload Error: {e}")
        
        os.remove(temp_path)

    results = query_system(message, chat_id=chat_id)
    
    context_parts = []
    for r in results:
        doc = documents_collection.find_one({"_id": r['document_id']})
        filename = doc['filename'] if doc else "Unknown Source"
        context_parts.append(f"--- SOURCE: {filename} ---\n{r['text']}")
    
    context = "\n\n".join(context_parts) if context_parts else "No direct academic context found."
    
    # Format history for LLM
    formatted_history = []
    for msg in chat["messages"][-5:]:
        formatted_history.append({"role": "user" if msg["role"] == "user" else "assistant", "content": msg["content"]})

    # Generate AI Response
    ai_answer = generate_ai_response(message, context, formatted_history)

    # Save user message and AI response immediately
    timestamp = datetime.utcnow()
    chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {"$push": {"messages": {
            "$each": [
                {"role": "user", "content": message, "timestamp": timestamp},
                {"role": "ai", "content": ai_answer, "timestamp": timestamp}
            ]
        }}}
    )

    if len(chat["messages"]) == 0:
        chats_collection.update_one({"_id": ObjectId(chat_id)}, {"$set": {"title": message[:30] + "..."}})

    # Log to global history for tracking (if needed)
    query_logs_collection.insert_one({
        "user_email": user['email'],
        "question": message,
        "answer": ai_answer,
        "timestamp": timestamp,
        "chat_id": chat_id
    })

    for r in results:
        r["_id"] = str(r["_id"])
        doc = documents_collection.find_one({"_id": r['document_id']})
        r["filename"] = doc['filename'] if doc else "Unknown"
        if "document_id" in r:
            r["document_id"] = str(r["document_id"])
            
    return {"answer": ai_answer, "context": context, "sources": results}

@app.post("/chat/{chat_id}/save_ai_response")
async def save_ai_response(chat_id: str, answer: str = Form(...), user = Depends(get_current_user)):
    chats_collection.update_one(
        {"_id": ObjectId(chat_id)},
        {"$push": {"messages": {"role": "ai", "content": answer, "timestamp": datetime.utcnow()}}}
    )
    return {"status": "saved"}


# --- FACULTY & HISTORY ---
@app.get("/documents")
async def get_documents(user = Depends(get_current_user)):
    """
    Returns documents relevant to the user.
    - Students see Global (chat_id: None) AND their current session docs (chat_id logic handled in search).
    - For the LIST, we show Global docs and any session-specific docs if requested.
    """
    # For now, show all Global documents in the library
    docs = list(documents_collection.find({"chat_id": None}).sort("upload_date", -1))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        if "file_id" in doc: doc["file_id"] = str(doc["file_id"])
        if "chat_id" in doc and doc["chat_id"]: doc["chat_id"] = str(doc["chat_id"])
        if "upload_date" in doc and doc["upload_date"]: doc["upload_date"] = doc["upload_date"].isoformat()
    return docs

@app.post("/upload")
async def upload_global(file: UploadFile = File(...), subject: str = Form(...), admin = Depends(check_admin)):
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    with open(temp_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    
    doc_id = process_document(temp_path, file.filename, subject, admin['email'], chat_id=None)
    
    if doc_id:
        try:
            with open(temp_path, "rb") as f:
                file_id = fs.put(f, filename=file.filename)
                documents_collection.update_one({"_id": doc_id}, {"$set": {"file_id": file_id}})
            print(f"Global Document {file.filename} stored in GridFS")
        except Exception as e:
            print(f"GridFS Global Upload Error: {e}")
            
    os.remove(temp_path)
    return {"message": "Global resource added"}

@app.get("/documents/{doc_id}/view")
async def view_document(doc_id: str, query_token: Optional[str] = None, user = Depends(get_current_user)):
    doc = documents_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc or "file_id" not in doc:
        raise HTTPException(status_code=404, detail="Document or file content not found")
    
    try:
        grid_file = fs.get(doc["file_id"])
        return StreamingResponse(io.BytesIO(grid_file.read()), media_type="application/octet-stream", headers={
            "Content-Disposition": f'attachment; filename="{doc["filename"]}"'
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error retrieving file: {str(e)}")

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, admin = Depends(check_admin)):
    doc = documents_collection.find_one({"_id": ObjectId(doc_id)})
    if doc and "file_id" in doc:
        try:
            fs.delete(doc["file_id"])
        except:
            pass
            
    documents_collection.delete_one({"_id": ObjectId(doc_id)})
    chunks_collection.delete_many({"document_id": ObjectId(doc_id)})
    return {"message": "Document deleted from library and database"}

@app.get("/history")
async def get_history(user = Depends(get_current_user)):
    logs = list(query_logs_collection.find({"user_email": user['email']}).sort("timestamp", -1))
    for log in logs:
        log["_id"] = str(log["_id"])
        if "chat_id" in log and log["chat_id"]: log["chat_id"] = str(log["chat_id"])
        if "timestamp" in log and log["timestamp"]: log["timestamp"] = log["timestamp"].isoformat()
    return logs
