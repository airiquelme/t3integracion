from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query(request: QueryRequest):
    # Por ahora retorna error claro — después conectamos Nomic y LLM
    return {
        "answer": "El sistema aún no está configurado.",
        "references": []
    }

# Servir el frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")