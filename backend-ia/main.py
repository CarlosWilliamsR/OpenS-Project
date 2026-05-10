import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
import httpx
import asyncio
import time
import json
import hashlib
from pathlib import Path
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from anchorpy import Program, Provider, Wallet, Idl, Context
from solana.rpc.core import RPCException

load_dotenv()

app = FastAPI(title="Medical AI Assistant API")

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
# using Gemini as the exclusive cloud model
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


# Pydantic models
class PatientQueryRequest(BaseModel):
    patient_id: str
    prompt_text: str


class AssistantResponse(BaseModel):
    response: str
    patient_id: str
    engine_used: str

class TTSRequest(BaseModel):
    text: str


class RecordSealRequest(BaseModel):
    patient_id: str
    diagnosis_text: str
    notes: Optional[str] = None
    date: Optional[str] = None


# Health check endpoint
@app.get("/")
async def root():
    return {"status": "ok"}


# Function to fetch patient history from Supabase
async def fetch_patient_history(patient_id: str) -> List[Dict[str, Any]]:
    """
    Fetch patient medical history from Supabase medical_records table.
    Returns a list of medical records for the given patient_id.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("medical_records").select("*").eq("patient_id", patient_id).execute()
        # Type cast to resolve LSP type incompatibility
        result: List[Dict[str, Any]] = list(response.data) if response.data else []
        return result
    except Exception as e:
        print(f"Error fetching patient history: {e}")
        return []



async def register_patient_hash(patient_id: str, medical_hash: str) -> str:
    """
    Register a patient's medical hash on the Solana Devnet.
    Loads the local Keypair and the Anchor IDL to interact with the program.
    """
    program_id_str = "8AcadEGS6Vmcj7kcQ8WroPoWioNkBhXFjkH8Db5hSVUX"
    idl_path = Path(__file__).parent / "app" / "utils" / "opens_anchor.json"
    keypair_path = Path("~/.config/solana/id.json").expanduser()

    # Load local Keypair
    try:
        with keypair_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        secret = payload["secret_key"] if isinstance(payload, dict) and "secret_key" in payload else payload
        keypair = Keypair.from_bytes(bytes(secret))
        wallet = Wallet(keypair)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load Keypair: {e}")

    try:
        # Load and patch IDL to make it compatible with anchorpy
        with idl_path.open("r", encoding="utf-8") as f:
            idl_dict = json.load(f)

        if "metadata" in idl_dict:
            if "name" in idl_dict["metadata"]: idl_dict["name"] = idl_dict["metadata"]["name"]
            if "version" in idl_dict["metadata"]: idl_dict["version"] = idl_dict["metadata"]["version"]

        for inst in idl_dict.get("instructions", []):
            for acc in inst.get("accounts", []):
                if "pda" in acc: del acc["pda"]
                if "writable" in acc: acc["isMut"] = acc.pop("writable")
                if "signer" in acc: acc["isSigner"] = acc.pop("signer")
                if "address" in acc: del acc["address"]
                if "isMut" not in acc: acc["isMut"] = False
                if "isSigner" not in acc: acc["isSigner"] = False

        for acc in idl_dict.get("accounts", []):
            if "type" not in acc:
                for t in idl_dict.get("types", []):
                    if t["name"] == acc["name"]:
                        import copy
                        acc["type"] = copy.deepcopy(t["type"])
                        if "fields" in acc["type"]:
                            for field in acc["type"]["fields"]:
                                if field["type"] == "pubkey": field["type"] = "publicKey"

        for t in idl_dict.get("types", []):
            if "type" in t and "fields" in t["type"]:
                for field in t["type"]["fields"]:
                    if field["type"] == "pubkey": field["type"] = "publicKey"

        idl_str = json.dumps(idl_dict)
        idl = Idl.from_json(idl_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse IDL: {e}")

    client = AsyncClient("https://api.devnet.solana.com")
    try:
        provider = Provider(client, wallet)
        program_id = Pubkey.from_string(program_id_str)
        program = Program(idl, program_id, provider)

        # Prepare parameters
        patient_id_bytes = hashlib.sha256(patient_id.encode("utf-8")).digest()
        medical_hash_bytes = bytes.fromhex(medical_hash)

        # Derive PDA
        record_pda, _ = Pubkey.find_program_address(
            [b"record", patient_id_bytes],
            program_id
        )

        system_program = Pubkey.from_string("11111111111111111111111111111111")

        # Build and send transaction with retry backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                tx_signature = await program.rpc["register_record"](
                    list(patient_id_bytes),
                    list(medical_hash_bytes),
                    int(time.time()),
                    ctx=Context(accounts={
                        "record_account": record_pda,
                        "authority": wallet.public_key,
                        "system_program": system_program,
                    })
                )
                return str(tx_signature)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)

    except RPCException as rpc_err:
        raise HTTPException(status_code=500, detail=f"Solana RPC Connection Error: {rpc_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error anchoring hash: {e}")
    finally:
        await client.close()


@app.post("/api/v1/assistant/seal_record")
async def seal_record(request: RecordSealRequest):
    """Seal a medical diagnosis on Solana and store the metadata in Supabase."""
    try:
        # 1. Deterministic Hash Generation
        data = {
            "patient_id": request.patient_id,
            "diagnosis_text": request.diagnosis_text,
            "notes": request.notes or "",
            "date": request.date or ""
        }
        data_str = json.dumps(data, sort_keys=True)
        medical_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()

        # 2. Call Solana via register_patient_hash (which now has retry backoff)
        tx_signature = await register_patient_hash(request.patient_id, medical_hash)

        # Calculate PDA locally to return it and save to DB
        program_id_str = "8AcadEGS6Vmcj7kcQ8WroPoWioNkBhXFjkH8Db5hSVUX"
        patient_id_bytes = hashlib.sha256(request.patient_id.encode("utf-8")).digest()
        record_pda, _ = Pubkey.find_program_address(
            [b"record", patient_id_bytes],
            Pubkey.from_string(program_id_str)
        )

        # 3. Update/Insert in Supabase with blockchain_signature
        if SUPABASE_URL and SUPABASE_KEY:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            record_payload = {
                "patient_id": request.patient_id,
                "patient_id_hash": patient_id_bytes.hex(),
                "medical_hash": medical_hash,
                "on_chain_pda": str(record_pda),
                "transaction_signature": tx_signature,
                "notes": request.notes or "",
                "date": request.date or "",
            }
            res = supabase.table("medical_records").insert(record_payload).execute()
            if res.status_code not in (200, 201):
                print("Warning: Failed to save medical record to Supabase.", res)

        # 4. Detailed Response
        solscan_url = f"https://solscan.io/tx/{tx_signature}?cluster=devnet"
        return {
            "status": "success",
            "message": "Medical record successfully sealed on Solana.",
            "patient_id": request.patient_id,
            "medical_hash": medical_hash,
            "record_pda": str(record_pda),
            "blockchain_signature": tx_signature,
            "solscan_url": solscan_url
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sealing record: {e}")

@app.post("/api/v1/assistant/tts")
async def synthesize_voice(request: TTSRequest):
    """Generate audio from text using ElevenLabs API or a fallback."""
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") # default voice
    
    if not elevenlabs_key:
        raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")
        
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": elevenlabs_key
    }
    data = {
        "text": request.text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=headers, timeout=30.0)
            response.raise_for_status()
            from fastapi.responses import Response
            return Response(content=response.content, media_type="audio/mpeg")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


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
        
        engine_used = "gemini" # Used as a proxy identifier for cloud in the UI
        assistant_response = ""
        cloud_failed = False
        
        # If Gemini is available, try using it first
        if GEMINI_API_KEY and not cloud_failed:
            try:
                system_prompt = (
                    "You are a helpful medical AI assistant. Provide informative and supportive responses "
                    "to patient queries based on their medical history. Always remind users that you are "
                    "an AI assistant and not a replacement for professional medical advice."
                )
                user_message = f"{request.prompt_text}{context}"
                
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-pro",
                    system_instruction=system_prompt
                )
                response = model.generate_content(user_message)
                assistant_response = response.text or "No response generated."
            except Exception as e:
                print(f"Cloud AI failed: {e}. Falling back to local Ollama.")
                cloud_failed = True # Force fallback
        else:
            cloud_failed = True
        
        if cloud_failed or not assistant_response:
            # Fallback to Ollama local instance
            engine_used = "qwen" # Local indicator
            ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            
            system_prompt = (
                "You are a helpful medical AI assistant. Provide informative and supportive responses "
                "to patient queries based on their medical history."
            )
            prompt = f"System: {system_prompt}\n{context}\nUser: {request.prompt_text}\nAssistant:"
            
            async with httpx.AsyncClient() as client:
                try:
                    payload = {
                        "model": "qwen2.5:0.5b", # Adjust to your local model
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7
                        }
                    }
                    res = await client.post(f"{ollama_host}/api/generate", json=payload, timeout=60.0)
                    res.raise_for_status()
                    assistant_response = res.json().get("response", "No response from local model.")
                except Exception as ex:
                    assistant_response = f"Error: The AI service is currently unavailable. Both cloud and local inference failed. ({ex})"
        
        return AssistantResponse(
            response=assistant_response,
            patient_id=request.patient_id,
            engine_used=engine_used
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
