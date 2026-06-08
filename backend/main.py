from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

NOMIC_API_KEY = os.getenv("NOMIC_API_KEY")
NOMIC_PROJECTION_ID = os.getenv("NOMIC_PROJECTION_ID")

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query(request: QueryRequest):
    try:
        async with httpx.AsyncClient() as client:
            nomic_response = await client.post(
                "https://api-atlas.nomic.ai/v1/query/topk",
                headers={
                    "Authorization": f"Bearer {NOMIC_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "projection_id": NOMIC_PROJECTION_ID,
                    "k": 3,
                    "fields": ["text", "metadata"],
                    "query": request.question
                },
                timeout=30
            )
            nomic_response.raise_for_status()
            nomic_data = nomic_response.json()
    except Exception as e:
        return {"error": f"Error al buscar fragmentos: {str(e)}"}

    try:
        neighbors = nomic_data.get("data", [])
        if not neighbors:
            return {"error": "No se encontraron fragmentos relacionados con la consulta."}

        fragments = []
        references = []
        for neighbor in neighbors:
            text = neighbor.get("text", "")
            metadata = neighbor.get("metadata", {})
            if isinstance(metadata, str):
                import json
                metadata = json.loads(metadata)
            fragments.append(text)
            references.append({
                "title": metadata.get("title", ""),
                "url": metadata.get("url", ""),
                "line": metadata.get("line_number", "")
            })
    except Exception as e:
        return {"error": f"Error al procesar fragmentos: {str(e)}"}

    # Paso 3: Llamar al LLM
    prompt = f"""Responde la pregunta según el contexto:

Pregunta del usuario:
{request.question}

Contexto (fragmentos relevantes de los artículos):
{fragments[0] if len(fragments) > 0 else ""}
{fragments[1] if len(fragments) > 1 else ""}
{fragments[2] if len(fragments) > 2 else ""}
"""

    try:
        async with httpx.AsyncClient() as client:
            llm_response = await client.post(
                "https://iic3103-gemini-proxy-902587603657.us-central1.run.app/v1/generate",
                headers={
                    "X-Student-Email": "ai.riquelme@uc.cl",
                    "X-Student-Id": "19637276"
                },
                json={
                    "content": prompt
                },
                timeout=120
            )
            llm_response.raise_for_status()
            answer = llm_response.json().get("answer", "Sin respuesta")
    except Exception as e:
        return {"error": f"Error al generar respuesta: {str(e)}"}

    return {
        "answer": answer,
        "references": references
    }

# Servir el frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")