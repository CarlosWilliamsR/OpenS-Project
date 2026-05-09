import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client
from typing import Optional, List, Dict, Any

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

# Initialize OpenAI client
# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


# Pydantic models
class PatientQueryRequest(BaseModel):
    patient_id: int
    prompt_text: str


class AssistantResponse(BaseModel):
    response: str
    patient_id: int


# Health check endpoint
@app.get("/")
async def root():
    return {"status": "ok"}


# Function to fetch patient history from Supabase
async def fetch_patient_history(patient_id: int) -> List[Dict[str, Any]]:
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
        
        # If OpenAI client is available, use it
        if openai_client:
            system_prompt = (
                "You are a helpful medical AI assistant. Provide informative and supportive responses "
                "to patient queries based on their medical history. Always remind users that you are "
                "an AI assistant and not a replacement for professional medical advice."
            )
            
            user_message = f"{request.prompt_text}{context}"
            
            response = openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_completion_tokens=500
            )
            
            assistant_response = response.choices[0].message.content or "No response generated."
        else:
            # Fallback response when OpenAI is not configured
            assistant_response = (
                f"Hello! I received your query: '{request.prompt_text}'. "
                f"I would be happy to help you, but the AI service is currently being configured. "
                f"Please ensure the OPENAI_API_KEY is set up properly."
            )
        
        return AssistantResponse(
            response=assistant_response,
            patient_id=request.patient_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
