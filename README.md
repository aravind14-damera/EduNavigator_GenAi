# 🏛️ EduNavigator AI: SRMAP Conversational Academic Portal

EduNavigator AI is a premium, next-generation conversational academic assistant designed specifically for **SRM University AP**. It transforms traditional academic search into a robust AI-driven workspace where students and faculty can interact with institutional knowledge, research papers, and course materials through a professional chat interface.

---

## 🚀 Key Features

### 💬 Conversational AI Workspace
*   **Persistent Chat Sessions**: Create, rename, and manage multiple academic discussions.
*   **Full Context Memory**: Powered by Groq's Grok AI, the assistant remembers the entire conversation thread.
*   **Institutional Intelligence**: Queries are grounded in the SRMAP Knowledge Base (Faculty uploads) and temporary session documents (Student uploads).

### 🔍 Hybrid Smart Search
*   **Vector Search Engine**: Uses `SentenceTransformers` for context-aware semantic retrieval.
*   **Dual-Scope Indexing**: Simultaneously searches Global Faculty Resources and session-specific temporary attachments.
*   **Source Citations**: AI responses include direct links to relevant document chunks.

### 🏛️ Premium Institutional Branding
*   **Fazal Style Aesthetics**: High-end UI with Navy & Gold SRMAP branding, glassmorphism effects, and dynamic animations.
*   **Dynamic Backgrounds**: Responsive campus imagery across Login, Registration, and Landing pages.

---

## 🛠️ Tech Stack

*   **Backend**: Python 3.10+, FastAPI, Uvicorn
*   **AI Engine**: Groq API - LLaMA-3.3-70B Versatile (`llama-3.3-70b-versatile`)
*   **Embedding Model**: HuggingFace SentenceTransformers (`all-MiniLM-L6-v2`, 384-dim vectors)
*   **Vector Search**: MongoDB Atlas Vector Search Engine
*   **Database**: MongoDB Atlas (M0-Free to M2 tier)
*   **File Storage**: GridFS for document persistence
*   **Frontend**: Native HTML5, CSS3 (Vanilla), JavaScript (ES6+)
*   **Security**: JWT (JSON Web Tokens), BCrypt Password Hashing, Argon2 Support
*   **Document Processing**: PyPDF2, python-docx for PDF, DOCX, and plain text parsing

---

## ⚙️ Technical Specifications & Configuration

### 📄 Document Processing & Chunking
| Parameter | Value | Description |
|-----------|-------|-------------|
| **Chunk Size** | 500 characters | Documents are split into 500-char overlapping chunks for vector indexing |
| **Overlap Strategy** | Sequential (no overlap) | Chunks are created incrementally; context continuity ensured by hybrid search |
| **Supported Formats** | PDF, DOCX, TXT | Plain text extraction from all formats using PyPDF2 and python-docx |
| **Max File Size** | Depends on MongoDB tier | Typically 16MB for standard Atlas clusters (via GridFS) |
| **Text Extraction** | Per-page (PDF), Per-paragraph (DOCX) | Maintains document structure during parsing |

