import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Awaitable, Callable, List

import httpx
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient

load_dotenv()


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def missing_secret_message(var_names: List[str]) -> str:
    return f"Faltan variables de entorno: {', '.join(var_names)}"


async def check_supabase(strict: bool) -> CheckResult:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        detail = missing_secret_message(["SUPABASE_URL", "SUPABASE_KEY"])
        if strict:
            return CheckResult("Supabase", False, detail)
        return CheckResult("Supabase", True, f"SKIP: {detail}")

    try:
        from supabase import Client, create_client

        supabase: Client = create_client(url, key)
        response = supabase.table("patients").select("id").limit(1).execute()
        rows = response.data or []
        return CheckResult("Supabase", True, f"Conexión OK (patients sample size: {len(rows)})")
    except Exception as err:
        return CheckResult("Supabase", False, str(err))


async def check_gemini(strict: bool) -> CheckResult:
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        detail = missing_secret_message(["GOOGLE_API_KEY/GEMINI_API_KEY"])
        if strict:
            return CheckResult("Gemini", False, detail)
        return CheckResult("Gemini", True, f"SKIP: {detail}")

    try:
        import google.generativeai as genai

        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            "Responde exactamente con: OpenS Gemini OK"
        )
        text = (response.text or "").strip()
        if "OpenS Gemini OK" in text:
            return CheckResult("Gemini", True, f"Conexión OK ({model_name})")
        return CheckResult("Gemini", False, f"Respuesta inesperada: {text}")
    except Exception as err:
        return CheckResult("Gemini", False, str(err))


async def check_ollama_qwen() -> CheckResult:
    ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    url = f"{ollama_base.rstrip('/')}/api/tags"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=8.0)
            response.raise_for_status()
            models = [m.get("name", "") for m in response.json().get("models", [])]
            qwen_found = any("qwen" in model.lower() for model in models)
            if qwen_found:
                return CheckResult("Ollama/Qwen", True, f"Modelos detectados: {', '.join(models)}")
            return CheckResult(
                "Ollama/Qwen",
                False,
                "Ollama activo pero no se encontró modelo Qwen (ej: qwen2.5:7b).",
            )
    except Exception as err:
        return CheckResult("Ollama/Qwen", False, str(err))


async def check_elevenlabs(strict: bool) -> CheckResult:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        detail = missing_secret_message(["ELEVENLABS_API_KEY"])
        if strict:
            return CheckResult("ElevenLabs", False, detail)
        return CheckResult("ElevenLabs", True, f"SKIP: {detail}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": api_key},
                timeout=8.0,
            )
            response.raise_for_status()
            tier = response.json().get("subscription", {}).get("tier", "unknown")
            return CheckResult("ElevenLabs", True, f"Conexión OK (tier: {tier})")
    except Exception as err:
        return CheckResult("ElevenLabs", False, str(err))


async def check_solana(strict: bool) -> CheckResult:
    program_id = os.environ.get("SOLANA_PROGRAM_ID")
    if strict and not program_id:
        return CheckResult(
            "Solana Devnet",
            False,
            missing_secret_message(["SOLANA_PROGRAM_ID"]),
        )

    client = AsyncClient("https://api.devnet.solana.com")
    try:
        connected = await client.is_connected()
        if not connected:
            return CheckResult("Solana Devnet", False, "No se pudo conectar a Devnet.")

        version_resp = await client.get_version()
        blockhash_resp = await client.get_latest_blockhash()

        version_value = getattr(version_resp, "value", {})
        if isinstance(version_value, dict):
            version = version_value.get("solana-core", "unknown")
        else:
            version = str(version_value)

        blockhash_value = getattr(blockhash_resp, "value", None)
        if blockhash_value is None:
            blockhash = "unknown"
        else:
            blockhash = str(getattr(blockhash_value, "blockhash", blockhash_value))
        detail = f"Conexión OK (solana-core: {version}, latest blockhash: {blockhash})"

        if program_id:
            detail += f", program_id: {program_id}"
        else:
            detail += ", program_id: no configurado"

        return CheckResult("Solana Devnet", True, detail)
    except Exception as err:
        return CheckResult("Solana Devnet", False, str(err))
    finally:
        await client.close()


def print_result(result: CheckResult) -> None:
    is_skip = result.ok and result.detail.startswith("SKIP:")
    if is_skip:
        icon = "⚠️"
        color = YELLOW
    else:
        icon = "✅" if result.ok else "❌"
        color = GREEN if result.ok else RED
    print(f"{color}{icon} {result.name}:{RESET} {result.detail}")


async def run_checks(strict: bool) -> List[CheckResult]:
    checks: List[Callable[[], Awaitable[CheckResult]]] = [
        lambda: check_supabase(strict),
        lambda: check_gemini(strict),
        check_ollama_qwen,
        lambda: check_elevenlabs(strict),
        lambda: check_solana(strict),
    ]

    results: List[CheckResult] = []
    for check in checks:
        results.append(await check())
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verifica integraciones externas de OpenS (Supabase, Gemini, Ollama/Qwen, ElevenLabs, Solana)."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Falla si faltan variables de entorno requeridas.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"{CYAN}=================================================={RESET}")
    print(f"{CYAN}🚀 OpenS Colosseum Hackathon Integration Verifier{RESET}")
    print(f"{CYAN}=================================================={RESET}")
    print(f"Modo estricto: {'ON' if args.strict else 'OFF'}")

    results = asyncio.run(run_checks(strict=args.strict))
    print()
    for result in results:
        print_result(result)

    failed = [result for result in results if not result.ok]
    print()
    if failed:
        print(f"{RED}Resultado final: FAIL ({len(failed)} verificación(es) fallida(s)).{RESET}")
        sys.exit(1)

    print(f"{GREEN}Resultado final: PASS (todas las integraciones verificadas).{RESET}")


if __name__ == "__main__":
    main()
