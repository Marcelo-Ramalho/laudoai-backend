from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import laudos, users

app = FastAPI(
    title="LaudoAI API",
    description="Backend do LaudoAI — Laudos Técnicos com IA",
    version="1.0.0"
)

# CORS — permite frontend acessar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção: trocar pelo domínio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(users.router)
app.include_router(laudos.router)


@app.get("/")
async def root():
    return {
        "produto": "LaudoAI",
        "versao": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