### 🧠 Embedding & Vector Search
| Component | Specification | Details |
|-----------|--------------|---------|
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` | Lightweight 384-dimensional vectors, optimized for semantic search |
| **Vector Index Name** | `vector_index` | Must be created manually in MongoDB Atlas UI with cosine similarity |
| **Search Candidates** | 100 | Vector search examines 100 candidate chunks before ranking |
| **Top-K Results** | 10 (combined) | Returns top 10 chunks: 5 global + 5 chat-specific (prioritized) |
| **Similarity Metric** | Cosine Similarity | Default MongoDB Atlas vector search metric |

### 🤖 AI Generation Parameters
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Model** | `llama-3.3-70b-versatile` | State-of-the-art LLaMA 3.3 with 70B parameters, best for academic context |
| **Temperature** | 0.7 | Balanced between creativity (0.5-0.7) and accuracy (0.0-0.3) |
| **Max Tokens** | 1024 | Sufficient for detailed academic answers without excessive latency |
| **System Prompt** | Academic Assistant Persona | Enforces source citation: "As per [filename]..." or "[filename]" |
| **Chat History** | Full Conversation Memory | All previous messages in current chat thread included in context |

### 📊 Search Architecture
- **Dual-Scope Indexing**:
  - **Global Index**: Faculty-uploaded permanent documents (accessible to all users)
  - **Temporary Index**: Session-specific student uploads (chat_id tagged, auto-cleanup available)
  
- **Hybrid Query Strategy**:
  - Vector search on embedding similarity
  - Recent uploads (5 most recent chunks) prepended for strong consistency
  - Manual Python filtering to avoid MongoDB index constraints

### 🔐 Security & Authentication
| Feature | Implementation |
|---------|-----------------|
| **Password Hashing** | BCrypt (primary) + Argon2 (fallback) |
| **JWT Tokens** | HS256 algorithm, includes email + role in payload |
| **Session Management** | Stateless JWT, verified on each API call |
| **CORS Policy** | Permissive (`allow_origins=["*"]`) for local development |
| **Role-Based Access** | `admin` (faculty) vs `student` role enforcement |

### 📦 Database Schema

#### Users Collection
```json
{
  "email": "student@example.com",
  "password": "bcrypt_hashed_password",
  "role": "student" | "admin"
}
```

#### Documents Collection
```json
{
  "filename": "ML_Basics.pdf",
  "subject": "Machine Learning",
  "owner": "faculty@srmap.edu",
  "upload_date": "2024-01-15T10:30:00Z",
  "chat_id": null | "chat_object_id",
  "is_temporary": false | true
}
```

#### Chunks Collection
```json
{
  "document_id": "ObjectId",
  "text": "chunk_text_up_to_500_chars",
  "embedding": [0.123, 0.456, ...384_dimensions],
  "chat_id": null | "chat_object_id",
  "is_temporary": false | true
}
```

#### Chats Collection
```json
{
  "user_email": "student@example.com",
  "title": "Organic Chemistry Q&A",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
*   Python 3.10+
*   MongoDB Atlas Account
*   Groq API Key (optional for direct backend calls)

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
MONGO_URI=your_mongodb_atlas_uri
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_random_secret_key
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Seed Database (Optional)
Create test accounts for development:
```powershell
python seed_db.py
```
This creates:
- Admin: `admin@test.com` / `admin123`
- Student: `student@test.com` / `student123`

---

## 🏃‍♂️ How to Run

### Step 1: Start the AI Backend
```powershell
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```
*Wait for the `--- EDUNAVIGATOR BACKEND STARTING ---` message.*

### Step 2: Open the Portal
Simply open the `frontend/index.html` file in your preferred browser (**Firefox recommended** for the best experience in separate mode).

---

## 📂 Project Structure
```text
GENAI/
├── backend/            # FastAPI Logic & AI Processing
│   ├── app.py          # Main API Server (Auth, Chats, Messaging, Uploads)
│   ├── auth.py         # JWT Authentication & Security
│   ├── database.py     # MongoDB Connection & Collections
│   └── processor.py    # Document Chunking & Vector Search
├── frontend/           # Premium UI Files
│   ├── index.html      # Landing Page
│   ├── login.html      # Portal Access
│   ├── register.html   # User Registration
│   ├── dashboard.html  # Student Workspace
│   ├── admin.html      # Faculty Dashboard
│   ├── history.html    # Query History
│   └── styles.css      # Global Stylesheet
├── assets/             # Static Assets
│   ├── logo.png        # SRMAP Logo
│   ├── home page image.jpg # Landing Background
│   └── ...             # Additional Images
├── temp/               # Temporary File Storage
├── check_data.py       # Database Audit Script
├── debug_chat.py       # Chat Debugging Tool
├── seed_db.py          # Test Account Seeder
├── model_list.txt      # AI Model Configuration
├── PROJECT_REPORT.md   # Detailed Project Documentation
├── requirements.txt    # Python Dependencies
└── README.md           # This File
```

---

## 🔌 API Endpoints

### Authentication
- `POST /register` - User registration (email, password, role)
- `POST /login` - User login (returns JWT token with 24hr expiry)

### Chat Management
- `POST /chats` - Create new chat session (returns chat_id)
- `GET /chats` - List user's chat sessions (sorted by creation date, newest first)
- `GET /chat/{chat_id}` - Get full chat history with all messages
- `DELETE /chat/{chat_id}` - Delete chat session (removes all associated temporary chunks)

### Messaging & Search
- `POST /chat/{chat_id}/message` - Send message (supports optional file upload)
  - Triggers vector search + recent uploads lookup
  - Returns AI response with source citations
  - File stored in GridFS if provided
- `POST /chat/{chat_id}/save_ai_response` - Persist AI response to chat thread

### Document Management
- `GET /documents` - List global faculty documents (accessible to all users)
- `POST /upload` - Upload global document (admin/faculty only)
  - Automatically chunked (500 chars) and indexed
  - Vector index updated asynchronously
- `DELETE /documents/{doc_id}` - Delete document and associated chunks

### Query History
- `GET /history` - Get user's query logs with timestamps

### Response Format
All successful responses return JSON:
```json
{
  "message": "Operation completed",
  "data": {}
}
```

Error responses return:
```json
{
  "detail": "Error message",
  "status_code": 400|401|404|500
}
```

---

## 🗄️ Database Schema

### Collections Overview
| Collection | Purpose | Indexes | TTL |
|-----------|---------|---------|-----|
| **users** | User accounts (auth) | `email` (unique) | None |
| **documents** | Document metadata | `chat_id`, `owner` | Optional for temporary |
| **chunks** | Text + embeddings (searchable) | `document_id`, `chat_id`, `vector_index` | Optional cleanup |
| **chats** | Chat sessions & history | `user_email`, `created_at` | None |
| **query_logs** | Query analytics | `user_email`, `timestamp` | 30 days (optional) |

### Detailed Schemas

#### Users Collection
```json
{
  "_id": ObjectId,
  "email": "student@srmap.edu",
  "password": "bcrypt_hash_...",
  "role": "student|admin",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Documents Collection
```json
{
  "_id": ObjectId,
  "filename": "ML_Basics.pdf",
  "subject": "Machine Learning",
  "owner": "faculty@srmap.edu",
  "upload_date": "2024-01-15T10:30:00Z",
  "chat_id": null,  // null=global, ObjectId=temporary
  "is_temporary": false,
  "file_id": "GridFS_ObjectId",  // Reference to GridFS storage
  "file_size_bytes": 2048000,
  "chunk_count": 142
}
```

#### Chunks Collection (Vector-Indexed)
```json
{
  "_id": ObjectId,
  "document_id": ObjectId,
  "text": "The machine learning process involves...",  // 500 chars max
  "embedding": [0.123, 0.456, ..., 0.789],  // 384-dimensional vector
  "chat_id": null,  // null=global, ObjectId=temporary
  "is_temporary": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Chats Collection
```json
{
  "_id": ObjectId,
  "user_email": "student@srmap.edu",
  "title": "Organic Chemistry Discussion",
  "messages": [
    {
      "role": "user",
      "content": "What is molecular bonding?",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Molecular bonding is...",
      "timestamp": "2024-01-15T10:31:00Z"
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "document_uploads": ["doc_id_1", "doc_id_2"]  // References to uploaded files
}
```

#### Query Logs Collection
```json
{
  "_id": ObjectId,
  "user_email": "student@srmap.edu",
  "query": "What is photosynthesis?",
  "response_tokens": 256,
  "search_results_count": 5,
  "execution_time_ms": 1200,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Vector Index Configuration (MongoDB Atlas)
Must be created manually in Atlas UI:
```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "similarity": "cosine",
      "dimensions": 384
    }
  ],
  "vectorize": false
}
```

---

## 🛠️ Utility Scripts

### Database Audit
```powershell
python check_data.py
```
Audits the database for document/chunk counts and validates embeddings.

### Debug Chat
```powershell
python debug_chat.py
```
Tests the chat functionality and AI integration.

### Seed Database
```powershell
python seed_db.py
```
Creates test admin and student accounts.

---

## � Performance & Optimization Tips

### Chunking Strategy
- **Current**: 500 characters per chunk (semantic completeness vs. granularity)
- **For Longer Answers**: Increase to 750-1000 chars
- **For Precise Retrieval**: Decrease to 250-300 chars
- **Implementation**: Edit `chunk_size` in `backend/processor.py` line ~60

### Vector Search Optimization
- **numCandidates**: Set to 100 (balance between speed & accuracy)
- **limit**: 50 pre-filtered chunks → 10 final results
- **Reduce latency**: Lower `numCandidates` to 50, increase `limit` step-by-step
- **Improve accuracy**: Increase `numCandidates` to 200 (higher latency)

### AI Response Speed
| Parameter | Impact | Value |
|-----------|--------|-------|
| `max_tokens` | Generation speed | Current: 1024 (slow) → 512 (fast) |
| `temperature` | Response variety | 0.7 (varied) → 0.3 (deterministic) |
| `model` | Latency & quality | llama-3.3-70b (current best) |

### Database Optimization
- Create indexes on frequently queried fields: `email`, `chat_id`, `created_at`
- Archive old temporary chunks: Implement TTL policy for `is_temporary=true`
- Enable MongoDB compression: Reduces storage by ~30%

---

## 🐛 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| **"Vector index not found"** | Atlas index not created | Create index manually in Atlas UI following schema above |
| **"No results found"** | Embeddings not generated | Ensure SentenceTransformer model downloaded; check internet |
| **"Slow search responses"** | Large chunk volume | Implement pagination; archive old temporary chunks |
| **"CORS error in frontend"** | Backend CORS config | Already permissive; check browser console for specifics |
| **"JWT token expired"** | Session timeout | Re-login; token TTL is 24 hours (editable in `auth.py`) |
| **"GridFS storage error"** | MongoDB file size limit | Upgrade Atlas cluster to M2+ tier |
| **File not indexed after upload** | Atlas search indexing delay | Atlas takes 30-60s to index; retry query after 2 minutes |
| **"No text extracted from PDF"** | Corrupted/scanned PDF | Use OCR preprocessing or re-upload text-based PDF |

---

## 📋 Environment Variables Reference

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `MONGO_URI` | ✅ Yes | - | MongoDB Atlas connection string (include credentials) |
| `GROQ_API_KEY` | ✅ Yes | - | Get from https://console.groq.com/keys |
| `SECRET_KEY` | ✅ Yes | - | Random 32+ char string for JWT signing |
| `UPLOAD_DIR` | ❌ No | `uploads/` | Directory for file uploads |
| `TEMP_DIR` | ❌ No | `temp/` | Temporary storage for processing |
| `JWT_EXPIRY` | ❌ No | `1440` | Token expiry in minutes (default: 24h) |
| `GROQ_MODEL` | ❌ No | `llama-3.3-70b-versatile` | Change AI model if needed |
| `EMBEDDING_MODEL` | ❌ No | `all-MiniLM-L6-v2` | HuggingFace model for vectors |

---

## 📊 Capacity & Limits

| Metric | Limit | Notes |
|--------|-------|-------|
| **File Upload Size** | 16 MB | MongoDB GridFS default; increase with cluster upgrade |
| **Chunk Count** | ~100M | MongoDB Atlas cluster-dependent |
| **Concurrent Connections** | Depends on tier | M0 (free): 3, M2: 512 |
| **Vector Dimensions** | 384 | Fixed by SentenceTransformers model |
| **Top-K Results** | 10 | Can increase; impacts response time |
| **Session History** | Unlimited | Stored in MongoDB; may impact query speed |

---
## 🎨 Frontend Configuration

### Browser Compatibility
| Browser | Support | Notes |
|---------|---------|-------|
| **Chrome/Chromium** | ✅ Full | Recommended for performance |
| **Firefox** | ✅ Full | Best experience (developer recommended) |
| **Safari** | ✅ Full | CSS animations may vary |
| **Edge** | ✅ Full | Chromium-based, full support |

### UI Features & Technical Details
- **Chat Interface**: Responsive flexbox layout, ~1.2s animation for message appearance
- **Auto-scroll**: Automatically scrolls to latest message when new responses arrive
- **File Upload Progress**: Visual feedback on file processing (temporary status messages)
- **Session Persistence**: Chat history persists until manual deletion; no auto-cleanup
- **Dark/Light Theme**: CSS variables defined in `styles.css` (customizable via `:root` selector)
- **Glassmorphism Effects**: Backdrop blur 10px, opacity 0.9 for modern aesthetic

### Static Assets
```
assets/
├── logo.png              # 128x128px, SRMAP university logo
├── home page image.jpg   # 1920x1080px, landing page background
├── [additional images]   # Campus photos, icons (optimize to <100KB each)
```

### API Configuration (Frontend)
Update these constants in JavaScript if backend URL changes:
```javascript
const API_BASE = 'http://127.0.0.1:8000';  // Backend URL
const LOGIN_REDIRECT = 'dashboard.html';    // Post-login redirect
const IDLE_TIMEOUT_MS = 900000;             // 15 min auto-logout
```

---

## 🚢 Deployment Guide

### Local Development (Current Setup)
- Backend: `http://127.0.0.1:8000` (FastAPI dev server)
- Frontend: File protocol or simple HTTP server
- Database: MongoDB Atlas (cloud)

