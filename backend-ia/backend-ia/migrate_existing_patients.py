import asyncio
import os
import time
import json
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm

# Importamos la función de anclaje de Solana que ya está en main.py
from main import register_patient_hash

# Cargamos variables de entorno (.env)
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

LOG_FILE = "migration_log.json"

async def migrate_records():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Las credenciales de Supabase no están configuradas.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print("Obteniendo registros de Supabase sin anclar a la blockchain...")
    
    # 1. Filtrar registros donde transaction_signature es NULL
    try:
        response = supabase.table("medical_records").select("*").is_("transaction_signature", "null").execute()
        records = response.data
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")
        return

    if not records:
        print("¡No hay registros pendientes de migración! Todos están anclados a Solana.")
        return

    print(f"Se encontraron {len(records)} registros para migrar.")

    processed_ids = []
    failed_ids = []

    # Cargamos logs previos por si el script se reinicia
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                prev_logs = json.load(f)
                processed_ids = prev_logs.get("processed", [])
                failed_ids = prev_logs.get("failed", [])
            except json.JSONDecodeError:
                pass

    # Mostrar barra de progreso
    pbar = tqdm(total=len(records), desc="Migrando a Solana", unit="registro")

    for record in records:
        # Extraemos el identificador único de la fila y el patient_id
        record_id = record.get("id")
        patient_id = record.get("patient_id")
        
        # Generar Hash determinista usando los campos clave
        # Nos aseguramos de tener campos básicos para que el hash sea inmutable y único para cada visita
        data_to_hash = {
            "patient_id": patient_id,
            "notes": record.get("notes", ""),
            "date": record.get("date", ""),
            "created_at": record.get("created_at", "")
        }
        
        data_str = json.dumps(data_to_hash, sort_keys=True)
        medical_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()

        try:
            # 2. Llamar a la función existente en main.py para generar transacción
            tx_signature = await register_patient_hash(str(patient_id), medical_hash)

            # 3. Actualizar la fila en Supabase
            update_payload = {
                "transaction_signature": tx_signature,
                "medical_hash": medical_hash # Actualizamos por si también estaba vacío
            }
            
            # Usamos el id de la fila si existe, de lo contrario usamos patient_id (menos preciso)
            if record_id:
                supabase.table("medical_records").update(update_payload).eq("id", record_id).execute()
            else:
                supabase.table("medical_records").update(update_payload).eq("patient_id", patient_id).execute()

            # Guardamos el estado de éxito
            processed_ids.append({
                "patient_id": patient_id,
                "record_id": record_id,
                "tx_signature": tx_signature,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            # Capturamos cualquier error (falla de internet, timeout RPC, error de DB)
            failed_ids.append({
                "patient_id": patient_id,
                "record_id": record_id,
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            })

        pbar.update(1)

        # 4. Escribir log en cada iteración para evitar pérdida de datos si se cae la luz/internet
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "processed": processed_ids, 
                "failed": failed_ids
            }, f, indent=4)

        # 5. Retraso de 2 segundos para evitar Rate Limits del Devnet de Solana
        await asyncio.sleep(2)

    pbar.close()

    print("\n--- Resumen de Migración ---")
    print(f"Registros migrados exitosamente: {len([p for p in processed_ids if p.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))])}")
    print(f"Registros fallidos en esta sesión: {len([f for f in failed_ids if f.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))])}")
    print(f"El log completo se ha guardado en: {LOG_FILE}")

if __name__ == "__main__":
    asyncio.run(migrate_records())
