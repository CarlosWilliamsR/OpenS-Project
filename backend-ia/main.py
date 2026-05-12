import os
from dotenv import load_dotenv
load_dotenv()

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import google.generativeai as genai
from openai import OpenAI
from supabase import create_client, Client
from typing import Optional, List, Dict, Any

from solana_service import seal_diagnosis_on_chain

app = FastAPI(title="Medical AI Assistant API")

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI clients
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL")
OLLAMA_MODELS = os.environ.get("OLLAMA_MODELS", "").split(",")
ollama_client = OpenAI(base_url=f"{OLLAMA_BASE_URL}/v1", api_key="ollama") if OLLAMA_BASE_URL else None

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
ELEVENLABS_MODEL_ID = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
SOLANA_PROGRAM_ID = os.environ.get("SOLANA_PROGRAM_ID", "REPLACE_WITH_PROGRAM_ID")


# Pydantic models
class PatientQueryRequest(BaseModel):
    patient_id: int
    prompt_text: str


class AssistantResponse(BaseModel):
    response: str
    patient_id: int


class RecordSealRequest(BaseModel):
    patient_id: int
    diagnosis_text: str
    notes: Optional[str] = None
    date: Optional[str] = None


class VoiceRequest(BaseModel):
    text: str


def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase configuration is missing.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# Health check endpoint
@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "supabase": bool(SUPABASE_URL and SUPABASE_KEY),
        "elevenlabs": bool(ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID),
        "solana": bool(SOLANA_PROGRAM_ID and SOLANA_PROGRAM_ID != "REPLACE_WITH_PROGRAM_ID"),
    }


@app.get("/api/v1/patients")
async def list_patients():
    """Return patients from Supabase, with a safe fallback derived from medical records."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    supabase = get_supabase_client()

    try:
        response = supabase.table("patients").select("*").execute()
        if response.data:
            return list(response.data)
    except Exception as exc:
        print(f"Error fetching patients table: {exc}")

    try:
        records = supabase.table("medical_records").select("patient_id").execute().data or []
        unique_ids = sorted({str(record.get("patient_id")) for record in records if record.get("patient_id") is not None})
        return [{"id": patient_id, "name": f"Paciente {patient_id}"} for patient_id in unique_ids]
    except Exception as exc:
        print(f"Error building fallback patient list: {exc}")
        return []


@app.get("/api/v1/patients/{patient_id}/records")
async def get_patient_records(patient_id: int):
    """Return Supabase medical records for a patient."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"records": []}

    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("medical_records")
            .select("*")
            .eq("patient_id", patient_id)
            .execute()
        )
        return {"records": list(response.data) if response.data else []}
    except Exception as exc:
        print(f"Error fetching records for patient {patient_id}: {exc}")
        return {"records": []}


# Function to fetch patient history from Supabase
async def fetch_patient_history(patient_id: int) -> List[Dict[str, Any]]:
    """
    Fetch patient medical history from Supabase medical_records table.
    Returns a list of medical records for the given patient_id.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    
    try:
        supabase: Client = get_supabase_client()
        response = supabase.table("medical_records").select("*").eq("patient_id", patient_id).execute()
        # Type cast to resolve LSP type incompatibility
        result: List[Dict[str, Any]] = list(response.data) if response.data else []
        return result
    except Exception as e:
        print(f"Error fetching patient history: {e}")
        return []


async def persist_record_to_supabase(
    patient_id: int,
    diagnosis_text: str,
    notes: Optional[str] = None,
    date: Optional[str] = None,
) -> Dict[str, Any]:
    """Seal a diagnosis on Solana and persist the metadata in Supabase."""
    chain_result = await seal_diagnosis_on_chain(patient_id, diagnosis_text)
    supabase = get_supabase_client()

    import datetime
    
    record_payload = {
        "patient_id": patient_id,
        "medical_hash": chain_result["medical_hash"],
        "transaction_signature": chain_result["tx_signature"],
        "description": notes or "",
        "diagnosis": diagnosis_text,
        "date": date if date else datetime.datetime.utcnow().isoformat(),
    }

    response = supabase.table("medical_records").insert(record_payload).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to save medical record to Supabase.")

    return chain_result


async def synthesize_voice(text: str) -> bytes:
    """Generate speech with ElevenLabs and return raw MP3 bytes."""
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ElevenLabs configuration is missing.")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"ElevenLabs error: {response.text}")

    return response.content


# Virtual Assistant endpoint
@app.post("/api/v1/assistant/ask", response_model=AssistantResponse)
async def ask_assistant(request: PatientQueryRequest):
    """
    Process patient queries using the AI assistant.
    Fetches patient history and uses LLM to provide medical assistance.
    """
    try:
        # Fetch patient history
        patient_history = await fetch_patient_history(request.patient_id)
        
        # Build context with patient history
        context = ""
        if patient_history:
            context = "\n\nPatient Medical History:\n"
            for record in patient_history:
                context += f"- Date: {record.get('date', 'N/A')}, Notes: {record.get('notes', 'N/A')}\n"
        
        # Try Gemini first
        if GOOGLE_API_KEY:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                system_instruction = (
                    "You are a helpful medical AI assistant. Provide informative and supportive responses "
                    "to patient queries based on their medical history. Always remind users that you are "
                    "an AI assistant and not a replacement for professional medical advice."
                )
                user_message = f"{system_instruction}\n\nUser: {request.prompt_text}{context}"
                response = model.generate_content(user_message)
                assistant_response = response.text or "No response generated."
            except Exception as e:
                print(f"Gemini failed: {e}. Falling back to Ollama.")
                if ollama_client and OLLAMA_MODELS:
                    model_to_use = OLLAMA_MODELS[0] if OLLAMA_MODELS[0] else "qwen2.5:7b"
                    system_prompt = "You are a helpful medical AI assistant."
                    user_message = f"{request.prompt_text}{context}"
                    response = ollama_client.chat.completions.create(
                        model=model_to_use,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        max_tokens=500
                    )
                    assistant_response = response.choices[0].message.content or "No response generated."
                else:
                    assistant_response = "Both AI services failed or are not configured properly."
        else:
            # Fallback response when no AI is configured
            assistant_response = (
                f"Hello! I received your query: '{request.prompt_text}'. "
                f"I would be happy to help you, but the AI service is currently being configured. "
                f"Please ensure the GOOGLE_API_KEY is set up properly."
            )
        
        return AssistantResponse(
            response=assistant_response,
            patient_id=request.patient_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.post("/api/v1/assistant/seal_record")
async def seal_record(request: RecordSealRequest):
    """Seal a medical diagnosis on Solana and store its metadata in Supabase."""
    try:
        result = await persist_record_to_supabase(
            patient_id=request.patient_id,
            diagnosis_text=request.diagnosis_text,
            notes=request.notes,
            date=request.date,
        )
        return {
            "status": "sealed",
            "record_pda": result["record_pda"],
            "tx_signature": result["tx_signature"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sealing record: {str(e)}")


@app.post("/api/v1/assistant/tts")
@app.post("/api/v1/voice/generate")
async def generate_voice(request: VoiceRequest):
    """Generate ElevenLabs speech for the provided text."""
    audio_bytes = await synthesize_voice(request.text)
    return Response(content=audio_bytes, media_type="audio/mpeg")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