### Production Deployment

#### Backend (Gunicorn + NGINX)
```bash
# Install production ASGI server
pip install gunicorn

# Run with Gunicorn (4 workers, port 8000)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 backend.app:app
```

#### Frontend (Static Hosting)
- Build tools not required (vanilla HTML/CSS/JS)
- Deploy `frontend/` folder to: AWS S3, Vercel, Netlify, or NGINX
- Update `API_BASE` URL to production backend

#### Environment Setup
```bash
# Production .env
MONGO_URI=mongodb+srv://<prod-user>:<prod-pass>@prod-cluster.mongodb.net/GenaiProject
GROQ_API_KEY=<prod-key>
SECRET_KEY=<prod-random-32-char-key>
JWT_EXPIRY=1440
```

#### Database Scaling
| Tier | Connections | Storage | Use Case |
|------|-----------|---------|----------|
| **M0 (Free)** | 3 | 512MB | Development |
| **M2** | 512 | 2GB | 100-500 students |
| **M5** | 10k+ | 10GB+ | 1000+ students |

---

## 📌 Important Notes

- **Token Expiry**: Default 24 hours; users re-login after expiry
- **Temporary Uploads**: Not auto-deleted; implement cleanup job if needed
- **Vector Index**: Must be manually created in MongoDB Atlas (one-time setup)
- **Groq Rate Limits**: Free tier: ~10 requests/min; upgrade for production
- **CORS**: Currently permissive for development; restrict in production
- **File Types**: PDF, DOCX, TXT only; add MIME validation for security

---
## �📜 License
© 2026 SRM University AP. Intelligent Learning Systems. All Rights Reserved.
