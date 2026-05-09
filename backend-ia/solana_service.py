import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

from anchorpy import Idl, Program, Provider, Wallet
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.system_program import SYS_PROGRAM_ID

SOLANA_RPC_URL = os.environ.get("SOLANA_RPC_URL", "https://api.devnet.solana.com")
SOLANA_PROGRAM_ID = os.environ.get("SOLANA_PROGRAM_ID", "REPLACE_WITH_PROGRAM_ID")
WALLET_KEYPAIR_PATH = os.environ.get("SOLANA_WALLET_KEYPAIR", "~/.config/solana/id.json")

IDL = {
    "version": "0.1.0",
    "name": "opens_anchor",
    "instructions": [
        {
            "name": "register_record",
            "accounts": [
                {"name": "recordAccount", "isMut": True, "isSigner": False},
                {"name": "authority", "isMut": True, "isSigner": True},
                {"name": "systemProgram", "isMut": False, "isSigner": False},
            ],
            "args": [
                {"name": "patient_id", "type": {"array": "u8", "size": 32}},
                {"name": "medical_hash", "type": {"array": "u8", "size": 32}},
                {"name": "timestamp", "type": "i64"},
            ],
        }
    ],
    "accounts": [
        {
            "name": "MedicalRecord",
            "type": {
                "kind": "struct",
                "fields": [
                    {"name": "patient_id", "type": {"array": "u8", "size": 32}},
                    {"name": "medical_hash", "type": {"array": "u8", "size": 32}},
                    {"name": "doctor_pubkey", "type": "publicKey"},
                    {"name": "timestamp", "type": "i64"},
                ],
            },
        }
    ],
}


def load_keypair(path: str) -> Keypair:
    keypair_path = Path(path).expanduser()
    if not keypair_path.exists():
        raise FileNotFoundError(f"Solana keypair file not found: {keypair_path}")

    with keypair_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, dict) and "secret_key" in payload:
        secret = payload["secret_key"]
    else:
        secret = payload

    secret_bytes = bytes(secret)
    return Keypair.from_secret_key(secret_bytes)


def normalize_patient_id(patient_id: Union[str, int]) -> bytes:
    """Deterministically normalize a patient identifier into a 32-byte hash."""
    raw = str(patient_id).encode("utf-8")
    return hashlib.sha256(raw).digest()


def compute_diagnosis_hash(diagnosis_text: str) -> bytes:
    return hashlib.sha256(diagnosis_text.encode("utf-8")).digest()


def get_provider() -> Provider:
    if SOLANA_PROGRAM_ID == "REPLACE_WITH_PROGRAM_ID":
        raise ValueError(
            "Set the SOLANA_PROGRAM_ID environment variable to your deployed Anchor program ID."
        )

    wallet = Wallet(load_keypair(WALLET_KEYPAIR_PATH))
    client = Client(SOLANA_RPC_URL)
    return Provider(client, wallet)


def get_program() -> Program:
    program_id = PublicKey(SOLANA_PROGRAM_ID)
    idl = Idl.from_json(IDL)
    return Program(idl, program_id, get_provider())


def derive_record_address(patient_id: Union[str, int]) -> PublicKey:
    patient_id_hash = normalize_patient_id(patient_id)
    return PublicKey.find_program_address([b"record", patient_id_hash], PublicKey(SOLANA_PROGRAM_ID))[0]


def seal_diagnosis_on_chain(patient_id: Union[str, int], diagnosis_text: str) -> Dict[str, Any]:
    """Seal the diagnosis on Solana Devnet and return PDA + transaction metadata."""
    program = get_program()
    patient_id_hash = normalize_patient_id(patient_id)
    medical_hash = compute_diagnosis_hash(diagnosis_text)

    record_pda, _ = PublicKey.find_program_address(
        [b"record", patient_id_hash],
        program.program_id,
    )

    tx_signature = program.rpc["register_record"](
        list(patient_id_hash),
        list(medical_hash),
        int(time.time()),
        ctx={
            "accounts": {
                "recordAccount": record_pda,
                "authority": program.provider.wallet.public_key,
                "systemProgram": SYS_PROGRAM_ID,
            }
        },
    )

    return {
        "tx_signature": tx_signature,
        "record_pda": str(record_pda),
        "medical_hash": medical_hash.hex(),
        "patient_id_hash": patient_id_hash.hex(),
    }
