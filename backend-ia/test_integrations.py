import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

async def test_supabase():
    print(f"\n{YELLOW}Testing Supabase Connection...{RESET}")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print(f"{RED}❌ SUPABASE_URL or SUPABASE_KEY missing in .env{RESET}")
        return False
    
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(url, key)
        # Attempt a simple query
        res = supabase.table("patients").select("*").limit(1).execute()
        print(f"{GREEN}✅ Supabase Connected Successfully! Found patients table.{RESET}")
        return True
    except Exception as e:
        print(f"{RED}❌ Supabase Error: {str(e)}{RESET}")
        return False

async def test_gemini():
    print(f"\n{YELLOW}Testing Google Gemini API...{RESET}")
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(f"{RED}❌ GOOGLE_API_KEY missing in .env{RESET}")
        return False
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("Responde 'Hola, Gemini funciona' si recibes este mensaje.")
        if "Hola" in response.text or "funciona" in response.text:
            print(f"{GREEN}✅ Gemini API Connected! Response: {response.text.strip()}{RESET}")
            return True
        else:
            print(f"{YELLOW}⚠️ Gemini responded, but unexpected text: {response.text}{RESET}")
            return True
    except Exception as e:
        print(f"{RED}❌ Gemini Error: {str(e)}{RESET}")
        return False

async def test_ollama():
    print(f"\n{YELLOW}Testing Ollama (Local AI) Connection...{RESET}")
    # Default Ollama port
    url = "http://localhost:11434/api/tags"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=5.0)
            if resp.status_code == 200:
                models = [m['name'] for m in resp.json().get('models', [])]
                print(f"{GREEN}✅ Ollama is running! Available models: {', '.join(models)}{RESET}")
                if any("qwen" in m for m in models):
                    print(f"{GREEN}✅ Qwen model is installed.{RESET}")
                else:
                    print(f"{YELLOW}⚠️ Ollama is running, but 'qwen2.5' model not found. Run 'ollama run qwen2.5:7b'{RESET}")
                return True
            else:
                print(f"{RED}❌ Ollama returned status {resp.status_code}{RESET}")
                return False
        except Exception as e:
            print(f"{YELLOW}⚠️ Ollama not reachable (Is the service running?): {str(e)}{RESET}")
            return False

async def test_elevenlabs():
    print(f"\n{YELLOW}Testing ElevenLabs TTS API...{RESET}")
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print(f"{RED}❌ ELEVENLABS_API_KEY missing in .env{RESET}")
        return False
        
    url = "https://api.elevenlabs.io/v1/user"
    headers = {"xi-api-key": api_key}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=5.0)
            if resp.status_code == 200:
                user_info = resp.json()
                print(f"{GREEN}✅ ElevenLabs API Connected! Subscription tier: {user_info.get('subscription', {}).get('tier')}{RESET}")
                return True
            else:
                print(f"{RED}❌ ElevenLabs Error {resp.status_code}: {resp.text}{RESET}")
                return False
        except Exception as e:
            print(f"{RED}❌ ElevenLabs Request Error: {str(e)}{RESET}")
            return False

async def test_solana():
    print(f"\n{YELLOW}Testing Solana Devnet Connection...{RESET}")
    try:
        from solana.rpc.async_api import AsyncClient
        client = AsyncClient("https://api.devnet.solana.com")
        is_connected = await client.is_connected()
        if is_connected:
            print(f"{GREEN}✅ Solana Devnet Connected!{RESET}")
        else:
             print(f"{RED}❌ Could not connect to Solana Devnet.{RESET}")
             return False
             
        program_id = os.environ.get("SOLANA_PROGRAM_ID")
        if program_id and program_id != "REPLACE_WITH_PROGRAM_ID":
            print(f"{GREEN}✅ SOLANA_PROGRAM_ID is configured: {program_id}{RESET}")
        else:
            print(f"{YELLOW}⚠️ SOLANA_PROGRAM_ID is missing or default in .env{RESET}")
            
        await client.close()
        return True
    except ImportError:
         print(f"{RED}❌ solana python package not installed.{RESET}")
         return False
    except Exception as e:
        print(f"{RED}❌ Solana Connection Error: {str(e)}{RESET}")
        return False

async def main():
    print("==================================================")
    print("🚀 OpenS Colosseum Hackathon Environment Verifier")
    print("==================================================")
    
    await test_supabase()
    await test_gemini()
    await test_ollama()
    await test_elevenlabs()
    await test_solana()
    
    print(f"\n{YELLOW}Note: If any test failed, check your .env file and ensure required services are running.{RESET}")

if __name__ == "__main__":
    asyncio.run(main())
