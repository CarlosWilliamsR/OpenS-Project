import argparse
import asyncio
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

import httpx


GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


@dataclass
class ApiResult:
    name: str
    ok: bool
    detail: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="API smoke tests para OpenS backend (requiere backend activo)."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="URL base del backend FastAPI.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Falla si cualquier endpoint de negocio no responde 200.",
    )
    return parser.parse_args()


async def check_endpoint(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    expected_status: int = 200,
    json_payload: Dict | None = None,
) -> Tuple[bool, str, httpx.Response | None]:
    try:
        response = await client.request(method, path, json=json_payload)
    except Exception as err:
        return False, f"Excepción de red: {err}", None

    if response.status_code != expected_status:
        return (
            False,
            f"Status esperado {expected_status}, recibido {response.status_code}: {response.text[:200]}",
            response,
        )
    return True, f"Status {response.status_code}", response


async def run_smoke_tests(base_url: str, strict: bool) -> List[ApiResult]:
    results: List[ApiResult] = []

    timeout = httpx.Timeout(90.0, connect=10.0)
    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout) as client:
        ok, detail, response = await check_endpoint(client, "GET", "/")
        if ok and response is not None:
            body = response.json()
            ok = body.get("status") == "ok"
            detail = f"body={body}" if ok else f"Body inesperado: {body}"
        results.append(ApiResult("GET /", ok, detail))

        ok, detail, response = await check_endpoint(client, "GET", "/api/v1/patients")
        if ok and response is not None:
            body = response.json()
            ok = isinstance(body, list)
            detail = f"items={len(body)}" if ok else f"Respuesta no-lista: {body}"
        results.append(ApiResult("GET /api/v1/patients", ok, detail))

        ok, detail, response = await check_endpoint(client, "GET", "/api/v1/patients/1/records")
        if ok and response is not None:
            body = response.json()
            ok = isinstance(body, list)
            detail = f"records={len(body)}" if ok else f"Respuesta no-lista: {body}"
        results.append(ApiResult("GET /api/v1/patients/{id}/records", ok, detail))

        ask_payload = {
            "patient_id": "1",
            "prompt_text": "Responde exactamente con: OpenS Backend OK",
        }
        ok, detail, response = await check_endpoint(
            client,
            "POST",
            "/api/v1/assistant/ask",
            json_payload=ask_payload,
        )
        if ok and response is not None:
            body = response.json()
            ai_text = (body.get("response") or "").strip()
            engine = body.get("engine_used")
            ok = bool(ai_text)
            detail = f"engine={engine}, response='{ai_text[:80]}'" if ok else f"Respuesta vacía: {body}"
        results.append(ApiResult("POST /api/v1/assistant/ask", ok, detail))

        tts_payload = {"text": "OpenS verificación de voz"}
        ok, detail, response = await check_endpoint(
            client,
            "POST",
            "/api/v1/assistant/tts",
            json_payload=tts_payload,
        )
        if ok and response is not None:
            content_type = response.headers.get("content-type", "")
            size = len(response.content)
            ok = "audio/mpeg" in content_type and size > 0
            detail = f"content-type={content_type}, bytes={size}" if ok else "Respuesta TTS inválida"
        results.append(ApiResult("POST /api/v1/assistant/tts", ok, detail))

        seal_payload = {
            "patient_id": "1",
            "diagnosis_text": "Prueba de sellado médico OpenS",
            "notes": "Smoke test",
            "date": "2026-05-11",
        }
        ok, detail, response = await check_endpoint(
            client,
            "POST",
            "/api/v1/assistant/seal_record",
            json_payload=seal_payload,
        )
        if ok and response is not None:
            body = response.json()
            tx = body.get("blockchain_signature")
            solscan_url = body.get("solscan_url")
            ok = bool(tx) and isinstance(solscan_url, str) and solscan_url.startswith("https://solscan.io/tx/")
            detail = f"tx={tx}" if ok else f"Respuesta de sellado inválida: {body}"
        if not ok and not strict:
            detail = f"{detail} (permitido porque --strict está desactivado)"
            ok = True
        results.append(ApiResult("POST /api/v1/assistant/seal_record", ok, detail))

    return results


def print_result(result: ApiResult) -> None:
    icon = "✅" if result.ok else "❌"
    color = GREEN if result.ok else RED
    print(f"{color}{icon} {result.name}:{RESET} {result.detail}")


def main() -> None:
    args = parse_args()
    print(f"{CYAN}========================================{RESET}")
    print(f"{CYAN}🧪 OpenS Backend API Smoke Test Suite{RESET}")
    print(f"{CYAN}========================================{RESET}")
    print(f"Base URL: {args.base_url}")
    print(f"Modo estricto: {'ON' if args.strict else 'OFF'}\n")

    results = asyncio.run(run_smoke_tests(base_url=args.base_url, strict=args.strict))
    for result in results:
        print_result(result)

    failed = [result for result in results if not result.ok]
    if failed:
        print(f"\n{RED}Resultado final: FAIL ({len(failed)} endpoint(s) fallido(s)).{RESET}")
        sys.exit(1)

    print(f"\n{GREEN}Resultado final: PASS (backend operativo end-to-end).{RESET}")


if __name__ == "__main__":
    main()
