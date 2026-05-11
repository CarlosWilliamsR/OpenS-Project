import json
from pathlib import Path

path = Path("/home/david/Descargas/OpenS Demo/OpenS/backend-ia/solana_service.py")
content = path.read_text()

old_code = """IDL_PATH = Path(__file__).parent.parent / "anchor_program" / "target" / "idl" / "opens_anchor.json"
with open(IDL_PATH, "r") as f:
    IDL = json.load(f)"""

new_code = """IDL = {
    "version": "0.1.0",
    "name": "opens_anchor",
    "instructions": [
        {
            "name": "register_record",
            "accounts": [
                {"name": "record_account", "isMut": True, "isSigner": False},
                {"name": "authority", "isMut": True, "isSigner": True},
                {"name": "system_program", "isMut": False, "isSigner": False},
            ],
            "args": [
                {"name": "patient_id", "type": {"array": ["u8", 32]}},
                {"name": "medical_hash", "type": {"array": ["u8", 32]}},
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
                    {"name": "patient_id", "type": {"array": ["u8", 32]}},
                    {"name": "medical_hash", "type": {"array": ["u8", 32]}},
                    {"name": "doctor_pubkey", "type": "publicKey"},
                    {"name": "timestamp", "type": "i64"},
                ],
            },
        }
    ],
}"""

content = content.replace(old_code, new_code)

# We also need to fix the account names in the Python call to match IDL
content = content.replace('"recordAccount"', '"record_account"')
content = content.replace('"systemProgram"', '"system_program"')

path.write_text(content)
