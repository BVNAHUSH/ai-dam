from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.search import router as search_router
from app.api.assets import router as assets_router
from app.api.indexing import router as indexing_router

app = FastAPI(
    title="AI-Powered Digital Asset Management",
    description=(
        "Multimodal AI-powered Digital Asset Management "
        "system with semantic search, metadata indexing, "
        "and asset preview."
    ),
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# API ROUTERS
# =========================================================

app.include_router(search_router)
app.include_router(assets_router)
app.include_router(indexing_router)

# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "name": "AI-Powered Digital Asset Management",
        "version": "1.0.0",
        "status": "running",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }