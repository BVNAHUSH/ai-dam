

````markdown
# 🚀 AI-Powered Digital Asset Management (DAM)

> A multimodal AI-powered system for indexing, understanding, and semantically searching images, videos, and PDF documents.

---

## 📌 Overview

The **AI-Powered Digital Asset Management (DAM)** system enables users to...

---

## ✨ Features

- 🖼️ Image understanding and semantic search
- 🎥 Video understanding using representative frames
- 📄 PDF text extraction and semantic search
- 🔎 Natural-language search
- 📊 Relevance-ranked results
- 🔁 Incremental indexing
- ♻️ Duplicate detection
- 💾 Persistent SQLite + FAISS storage
- 🛡️ Failure handling for unsupported/corrupted files
- 👀 Asset preview
- 🎛️ File-type filtering
- 📈 Indexing progress tracking

---

## 🏗️ Architecture

```text
                    ┌──────────────────┐
                    │   React Frontend │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   FastAPI API    │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
      ┌───────────────┐             ┌───────────────┐
      │ Image / Video │             │     PDFs       │
      │   OpenCLIP    │             │    MiniLM      │
      └───────┬───────┘             └───────┬───────┘
              │                             │
              ▼                             ▼
        ┌───────────┐                 ┌─────────────┐
        │   FAISS   │                 │ PDF FAISS   │
        └─────┬─────┘                 └──────┬──────┘
              │                              │
              └──────────────┬───────────────┘
                             ▼
                       ┌───────────┐
                       │  SQLite   │
                       └───────────┘
````

---

## 🧠 AI Pipeline

### 🖼️ Images

1. Scan image
2. Calculate SHA-256
3. Extract metadata
4. Generate OpenCLIP embedding
5. Store embedding in SQLite
6. Add vector to FAISS
7. Make asset searchable

### 🎥 Videos

1. Scan video
2. Extract metadata
3. Select representative frames
4. Generate CLIP embeddings
5. Average frame embeddings
6. Store vector
7. Index in FAISS

### 📄 PDFs

1. Extract text using PyMuPDF
2. Split text into chunks
3. Generate MiniLM embeddings
4. Store chunk embeddings
5. Index using FAISS
6. Return matching page and text

---

## 🔍 Semantic Search

Users can search using natural language instead of filenames.

### Example

```text
"modern living room"
```

The system searches the **actual visual content** of images/videos rather than matching filenames.

For PDFs:

```text
"indoor swimming pool"
```

The system searches semantic representations of PDF text chunks and returns the relevant document and matching page.

---

## 📊 Dataset

| Asset Type |   Count |
| ---------- | ------: |
| Images     |     100 |
| Videos     |      20 |
| PDFs       |      16 |
| **Total**  | **136** |

Approximate dataset size: **1.6 GB**

The dataset size was intentionally kept below the suggested 5–10 GB range because of local hardware, storage, and internet constraints.

---

## 🛠️ Tech Stack

| Component              | Technology                     |
| ---------------------- | ------------------------------ |
| Frontend               | React + Vite + Tailwind CSS    |
| Backend                | FastAPI                        |
| Database               | SQLite + SQLAlchemy            |
| Image/Video Embeddings | OpenCLIP                       |
| PDF Embeddings         | Sentence Transformers / MiniLM |
| Vector Search          | FAISS                          |
| Image Processing       | Pillow                         |
| Video Processing       | OpenCV                         |
| PDF Processing         | PyMuPDF                        |
| Runtime                | Python 3.13                    |
| UI Icons               | Lucide React                   |

---

## 📁 Project Structure

```text
ai-dam/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── backend/
│   └── app/
│       ├── api/
│       ├── ai/
│       ├── database/
│       ├── ingestion/
│       ├── processors/
│       ├── search/
│       └── main.py
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── dataset/
│   ├── images/
│   ├── videos/
│   └── pdfs/
│
└── data/
    ├── dam.db
    ├── multimodal.index.faiss
    └── pdf_chunks.index.faiss
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <https://github.com/BVNAHUSH/ai-dam>
cd ai-dam
```

### 2. Create virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```cmd
.venv\Scripts\activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create:

```text
backend/.env
```

Example:

```env
SEARCH_IMAGE_VIDEO_THRESHOLD=0.27
SEARCH_PDF_THRESHOLD=0.30
```

> Gemini is not required for the core indexing and search pipeline.

---

## ▶️ Running the Backend

```cmd
cd backend
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

---

## ▶️ Running the Frontend

Open another terminal:

```cmd
cd frontend
npm install
npm run dev
```

Then open the Vite development URL shown in the terminal.

---

## 🔄 Indexing

The indexing pipeline supports:

* New assets
* Incremental indexing
* Duplicate detection
* SHA-256 hashing
* Persistent embeddings
* Failed-file tracking
* Indexing progress

Already indexed assets are skipped when their content has not changed.

Example:

```text
MULTIMODAL INDEX COMPLETE

New embeddings : 0
Skipped        : 136
Failed         : 0
FAISS vectors  : 120
```

The 120-vector main FAISS index represents image/video assets. PDFs use a separate chunk-level FAISS index.

---

## 📄 PDF Semantic Search

PDFs are handled separately from image/video embeddings.

The current dataset produced:

```text
PDF assets       : 16
Total chunks     : 993
Successful       : 993
Failed           : 0
Embedding dim    : 384
```

This allows searches such as:

```text
healthcare
```

```text
indoor swimming pool
```

```text
workplace collaboration
```

to retrieve relevant PDF documents and matching pages.

---

## 🔎 Search Examples

| Query                | Expected Result                          |
| -------------------- | ---------------------------------------- |
| `modern living room` | Relevant interior/living-room images     |
| `swimming pool`      | PDF containing swimming-pool information |
| `healthcare`         | Healthcare-related PDF content           |
| `elephant`           | No relevant result                       |
| `office workspace`   | Workspace-related images/PDFs            |
| `people outdoors`    | Relevant outdoor images                  |
| `food`               | Food-related visual assets               |
| `building`           | Building/architecture assets             |
| `sports`             | Sports-related assets                    |
| `technology`         | Technology-related assets                |

---

## 🧪 Search Evaluation

The system is evaluated using at least 10 natural-language test queries.

For each query, evaluation considers:

* Search intent
* Expected assets
* Returned results
* Relevance
* False positives
* Cases where no relevant asset exists

Example:

| Query                | Intent        | Expected           | Result    |
| -------------------- | ------------- | ------------------ | --------- |
| `modern living room` | Visual scene  | Living-room images | Relevant  |
| `swimming pool`      | PDF concept   | Pool-related PDF   | Relevant  |
| `healthcare`         | PDF concept   | Healthcare PDF     | Relevant  |
| `elephant`           | Visual object | No matching asset  | No result |

---

## 🛡️ Reliability & Failure Handling

The system accounts for:

### Duplicate files

SHA-256 hashes are used to detect identical files.

### Incremental indexing

Previously indexed unchanged files are skipped.

### Unsupported files

Unsupported extensions are ignored by the scanner.

### Corrupted files

Processing failures are recorded instead of stopping the complete indexing pipeline.

### AI/model failure

Embedding failures are recorded at the asset level.

---

## 📈 Scalability Considerations

The current implementation uses:

* SQLite for persistent metadata
* FAISS for vector search
* Batch-oriented indexing
* Incremental processing
* Persistent embeddings
* Separate PDF chunk indexing
* Representative video frames

For a production-scale deployment, the architecture could be extended with:

* PostgreSQL
* pgvector
* Distributed workers
* Object storage
* Message queues
* GPU inference workers
* Distributed vector databases
* Parallel ingestion

---

## 🔌 API Endpoints

### Assets

```text
GET /api/assets
GET /api/assets/{id}/preview
```

### Search

```text
GET /api/search
```

### Indexing

```text
POST /api/indexing/start
GET  /api/indexing/status
```

---

## 🎯 Assignment Coverage

| Requirement             | Implementation                   |
| ----------------------- | -------------------------------- |
| Images                  | OpenCLIP                         |
| Videos                  | Representative frames + OpenCLIP |
| PDFs                    | PyMuPDF + MiniLM                 |
| Metadata                | SQLite                           |
| Semantic search         | CLIP + MiniLM                    |
| Relevance ranking       | FAISS similarity                 |
| Filters                 | File type                        |
| Preview                 | API + frontend                   |
| Index progress          | Indexing status API              |
| Duplicate detection     | SHA-256                          |
| Incremental indexing    | Persistent embedding state       |
| Failure handling        | Per-file status/error            |
| Persistent storage      | SQLite + FAISS                   |
| Natural-language search | Yes                              |
| Test searches           | 10+                              |
| UI                      | React + Tailwind                 |

---



## ⚠️ Limitations

* Dataset size is approximately 1.6 GB rather than the suggested 5–10 GB due to local hardware, storage, and internet constraints.
* Video understanding uses representative frames rather than every frame.
* Semantic similarity depends on the embedding models.
* Very domain-specific queries may produce weaker results.
* SQLite and local FAISS are intended for this take-home/local deployment rather than large distributed production environments.
* PDF retrieval is text-based rather than full visual PDF understanding.

---

## 🚀 Future Production Improvements

Potential production improvements include:

* Distributed ingestion workers
* GPU inference queues
* Object storage such as S3
* PostgreSQL + pgvector
* Advanced multimodal foundation models
* OCR for scanned PDFs
* Audio/transcript indexing for videos
* Face/entity recognition with appropriate privacy controls
* Advanced metadata extraction
* Hybrid keyword + vector search
* Reranking models
* Access control and authentication
* Monitoring and observability

---

## 👨‍💻 Author

**Nahush B. V.**

AI / Machine Learning / Full-Stack Developer

---

## 📜 License

This project was developed as a technical take-home assignment and demonstration of multimodal AI-powered digital asset management.

```


