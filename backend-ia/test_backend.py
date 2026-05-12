import httpx
import asyncio

async def test_services():
    base_url = "http://localhost:8000"
    print("4. Testing /api/v1/assistant/seal_record...")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{base_url}/api/v1/assistant/seal_record", json={
            "patient_id": 1,
            "diagnosis_text": "Paciente presenta fiebre ligera, se recomienda reposo y antipiréticos. Observar evolución.",
            "notes": "Consulta de rutina hackathon test",
            "date": "2026-05-11"
        })
        print("Seal Record Response:", resp.json())
        
if __name__ == "__main__":
    asyncio.run(test_services())
