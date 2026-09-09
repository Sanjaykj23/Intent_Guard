import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.api.v1 import auth, chat, policy, transactions, audit

app = FastAPI(
    title=settings.APP_NAME,
    description="Ask. Search. Decide. Pay Safely. — Full-stack AI Commerce & Security Platform",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(policy.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
