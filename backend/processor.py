import os
from dotenv import load_dotenv
import PyPDF2
from docx import Document
from sentence_transformers import SentenceTransformer
from backend.database import chunks_collection, documents_collection
from bson import ObjectId
from datetime import datetime
from groq import Groq

load_dotenv()

# Load models once
model = SentenceTransformer('all-MiniLM-L6-v2')
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def process_document(file_path, filename, subject, owner_email, chat_id=None):
    """
    Processes a document and indexes it. 
    If chat_id is provided, the chunks are marked as temporary for that specific chat.
    """
    text = ""
    try:
        if filename.endswith(".pdf"):
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        elif filename.endswith(".docx"):
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        print(f"Extracted {len(text)} characters from {filename}")
        if not text.strip():
            print(f"No text extracted from {filename}")
            return None

        # Create Document Entry
        doc_entry = {
            "filename": filename,
            "subject": subject,
            "owner": owner_email,
            "upload_date": datetime.utcnow(),
            "chat_id": chat_id, # If None, it's global (Faculty)
            "is_temporary": chat_id is not None
        }
        doc_id = documents_collection.insert_one(doc_entry).inserted_id

        # Chunking
        chunks = []
        chunk_size = 500
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i+chunk_size]
            embedding = model.encode(chunk_text).tolist()
            chunks.append({
                "document_id": doc_id,
                "text": chunk_text,
                "embedding": embedding,
                "chat_id": chat_id, # Tag chunks for temporary search
                "is_temporary": chat_id is not None
            })
        
        if chunks:
            chunks_collection.insert_many(chunks)
        
        return doc_id
    except Exception as e:
        print(f"Processing Error: {e}")
        return None

def query_system(question, chat_id=None):
    """
    Search both global content AND chat-specific content.
    Filters in Python to avoid MongoDB index requirement on chat_id.
    """
    try:
        query_vector = model.encode(question).tolist()
        
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": 100,
                    "limit": 50
                }
            },
            {
                "$project": {
                    "text": 1,
                    "score": {"$meta": "searchScore"},
                    "document_id": 1,
                    "chat_id": 1
                }
            }
        ]
        
        raw_results = list(chunks_collection.aggregate(pipeline))
        print(f"Vector search returned {len(raw_results)} raw results")
        
        # Filter manually for vector results
        results = []
        for r in raw_results:
            if r.get("chat_id") is None or r.get("chat_id") == chat_id:
                results.append(r)
        
        # STRONG CONSISTENCY FALLBACK:
        # Fetch the most recent chunks for this specific chat directly from the DB
        # This ensures that newly uploaded files are available even before Atlas Search indexes them.
        if chat_id:
            recent_chunks = list(chunks_collection.find({"chat_id": chat_id}).sort("_id", -1).limit(5))
            for rc in recent_chunks:
                # Avoid duplicates
                if not any(str(r.get("_id")) == str(rc.get("_id")) for r in results):
                    results.insert(0, rc) # Prepend to prioritize over global docs
                    
        print(f"Found {len(results)} relevant chunks (including recent uploads) for chat_id: {chat_id}")
        return results[:10] # Return top 10 combined
    except Exception as e:
        print(f"Query Error: {e}")
        return []

def generate_ai_response(question, context, history=None):
    """
    Generates an AI response using Groq based on context and history.
    """
    try:
        messages = [
            {"role": "system", "content": "You are EduNavigator AI, a professional academic assistant. Use the provided context to answer questions accurately. ALWAYS cite your sources by mentioning the filename (e.g., 'As per [filename]...') or using [filename] at the end of sentences. If the context is unhelpful, use your general knowledge but clearly state that it is from general knowledge and not the provided documents."}
        ]
        
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"})
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return f"I'm sorry, I encountered an error while thinking: {str(e)}"
